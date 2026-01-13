"""OCR识别模块"""

from typing import List, Tuple
from PIL import Image
import numpy as np
from rapidocr_onnxruntime import RapidOCR  # type: ignore[import-untyped]
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OCRProcessor:
    """OCR处理器"""

    def __init__(self):
        """初始化OCR处理器（使用ONNX CPU模式）"""
        self.ocr_engine = None
        self._init_ocr()

    def _init_ocr(self):
        """初始化RapidOCR引擎"""
        try:
            # 使用ONNX CPU模式
            self.ocr_engine = RapidOCR(
                use_angle_cls=True, use_text_detector=True
            )
        except Exception as e:
            logger.error(f"初始化OCR引擎失败: {e}", exc_info=True)
            self.ocr_engine = None

    def recognize(self, image: Image.Image) -> List[Tuple[str, float]]:
        """
        识别图片中的文字

        Args:
            image: PIL Image对象

        Returns:
            识别结果列表，每个元素为(文本, 置信度)
        """
        if self.ocr_engine is None:
            logger.warning("OCR引擎未初始化")
            return []

        try:
            # 将PIL Image转换为numpy数组
            img_array = np.array(image)

            # 执行OCR识别
            result, _ = self.ocr_engine(img_array)

            if not result:
                logger.warning("OCR未识别到任何文字")
                return []

            # 提取文本和置信度
            texts = []
            for item in result:
                if len(item) >= 2:
                    text = item[1]  # 文本内容
                    confidence = item[2] if len(item) > 2 else 1.0  # 置信度
                    texts.append((text, confidence))

            return texts
        except Exception as e:
            logger.error(f"OCR识别失败: {e}", exc_info=True)
            return []

    def recognize_text(self, image: Image.Image) -> str:
        """
        识别图片中的文字并合并为单个字符串

        Args:
            image: PIL Image对象

        Returns:
            合并后的文本字符串
        """
        results = self.recognize(image)
        if not results:
            return ""

        # 合并所有识别的文本
        texts = [text for text, _ in results]
        return " ".join(texts)
