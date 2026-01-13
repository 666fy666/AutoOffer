"""资源文件路径工具模块"""

import sys
import os
from pathlib import Path
from typing import Optional


def get_resource_path(relative_path: str) -> Path:
    """
    获取资源文件路径，支持开发环境和打包环境

    Args:
        relative_path: 相对于项目根目录的路径，如 "data/resume_template.yaml"
                       文件在项目根目录的 data/ 目录下

    Returns:
        资源文件的完整路径
    """
    # 检查是否在 PyInstaller 打包环境中
    if hasattr(sys, "_MEIPASS"):
        # 打包环境：资源文件在临时解压目录
        base_path = Path(sys._MEIPASS)
    else:
        # 开发环境：资源文件在项目根目录
        # 从当前文件位置向上找到项目根目录
        # resource.py 在 src/utils/，所以 parent.parent.parent 是项目根目录
        base_path = Path(__file__).parent.parent.parent

    return base_path / relative_path


def get_user_data_dir() -> Path:
    """
    获取用户数据目录路径

    Returns:
        用户数据目录路径（如 Windows: AppData/Local/AutoOffer）
    """
    if sys.platform == "win32":
        # Windows: AppData/Local/AutoOffer
        appdata = os.getenv(
            "LOCALAPPDATA", os.path.expanduser("~/.local/share")
        )
        data_dir = Path(appdata) / "AutoOffer"
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/AutoOffer
        data_dir = (
            Path.home()
            / "Library"
            / "Application Support"
            / "AutoOffer"
        )
    else:
        # Linux: ~/.local/share/AutoOffer
        data_dir = Path.home() / ".local" / "share" / "AutoOffer"

    # 确保目录存在
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_user_data_path(relative_path: str) -> Path:
    """
    获取用户数据文件路径

    Args:
        relative_path: 相对于用户数据目录的路径，如 "resume_template.yaml"

    Returns:
        用户数据文件的完整路径
    """
    return get_user_data_dir() / relative_path


def ensure_resource_dir() -> None:
    """
    确保资源目录存在（仅在开发环境中）
    
    在打包环境中，资源文件已经包含在可执行文件中，不需要创建目录。
    在开发环境中，确保项目根目录的 data 目录存在。
    """
    # 只在开发环境中创建目录
    if hasattr(sys, "_MEIPASS"):
        # 打包环境，不需要创建目录
        return
    
    # 开发环境：确保项目根目录的 data 目录存在
    base_path = Path(__file__).parent.parent.parent
    data_dir = base_path / "data"
    
    # 创建 data 目录（如果不存在）
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 如果 resume_template.yaml 不存在，尝试从示例文件复制
    template_path = data_dir / "resume_template.yaml"
    example_path = data_dir / "resume_template_example.yaml"
    
    if not template_path.exists() and example_path.exists():
        import shutil
        import logging
        try:
            shutil.copy2(example_path, template_path)
            logging.info(f"已从示例文件创建: {template_path}")
        except Exception as e:
            logging.warning(f"无法从示例文件创建模板文件: {e}")


def ensure_user_data_from_resource(
    resource_relative_path: str, user_data_filename: Optional[str] = None, force_update: bool = False
) -> Path:
    """
    确保用户数据文件存在，如果不存在则从资源文件复制

    Args:
        resource_relative_path: 资源文件相对路径，如 "data/resume_template.yaml"
        user_data_filename: 用户数据文件名，如果为 None 则使用资源文件名
        force_update: 如果为 True，即使文件存在也会从资源文件更新

    Returns:
        用户数据文件的完整路径
    """
    if user_data_filename is None:
        # 从资源路径中提取文件名
        user_data_filename = Path(resource_relative_path).name

    user_data_path = get_user_data_path(user_data_filename)
    resource_path = get_resource_path(resource_relative_path)

    # 如果用户数据文件不存在，或需要强制更新，从资源文件复制
    if not user_data_path.exists() or force_update:
        if resource_path.exists():
            import shutil
            # 确保目标目录存在
            user_data_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(resource_path, user_data_path)
        elif not user_data_path.exists():
            # 如果资源文件也不存在，记录警告
            import logging
            logging.warning(f"资源文件不存在: {resource_path}")

    return user_data_path
