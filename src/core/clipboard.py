"""剪切板操作模块"""

import pyperclip  # type: ignore[import-untyped]


def copy_to_clipboard(text: str) -> bool:
    """
    复制文本到系统剪切板

    Args:
        text: 要复制的文本

    Returns:
        是否成功
    """
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        print(f"复制到剪切板失败: {e}")
        return False


def get_clipboard_text() -> str:
    """
    从系统剪切板获取文本

    Returns:
        剪切板文本内容
    """
    try:
        return pyperclip.paste()
    except Exception as e:
        print(f"从剪切板获取文本失败: {e}")
        return ""
