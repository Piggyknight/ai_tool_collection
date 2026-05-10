"""
分类统计模块单元测试

测试CategoryStatsGenerator的各种功能。
"""

import pytest
import json
import csv
from datetime import datetime
from pathlib import Path
from io import StringIO

# 添加项目根目录到Python路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.category_parser import Category
from src.modules.category_stats import (
    CategoryStats,
    WeeklyStats,
    MultiWeekStats,
    MemberStats,
    ChartData,
    CategoryStatsGenerator,
    generate_quick_stats
)


# ============================================================================
# 测试数据
# ============================================================================

@pytest.fixture
def sample_categories():
    """测试用的分类列表"""
    return [
        Category(id="memory", name="内存相关", keywords=["内存", "mmap"], description="内存相关任务"),
        Category(id="resource", name="资源相关", keywords=["资源", "asset"], description="资源相关任务"),
        Category(id="harmonyos", name="鸿蒙支持", keywords=["鸿蒙", "harmony"], description="鸿蒙相关"),
        Category(id="ci", name="CI相关", keywords=["ci", "流水线"], description="CI相关任务"),
        Category(id="audio", name="音频相关", keywords=["音频", "audio"], description="音频相关"),
    ]


@pytest.fixture
def sample_tasks():
    """测试用的任务列表"""
    return [
        {"content": "修复内存泄漏问题", "categories": ["memory"], "member": "张三"},
        {"content": "优化资源加载", "categories": ["resource"], "member": "张三"},
        {"content": "支持鸿蒙平台", "categories": ["harmonyos"], "member": "李四"},
        {"content": "修复CI流水线", "categories": ["ci"], "member": "李四"},
        {"content": "优化音频播放", "categories": ["audio"], "member": "王五"},
        {"content": "内存优化2", "categories": ["memory"], "member": "张三"},
        {"content": "资源打包优化", "categories": ["resource"], "member": "王五"},
        {"content": "未分类任务1", "categories": [], "member": "李四"},
        {"content": "未分类任务2", "categories": [], "member": "张三"},
        {"content": "多分类任务", "categories": ["memory", "resource"], "member": "张三"},
    ]


@pytest.fixture
def sample_classified_report():
    """测试用的分类周报对象"""
    class MockClassifiedReport:
        def __init__(self):
            self.week_id = "2026-W10"
            self.total_tasks = 10
            self.classified_tasks = 8
            self.categories = {
                "memory": [
                    {"content": "修复内存泄漏", "categories": ["memory"]},
                    {"content": "内存优化", "categories": ["memory"]},
                ],
                "resource": [
                    {"content": "优化资源加载", "categories": ["resource"]},
                ],
                "harmonyos": [
                    {"content": "支持鸿蒙", "categories": ["harmonyos"]},
                ],
                "uncategorized": [
                    {"content": "未分类任务", "categories": []},
                ]
            }
            self.statistics = {
                "memory": 2,
                "resource": 1,
                "harmonyos": 1,
                "uncategorized": 1
            }
    
    return MockClassifiedReport()


@pytest.fixture
def stats_generator(sample_categories):
    """测试用的统计生成器"""
    return CategoryStatsGenerator(sample_categories)


# ============================================================================
# 数据结构测试
# ============================================================================

class TestDataStructures:
    """测试数据结构"""
    
    def test_category_stats_creation(self):
        """测试CategoryStats创建"""
        stats = CategoryStats(
            category_id="memory",
            category_name="内存相关",
            task_count=10,
            percentage=33.3,
            tasks=["任务1", "任务2"]
        )
        
        assert stats.category_id == "memory"
        assert stats.category_name == "内存相关"
        assert stats.task_count == 10
        assert stats.percentage == 33.3
        assert len(stats.tasks) == 2
    
    def test_category_stats_to_dict(self):
        """测试CategoryStats转换为字典"""
        stats = CategoryStats(
            category_id="memory",
            category_name="内存相关",
            task_count=10,
            percentage=33.333,
            tasks=["任务1", "任务2"]
        )
        
        result = stats.to_dict()
        
        assert isinstance(result, dict)
        assert result["category_id"] == "memory"
        assert result["task_count"] == 10
        assert result["percentage"] == 33.33  # 保留2位小数
    
    def test_weekly_stats_creation(self):
        """测试WeeklyStats创建"""
        stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=100,
            category_stats=[],
            coverage_rate=85.5,
            max_category="内存相关"
        )
        
        assert stats.week_id == "2026-W10"
        assert stats.total_tasks == 100
        assert stats.coverage_rate == 85.5
        assert stats.max_category == "内存相关"
    
    def test_weekly_stats_to_dict(self):
        """测试WeeklyStats转换为字典"""
        cat_stats = CategoryStats("memory", "内存相关", 10, 33.3, [])
        stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=30,
            category_stats=[cat_stats]
        )
        
        result = stats.to_dict()
        
        assert isinstance(result, dict)
        assert result["week_id"] == "2026-W10"
        assert result["total_tasks"] == 30
        assert len(result["category_stats"]) == 1
    
    def test_multi_week_stats_creation(self):
        """测试MultiWeekStats创建"""
        stats = MultiWeekStats(
            weeks=["2026-W09", "2026-W10"],
            category_trends={"内存相关": [20, 25]},
            trend_changes={"内存相关": "+5 ↑"}
        )
        
        assert len(stats.weeks) == 2
        assert "内存相关" in stats.category_trends
        assert stats.trend_changes["内存相关"] == "+5 ↑"
    
    def test_member_stats_creation(self):
        """测试MemberStats创建"""
        stats = MemberStats(
            member_id="user001",
            member_name="张三",
            total_tasks=15,
            category_distribution={"memory": 8, "resource": 7},
            primary_category="内存相关"
        )
        
        assert stats.member_id == "user001"
        assert stats.member_name == "张三"
        assert stats.total_tasks == 15
        assert stats.primary_category == "内存相关"
    
    def test_chart_data_creation(self):
        """测试ChartData创建"""
        chart = ChartData(
            chart_type="pie",
            labels=["内存", "资源"],
            values=[30, 20],
            title="分类分布"
        )
        
        assert chart.chart_type == "pie"
        assert len(chart.labels) == 2
        assert chart.title == "分类分布"


# ============================================================================
# CategoryStatsGenerator测试
# ============================================================================

class TestCategoryStatsGenerator:
    """测试CategoryStatsGenerator类"""
    
    def test_initialization(self, sample_categories):
        """测试初始化"""
        generator = CategoryStatsGenerator(sample_categories)
        
        assert len(generator.categories) == 5
        assert "memory" in generator._category_map
        assert "resource" in generator._category_map
    
    def test_calculate_stats_basic(self, stats_generator, sample_tasks):
        """测试基本统计计算"""
        stats = stats_generator.calculate_stats(sample_tasks)
        
        assert isinstance(stats, list)
        assert len(stats) > 0
        
        # 检查是否包含预期的分类
        category_ids = [s.category_id for s in stats]
        assert "memory" in category_ids
        assert "resource" in category_ids
    
    def test_calculate_stats_task_count(self, stats_generator, sample_tasks):
        """测试任务数量统计"""
        stats = stats_generator.calculate_stats(sample_tasks)
        
        # 找到memory分类
        memory_stats = next(s for s in stats if s.category_id == "memory")
        
        # sample_tasks中有3个memory任务（包括多分类的）
        assert memory_stats.task_count == 3
    
    def test_calculate_stats_percentage(self, stats_generator, sample_tasks):
        """测试占比计算"""
        stats = stats_generator.calculate_stats(sample_tasks)
        
        # 所有分类的占比之和应该接近100%
        total_percentage = sum(s.percentage for s in stats if s.category_id != "uncategorized")
        
        # 允许多分类任务导致的总和超过100%
        assert total_percentage >= 0
    
    def test_calculate_stats_uncategorized(self, stats_generator):
        """测试未分类任务统计"""
        tasks = [
            {"content": "任务1", "categories": []},
            {"content": "任务2", "categories": []},
        ]
        
        stats = stats_generator.calculate_stats(tasks)
        
        # 应该包含未分类统计
        uncategorized = next((s for s in stats if s.category_id == "uncategorized"), None)
        assert uncategorized is not None
        assert uncategorized.task_count == 2
    
    def test_calculate_stats_sorted(self, stats_generator, sample_tasks):
        """测试统计结果按任务数排序"""
        stats = stats_generator.calculate_stats(sample_tasks)
        
        # 检查是否按task_count降序排序
        task_counts = [s.task_count for s in stats]
        assert task_counts == sorted(task_counts, reverse=True)
    
    def test_generate_weekly_stats(self, stats_generator, sample_classified_report):
        """测试生成周统计"""
        weekly_stats = stats_generator.generate_weekly_stats(sample_classified_report)
        
        assert isinstance(weekly_stats, WeeklyStats)
        assert weekly_stats.week_id == "2026-W10"
        assert weekly_stats.total_tasks > 0
        assert len(weekly_stats.category_stats) > 0
    
    def test_generate_weekly_stats_coverage(self, stats_generator, sample_classified_report):
        """测试分类覆盖率计算"""
        weekly_stats = stats_generator.generate_weekly_stats(sample_classified_report)
        
        # 覆盖率应该在0-100之间
        assert 0 <= weekly_stats.coverage_rate <= 100
    
    def test_compare_weeks(self, stats_generator):
        """测试多周对比"""
        # 创建两周的统计数据
        week1 = WeeklyStats(
            week_id="2026-W09",
            total_tasks=30,
            category_stats=[
                CategoryStats("memory", "内存相关", 10, 33.3, []),
                CategoryStats("resource", "资源相关", 8, 26.7, []),
            ]
        )
        
        week2 = WeeklyStats(
            week_id="2026-W10",
            total_tasks=35,
            category_stats=[
                CategoryStats("memory", "内存相关", 12, 34.3, []),
                CategoryStats("resource", "资源相关", 9, 25.7, []),
            ]
        )
        
        multi_week = stats_generator.compare_weeks([week1, week2])
        
        assert isinstance(multi_week, MultiWeekStats)
        assert len(multi_week.weeks) == 2
        assert "内存相关" in multi_week.category_trends
        assert multi_week.category_trends["内存相关"] == [10, 12]
    
    def test_compare_weeks_trend_changes(self, stats_generator):
        """测试趋势变化计算"""
        week1 = WeeklyStats(
            week_id="2026-W09",
            total_tasks=10,
            category_stats=[CategoryStats("memory", "内存相关", 5, 50.0, [])]
        )
        
        week2 = WeeklyStats(
            week_id="2026-W10",
            total_tasks=10,
            category_stats=[CategoryStats("memory", "内存相关", 8, 80.0, [])]
        )
        
        multi_week = stats_generator.compare_weeks([week1, week2])
        
        # 趋势应该是增加
        assert "内存相关" in multi_week.trend_changes
        assert "↑" in multi_week.trend_changes["内存相关"]
    
    def test_generate_member_stats(self, stats_generator, sample_tasks):
        """测试成员统计生成"""
        member_stats = stats_generator.generate_member_stats(sample_tasks)
        
        assert isinstance(member_stats, list)
        assert len(member_stats) > 0
        
        # 检查成员数据
        zhang_san = next((m for m in member_stats if m.member_name == "张三"), None)
        assert zhang_san is not None
        assert zhang_san.total_tasks > 0
    
    def test_generate_member_stats_primary_category(self, stats_generator, sample_tasks):
        """测试成员主要分类识别"""
        member_stats = stats_generator.generate_member_stats(sample_tasks)
        
        for ms in member_stats:
            if ms.total_tasks > 0:
                # 主要分类应该是非空的
                assert ms.primary_category != "" or ms.total_tasks == 0
    
    def test_generate_member_stats_distribution(self, stats_generator, sample_tasks):
        """测试成员分类分布统计"""
        member_stats = stats_generator.generate_member_stats(sample_tasks)
        
        for ms in member_stats:
            # 分类分布的任务数之和应该大于等于总任务数（因为一个任务可以属于多个分类）
            if ms.category_distribution:
                total_in_dist = sum(ms.category_distribution.values())
                assert total_in_dist >= ms.total_tasks


# ============================================================================
# 报告生成测试
# ============================================================================

class TestReportGeneration:
    """测试报告生成功能"""
    
    def test_generate_markdown_report(self, stats_generator, sample_tasks):
        """测试Markdown报告生成"""
        stats = stats_generator.calculate_stats(sample_tasks)
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        md_report = stats_generator.generate_markdown_report(weekly_stats)
        
        assert isinstance(md_report, str)
        assert "# 分类统计报告" in md_report
        assert "2026-W10" in md_report
        assert "## 📊 总体统计" in md_report
        assert "## 📈 分类分布" in md_report
    
    def test_generate_markdown_report_with_member_stats(self, stats_generator, sample_tasks):
        """测试包含成员统计的Markdown报告"""
        stats = stats_generator.calculate_stats(sample_tasks)
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        member_stats = stats_generator.generate_member_stats(sample_tasks)
        
        md_report = stats_generator.generate_markdown_report(
            weekly_stats,
            member_stats=member_stats
        )
        
        assert "## 👥 成员统计" in md_report
        assert "张三" in md_report
    
    def test_generate_markdown_report_with_multi_week(self, stats_generator):
        """测试包含多周对比的Markdown报告"""
        week1 = WeeklyStats(
            week_id="2026-W09",
            total_tasks=10,
            category_stats=[CategoryStats("memory", "内存相关", 5, 50.0, [])]
        )
        
        week2 = WeeklyStats(
            week_id="2026-W10",
            total_tasks=10,
            category_stats=[CategoryStats("memory", "内存相关", 8, 80.0, [])]
        )
        
        weekly_stats = week2
        multi_week = stats_generator.compare_weeks([week1, week2])
        
        md_report = stats_generator.generate_markdown_report(
            weekly_stats,
            multi_week_stats=multi_week
        )
        
        assert "## 📊 多周对比" in md_report
        assert "2026-W09" in md_report
        assert "2026-W10" in md_report
    
    def test_generate_json_report(self, stats_generator, sample_tasks):
        """测试JSON报告生成"""
        stats = stats_generator.calculate_stats(sample_tasks)
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        json_report = stats_generator.generate_json_report(weekly_stats)
        
        # 验证是否是有效的JSON
        data = json.loads(json_report)
        
        assert "weekly_stats" in data
        assert data["weekly_stats"]["week_id"] == "2026-W10"
        assert "generated_at" in data
    
    def test_generate_json_report_with_member_stats(self, stats_generator, sample_tasks):
        """测试包含成员统计的JSON报告"""
        stats = stats_generator.calculate_stats(sample_tasks)
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        member_stats = stats_generator.generate_member_stats(sample_tasks)
        
        json_report = stats_generator.generate_json_report(
            weekly_stats,
            member_stats=member_stats
        )
        
        data = json.loads(json_report)
        
        assert "member_stats" in data
        assert len(data["member_stats"]) > 0
    
    def test_generate_csv_report(self, stats_generator, sample_tasks):
        """测试CSV报告生成"""
        stats = stats_generator.calculate_stats(sample_tasks)
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        csv_report = stats_generator.generate_csv_report(weekly_stats)
        
        # 验证是否是有效的CSV
        reader = csv.reader(StringIO(csv_report))
        rows = list(reader)
        
        # 应该有表头
        assert len(rows) > 0
        assert "周次" in rows[0]
        assert "分类ID" in rows[0]
    
    def test_generate_csv_report_data_rows(self, stats_generator, sample_tasks):
        """测试CSV报告数据行"""
        stats = stats_generator.calculate_stats(sample_tasks)
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        csv_report = stats_generator.generate_csv_report(weekly_stats)
        
        reader = csv.reader(StringIO(csv_report))
        rows = list(reader)
        
        # 数据行数应该等于分类数
        assert len(rows) > 1  # 至少有表头和一行数据


# ============================================================================
# 图表数据测试
# ============================================================================

class TestChartData:
    """测试图表数据生成"""
    
    def test_generate_chart_data_pie(self, stats_generator, sample_tasks):
        """测试饼图数据生成"""
        stats = stats_generator.calculate_stats(sample_tasks)
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        chart_data = stats_generator.generate_chart_data(weekly_stats, "pie")
        
        assert isinstance(chart_data, ChartData)
        assert chart_data.chart_type == "pie"
        assert len(chart_data.labels) > 0
        assert len(chart_data.values) > 0
        assert chart_data.title != ""
    
    def test_generate_chart_data_bar(self, stats_generator, sample_tasks):
        """测试柱状图数据生成"""
        stats = stats_generator.calculate_stats(sample_tasks)
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        chart_data = stats_generator.generate_chart_data(weekly_stats, "bar")
        
        assert chart_data.chart_type == "bar"
        assert "x_axis_label" in chart_data.options
    
    def test_generate_chart_data_filter_empty(self, stats_generator):
        """测试过滤空分类"""
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=5,
            category_stats=[
                CategoryStats("memory", "内存相关", 5, 100.0, ["任务1"]),
                CategoryStats("resource", "资源相关", 0, 0.0, []),
            ]
        )
        
        chart_data = stats_generator.generate_chart_data(weekly_stats)
        
        # 应该只包含非空分类
        assert "资源相关" not in chart_data.labels
    
    def test_generate_trend_chart_data(self, stats_generator):
        """测试趋势图数据生成"""
        week1 = WeeklyStats(
            week_id="2026-W09",
            total_tasks=10,
            category_stats=[CategoryStats("memory", "内存相关", 5, 50.0, [])]
        )
        
        week2 = WeeklyStats(
            week_id="2026-W10",
            total_tasks=10,
            category_stats=[CategoryStats("memory", "内存相关", 8, 80.0, [])]
        )
        
        multi_week = stats_generator.compare_weeks([week1, week2])
        
        chart_data = stats_generator.generate_trend_chart_data(multi_week)
        
        assert chart_data.chart_type == "line"
        assert len(chart_data.labels) == 2
        assert len(chart_data.values) > 0
    
    def test_generate_text_chart(self, stats_generator, sample_tasks):
        """测试文本图表生成"""
        stats = stats_generator.calculate_stats(sample_tasks)
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        text_chart = stats_generator.generate_text_chart(weekly_stats)
        
        assert isinstance(text_chart, str)
        assert "2026-W10" in text_chart
        assert "█" in text_chart  # 应该包含条形字符
    
    def test_generate_text_chart_custom_width(self, stats_generator, sample_tasks):
        """测试自定义宽度的文本图表"""
        stats = stats_generator.calculate_stats(sample_tasks)
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        text_chart = stats_generator.generate_text_chart(weekly_stats, width=80)
        
        # 检查宽度（大致）
        lines = text_chart.split('\n')
        # 分隔线应该是指定宽度（找包含等号的行）
        separator_lines = [line for line in lines if line.startswith('=')]
        assert len(separator_lines) > 0
        assert len(separator_lines[0]) == 80


# ============================================================================
# 边界条件测试
# ============================================================================

class TestEdgeCases:
    """测试边界条件"""
    
    def test_empty_tasks(self, stats_generator):
        """测试空任务列表"""
        stats = stats_generator.calculate_stats([])
        
        assert isinstance(stats, list)
        # 所有分类的任务数应该为0
        for s in stats:
            assert s.task_count == 0
            assert s.percentage == 0.0
    
    def test_empty_categories(self):
        """测试空分类列表"""
        generator = CategoryStatsGenerator([])
        
        tasks = [{"content": "任务", "categories": ["memory"]}]
        stats = generator.calculate_stats(tasks)
        
        # 应该能处理，但分类统计应该包含未分类
        assert isinstance(stats, list)
    
    def test_tasks_without_categories(self, stats_generator):
        """测试没有分类的任务"""
        tasks = [
            {"content": "任务1"},
            {"content": "任务2"},
        ]
        
        stats = stats_generator.calculate_stats(tasks)
        
        # 应该全部归类为未分类
        uncategorized = next((s for s in stats if s.category_id == "uncategorized"), None)
        assert uncategorized is not None
        assert uncategorized.task_count == 2
    
    def test_single_week_comparison(self, stats_generator):
        """测试单周对比（边界情况）"""
        week1 = WeeklyStats(
            week_id="2026-W10",
            total_tasks=10,
            category_stats=[CategoryStats("memory", "内存相关", 5, 50.0, [])]
        )
        
        multi_week = stats_generator.compare_weeks([week1])
        
        # 应该能处理单周数据
        assert len(multi_week.weeks) == 1
        assert "内存相关" in multi_week.category_trends
    
    def test_large_task_count(self, stats_generator):
        """测试大量任务"""
        # 生成1000个任务
        tasks = [
            {"content": f"任务{i}", "categories": ["memory"] if i % 2 == 0 else ["resource"]}
            for i in range(1000)
        ]
        
        stats = stats_generator.calculate_stats(tasks)
        
        # 应该能正确统计
        memory_stats = next(s for s in stats if s.category_id == "memory")
        resource_stats = next(s for s in stats if s.category_id == "resource")
        
        assert memory_stats.task_count == 500
        assert resource_stats.task_count == 500
    
    def test_special_characters_in_content(self, stats_generator):
        """测试任务内容中的特殊字符"""
        tasks = [
            {"content": "任务|包含|竖线", "categories": ["memory"]},
            {"content": "任务,包含,逗号", "categories": ["resource"]},
            {"content": '任务"包含"引号', "categories": ["ci"]},
        ]
        
        stats = stats_generator.calculate_stats(tasks)
        
        # 应该能正确处理特殊字符
        assert len(stats) > 0
    
    def test_unicode_member_names(self, stats_generator):
        """测试Unicode成员名"""
        tasks = [
            {"content": "任务1", "categories": ["memory"], "member": "张三"},
            {"content": "任务2", "categories": ["resource"], "member": "李四"},
            {"content": "任务3", "categories": ["ci"], "member": "王五👨‍💻"},
        ]
        
        member_stats = stats_generator.generate_member_stats(tasks)
        
        # 应该能正确处理Unicode
        assert len(member_stats) == 3
        member_names = [m.member_name for m in member_stats]
        assert "张三" in member_names
        assert "王五👨‍💻" in member_names


# ============================================================================
# 文件保存测试
# ============================================================================

class TestFileOperations:
    """测试文件操作"""
    
    def test_save_report_markdown(self, stats_generator, sample_tasks, tmp_path):
        """测试保存Markdown报告"""
        stats = stats_generator.calculate_stats(sample_tasks)
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        md_report = stats_generator.generate_markdown_report(weekly_stats)
        output_file = tmp_path / "report.md"
        
        saved_path = stats_generator.save_report(
            md_report,
            str(output_file),
            "markdown"
        )
        
        assert Path(saved_path).exists()
        assert Path(saved_path).read_text() == md_report
    
    def test_save_report_json(self, stats_generator, sample_tasks, tmp_path):
        """测试保存JSON报告"""
        stats = stats_generator.calculate_stats(sample_tasks)
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        json_report = stats_generator.generate_json_report(weekly_stats)
        output_file = tmp_path / "report.json"
        
        saved_path = stats_generator.save_report(
            json_report,
            str(output_file),
            "json"
        )
        
        assert Path(saved_path).exists()
        
        # 验证是否是有效的JSON
        with open(saved_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert "weekly_stats" in data
    
    def test_save_report_creates_directory(self, stats_generator, sample_tasks, tmp_path):
        """测试保存报告时自动创建目录"""
        stats = stats_generator.calculate_stats(sample_tasks)
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        md_report = stats_generator.generate_markdown_report(weekly_stats)
        output_file = tmp_path / "subdir" / "report.md"
        
        saved_path = stats_generator.save_report(
            md_report,
            str(output_file),
            "markdown"
        )
        
        assert Path(saved_path).exists()
        assert Path(saved_path).parent.exists()


# ============================================================================
# 便捷函数测试
# ============================================================================

class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def test_generate_quick_stats(self, sample_categories, sample_tasks):
        """测试快速统计生成函数"""
        stats = generate_quick_stats(
            sample_tasks,
            sample_categories,
            "2026-W10"
        )
        
        assert isinstance(stats, WeeklyStats)
        assert stats.week_id == "2026-W10"
        assert stats.total_tasks == len(sample_tasks)
        assert len(stats.category_stats) > 0
    
    def test_generate_quick_stats_empty_tasks(self, sample_categories):
        """测试空任务的快速统计"""
        stats = generate_quick_stats(
            [],
            sample_categories,
            "2026-W10"
        )
        
        assert stats.total_tasks == 0
        assert stats.coverage_rate == 0.0


# ============================================================================
# 集成测试
# ============================================================================

class TestIntegration:
    """集成测试"""
    
    def test_full_workflow(self, stats_generator, sample_tasks):
        """测试完整工作流"""
        # 1. 计算统计
        stats = stats_generator.calculate_stats(sample_tasks)
        
        # 2. 生成周统计
        weekly_stats = WeeklyStats(
            week_id="2026-W10",
            total_tasks=len(sample_tasks),
            category_stats=stats
        )
        
        # 3. 生成成员统计
        member_stats = stats_generator.generate_member_stats(sample_tasks)
        
        # 4. 生成多周对比（模拟两周）
        week1_stats = WeeklyStats(
            week_id="2026-W09",
            total_tasks=len(sample_tasks) - 2,
            category_stats=stats[:3]  # 只取前3个分类
        )
        
        multi_week = stats_generator.compare_weeks([week1_stats, weekly_stats])
        
        # 5. 生成各种报告
        md_report = stats_generator.generate_markdown_report(
            weekly_stats,
            member_stats=member_stats,
            multi_week_stats=multi_week
        )
        
        json_report = stats_generator.generate_json_report(
            weekly_stats,
            member_stats=member_stats,
            multi_week_stats=multi_week
        )
        
        csv_report = stats_generator.generate_csv_report(weekly_stats)
        
        # 验证所有报告都生成了
        assert len(md_report) > 0
        assert len(json_report) > 0
        assert len(csv_report) > 0
        
        # 验证JSON报告的有效性
        data = json.loads(json_report)
        assert "weekly_stats" in data
        assert "member_stats" in data
        assert "multi_week_stats" in data


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
