"""打包脚本"""
import PyInstaller.__main__
import os
import sys
from pathlib import Path

# 设置UTF-8编码，解决Windows环境下的中文输出问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def build_exe():
    """使用PyInstaller打包成exe"""
    
    # 获取项目根目录
    base_dir = Path(__file__).parent
    
    # 确定数据文件路径分隔符（Windows使用分号，Linux/Mac使用冒号）
    if sys.platform == 'win32':
        data_separator = ';'
    else:
        data_separator = ':'
    
    # PyInstaller参数
    args = [
        'src/main.py',
        '--name=AutoOffer',
        '--onefile',
        '--windowed',  # 不显示控制台窗口
        '--clean',
        '--noconfirm',
        # 包含数据文件：源路径;目标路径（Windows）或 源路径:目标路径（Linux/Mac）
        # 打包后，data目录会在sys._MEIPASS/data下
        f'--add-data=data{data_separator}data',
        '--hidden-import=rapidocr',
        '--hidden-import=rapidocr_onnxruntime',
        '--hidden-import=yaml',
        '--hidden-import=keyboard',
        '--hidden-import=pyperclip',
        '--hidden-import=Levenshtein',
        '--hidden-import=PIL',
        '--hidden-import=numpy',
        '--hidden-import=onnxruntime',
        '--collect-all=rapidocr',  # 收集rapidocr的所有资源
        '--collect-all=rapidocr_onnxruntime',  # 收集rapidocr_onnxruntime的所有资源
    ]
    
    # 如果是Windows，添加Windows特定参数
    if sys.platform == 'win32':
        args.extend([
            '--icon=NONE',  # 可以添加图标文件路径
        ])
    
    print("开始打包...")
    print(f"参数: {' '.join(args)}")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n打包完成！")
        print(f"可执行文件位置: {base_dir / 'dist' / 'AutoOffer.exe'}")
    except Exception as e:
        print(f"打包失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
