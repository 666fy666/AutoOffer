"""多匹配选择对话框"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QScrollArea,
    QWidget,
)
from PySide6.QtCore import Signal
from typing import List, Tuple


class SelectionDialog(QDialog):
    """多匹配选择对话框"""

    # 信号：选择了某个匹配项
    item_selected = Signal(str, str)  # label, value

    def __init__(self, matches: List[Tuple[str, str, float]], parent=None):
        """
        初始化对话框

        Args:
            matches: 匹配结果列表，每个元素为(标签, 值, 相似度)
            parent: 父窗口
        """
        super().__init__(parent)
        self.matches = matches
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("多个匹配结果")
        self.setMinimumSize(400, 300)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # 提示标签
        info_label = QLabel(
            f"找到 {len(self.matches)} 个匹配结果，请选择："
        )
        info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(info_label)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        # 创建内容部件
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(8)

        # 添加每个匹配项
        for label, value, similarity in self.matches:
            item_widget = self._create_match_item(label, value, similarity)
            content_layout.addWidget(item_widget)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        main_layout.addWidget(cancel_btn)

        # 设置样式 - 低饱和度小清新配色
        self.setStyleSheet(
            """
            QDialog {
                background-color: #FAFAFA;
            }
            QPushButton {
                background-color: #A8D5BA;
                color: #555555;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #95C5A6;
            }
            QLabel {
                color: #555555;
            }
        """
        )

    def _create_match_item(
        self, label: str, value: str, similarity: float
    ) -> QWidget:
        """创建匹配项部件"""
        item_widget = QWidget()
        item_widget.setStyleSheet(
            """
            QWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px;
            }
        """
        )

        layout = QVBoxLayout(item_widget)
        layout.setSpacing(4)

        # 标签和相似度
        header_layout = QHBoxLayout()

        label_widget = QLabel(f"<b>{label}</b>")
        label_widget.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(label_widget)

        similarity_label = QLabel(f"相似度: {similarity:.1%}")
        similarity_label.setStyleSheet("color: #777777; font-size: 12px;")
        header_layout.addWidget(similarity_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 值
        value_label = QLabel(value)
        value_label.setWordWrap(True)
        value_label.setStyleSheet(
            "color: #555555; font-size: 12px; padding: 4px;"
        )
        layout.addWidget(value_label)

        # 复制按钮
        copy_btn = QPushButton("复制")
        copy_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #B8D4E3;
                color: #555555;
                font-size: 12px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #A8C4D3;
            }
        """
        )
        copy_btn.clicked.connect(lambda: self._on_copy_clicked(label, value))
        layout.addWidget(copy_btn)

        return item_widget

    def _on_copy_clicked(self, label: str, value: str):
        """复制按钮点击"""
        self.item_selected.emit(label, value)
        self.accept()
