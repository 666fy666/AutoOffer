"""编辑距离计算工具"""

from Levenshtein import distance as levenshtein_distance


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（基于编辑距离）

    Args:
        text1: 第一个文本
        text2: 第二个文本

    Returns:
        相似度（0-1之间，1表示完全相同）
    """
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0

    max_len = max(len(text1), len(text2))
    if max_len == 0:
        return 1.0

    edit_dist = levenshtein_distance(text1, text2)
    similarity = 1.0 - (edit_dist / max_len)
    return similarity


def find_best_matches(
    query: str, candidates: list[str], threshold: float = 0.5
) -> list[tuple[str, float]]:
    """
    在候选项中找到与查询文本最匹配的项

    Args:
        query: 查询文本
        candidates: 候选项列表
        threshold: 相似度阈值（默认0.5）

    Returns:
        匹配结果列表，每个元素为(候选项, 相似度)，按相似度降序排列
    """
    matches = []
    for candidate in candidates:
        similarity = calculate_similarity(query, candidate)
        if similarity >= threshold:
            matches.append((candidate, similarity))

    # 按相似度降序排序
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches
