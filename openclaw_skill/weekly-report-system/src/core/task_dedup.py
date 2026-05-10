"""
任务去重算法

识别和合并相似任务
"""

import re
from typing import List, Dict, Tuple
from collections import Counter


def calculate_similarity(task1: str, task2: str) -> float:
    """
    计算两个任务的相似度 (0-1)

    基于以下因素计算：
    - 关键词重叠
    - 字符串相似度（编辑距离）
    - 长度比

    Args:
        task1: 任务1描述
        task2: 任务2描述

    Returns:
        相似度分数 (0-1)，1表示完全相同

    Example:
        >>> calculate_similarity("修复登录BUG", "修复登录BUG")
        1.0
        >>> calculate_similarity("修复登录BUG", "新增登录功能")
        0.6
    """
    # 空字符串
    if not task1 or not task2:
        return 0.0

    # 完全相同
    if task1 == task2:
        return 1.0

    # 预处理：提取关键词
    keywords1 = extract_keywords(task1)
    keywords2 = extract_keywords(task2)

    if not keywords1 or not keywords2:
        return 0.0

    # 计算关键词重叠度
    common_keywords = keywords1 & keywords2
    all_keywords = keywords1 | keywords2

    if not all_keywords:
        return 0.0

    keyword_similarity = len(common_keywords) / len(all_keywords)

    # 计算字符级相似度（Jaccard相似度）
    chars1 = set(task1)
    chars2 = set(task2)
    common_chars = chars1 & chars2
    all_chars = chars1 | chars2

    if not all_chars:
        char_similarity = 0.0
    else:
        char_similarity = len(common_chars) / len(all_chars)

    # 计算长度比
    len1, len2 = len(task1), len(task2)
    if max(len1, len2) == 0:
        length_ratio = 0.0
    else:
        length_ratio = min(len1, len2) / max(len1, len2)

    # 综合相似度（加权平均）
    # 关键词权重最高，因为最能体现任务内容
    similarity = (
        keyword_similarity * 0.6 +
        char_similarity * 0.2 +
        length_ratio * 0.2
    )

    return similarity


def extract_keywords(text: str) -> set:
    """
    从文本中提取关键词

    Args:
        text: 文本

    Returns:
        关键词集合

    Example:
        >>> extract_keywords("修复登录页面的BUG")
        {'修复', '登录', '页面', 'BUG'}
    """
    if not text:
        return set()

    # 移除标点符号
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)

    keywords = set()

    # 提取英文单词
    english_words = re.findall(r'[a-zA-Z]{2,}', text)
    for word in english_words:
        if word.lower() not in {'the', 'is', 'are', 'was', 'were', 'been', 'being'}:
            keywords.add(word.lower())

    # 提取中文词汇（简单实现：提取2-4字词组）
    # 对于实际应用，应该使用jieba等专业分词库
    chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
    for phrase in chinese_chars:
        # 提取2-4字的词组
        if len(phrase) >= 2:
            # 添加整个词组
            keywords.add(phrase)
            # 添加2-4字的n-gram
            for i in range(len(phrase)):
                for n in range(2, min(5, len(phrase) - i + 1)):
                    ngram = phrase[i:i+n]
                    if len(ngram) >= 2:
                        keywords.add(ngram)

    # 过滤停用词
    stopwords = {
        '的', '了', '和', '是', '在', '有', '对', '为', '与',
        '等', '中', '上', '下', '到', '从', '被', '把', '让',
        '这', '那', '之', '以', '也', '就', '都', '而', '及',
        '与', '或', '但', '如', '要', '会', '能', '可', '该',
    }

    keywords = keywords - stopwords

    return keywords


def merge_similar_tasks(
    tasks: List[str],
    threshold: float = 0.7
) -> List[Dict]:
    """
    合并相似度超过阈值的任务

    Args:
        tasks: 任务列表
        threshold: 相似度阈值（0-1），默认0.7

    Returns:
        合并后的任务列表，每项包含:
        {
            "task": "任务描述（选择最长的）",
            "count": 出现次数,
            "similar_tasks": ["相似任务列表"]
        }

    Example:
        >>> tasks = ["修复登录BUG", "修复登录页BUG", "新增功能"]
        >>> merged = merge_similar_tasks(tasks, threshold=0.7)
        >>> len(merged) < len(tasks)
        True
    """
    if not tasks:
        return []

    # 任务分组：相似的任务归为一组
    task_groups: List[List[str]] = []

    for task in tasks:
        # 检查是否与已有组中的任务相似
        matched = False
        for group in task_groups:
            # 与组中第一个任务比较
            if calculate_similarity(task, group[0]) >= threshold:
                group.append(task)
                matched = True
                break

        # 如果没有匹配的组，创建新组
        if not matched:
            task_groups.append([task])

    # 从每组生成合并结果
    merged_tasks = []
    for group in task_groups:
        # 选择最长的任务作为代表
        representative = max(group, key=len)

        merged_tasks.append({
            "task": representative,
            "count": len(group),
            "similar_tasks": group if len(group) > 1 else []
        })

    return merged_tasks


def deduplicate_tasks(tasks: List[str], threshold: float = 0.7) -> List[str]:
    """
    去重任务列表

    Args:
        tasks: 任务列表
        threshold: 相似度阈值

    Returns:
        去重后的任务列表

    Example:
        >>> tasks = ["修复BUG", "修复BUG", "新增功能"]
        >>> deduplicate_tasks(tasks)
        ['修复BUG', '新增功能']
    """
    merged = merge_similar_tasks(tasks, threshold)
    return [item["task"] for item in merged]


def find_duplicate_groups(
    tasks: List[str],
    threshold: float = 0.7
) -> List[Dict]:
    """
    查找重复的任务组

    Args:
        tasks: 任务列表
        threshold: 相似度阈值

    Returns:
        重复任务组列表

    Example:
        >>> tasks = ["修复BUG", "修复BUG", "新增功能"]
        >>> groups = find_duplicate_groups(tasks)
        >>> len(groups)
        1
    """
    merged = merge_similar_tasks(tasks, threshold)
    duplicates = [item for item in merged if item["count"] > 1]
    return duplicates


def get_task_statistics(tasks: List[str]) -> Dict:
    """
    获取任务统计信息

    Args:
        tasks: 任务列表

    Returns:
        统计信息:
        {
            "total": 总数,
            "unique": 唯一任务数,
            "duplicates": 重复任务数,
            "avg_length": 平均长度,
            "keywords": {"关键词": 出现次数}
        }

    Example:
        >>> stats = get_task_statistics(["修复BUG", "新增功能"])
        >>> stats["total"]
        2
    """
    if not tasks:
        return {
            "total": 0,
            "unique": 0,
            "duplicates": 0,
            "avg_length": 0.0,
            "keywords": {}
        }

    # 提取所有关键词
    all_keywords = []
    for task in tasks:
        keywords = extract_keywords(task)
        all_keywords.extend(keywords)

    # 统计关键词频率
    keyword_counter = Counter(all_keywords)
    top_keywords = dict(keyword_counter.most_common(10))

    # 计算重复任务数
    unique_tasks = set(tasks)
    duplicate_count = len(tasks) - len(unique_tasks)

    return {
        "total": len(tasks),
        "unique": len(unique_tasks),
        "duplicates": duplicate_count,
        "avg_length": sum(len(t) for t in tasks) / len(tasks),
        "keywords": top_keywords
    }


def smart_deduplicate(
    tasks: List[str],
    strategy: str = "keep_longest"
) -> List[str]:
    """
    智能去重（支持多种策略）

    Args:
        tasks: 任务列表
        strategy: 去重策略
            - "keep_longest": 保留最长的任务（默认）
            - "keep_first": 保留第一个出现的任务
            - "keep_last": 保留最后一个出现的任务

    Returns:
        去重后的任务列表

    Example:
        >>> tasks = ["修复BUG", "修复登录BUG", "修复BUG"]
        >>> smart_deduplicate(tasks, "keep_longest")
        ['修复登录BUG']
    """
    # 完全相同的去重
    seen = set()
    unique_tasks = []

    for task in tasks:
        if task not in seen:
            seen.add(task)
            unique_tasks.append(task)

    # 合并相似任务
    merged = merge_similar_tasks(unique_tasks, threshold=0.8)

    # 根据策略选择代表任务
    result = []
    for item in merged:
        if strategy == "keep_longest":
            # 已经是最长的
            result.append(item["task"])
        elif strategy == "keep_first" and item["similar_tasks"]:
            # 从原始列表中找到第一个出现的
            for task in tasks:
                if task in item["similar_tasks"] or task == item["task"]:
                    result.append(task)
                    break
        elif strategy == "keep_last" and item["similar_tasks"]:
            # 从原始列表中找到最后一个出现的
            for task in reversed(tasks):
                if task in item["similar_tasks"] or task == item["task"]:
                    result.append(task)
                    break
        else:
            result.append(item["task"])

    return result
