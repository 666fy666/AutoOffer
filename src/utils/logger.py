"""日志模块"""

import logging
import sys
from pathlib import Path
from typing import Optional
from .resource import get_user_data_dir


def setup_logger(
    name: str = "AutoOffer", log_file: Optional[str] = None
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，如果为None则只输出到控制台

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 日志格式：时间戳 - 级别 - 模块 - 消息
    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s - %(levelname)s - "
            "[%(name)s:%(lineno)d] - %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（如果指定了日志文件）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 创建全局日志记录器
_logger = None


def get_logger(name: str = "AutoOffer") -> logging.Logger:
    """
    获取日志记录器（单例模式）

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器实例
    """
    global _logger
    if _logger is None:
        # 日志文件保存在用户数据目录的logs文件夹
        log_dir = get_user_data_dir() / "logs"
        log_file = log_dir / "auto_offer.log"
        _logger = setup_logger(name, str(log_file))
    return _logger
