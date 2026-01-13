"""Toast提醒组件"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QGuiApplication, QFontMetrics


class ToastWidget(QWidget):
    """Toast提醒窗口（屏幕中央显示）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self._fade_out)
        self.fade_animation = None

    def _init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowTransparentForInput
        )

        # 设置半透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # 创建标签
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(
            """
            QLabel {
                background-color: rgba(255, 255, 255, 240);
                color: #555555;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
        """
        )
        layout.addWidget(self.label)

        # 初始隐藏
        self.setWindowOpacity(0)

    def show_message(self, label: str, value: str, duration: int = 5000):
        """
        显示Toast消息

        Args:
            label: 标签名称
            value: 值内容
            duration: 显示时长（毫秒）
        """
        # 设置文本（三行）
        text = (
            f"已复制: {label}\n"
            f"内容: {value[:50]}{'...' if len(value) > 50 else ''}\n"
            f"请使用Ctrl+V复制到对应表格"
        )
        self.label.setText(text)

        # 动态计算窗口高度以适应三行文本
        font_metrics = QFontMetrics(self.label.font())
        line_height = font_metrics.lineSpacing()
        line_count = text.count("\n") + 1
        # 文本高度 + padding + 布局边距
        required_height = line_count * line_height + 64
        window_height = max(required_height, 120)
        self.setFixedSize(300, window_height)

        # 居中显示
        self._center_on_screen()

        # 显示窗口
        self.show()

        # 淡入动画
        self._fade_in()

        # 设置定时器
        self.timer.stop()
        self.timer.start(duration)

    def _center_on_screen(self):
        """居中显示在屏幕上"""
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def _fade_in(self):
        """淡入动画"""
        if self.fade_animation:
            self.fade_animation.stop()

        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_animation.start()

    def _fade_out(self):
        """淡出动画"""
        if self.fade_animation:
            self.fade_animation.stop()

        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()
