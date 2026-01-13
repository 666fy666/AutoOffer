"""简历编辑窗口"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QLineEdit,
    QLabel,
    QStyledItemDelegate,
    QPlainTextEdit,
    QStyleOptionViewItem,
)
from PySide6.QtCore import (
    Qt,
    Signal,
    QModelIndex,
    QRect,
    QSize,
    QPersistentModelIndex,
)
from PySide6.QtGui import QPainter, QTextDocument, QShowEvent
from typing import Tuple, Dict
from ..core.resume_manager import ResumeManager
from ..utils.distance import find_best_matches


class MultiLineDisplayDelegate(QStyledItemDelegate):
    """支持多行文本显示的委托（仅用于显示，不支持编辑）"""

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ):
        """绘制多行文本"""
        if index.column() == 1:  # 只对"值"列使用多行显示
            text = index.data(Qt.ItemDataRole.DisplayRole)
            if text and "\n" in str(text):
                # 使用QTextDocument来绘制多行文本
                painter.save()

                # 设置绘制区域
                rect = option.rect.adjusted(
                    4, 4, -4, -4
                )  # type: ignore[attr-defined]
                painter.setClipRect(rect)

                # 创建文本文档
                doc = QTextDocument()
                doc.setPlainText(str(text))
                doc.setTextWidth(rect.width())

                # 设置文档样式
                doc.setDefaultStyleSheet(
                    """
                    body {
                        font-size: 12px;
                        color: #555555;
                    }
                """
                )

                # 绘制文档
                painter.translate(rect.topLeft())
                doc.drawContents(
                    painter, QRect(0, 0, rect.width(), rect.height())
                )
                painter.restore()
            else:
                # 单行文本使用默认绘制
                super().paint(painter, option, index)
        else:
            # 其他列使用默认绘制
            super().paint(painter, option, index)

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QSize:
        """计算单元格大小"""
        if index.column() == 1:  # 只对"值"列计算多行高度
            text = index.data(Qt.ItemDataRole.DisplayRole)
            if text and "\n" in str(text):
                # 使用QTextDocument计算多行文本的高度
                doc = QTextDocument()
                doc.setPlainText(str(text))
                # 减去左右边距
                doc.setTextWidth(
                    option.rect.width() - 8
                )  # type: ignore[attr-defined]

                # 计算所需高度
                height = int(doc.size().height()) + 8  # 加上上下边距
                return QSize(
                    option.rect.width(), max(30, height)
                )  # type: ignore[attr-defined]

        # 其他情况使用默认大小
        return super().sizeHint(option, index)


class FieldEditDialog(QDialog):
    """字段编辑对话框"""

    def __init__(self, label: str, value: str, parent=None):
        super().__init__(parent)
        self.original_label = label
        self.original_value = value
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("编辑字段")
        self.setMinimumSize(500, 400)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # 标签输入
        label_layout = QVBoxLayout()
        label_layout.addWidget(QLabel("标签:"))
        self.label_input = QLineEdit()
        self.label_input.setText(self.original_label)
        label_layout.addWidget(self.label_input)
        main_layout.addLayout(label_layout)

        # 值输入（多行）
        value_layout = QVBoxLayout()
        value_layout.addWidget(QLabel("值:"))
        self.value_input = QPlainTextEdit()
        self.value_input.setPlainText(self.original_value)
        self.value_input.setPlaceholderText("支持多行输入，直接按Enter键换行")
        value_layout.addWidget(self.value_input)
        main_layout.addLayout(value_layout)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        main_layout.addLayout(button_layout)

        # 设置样式 - 低饱和度小清新配色
        self.setStyleSheet(
            """
            QDialog {
                background-color: #FAFAFA;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #555555;
            }
            QPlainTextEdit {
                padding: 8px;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #555555;
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

        # 设置值输入框为焦点，并在对话框显示后将光标移动到末尾
        self.value_input.setFocus()

    def showEvent(self, event: QShowEvent) -> None:
        """对话框显示事件 - 将光标移动到值输入框的末尾"""
        super().showEvent(event)
        # 将光标移动到文本末尾
        cursor = self.value_input.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.value_input.setTextCursor(cursor)
        # 确保值输入框获得焦点
        self.value_input.setFocus()

    def get_data(self) -> Tuple[str, str]:
        """获取编辑后的数据"""
        label = self.label_input.text().strip()
        value = self.value_input.toPlainText()
        # 去除首尾空白行，但保留中间的换行
        if value:
            lines = value.split("\n")
            # 去除开头的空行
            while lines and not lines[0].strip():
                lines.pop(0)
            # 去除结尾的空行
            while lines and not lines[-1].strip():
                lines.pop()
            value = "\n".join(lines)
        return label, value


class ResumeEditorDialog(QDialog):
    """简历编辑对话框"""

    # 信号：简历已更新
    resume_updated = Signal()

    def __init__(self, resume_manager: ResumeManager, parent=None):
        super().__init__(parent)
        self.resume_manager = resume_manager
        self.all_resume_data: Dict[str, str] = {}  # 保存所有原始数据
        self._init_ui()
        self._load_resume_data()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("编辑简历")
        self.setMinimumSize(500, 600)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # 说明标签
        info_label = QLabel(
            "双击记录打开编辑窗口，右键可删除"
        )
        info_label.setStyleSheet("color: #777777; font-size: 12px;")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        # 搜索框区域
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索标签:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词进行模糊查找...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["标签", "值"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        # 禁用直接编辑，改为双击打开对话框
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # 为"值"列设置多行文本显示委托（仅用于显示）
        self.table.setItemDelegateForColumn(
            1, MultiLineDisplayDelegate(self)
        )

        main_layout.addWidget(self.table)

        # 添加字段区域
        add_layout = QHBoxLayout()

        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("标签名称")
        add_layout.addWidget(QLabel("标签:"))
        add_layout.addWidget(self.label_input)

        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("值")
        add_layout.addWidget(QLabel("值:"))
        add_layout.addWidget(self.value_input)

        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self._on_add_clicked)
        add_layout.addWidget(add_btn)

        main_layout.addLayout(add_layout)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        main_layout.addLayout(button_layout)

        # 设置样式 - 低饱和度小清新配色
        self.setStyleSheet(
            """
            QDialog {
                background-color: #FAFAFA;
            }
            QTableWidget {
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                background-color: #FFFFFF;
                color: #555555;
            }
            QTableWidgetItem {
                padding: 4px;
                color: #555555;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                color: #555555;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #E0E0E0;
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
            QLineEdit {
                padding: 6px;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                background-color: #FFFFFF;
                color: #555555;
            }
            QPlainTextEdit {
                padding: 4px;
                border: 1px solid #A8D5BA;
                border-radius: 6px;
                background-color: #FFFFFF;
                color: #555555;
            }
            QLabel {
                color: #555555;
            }
        """
        )

    def _load_resume_data(self, filter_query: str = ""):
        """加载简历数据到表格"""
        self.all_resume_data = self.resume_manager.get_all_fields()

        # 如果有搜索条件，进行过滤
        if filter_query:
            filtered_data = self._filter_resume_data(filter_query)
        else:
            filtered_data = self.all_resume_data

        self.table.setRowCount(len(filtered_data))

        for row, (label, value) in enumerate(filtered_data.items()):
            # 标签列（不可编辑）
            label_item = QTableWidgetItem(label)
            label_item.setFlags(
                label_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            self.table.setItem(row, 0, label_item)

            # 值列 - 支持多行显示（不可编辑）
            value_item = QTableWidgetItem(value)
            value_item.setFlags(
                value_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            self.table.setItem(row, 1, value_item)

        # 根据内容自动调整行高（委托的sizeHint会自动计算多行文本的高度）
        self.table.resizeRowsToContents()

    def _filter_resume_data(self, query: str) -> dict:
        """根据查询条件过滤简历数据"""
        query = query.strip()
        if not query:
            return self.all_resume_data

        # 获取所有标签
        all_labels = list(self.all_resume_data.keys())

        # 进行模糊匹配
        matches = find_best_matches(query, all_labels, threshold=0.3)

        # 提取匹配的标签
        matched_labels = {label for label, _ in matches}

        # 返回匹配的字段
        filtered_data = {
            label: value
            for label, value in self.all_resume_data.items()
            if label in matched_labels
        }

        return filtered_data

    def _on_search_changed(self, text: str):
        """搜索框内容改变时，过滤表格显示"""
        self._load_resume_data(filter_query=text)

    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """表格项双击事件 - 打开编辑对话框"""
        row = item.row()
        label_item = self.table.item(row, 0)
        value_item = self.table.item(row, 1)

        if label_item and value_item:
            label = label_item.text()
            value = value_item.text()

            # 打开编辑对话框
            dialog = FieldEditDialog(label, value, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_label, new_value = dialog.get_data()

                if not new_label:
                    QMessageBox.warning(self, "警告", "标签不能为空")
                    return

                # 如果标签改变了，检查新标签是否已存在
                if (
                    new_label != label
                    and new_label
                    in self.resume_manager.get_all_fields()
                ):
                    QMessageBox.warning(self, "警告", f"标签 '{new_label}' 已存在")
                    return

                # 如果标签改变了，先删除旧标签
                if new_label != label:
                    self.resume_manager.delete_field(label)

                # 保存新数据
                self.resume_manager.set_field(new_label, new_value)

                # 刷新表格
                current_search = self.search_input.text()
                self._load_resume_data(filter_query=current_search)

    def _on_add_clicked(self):
        """添加按钮点击"""
        label = self.label_input.text().strip()
        value = self.value_input.text().strip()

        if not label:
            QMessageBox.warning(self, "警告", "请输入标签名称")
            return

        # 检查标签是否已存在
        if label in self.resume_manager.get_all_fields():
            QMessageBox.warning(self, "警告", f"标签 '{label}' 已存在")
            return

        # 添加字段
        if self.resume_manager.add_field(label, value):
            # 刷新表格（保持当前搜索条件）
            current_search = self.search_input.text()
            self._load_resume_data(filter_query=current_search)
            # 清空输入框
            self.label_input.clear()
            self.value_input.clear()
        else:
            QMessageBox.warning(self, "错误", "添加字段失败")

    def _on_save_clicked(self):
        """保存按钮点击"""
        # 更新所有数据
        self.all_resume_data = self.resume_manager.get_all_fields()
        self.resume_updated.emit()
        QMessageBox.information(self, "成功", "简历已保存")
        self.accept()

    def _show_context_menu(self, position):
        """显示右键菜单"""
        item = self.table.itemAt(position)
        if item is None:
            return

        row = item.row()
        label_item = self.table.item(row, 0)

        if label_item:
            label = label_item.text()

            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除标签 '{label}' 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                if self.resume_manager.delete_field(label):
                    # 刷新表格（保持当前搜索条件）
                    current_search = self.search_input.text()
                    self._load_resume_data(filter_query=current_search)
                    self.resume_updated.emit()
                else:
                    QMessageBox.warning(self, "错误", "删除字段失败")
