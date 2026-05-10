"""
Markdown日报解析器单元测试
"""

import pytest
from src.core.parser import (
    parse_daily_report,
    extract_member_name,
    extract_tasks,
    validate_report,
    merge_reports,
    get_member_statistics,
)


class TestParseDailyReport:
    """测试 parse_daily_report 函数"""

    def test_single_member_basic(self):
        """测试单个成员的基本格式"""
        markdown = """
HLQ:
今:
- 任务1
- 任务2
明:
- 任务3
"""
        report = parse_daily_report(markdown, "20260307")

        assert report["date"] == "20260307"
        assert "HLQ" in report["members"]
        assert report["members"]["HLQ"]["today"] == ["任务1", "任务2"]
        assert report["members"]["HLQ"]["tomorrow"] == ["任务3"]

    def test_multiple_members(self):
        """测试多个成员"""
        markdown = """
HLQ:
今:
- HLQ任务1
明:
- HLQ任务2

DJZ:
今:
- DJZ任务1
明:
- DJZ任务2
"""
        report = parse_daily_report(markdown)

        assert "HLQ" in report["members"]
        assert "DJZ" in report["members"]
        assert report["members"]["HLQ"]["today"] == ["HLQ任务1"]
        assert report["members"]["DJZ"]["today"] == ["DJZ任务1"]

    def test_bulleted_format(self):
        """测试带圆点的格式"""
        markdown = """
HLQ:
今:
• 任务1
• 任务2
明:
• 任务3
"""
        report = parse_daily_report(markdown)

        assert report["members"]["HLQ"]["today"] == ["任务1", "任务2"]
        assert report["members"]["HLQ"]["tomorrow"] == ["任务3"]

    def test_empty_today(self):
        """测试今日任务为空"""
        markdown = """
HLQ:
今:
明:
- 任务1
"""
        report = parse_daily_report(markdown)

        assert report["members"]["HLQ"]["today"] == []
        assert report["members"]["HLQ"]["tomorrow"] == ["任务1"]

    def test_no_date_provided(self):
        """测试不提供日期"""
        markdown = "HLQ:\n今:\n- 任务1\n明:\n"
        report = parse_daily_report(markdown)

        assert "date" in report
        assert len(report["date"]) == 8  # YYYYMMDD格式

    def test_inline_format(self):
        """测试行内格式（今: 后面直接跟任务）"""
        markdown = """
HLQ: 今: 任务1
明: 任务2
"""
        report = parse_daily_report(markdown)

        # 行内格式不是标准格式，解析可能不完整
        # 但至少不应该崩溃
        assert isinstance(report, dict)
        assert "members" in report

    def test_empty_report(self):
        """测试空日报"""
        report = parse_daily_report("")

        assert report["members"] == {}


class TestExtractMemberName:
    """测试 extract_member_name 函数"""

    def test_valid_member(self):
        """测试有效的成员名称"""
        assert extract_member_name("HLQ: 任务列表") == "HLQ"
        assert extract_member_name("DJZ:") == "DJZ"
        assert extract_member_name("XZY: 今:") == "XZY"

    def test_invalid_member(self):
        """测试无效的成员名称"""
        assert extract_member_name("这是一行文本") is None
        assert extract_member_name("小写: 内容") is None
        assert extract_member_name("") is None

    def test_edge_cases(self):
        """测试边界情况"""
        # 2个字母
        assert extract_member_name("AB:") == "AB"
        # 4个字母
        assert extract_member_name("ABCD:") == "ABCD"
        # 5个字母（不应匹配）
        assert extract_member_name("ABCDE:") is None


class TestExtractTasks:
    """测试 extract_tasks 函数"""

    def test_extract_today_tasks(self):
        """测试提取今日任务"""
        text = """
今:
- 任务1
- 任务2
明:
- 任务3
"""
        tasks = extract_tasks(text, "today")
        assert "任务1" in tasks
        assert "任务2" in tasks
        assert "任务3" not in tasks

    def test_extract_tomorrow_tasks(self):
        """测试提取明日任务"""
        text = """
今:
- 任务1
明:
- 任务2
- 任务3
"""
        tasks = extract_tasks(text, "tomorrow")
        assert "任务1" not in tasks
        assert "任务2" in tasks
        assert "任务3" in tasks

    def test_extract_all_tasks(self):
        """测试提取所有任务"""
        text = """
今:
- 任务1
明:
- 任务2
"""
        tasks = extract_tasks(text, "all")
        assert "任务1" in tasks
        assert "任务2" in tasks


class TestValidateReport:
    """测试 validate_report 函数"""

    def test_valid_report(self):
        """测试有效的日报"""
        report = {
            "date": "20260307",
            "members": {
                "HLQ": {
                    "today": ["任务1"],
                    "tomorrow": ["任务2"]
                }
            }
        }
        errors = validate_report(report)
        assert len(errors) == 0

    def test_missing_date(self):
        """测试缺少日期"""
        report = {
            "members": {
                "HLQ": {"today": [], "tomorrow": []}
            }
        }
        errors = validate_report(report)
        assert "缺少date字段" in errors

    def test_missing_members(self):
        """测试缺少成员"""
        report = {
            "date": "20260307"
        }
        errors = validate_report(report)
        assert "缺少members字段" in errors

    def test_empty_members(self):
        """测试成员为空"""
        report = {
            "date": "20260307",
            "members": {}
        }
        errors = validate_report(report)
        assert "members字段不能为空" in errors

    def test_missing_member_fields(self):
        """测试成员缺少字段"""
        report = {
            "date": "20260307",
            "members": {
                "HLQ": {}
            }
        }
        errors = validate_report(report)
        assert any("缺少today字段" in e for e in errors)
        assert any("缺少tomorrow字段" in e for e in errors)


class TestMergeReports:
    """测试 merge_reports 函数"""

    def test_merge_two_reports(self):
        """测试合并两个日报"""
        report1 = {
            "date": "20260307",
            "members": {
                "HLQ": {"today": ["任务1"], "tomorrow": []}
            }
        }
        report2 = {
            "date": "20260308",
            "members": {
                "HLQ": {"today": ["任务2"], "tomorrow": []}
            }
        }

        merged = merge_reports([report1, report2])

        assert "HLQ" in merged["members"]
        assert "任务1" in merged["members"]["HLQ"]["today"]
        assert "任务2" in merged["members"]["HLQ"]["today"]

    def test_merge_different_members(self):
        """测试合并不同成员的日报"""
        report1 = {
            "date": "20260307",
            "members": {
                "HLQ": {"today": ["任务1"], "tomorrow": []}
            }
        }
        report2 = {
            "date": "20260308",
            "members": {
                "DJZ": {"today": ["任务2"], "tomorrow": []}
            }
        }

        merged = merge_reports([report1, report2])

        assert "HLQ" in merged["members"]
        assert "DJZ" in merged["members"]

    def test_merge_empty_list(self):
        """测试合并空列表"""
        merged = merge_reports([])
        assert merged["members"] == {}


class TestGetMemberStatistics:
    """测试 get_member_statistics 函数"""

    def test_statistics(self):
        """测试统计功能"""
        report = {
            "members": {
                "HLQ": {
                    "today": ["任务1", "任务2"],
                    "tomorrow": ["任务3"]
                },
                "DJZ": {
                    "today": ["任务4"],
                    "tomorrow": []
                }
            }
        }

        stats = get_member_statistics(report)

        assert stats["HLQ"] == 3  # 2 + 1
        assert stats["DJZ"] == 1  # 1 + 0

    def test_empty_report(self):
        """测试空日报"""
        report = {"members": {}}
        stats = get_member_statistics(report)
        assert stats == {}
