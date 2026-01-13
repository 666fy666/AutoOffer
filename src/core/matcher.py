"""标签匹配模块"""

from typing import List, Tuple
from .resume_manager import ResumeManager
from ..utils.distance import calculate_similarity
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LabelMatcher:
    """标签匹配器"""

    def __init__(self, resume_manager: ResumeManager, threshold: float = 0.5):
        """
        初始化标签匹配器

        Args:
            resume_manager: 简历管理器实例
            threshold: 相似度阈值（默认0.5，即50%）
        """
        self.resume_manager = resume_manager
        self.threshold = threshold

    def match(self, ocr_text: str) -> List[Tuple[str, str, float]]:
        """
        匹配OCR识别的文本到简历标签（双向包含匹配）

        Args:
            ocr_text: OCR识别的文本

        Returns:
            匹配结果列表，每个元素为(标签, 值, 相似度)
        """
        if not ocr_text:
            logger.warning("OCR文本为空，无法匹配")
            return []

        # 清理OCR文本（去除空格、标点等）
        cleaned_text = self._clean_text(ocr_text)

        # 获取所有简历字段
        resume_data = self.resume_manager.get_all_fields()

        matches = []
        for label, value in resume_data.items():
            if not value:  # 跳过空值
                continue

            # 清理标签文本
            cleaned_label = self._clean_text(label)

            # 双向包含匹配：结果中有字段，或者字段中有识别结果
            is_match = False
            if cleaned_label and cleaned_text:
                # 检查OCR文本中是否包含标签，或标签中是否包含OCR文本
                if (
                    cleaned_label in cleaned_text
                    or cleaned_text in cleaned_label
                ):
                    is_match = True
                    # 计算相似度用于排序（使用包含关系计算）
                    if cleaned_label in cleaned_text:
                        # 标签在OCR文本中，相似度 = 标签长度 / OCR文本长度
                        similarity = (
                            len(cleaned_label) / len(cleaned_text)
                            if cleaned_text
                            else 0
                        )
                    else:
                        # OCR文本在标签中，相似度 = OCR文本长度 / 标签长度
                        similarity = (
                            len(cleaned_text) / len(cleaned_label)
                            if cleaned_label
                            else 0
                        )
                else:
                    # 如果不包含，使用原来的相似度计算作为备选
                    similarity = calculate_similarity(
                        cleaned_text, cleaned_label
                    )
                    if similarity >= self.threshold:
                        is_match = True

            if is_match:
                matches.append((label, value, similarity))

        # 按相似度降序排序
        matches.sort(key=lambda x: x[2], reverse=True)

        return matches

    def _clean_text(self, text: str) -> str:
        """
        清理文本（去除空格、标点等）

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 去除空格
        text = text.replace(" ", "").replace("\n", "").replace("\t", "")
        # 去除常见标点
        punctuation = "：:，。、；;！!？?（）()【】[]"
        for p in punctuation:
            text = text.replace(p, "")
        return text.strip()
