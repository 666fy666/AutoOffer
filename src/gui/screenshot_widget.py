"""截图窗口组件"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QBuffer, QIODevice
from PySide6.QtGui import QPainter, QColor, QPen, QGuiApplication, QPixmap
from PIL import Image
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ScreenshotWidget(QWidget):
    """截图窗口（类似微信截图）"""

    # 信号：截图完成
    screenshot_taken = Signal(object)  # 传递PIL Image对象

    def __init__(self):
        super().__init__()
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_selecting = False
        self.screenshot_pixmap = None
        self.virtual_geometry = QRect()  # 虚拟桌面几何信息
        self._init_ui()
        self._capture_screen()

    def _init_ui(self):
        """初始化UI"""
        # 设置窗口为全屏、无边框、置顶
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.FramelessWindowHint
            | Qt.Tool
        )

        # 设置窗口为半透明
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 获取所有屏幕并计算虚拟桌面区域
        screens = QGuiApplication.screens()
        if screens:
            # 计算所有屏幕的联合区域（虚拟桌面）
            self.virtual_geometry = QRect()
            for screen in screens:
                screen_geometry = screen.geometry()
                self.virtual_geometry = (
                    self.virtual_geometry.united(screen_geometry)
                )

            # 设置窗口大小为虚拟桌面大小
            self.setGeometry(self.virtual_geometry)

        # 设置鼠标跟踪
        self.setMouseTracking(True)

    def _capture_screen(self):
        """捕获屏幕（包括所有显示器）"""
        screens = QGuiApplication.screens()
        if not screens:
            logger.error("未找到屏幕")
            return

        # 计算所有屏幕的联合区域（虚拟桌面）
        virtual_geometry = QRect()
        for screen in screens:
            screen_geometry = screen.geometry()
            virtual_geometry = virtual_geometry.united(screen_geometry)

        # 找到最大DPI的屏幕作为基准
        max_dpr = 1.0
        for screen in screens:
            dpr = screen.devicePixelRatio()
            if dpr > max_dpr:
                max_dpr = dpr

        virtual_width = virtual_geometry.width()
        virtual_height = virtual_geometry.height()

        # 创建高分辨率画布（实际像素尺寸 = 逻辑尺寸 × DPR）
        actual_width = int(virtual_width * max_dpr)
        actual_height = int(virtual_height * max_dpr)
        virtual_pixmap = QPixmap(actual_width, actual_height)
        virtual_pixmap.setDevicePixelRatio(max_dpr)
        virtual_pixmap.fill(QColor(0, 0, 0))

        # 捕获每个屏幕并拼接到虚拟桌面
        painter = QPainter(virtual_pixmap)
        # 禁用平滑变换和抗锯齿以保持清晰度
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        for screen in screens:
            screen_geometry = screen.geometry()
            dpr = screen.devicePixelRatio()

            # 捕获整个屏幕的截图
            # grabWindow(0) 会捕获整个屏幕，返回的QPixmap已经包含了高分辨率数据
            screen_pixmap = screen.grabWindow(0)

            # 计算该屏幕在虚拟桌面中的位置（使用实际像素坐标）
            x_offset = int(
                (screen_geometry.x() - virtual_geometry.x()) * max_dpr
            )
            y_offset = int(
                (screen_geometry.y() - virtual_geometry.y()) * max_dpr
            )

            # 计算目标尺寸（使用最大DPI）
            target_width = int(screen_geometry.width() * max_dpr)
            target_height = int(screen_geometry.height() * max_dpr)

            # 如果屏幕的DPI与最大DPI不同，需要将截图缩放到目标尺寸
            # 但保持原始分辨率，不进行平滑缩放
            if (
                abs(screen_pixmap.width() - target_width) > 1
                or abs(screen_pixmap.height() - target_height) > 1
            ):
                # 使用最近邻插值进行缩放以保持清晰度
                scaled_pixmap = screen_pixmap.scaled(
                    target_width,
                    target_height,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    # 使用快速变换（最近邻）而不是平滑变换
                    Qt.TransformationMode.FastTransformation,
                )
                scaled_pixmap.setDevicePixelRatio(max_dpr)
                screen_pixmap = scaled_pixmap
            else:
                # 直接使用，但设置正确的DPI
                screen_pixmap.setDevicePixelRatio(max_dpr)

            # 将截图绘制到虚拟桌面的对应位置（不进行缩放）
            painter.drawPixmap(x_offset, y_offset, screen_pixmap)

        painter.end()

        self.screenshot_pixmap = virtual_pixmap
        self.max_dpr = max_dpr  # 保存最大DPI用于坐标转换

    def paintEvent(self, event):
        """绘制事件"""
        if self.screenshot_pixmap is None:
            return

        painter = QPainter(self)
        # 禁用平滑变换以保持清晰度
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # 先绘制正常的截图作为背景（不进行缩放，保持原始分辨率）
        painter.drawPixmap(self.rect(), self.screenshot_pixmap)

        # 绘制半透明的灰色遮罩层（覆盖整个屏幕）
        # 黑色，更高透明度（80/255 ≈ 31%）
        overlay_color = QColor(0, 0, 0, 80)
        painter.fillRect(self.rect(), overlay_color)

        # 如果有选择区域，在选择区域绘制正常颜色的截图（覆盖遮罩）
        if not self.start_point.isNull() and not self.end_point.isNull():
            # 计算选择区域（逻辑坐标）
            rect = QRect(self.start_point, self.end_point).normalized()

            # 将逻辑坐标转换为实际像素坐标（考虑DPI）
            # screenshot_pixmap 有 devicePixelRatio，所以需要转换
            dpr = self.screenshot_pixmap.devicePixelRatio()
            source_x = int(rect.x() * dpr)
            source_y = int(rect.y() * dpr)
            source_width = int(rect.width() * dpr)
            source_height = int(rect.height() * dpr)
            source_rect = QRect(
                source_x, source_y, source_width, source_height
            )

            # 在选择区域绘制正常颜色的截图（覆盖遮罩）
            painter.drawPixmap(rect, self.screenshot_pixmap, source_rect)

            # 绘制选择框边框 - 低饱和度小清新配色
            pen = QPen(QColor(168, 213, 186), 2)  # 淡绿色边框
            painter.setPen(pen)
            painter.drawRect(rect)

            # 绘制四个角的标记
            corner_size = 8
            pen.setWidth(3)
            painter.setPen(pen)

            # 左上角
            painter.drawLine(
                rect.left(),
                rect.top(),
                rect.left() + corner_size,
                rect.top(),
            )
            painter.drawLine(
                rect.left(),
                rect.top(),
                rect.left(),
                rect.top() + corner_size,
            )

            # 右上角
            painter.drawLine(
                rect.right() - corner_size,
                rect.top(),
                rect.right(),
                rect.top(),
            )
            painter.drawLine(
                rect.right(),
                rect.top(),
                rect.right(),
                rect.top() + corner_size,
            )

            # 左下角
            painter.drawLine(
                rect.left(),
                rect.bottom() - corner_size,
                rect.left(),
                rect.bottom(),
            )
            painter.drawLine(
                rect.left(),
                rect.bottom(),
                rect.left() + corner_size,
                rect.bottom(),
            )

            # 右下角
            painter.drawLine(
                rect.right() - corner_size,
                rect.bottom(),
                rect.right(),
                rect.bottom(),
            )
            painter.drawLine(
                rect.right(),
                rect.bottom() - corner_size,
                rect.right(),
                rect.bottom(),
            )

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.start_point = event.position().toPoint()
            self.end_point = self.start_point
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_selecting:
            self.end_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.end_point = event.position().toPoint()
            self.is_selecting = False

            # 计算选择区域
            rect = QRect(self.start_point, self.end_point).normalized()

            # 如果选择区域有效，截取图片
            if rect.width() > 10 and rect.height() > 10:
                self._capture_selection(rect)

            # 关闭窗口
            self.close()

    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key_Escape:
            # ESC取消截图
            self.close()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Enter确认截图
            if not self.start_point.isNull() and not self.end_point.isNull():
                rect = QRect(self.start_point, self.end_point).normalized()
                if rect.width() > 10 and rect.height() > 10:
                    self._capture_selection(rect)
            self.close()
        else:
            super().keyPressEvent(event)

    def _capture_selection(self, rect: QRect):
        """截取选择区域"""
        if self.screenshot_pixmap is None:
            logger.error("截图数据为空，无法截取选择区域")
            return

        try:
            # rect 是逻辑坐标，需要转换为实际像素坐标
            dpr = self.screenshot_pixmap.devicePixelRatio()
            actual_x = int(rect.x() * dpr)
            actual_y = int(rect.y() * dpr)
            actual_width = int(rect.width() * dpr)
            actual_height = int(rect.height() * dpr)

            # 确保坐标在有效范围内
            pixmap_actual_width = self.screenshot_pixmap.width()
            pixmap_actual_height = self.screenshot_pixmap.height()

            if actual_x < 0:
                actual_x = 0
            if actual_y < 0:
                actual_y = 0
            if actual_x + actual_width > pixmap_actual_width:
                actual_width = pixmap_actual_width - actual_x
            if actual_y + actual_height > pixmap_actual_height:
                actual_height = pixmap_actual_height - actual_y

            # 从截图中提取选择区域（使用实际像素坐标）
            adjusted_rect = QRect(
                actual_x, actual_y, actual_width, actual_height
            )
            selected_pixmap = self.screenshot_pixmap.copy(adjusted_rect)

            # 转换为PIL Image
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            selected_pixmap.save(buffer, format="PNG")
            buffer.close()

            # 从QBuffer获取字节数据并转换为PIL Image
            byte_array = buffer.data()
            # QByteArray转换为bytes
            from io import BytesIO

            # 将QByteArray转换为bytes（PySide6中QByteArray可以直接转换为bytes）
            image_bytes = bytes(byte_array)
            pil_image: Image.Image = Image.open(BytesIO(image_bytes))
            pil_image = pil_image.convert("RGB")

            # 发送信号
            self.screenshot_taken.emit(pil_image)
        except Exception as e:
            logger.error(f"截取选择区域失败: {e}", exc_info=True)
