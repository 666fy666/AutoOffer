"""主窗口GUI"""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QFrame,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QGuiApplication, QFontMetrics
from ..core.resume_manager import ResumeManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """主窗口"""

    # 信号：需要显示截图窗口
    screenshot_requested = Signal()
    # 信号：需要编辑简历
    edit_resume_requested = Signal()
    # 信号：显示最新提醒
    show_notification = Signal(str, str)  # label, value
    # 信号：显示OCR识别结果
    show_ocr_result_signal = Signal(str)  # ocr_text

    def __init__(self, resume_manager: ResumeManager):
        super().__init__()
        self.resume_manager = resume_manager
        self._init_ui()
        self._load_resume_data()

    def _init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowTitle("简历填充助手")
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        # 手机比例尺寸 (300x580)
        self.setFixedSize(300, 580)

        # 设置窗口位置到屏幕右侧
        self._position_window_right()

        # 设置样式 - 低饱和度小清新配色
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #FAFAFA;
            }
            QPushButton {
                background-color: #A8D5BA;
                color: #555555;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #95C5A6;
            }
            QPushButton:pressed {
                background-color: #85B596;
            }
            QListWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
            }
            QListWidgetItem {
                padding: 8px;
                border-bottom: 1px solid #F0F0F0;
                color: #555555;
            }
            QListWidgetItem:hover {
                background-color: #F5F5F5;
            }
            QLabel {
                color: #555555;
            }
        """
        )

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # 标题
        title_label = QLabel("简历填充助手")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # 最新提醒区域
        notification_frame = QFrame()
        notification_frame.setFrameShape(QFrame.Box)
        notification_frame.setStyleSheet(
            """
            QFrame {
                background-color: #E8F4ED;
                border: 1px solid #C8E6D5;
                border-radius: 6px;
                padding: 8px;
            }
        """
        )
        notification_layout = QVBoxLayout(notification_frame)
        notification_layout.setContentsMargins(8, 8, 8, 8)

        notification_title = QLabel("最新提醒")
        notification_title.setStyleSheet("font-weight: bold; color: #6B9B7A;")
        notification_layout.addWidget(notification_title)

        self.notification_label = QLabel("暂无提醒")
        self.notification_label.setWordWrap(True)
        # 设置对齐方式，确保多行文本正确显示
        self.notification_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignTop
        )
        # 设置大小策略，允许垂直扩展以显示多行文本
        self.notification_label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding
        )
        # 设置最小高度，确保能显示多行文本
        self.notification_label.setMinimumHeight(60)
        self.notification_label.setStyleSheet(
            "color: #777777; font-size: 12px;"
        )
        notification_layout.addWidget(self.notification_label)

        main_layout.addWidget(notification_frame)

        # 简历信息列表
        list_label = QLabel("简历信息")
        list_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(list_label)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("border: none;")

        self.resume_list = QListWidget()
        self.resume_list.setAlternatingRowColors(True)
        scroll_area.setWidget(self.resume_list)

        main_layout.addWidget(scroll_area, stretch=1)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.edit_btn = QPushButton("编辑简历")
        self.edit_btn.clicked.connect(self._on_edit_clicked)
        button_layout.addWidget(self.edit_btn)

        self.screenshot_btn = QPushButton("截图识别 (Alt+C)")
        self.screenshot_btn.clicked.connect(self._on_screenshot_clicked)
        self.screenshot_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #B8D4E3;
                color: #555555;
            }
            QPushButton:hover {
                background-color: #A8C4D3;
            }
        """
        )
        button_layout.addWidget(self.screenshot_btn)

        main_layout.addLayout(button_layout)

        # 状态栏
        self.statusBar().showMessage("就绪")

        # 连接信号
        self.show_notification.connect(self._update_notification)
        self.show_ocr_result_signal.connect(self._update_ocr_result)

    def _position_window_right(self):
        """将窗口定位到屏幕右侧"""
        # 获取主屏幕的几何信息
        primary_screen = QGuiApplication.primaryScreen()
        if primary_screen:
            screen_geometry = primary_screen.availableGeometry()
            window_width = self.width()

            # 计算右侧位置（留出一些边距）
            margin = 20
            x = screen_geometry.right() - window_width - margin
            y = screen_geometry.top() + margin

            # 设置窗口位置
            self.move(x, y)

    def _load_resume_data(self):
        """加载简历数据到列表"""
        self.resume_list.clear()
        resume_data = self.resume_manager.get_all_fields()

        for label, value in resume_data.items():
            if value:  # 只显示有值的字段
                # 如果值包含换行符，在第一个字符前添加换行以保持对齐
                if "\n" in value:
                    item_text = f"{label}:\n{value}"
                else:
                    item_text = f"{label}: {value}"
                item = QListWidgetItem(item_text)
                self.resume_list.addItem(item)

    def _on_edit_clicked(self):
        """编辑按钮点击"""
        self.edit_resume_requested.emit()

    def _on_screenshot_clicked(self):
        """截图按钮点击"""
        self.screenshot_requested.emit()

    def _update_notification(self, label: str, value: str):
        """更新提醒显示"""
        notification_text = (
            f"已复制: {label}\n"
            f"内容: {value[:50]}{'...' if len(value) > 50 else ''}\n"
            f"请使用Ctrl+V复制到对应表格"
        )
        self.notification_label.setText(notification_text)

        # 动态调整高度以适应三行文本
        font_metrics = QFontMetrics(self.notification_label.font())
        line_height = font_metrics.lineSpacing()
        line_count = notification_text.count("\n") + 1
        required_height = line_count * line_height + 20
        min_height = max(required_height, 90)
        self.notification_label.setMinimumHeight(min_height)

        # 更新布局
        self.notification_label.updateGeometry()
        parent = self.notification_label.parent()
        if parent:
            parent.updateGeometry()
            layout = parent.layout()
            if layout:
                layout.invalidate()
                layout.update()

        self.statusBar().showMessage(f"已复制 {label} 到剪切板", 3000)

    def refresh_resume_list(self):
        """刷新简历列表"""
        self._load_resume_data()

    def show_ocr_result(self, ocr_text: str):
        """显示OCR识别结果（外部调用）"""
        self.show_ocr_result_signal.emit(ocr_text)

    def _update_ocr_result(self, ocr_text: str):
        """更新OCR识别结果显示"""
        if ocr_text:
            # 限制显示长度，避免过长
            display_text = (
                ocr_text[:100] + "..." if len(ocr_text) > 100 else ocr_text
            )
            notification_text = f"识别结果:\n{display_text}"
            self.notification_label.setText(notification_text)
            self.statusBar().showMessage(f"OCR识别完成: {display_text}", 5000)
        else:
            self.notification_label.setText("识别结果: 未识别到文字")
            self.statusBar().showMessage("未识别到文字", 3000)
