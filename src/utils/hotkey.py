"""全局快捷键模块"""

import keyboard  # type: ignore[import-untyped]
from typing import Callable


class HotkeyManager:
    """全局快捷键管理器"""

    def __init__(self):
        self.hotkeys = {}
        self.is_registered = False

    def register(self, hotkey: str, callback: Callable) -> bool:
        """
        注册全局快捷键

        Args:
            hotkey: 快捷键组合，如 'alt+c'
            callback: 回调函数

        Returns:
            是否成功注册
        """
        try:
            # 先尝试移除已存在的快捷键
            if hotkey in self.hotkeys:
                self.unregister(hotkey)

            # 注册新快捷键
            keyboard.add_hotkey(hotkey, callback)
            self.hotkeys[hotkey] = callback
            self.is_registered = True
            return True
        except Exception as e:
            print(f"注册快捷键失败: {e}")
            return False

    def unregister(self, hotkey: str) -> bool:
        """
        取消注册快捷键

        Args:
            hotkey: 快捷键组合

        Returns:
            是否成功取消注册
        """
        try:
            if hotkey in self.hotkeys:
                keyboard.remove_hotkey(hotkey)
                del self.hotkeys[hotkey]
                return True
        except Exception as e:
            print(f"取消注册快捷键失败: {e}")
        return False

    def unregister_all(self):
        """取消注册所有快捷键"""
        for hotkey in list(self.hotkeys.keys()):
            self.unregister(hotkey)
        self.is_registered = False

    def is_hotkey_available(self, hotkey: str) -> bool:
        """
        检查快捷键是否可用（不冲突）

        Args:
            hotkey: 快捷键组合

        Returns:
            是否可用
        """
        # 简单检查：如果已经注册过，则认为不可用
        return hotkey not in self.hotkeys
