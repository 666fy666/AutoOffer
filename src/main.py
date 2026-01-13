"""主程序入口"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Signal

from src.core.resume_manager import ResumeManager
from src.core.ocr import OCRProcessor
from src.core.matcher import LabelMatcher
from src.core.clipboard import copy_to_clipboard
from src.gui.main_window import MainWindow
from src.gui.screenshot_widget import ScreenshotWidget
from src.gui.resume_editor import ResumeEditorDialog
from src.gui.selection_dialog import SelectionDialog
from src.gui.toast import ToastWidget
from src.utils.hotkey import HotkeyManager
from src.utils.logger import get_logger
from src.utils.resource import ensure_resource_dir

logger = get_logger(__name__)


class OCRWorker(QThread):
    """OCR工作线程"""

    finished = Signal(str)  # 传递识别结果文本
    error = Signal(str)  # 传递错误信息

    def __init__(self, image, ocr_processor):
        super().__init__()
        self.image = image
        self.ocr_processor = ocr_processor

    def run(self):
        """执行OCR识别"""
        try:
            # 识别图片中的文字
            text = self.ocr_processor.recognize_text(self.image)
            self.finished.emit(text)
        except Exception as e:
            self.error.emit(str(e))


class Application:
    """应用程序主类"""

    def __init__(self):
        # 初始化Qt应用
        self.app = QApplication(sys.argv)

        # 初始化核心组件
        self.resume_manager = ResumeManager()
        self.ocr_processor = OCRProcessor()
        self.matcher = LabelMatcher(self.resume_manager, threshold=0.5)
        self.hotkey_manager = HotkeyManager()

        # 初始化GUI组件
        self.main_window = MainWindow(self.resume_manager)
        self.screenshot_widget = None
        self.toast_widget = ToastWidget()

        # 连接信号
        self._connect_signals()

        # 注册全局快捷键
        self._register_hotkey()

    def _connect_signals(self):
        """连接信号和槽"""
        # 主窗口信号
        self.main_window.screenshot_requested.connect(
            self._show_screenshot
        )
        self.main_window.edit_resume_requested.connect(
            self._show_resume_editor
        )
        # 主窗口内的通知会自动更新（通过信号槽连接）

    def _register_hotkey(self):
        """注册全局快捷键"""

        def on_hotkey():
            # 在主线程中显示截图窗口
            self.main_window.screenshot_requested.emit()

        if not self.hotkey_manager.register("alt+c", on_hotkey):
            logger.error("全局快捷键 Alt+C 注册失败")

    def _show_screenshot(self):
        """显示截图窗口"""
        if self.screenshot_widget is None:
            self.screenshot_widget = ScreenshotWidget()
            self.screenshot_widget.screenshot_taken.connect(
                self._on_screenshot_taken
            )

        self.screenshot_widget.show()
        self.screenshot_widget.raise_()
        # 注意：不调用 activateWindow()，避免在某些系统上最小化当前活动窗口
        # raise_() 已经足够将置顶窗口显示在最前面

    def _on_screenshot_taken(self, image):
        """截图完成回调"""
        # 创建OCR工作线程
        self.ocr_worker = OCRWorker(image, self.ocr_processor)
        self.ocr_worker.finished.connect(self._on_ocr_finished)
        self.ocr_worker.error.connect(self._on_ocr_error)
        self.ocr_worker.finished.connect(self.ocr_worker.deleteLater)
        self.ocr_worker.error.connect(self.ocr_worker.deleteLater)

        # 更新状态
        self.main_window.statusBar().showMessage("正在识别文字...")

        # 启动线程
        self.ocr_worker.start()

    def _on_ocr_finished(self, text: str):
        """OCR识别完成"""
        # 记录识别结果到日志
        logger.info(f"OCR识别结果: {text}")

        # 在主界面显示识别结果
        self.main_window.show_ocr_result(text)

        if not text:
            logger.warning("未识别到文字")
            self.main_window.statusBar().showMessage("未识别到文字", 3000)
            return

        # 匹配标签
        matches = self.matcher.match(text)

        if not matches:
            logger.warning(f"未找到匹配的标签，识别文本: {text}")
            self.main_window.statusBar().showMessage("未找到匹配的标签", 3000)
            return

        # 记录匹配结果到日志
        logger.info(f"找到 {len(matches)} 个匹配结果:")
        for label, value, similarity in matches:
            logger.info(f"  - {label}: {value} (相似度: {similarity:.1%})")

        # 处理匹配结果
        if len(matches) == 1:
            # 单个匹配，直接复制
            label, value, similarity = matches[0]
            logger.info(f"自动复制: {label} = {value}")
            self._copy_and_notify(label, value)
        else:
            # 多个匹配，显示选择对话框
            self._show_selection_dialog(matches)

    def _on_ocr_error(self, error_msg: str):
        """OCR识别错误"""
        logger.error(f"OCR识别失败: {error_msg}")
        self.main_window.statusBar().showMessage(f"OCR识别失败: {error_msg}", 5000)

    def _show_selection_dialog(self, matches):
        """显示选择对话框"""
        dialog = SelectionDialog(matches, self.main_window)
        dialog.item_selected.connect(
            lambda label, value: self._copy_and_notify(label, value)
        )
        dialog.exec()

    def _copy_and_notify(self, label: str, value: str):
        """复制到剪切板并显示通知"""
        # 复制到剪切板
        if copy_to_clipboard(value):
            # 显示Toast通知（屏幕中央）
            self.toast_widget.show_message(label, value, duration=5000)

            # 更新主窗口通知
            self.main_window.show_notification.emit(label, value)

            # 刷新简历列表
            self.main_window.refresh_resume_list()
        else:
            logger.error("复制到剪切板失败")
            self.main_window.statusBar().showMessage("复制失败", 3000)

    def _show_resume_editor(self):
        """显示简历编辑窗口"""
        dialog = ResumeEditorDialog(self.resume_manager, self.main_window)
        dialog.resume_updated.connect(self.main_window.refresh_resume_list)
        dialog.exec()

    def run(self):
        """运行应用"""
        # 显示主窗口
        self.main_window.show()

        # 运行应用
        sys.exit(self.app.exec())


def main():
    """主函数"""
    # 确保资源目录存在（仅在开发环境中）
    ensure_resource_dir()
    
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
