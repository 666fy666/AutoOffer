"""简历模板管理模块"""

import sys
import yaml  # type: ignore[import-untyped]
from pathlib import Path
from typing import Dict, Optional
from ..utils.logger import get_logger
from ..utils.resource import ensure_user_data_from_resource, get_resource_path

logger = get_logger(__name__)


class ResumeManager:
    """简历模板管理器"""

    # 预设标签类别
    PRESET_LABELS = [
        "姓名",
        "身份证",
        "电话",
        "手机",
        "邮箱",
        "地址",
        "邮编",
        "毕业院校",
        "专业",
        "工作经历",
        "技能",
        "学历",
        "出生日期",
        "性别",
        "民族",
        "政治面貌",
        "婚姻状况",
        "籍贯",
        "现居住地",
        "期望薪资",
        "求职意向",
        "自我评价",
        "项目经验",
        "获奖情况",
    ]

    def __init__(self, template_path: Optional[str] = None):
        """
        初始化简历管理器

        Args:
            template_path: YAML模板文件路径，如果为None，则根据环境自动选择：
                          - 开发环境：使用项目目录下的 data/resume_template.yaml
                          - 打包环境：使用用户数据目录中的文件
        """
        if template_path is None:
            # 检查是否在打包环境中
            if hasattr(sys, "_MEIPASS"):
                # 打包环境：使用用户数据目录，确保文件存在（如果不存在则从资源文件复制）
                self.template_path = ensure_user_data_from_resource(
                    "data/resume_template.yaml", "resume_template.yaml"
                )
                # 检查是否需要从资源文件更新（如果用户数据文件字段较少）
                self._check_and_update_from_resource()
            else:
                # 开发环境：直接使用项目目录下的 data/resume_template.yaml
                self.template_path = get_resource_path("data/resume_template.yaml")
                logger.info(f"开发环境：使用项目目录下的模板文件: {self.template_path}")
        else:
            self.template_path = Path(template_path)

        self._ensure_template_exists()
        self._load_template()

    def _check_and_update_from_resource(self):
        """检查用户数据文件是否需要从资源文件更新"""
        try:
            # 检查资源文件
            from ..utils.resource import get_resource_path
            resource_path = get_resource_path("data/resume_template.yaml")
            
            if resource_path.exists() and self.template_path.exists():
                # 加载两个文件比较字段数量
                with open(resource_path, "r", encoding="utf-8") as f:
                    resource_data = yaml.safe_load(f)
                with open(self.template_path, "r", encoding="utf-8") as f:
                    user_data = yaml.safe_load(f)
                
                resource_fields = len(resource_data.get("resume", {})) if resource_data else 0
                user_fields = len(user_data.get("resume", {})) if user_data else 0
                
                # 如果资源文件字段更多，更新用户数据文件
                if resource_fields > user_fields:
                    logger.info(f"检测到资源文件有更多字段 ({resource_fields} > {user_fields})，更新用户数据文件")
                    import shutil
                    shutil.copy2(resource_path, self.template_path)
        except Exception as e:
            logger.warning(f"检查资源文件更新时出错: {e}", exc_info=True)

    def _ensure_template_exists(self):
        """确保模板文件存在"""
        if not self.template_path.exists():
            self.template_path.parent.mkdir(parents=True, exist_ok=True)
            default_data = {
                "resume": {label: "" for label in self.PRESET_LABELS}
            }
            with open(self.template_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    default_data,
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                )

    def _load_template(self) -> None:
        """加载简历模板"""
        try:
            with open(self.template_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "resume" in data:
                    self.resume_data = data["resume"]
                else:
                    self.resume_data = {}
                    logger.warning("简历模板文件格式不正确")
        except Exception as e:
            logger.error(f"加载模板失败: {e}", exc_info=True)
            self.resume_data = {}

    def get_all_fields(self) -> Dict[str, str]:
        """获取所有简历字段"""
        return self.resume_data.copy()

    def get_field(self, label: str) -> Optional[str]:
        """获取指定标签的值"""
        return self.resume_data.get(label, None)

    def set_field(self, label: str, value: str) -> bool:
        """
        设置字段值

        Args:
            label: 标签名称
            value: 字段值

        Returns:
            是否成功
        """
        self.resume_data[label] = value
        return self._save_template()

    def add_field(self, label: str, value: str) -> bool:
        """
        添加新字段

        Args:
            label: 标签名称
            value: 字段值

        Returns:
            是否成功
        """
        if label in self.resume_data:
            return False  # 字段已存在
        self.resume_data[label] = value
        return self._save_template()

    def delete_field(self, label: str) -> bool:
        """
        删除字段

        Args:
            label: 标签名称

        Returns:
            是否成功
        """
        if label not in self.resume_data:
            return False
        del self.resume_data[label]
        return self._save_template()

    def update_field(self, old_label: str, new_label: str, value: str) -> bool:
        """
        更新字段（可重命名标签）

        Args:
            old_label: 旧标签名称
            new_label: 新标签名称
            value: 字段值

        Returns:
            是否成功
        """
        if old_label not in self.resume_data:
            return False

        # 如果标签名称改变，先删除旧的
        if old_label != new_label:
            del self.resume_data[old_label]

        self.resume_data[new_label] = value
        return self._save_template()

    def _save_template(self) -> bool:
        """保存模板到文件"""
        try:
            data = {"resume": self.resume_data}

            # 定义需要多行显示的字段（这些字段如果包含换行符，将使用多行格式）
            multiline_fields = {
                "工作经历",
                "项目经验",
                "自我评价",
                "获奖情况",
                "实习经历",
                "社团活动",
                "主修课程",
                "技能",
            }

            # 手动构建YAML内容以支持多行格式
            lines = ["resume:"]
            for label, value in data["resume"].items():
                if label in multiline_fields and value and "\n" in value:
                    # 使用 | 格式保存多行内容
                    lines.append(f"  {label}: |")
                    # 将多行内容按行添加，每行前加两个空格
                    for line in value.split("\n"):
                        lines.append(f"    {line}")
                else:
                    # 单行内容，使用引号包裹以避免特殊字符问题
                    if value and (
                        "\n" in value
                        or ":" in value
                        or value.startswith("|")
                        or value.startswith(">")
                    ):
                        # 如果包含特殊字符，使用引号
                        escaped_value = value.replace('"', '\\"').replace(
                            "\n", "\\n"
                        )
                        lines.append(f'  {label}: "{escaped_value}"')
                    else:
                        lines.append(f"  {label}: '{value}'")

            with open(self.template_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return True
        except Exception as e:
            logger.error(f"保存模板失败: {e}", exc_info=True)
            # 如果手动构建失败，使用默认方式保存
            try:
                data = {"resume": self.resume_data}
                with open(self.template_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        data,
                        f,
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    )
                return True
            except Exception as e2:
                logger.error(f"使用默认方式保存也失败: {e2}", exc_info=True)
                return False
