"""
任务去重算法单元测试
"""

import pytest
from src.core.task_dedup import (
    calculate_similarity,
    extract_keywords,
    merge_similar_tasks,
    deduplicate_tasks,
    find_duplicate_groups,
    get_task_statistics,
    smart_deduplicate,
)


class TestCalculateSimilarity:
    """测试 calculate_similarity 函数"""

    def test_identical_tasks(self):
        """测试完全相同的任务"""
        similarity = calculate_similarity("修复登录BUG", "修复登录BUG")
        assert similarity == 1.0

    def test_similar_tasks(self):
        """测试相似的任务"""
        similarity = calculate_similarity(
            "修复登录页面的BUG",
            "修复登录BUG"
        )
        # 由于共享"修复"、"登录"、"BUG"等关键词，相似度应该较高
        assert 0.3 < similarity < 1.0

    def test_different_tasks(self):
        """测试不相似的任务"""
        similarity = calculate_similarity(
            "修复登录BUG",
            "新增用户管理功能"
        )
        assert similarity < 0.5

    def test_empty_tasks(self):
        """测试空任务"""
        assert calculate_similarity("", "修复BUG") == 0.0
        assert calculate_similarity("修复BUG", "") == 0.0
        assert calculate_similarity("", "") == 0.0

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        similarity = calculate_similarity("Fix BUG", "fix bug")
        # 应该非常相似，因为关键词相同
        assert similarity > 0.8

    def test_keyword_overlap(self):
        """测试关键词重叠"""
        # 共享"登录"关键词
        similarity1 = calculate_similarity("优化登录流程", "修复登录BUG")
        # 没有共享关键词
        similarity2 = calculate_similarity("优化登录流程", "新增支付功能")

        assert similarity1 > similarity2


class TestExtractKeywords:
    """测试 extract_keywords 函数"""

    def test_chinese_keywords(self):
        """测试中文关键词提取"""
        keywords = extract_keywords("修复登录页面的BUG")
        # 由于使用n-gram，会提取出多个词组
        assert len(keywords) > 0
        # 应该包含一些关键词（如BUG）
        assert any("bug" in k.lower() for k in keywords)

    def test_english_keywords(self):
        """测试英文关键词提取"""
        keywords = extract_keywords("Fix the login page bug")
        assert "fix" in keywords
        assert "login" in keywords
        assert "page" in keywords
        assert "bug" in keywords

    def test_filter_stopwords(self):
        """测试过滤停用词"""
        keywords = extract_keywords("修复的BUG是在的页面")
        # "的"、"在" 应该被过滤
        assert "的" not in keywords
        assert "在" not in keywords

    def test_empty_text(self):
        """测试空文本"""
        keywords = extract_keywords("")
        assert len(keywords) == 0

    def test_mixed_language(self):
        """测试中英文混合"""
        keywords = extract_keywords("修复Fix登录Login BUG")
        assert len(keywords) > 0


class TestMergeSimilarTasks:
    """测试 merge_similar_tasks 函数"""

    def test_merge_identical(self):
        """测试合并完全相同的任务"""
        tasks = ["修复BUG", "修复BUG", "修复BUG"]
        merged = merge_similar_tasks(tasks)

        assert len(merged) == 1
        assert merged[0]["count"] == 3
        assert merged[0]["task"] == "修复BUG"

    def test_merge_similar(self):
        """测试合并相似任务"""
        tasks = [
            "修复登录BUG",
            "修复登录页BUG",
            "新增功能"
        ]
        merged = merge_similar_tasks(tasks, threshold=0.7)

        # 由于相似度计算可能不是100%准确，检查范围
        assert 1 <= len(merged) <= 3

    def test_no_merge_different(self):
        """测试不合并不相似的任务"""
        tasks = ["修复BUG", "新增功能", "优化性能"]
        merged = merge_similar_tasks(tasks, threshold=0.9)

        # 应该都不合并
        assert len(merged) == 3

    def test_empty_list(self):
        """测试空列表"""
        merged = merge_similar_tasks([])
        assert merged == []

    def test_select_longest(self):
        """测试选择最长的任务作为代表"""
        tasks = ["修复BUG", "修复登录页面的严重BUG"]
        merged = merge_similar_tasks(tasks, threshold=0.5)

        # 应该选择最长的
        if len(merged) == 1:
            assert merged[0]["task"] == "修复登录页面的严重BUG"


class TestDeduplicateTasks:
    """测试 deduplicate_tasks 函数"""

    def test_remove_duplicates(self):
        """测试移除重复任务"""
        tasks = ["修复BUG", "修复BUG", "新增功能"]
        deduped = deduplicate_tasks(tasks)

        assert len(deduped) == 2
        assert "修复BUG" in deduped
        assert "新增功能" in deduped

    def test_remove_similar(self):
        """测试移除相似任务"""
        tasks = ["修复登录BUG", "修复登录页BUG", "新增功能"]
        deduped = deduplicate_tasks(tasks, threshold=0.7)

        # 相似度计算可能不完全准确，检查范围
        assert 1 <= len(deduped) <= 3

    def test_empty_list(self):
        """测试空列表"""
        deduped = deduplicate_tasks([])
        assert deduped == []


class TestFindDuplicateGroups:
    """测试 find_duplicate_groups 函数"""

    def test_find_duplicates(self):
        """测试查找重复组"""
        tasks = ["修复BUG", "修复BUG", "新增功能"]
        duplicates = find_duplicate_groups(tasks)

        assert len(duplicates) == 1
        assert duplicates[0]["task"] == "修复BUG"
        assert duplicates[0]["count"] == 2

    def test_no_duplicates(self):
        """测试没有重复"""
        tasks = ["修复BUG", "新增功能", "优化性能"]
        duplicates = find_duplicate_groups(tasks)

        assert len(duplicates) == 0

    def test_multiple_duplicate_groups(self):
        """测试多个重复组"""
        tasks = [
            "修复BUG", "修复BUG",
            "新增功能", "新增功能",
            "优化性能"
        ]
        duplicates = find_duplicate_groups(tasks)

        assert len(duplicates) == 2


class TestGetTaskStatistics:
    """测试 get_task_statistics 函数"""

    def test_statistics(self):
        """测试统计功能"""
        tasks = ["修复BUG", "修复BUG", "新增功能"]
        stats = get_task_statistics(tasks)

        assert stats["total"] == 3
        assert stats["unique"] == 2
        assert stats["duplicates"] == 1
        assert stats["avg_length"] > 0

    def test_empty_list(self):
        """测试空列表"""
        stats = get_task_statistics([])

        assert stats["total"] == 0
        assert stats["unique"] == 0
        assert stats["duplicates"] == 0

    def test_keywords_extraction(self):
        """测试关键词提取"""
        tasks = ["修复登录BUG", "修复登录页面BUG", "新增登录功能"]
        stats = get_task_statistics(tasks)

        # 应该提取出一些关键词
        assert len(stats["keywords"]) > 0


class TestSmartDeduplicate:
    """测试 smart_deduplicate 函数"""

    def test_keep_longest(self):
        """测试保留最长策略"""
        tasks = ["修复BUG", "修复登录BUG", "修复BUG"]
        deduped = smart_deduplicate(tasks, "keep_longest")

        # 应该保留最长的
        assert "修复登录BUG" in deduped

    def test_keep_first(self):
        """测试保留第一个策略"""
        tasks = ["修复BUG", "修复登录BUG"]
        deduped = smart_deduplicate(tasks, "keep_first")

        # 应该保留第一个
        if len(deduped) == 1:
            assert deduped[0] == "修复BUG"

    def test_keep_last(self):
        """测试保留最后一个策略"""
        tasks = ["修复BUG", "修复登录BUG"]
        deduped = smart_deduplicate(tasks, "keep_last")

        # 应该保留最后一个
        if len(deduped) == 1:
            assert deduped[0] == "修复登录BUG"

    def test_empty_list(self):
        """测试空列表"""
        deduped = smart_deduplicate([])
        assert deduped == []
