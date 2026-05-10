"""
分类统计模块

对分类后的周报进行统计分析，生成统计报告。
支持多周对比、按成员统计、多种导出格式。
"""

import json
import csv
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from ..core.category_parser import Category

logger = logging.getLogger(__name__)


# ============================================================================
# 数据结构定义
# ============================================================================

@dataclass
class CategoryStats:
    """单个分类的统计数据"""
    category_id: str                          # 分类ID
    category_name: str                        # 分类名称
    task_count: int                           # 任务数量
    percentage: float                         # 占比（0-100）
    tasks: List[str] = field(default_factory=list)  # 任务内容列表
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "category_id": self.category_id,
            "category_name": self.category_name,
            "task_count": self.task_count,
            "percentage": round(self.percentage, 2),
            "tasks": self.tasks
        }


@dataclass
class WeeklyStats:
    """单周的统计数据"""
    week_id: str                              # 周次标识，如 "2026-W10"
    total_tasks: int                          # 总任务数
    category_stats: List[CategoryStats] = field(default_factory=list)  # 分类统计
    timestamp: datetime = field(default_factory=datetime.now)  # 统计时间
    coverage_rate: float = 0.0                # 分类覆盖率
    max_category: str = ""                    # 任务最多的分类
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "week_id": self.week_id,
            "total_tasks": self.total_tasks,
            "category_stats": [cs.to_dict() for cs in self.category_stats],
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "coverage_rate": round(self.coverage_rate, 2),
            "max_category": self.max_category
        }


@dataclass
class MultiWeekStats:
    """多周对比统计数据"""
    weeks: List[str] = field(default_factory=list)  # 周次列表
    category_trends: Dict[str, List[int]] = field(default_factory=dict)  # 分类趋势
    total_stats: Optional[CategoryStats] = None  # 总体统计
    trend_changes: Dict[str, str] = field(default_factory=dict)  # 趋势变化（↑↓→）
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "weeks": self.weeks,
            "category_trends": self.category_trends,
            "total_stats": self.total_stats.to_dict() if self.total_stats else None,
            "trend_changes": self.trend_changes
        }


@dataclass
class MemberStats:
    """成员统计数据"""
    member_id: str                            # 成员ID
    member_name: str                          # 成员名称
    total_tasks: int                          # 总任务数
    category_distribution: Dict[str, int] = field(default_factory=dict)  # 分类分布
    primary_category: str = ""                # 主要分类
    task_list: List[Dict[str, Any]] = field(default_factory=list)  # 任务列表
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "member_id": self.member_id,
            "member_name": self.member_name,
            "total_tasks": self.total_tasks,
            "category_distribution": self.category_distribution,
            "primary_category": self.primary_category,
            "task_list": self.task_list
        }


@dataclass
class ChartData:
    """图表数据结构"""
    chart_type: str                           # 图表类型：pie, bar, line
    labels: List[str] = field(default_factory=list)
    values: List[Any] = field(default_factory=list)
    title: str = ""
    options: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "chart_type": self.chart_type,
            "labels": self.labels,
            "values": self.values,
            "title": self.title,
            "options": self.options
        }


# ============================================================================
# 分类统计生成器
# ============================================================================

class CategoryStatsGenerator:
    """
    分类统计生成器
    
    统计各类别的任务数量和占比，生成多种格式的统计报告。
    支持多周对比和按成员统计。
    """
    
    def __init__(self, categories: List[Category]):
        """
        初始化统计生成器
        
        Args:
            categories: 分类列表
        """
        self.categories = categories
        self._category_map: Dict[str, Category] = {
            cat.id: cat for cat in categories
        }
        
        logger.info(f"初始化分类统计生成器，分类数: {len(categories)}")
    
    def calculate_stats(self, tasks: List[Dict]) -> List[CategoryStats]:
        """
        统计各类别的任务数量和占比
        
        Args:
            tasks: 任务列表，每个任务应包含：
                   - content: 任务内容
                   - categories: 分类ID列表（可选）
                   
        Returns:
            分类统计列表
        """
        # 初始化统计
        category_tasks: Dict[str, List[str]] = defaultdict(list)
        total_tasks = len(tasks)
        
        # 统计每个分类的任务
        for task in tasks:
            content = task.get("content", "")
            task_categories = task.get("categories", [])
            
            if task_categories:
                for cat_id in task_categories:
                    category_tasks[cat_id].append(content)
            else:
                # 未分类任务
                category_tasks["uncategorized"].append(content)
        
        # 生成统计结果
        stats = []
        for category in self.categories:
            cat_tasks = category_tasks.get(category.id, [])
            count = len(cat_tasks)
            percentage = (count / total_tasks * 100) if total_tasks > 0 else 0.0
            
            stats.append(CategoryStats(
                category_id=category.id,
                category_name=category.name,
                task_count=count,
                percentage=percentage,
                tasks=cat_tasks
            ))
        
        # 添加未分类统计
        uncategorized_tasks = category_tasks.get("uncategorized", [])
        if uncategorized_tasks:
            stats.append(CategoryStats(
                category_id="uncategorized",
                category_name="未分类",
                task_count=len(uncategorized_tasks),
                percentage=(len(uncategorized_tasks) / total_tasks * 100) if total_tasks > 0 else 0.0,
                tasks=uncategorized_tasks
            ))
        
        # 按任务数排序
        stats.sort(key=lambda x: x.task_count, reverse=True)
        
        return stats
    
    def generate_weekly_stats(
        self,
        classified_report: Any,
        week_id: Optional[str] = None
    ) -> WeeklyStats:
        """
        生成周统计报告
        
        Args:
            classified_report: 分类后的周报对象（ClassifiedWeeklyReport）
            week_id: 周次标识（可选，从report中提取）
            
        Returns:
            WeeklyStats对象
        """
        # 提取周次
        if not week_id:
            week_id = getattr(classified_report, 'week_id', 'unknown')
        
        # 提取任务列表
        tasks = self._extract_tasks_from_report(classified_report)
        
        # 计算分类统计
        category_stats = self.calculate_stats(tasks)
        
        # 计算覆盖率（排除未分类）
        total_tasks = len(tasks)
        classified_count = sum(
            cs.task_count for cs in category_stats 
            if cs.category_id != "uncategorized"
        )
        coverage_rate = (classified_count / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # 找出最大分类（排除未分类）
        max_category = ""
        for cs in category_stats:
            if cs.category_id != "uncategorized" and cs.task_count > 0:
                max_category = cs.category_name
                break
        
        return WeeklyStats(
            week_id=week_id,
            total_tasks=total_tasks,
            category_stats=category_stats,
            coverage_rate=coverage_rate,
            max_category=max_category
        )
    
    def _extract_tasks_from_report(self, report: Any) -> List[Dict]:
        """
        从分类周报中提取任务列表
        
        Args:
            report: ClassifiedWeeklyReport对象
            
        Returns:
            任务列表
        """
        tasks = []
        
        # 尝试从categories字段提取
        if hasattr(report, 'categories'):
            for cat_id, cat_tasks in report.categories.items():
                for task in cat_tasks:
                    if isinstance(task, dict):
                        tasks.append(task)
                    elif isinstance(task, str):
                        tasks.append({
                            "content": task,
                            "categories": [cat_id]
                        })
        
        # 如果没有categories字段，尝试从tasks字段提取
        elif hasattr(report, 'tasks'):
            for task in report.tasks:
                if isinstance(task, dict):
                    tasks.append(task)
        
        return tasks
    
    def compare_weeks(self, weekly_stats_list: List[WeeklyStats]) -> MultiWeekStats:
        """
        多周对比统计
        
        Args:
            weekly_stats_list: 多个WeeklyStats对象
            
        Returns:
            MultiWeekStats对象
        """
        if not weekly_stats_list:
            return MultiWeekStats()
        
        # 提取周次
        weeks = [ws.week_id for ws in weekly_stats_list]
        
        # 收集所有分类ID
        all_category_ids = set()
        for ws in weekly_stats_list:
            for cs in ws.category_stats:
                all_category_ids.add(cs.category_id)
        
        # 构建分类趋势数据
        category_trends: Dict[str, List[int]] = {}
        for cat_id in all_category_ids:
            cat_name = self._get_category_name(cat_id)
            trends = []
            for ws in weekly_stats_list:
                # 查找该分类在当前周的任务数
                count = 0
                for cs in ws.category_stats:
                    if cs.category_id == cat_id:
                        count = cs.task_count
                        break
                trends.append(count)
            category_trends[cat_name] = trends
        
        # 计算总体统计
        total_tasks = sum(ws.total_tasks for ws in weekly_stats_list)
        all_tasks = []
        for ws in weekly_stats_list:
            for cs in ws.category_stats:
                all_tasks.extend(cs.tasks)
        
        total_stats = CategoryStats(
            category_id="total",
            category_name="总计",
            task_count=total_tasks,
            percentage=100.0,
            tasks=all_tasks
        )
        
        # 计算趋势变化
        trend_changes = {}
        for cat_name, trends in category_trends.items():
            if len(trends) >= 2:
                change = trends[-1] - trends[-2]
                if change > 0:
                    trend_changes[cat_name] = f"+{change} ↑"
                elif change < 0:
                    trend_changes[cat_name] = f"{change} ↓"
                else:
                    trend_changes[cat_name] = "0 →"
            else:
                trend_changes[cat_name] = "-"
        
        return MultiWeekStats(
            weeks=weeks,
            category_trends=category_trends,
            total_stats=total_stats,
            trend_changes=trend_changes
        )
    
    def generate_member_stats(
        self,
        tasks: List[Dict],
        member_field: str = "member"
    ) -> List[MemberStats]:
        """
        按成员统计分类分布
        
        Args:
            tasks: 任务列表，每个任务应包含成员信息
            member_field: 成员字段名
            
        Returns:
            成员统计列表
        """
        # 按成员分组
        member_tasks: Dict[str, List[Dict]] = defaultdict(list)
        
        for task in tasks:
            member_info = task.get(member_field)
            if member_info:
                # 支持字符串或字典格式的成员信息
                if isinstance(member_info, dict):
                    member_id = member_info.get("id", member_info.get("name", "unknown"))
                    member_name = member_info.get("name", member_id)
                else:
                    member_id = str(member_info)
                    member_name = str(member_info)
                
                member_tasks[member_id].append({
                    **task,
                    "_member_name": member_name
                })
        
        # 生成成员统计
        member_stats_list = []
        
        for member_id, member_task_list in member_tasks.items():
            member_name = member_task_list[0].get("_member_name", member_id)
            
            # 统计分类分布
            category_distribution: Dict[str, int] = defaultdict(int)
            for task in member_task_list:
                task_categories = task.get("categories", [])
                if task_categories:
                    for cat_id in task_categories:
                        category_distribution[cat_id] += 1
                else:
                    category_distribution["uncategorized"] += 1
            
            # 找出主要分类
            primary_category = ""
            if category_distribution:
                primary_cat_id = max(category_distribution.items(), key=lambda x: x[1])[0]
                primary_category = self._get_category_name(primary_cat_id)
            
            # 准备任务列表（移除内部字段）
            task_list = [
                {k: v for k, v in task.items() if not k.startswith("_")}
                for task in member_task_list
            ]
            
            member_stats = MemberStats(
                member_id=member_id,
                member_name=member_name,
                total_tasks=len(member_task_list),
                category_distribution=dict(category_distribution),
                primary_category=primary_category,
                task_list=task_list
            )
            
            member_stats_list.append(member_stats)
        
        # 按任务数排序
        member_stats_list.sort(key=lambda x: x.total_tasks, reverse=True)
        
        return member_stats_list
    
    def generate_markdown_report(
        self,
        stats: WeeklyStats,
        member_stats: Optional[List[MemberStats]] = None,
        multi_week_stats: Optional[MultiWeekStats] = None
    ) -> str:
        """
        生成Markdown格式的统计报告
        
        Args:
            stats: 周统计数据
            member_stats: 成员统计（可选）
            multi_week_stats: 多周对比统计（可选）
            
        Returns:
            Markdown字符串
        """
        lines = []
        
        # 标题
        lines.append(f"# 分类统计报告 - {stats.week_id}")
        lines.append("")
        lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 总体统计
        lines.append("## 📊 总体统计")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|------|------|")
        lines.append(f"| 总任务数 | {stats.total_tasks} |")
        lines.append(f"| 分类覆盖率 | {stats.coverage_rate:.1f}% |")
        lines.append(f"| 最大分类 | {stats.max_category} |")
        lines.append("")
        
        # 分类分布
        lines.append("## 📈 分类分布")
        lines.append("")
        lines.append("| 分类 | 任务数 | 占比 |")
        lines.append("|------|--------|------|")
        
        for cs in stats.category_stats:
            if cs.task_count > 0:
                lines.append(f"| {cs.category_name} | {cs.task_count} | {cs.percentage:.1f}% |")
        
        lines.append("")
        
        # 多周对比（如果有）
        if multi_week_stats and multi_week_stats.weeks:
            lines.append("## 📊 多周对比")
            lines.append("")
            
            # 构建表格
            headers = ["周次"] + list(multi_week_stats.category_trends.keys())
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join(["------"] * len(headers)) + " |")
            
            # 每周数据
            for i, week in enumerate(multi_week_stats.weeks):
                row = [week]
                for cat_name in multi_week_stats.category_trends.keys():
                    trends = multi_week_stats.category_trends[cat_name]
                    row.append(str(trends[i]) if i < len(trends) else "0")
                lines.append("| " + " | ".join(row) + " |")
            
            # 变化趋势
            if multi_week_stats.trend_changes:
                row = ["变化"]
                for cat_name in multi_week_stats.category_trends.keys():
                    change = multi_week_stats.trend_changes.get(cat_name, "-")
                    row.append(change)
                lines.append("| " + " | ".join(row) + " |")
            
            lines.append("")
        
        # 详细统计
        lines.append("## 📋 详细统计")
        lines.append("")
        
        for cs in stats.category_stats:
            if cs.task_count > 0:
                lines.append(f"### {cs.category_name} ({cs.task_count}个任务)")
                lines.append("")
                
                # 显示任务列表（限制显示数量）
                max_display = 10
                for i, task in enumerate(cs.tasks[:max_display]):
                    lines.append(f"- {task}")
                
                if len(cs.tasks) > max_display:
                    lines.append(f"- ... 还有 {len(cs.tasks) - max_display} 个任务")
                
                lines.append("")
        
        # 成员统计（如果有）
        if member_stats:
            lines.append("## 👥 成员统计")
            lines.append("")
            lines.append("| 成员 | 总任务 | 主要分类 | 分类分布 |")
            lines.append("|------|--------|----------|----------|")
            
            for ms in member_stats[:10]:  # 只显示前10个成员
                dist_str = ", ".join([
                    f"{self._get_category_name(k)}:{v}"
                    for k, v in list(ms.category_distribution.items())[:3]
                ])
                lines.append(f"| {ms.member_name} | {ms.total_tasks} | {ms.primary_category} | {dist_str} |")
            
            lines.append("")
        
        # 页脚
        lines.append("---")
        lines.append("*此报告由分类统计模块自动生成*")
        
        return '\n'.join(lines)
    
    def generate_json_report(
        self,
        stats: WeeklyStats,
        member_stats: Optional[List[MemberStats]] = None,
        multi_week_stats: Optional[MultiWeekStats] = None
    ) -> str:
        """
        生成JSON格式的统计报告
        
        Args:
            stats: 周统计数据
            member_stats: 成员统计（可选）
            multi_week_stats: 多周对比统计（可选）
            
        Returns:
            JSON字符串
        """
        report = {
            "weekly_stats": stats.to_dict(),
            "generated_at": datetime.now().isoformat()
        }
        
        if member_stats:
            report["member_stats"] = [ms.to_dict() for ms in member_stats]
        
        if multi_week_stats:
            report["multi_week_stats"] = multi_week_stats.to_dict()
        
        return json.dumps(report, ensure_ascii=False, indent=2)
    
    def generate_csv_report(
        self,
        stats: WeeklyStats,
        output_path: Optional[str] = None
    ) -> str:
        """
        生成CSV格式的统计报告
        
        Args:
            stats: 周统计数据
            output_path: 输出路径（可选，用于写入文件）
            
        Returns:
            CSV字符串
        """
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            "周次", "分类ID", "分类名称", "任务数", "占比", "任务列表"
        ])
        
        # 写入数据
        for cs in stats.category_stats:
            task_list = "; ".join(cs.tasks[:5])  # 只取前5个任务
            if len(cs.tasks) > 5:
                task_list += f" ... (+{len(cs.tasks) - 5})"
            
            writer.writerow([
                stats.week_id,
                cs.category_id,
                cs.category_name,
                cs.task_count,
                f"{cs.percentage:.1f}%",
                task_list
            ])
        
        csv_content = output.getvalue()
        
        # 如果指定了输出路径，写入文件
        if output_path:
            Path(output_path).write_text(csv_content, encoding='utf-8')
            logger.info(f"CSV报告已保存: {output_path}")
        
        return csv_content
    
    def generate_chart_data(
        self,
        stats: WeeklyStats,
        chart_type: str = "pie"
    ) -> ChartData:
        """
        生成图表数据
        
        Args:
            stats: 周统计数据
            chart_type: 图表类型（pie, bar）
            
        Returns:
            ChartData对象
        """
        # 过滤掉空分类
        non_empty_stats = [cs for cs in stats.category_stats if cs.task_count > 0]
        
        labels = [cs.category_name for cs in non_empty_stats]
        values = [cs.task_count for cs in non_empty_stats]
        
        # 根据图表类型设置选项
        if chart_type == "pie":
            options = {
                "show_percentage": True,
                "colors": self._generate_colors(len(labels))
            }
        elif chart_type == "bar":
            options = {
                "x_axis_label": "分类",
                "y_axis_label": "任务数",
                "show_values": True
            }
        else:
            options = {}
        
        return ChartData(
            chart_type=chart_type,
            labels=labels,
            values=values,
            title=f"分类分布 - {stats.week_id}",
            options=options
        )
    
    def generate_trend_chart_data(
        self,
        multi_week_stats: MultiWeekStats,
        chart_type: str = "line"
    ) -> ChartData:
        """
        生成趋势图表数据
        
        Args:
            multi_week_stats: 多周统计数据
            chart_type: 图表类型（line, bar）
            
        Returns:
            ChartData对象
        """
        labels = multi_week_stats.weeks
        datasets = []
        
        for cat_name, trends in multi_week_stats.category_trends.items():
            datasets.append({
                "label": cat_name,
                "data": trends
            })
        
        options = {
            "x_axis_label": "周次",
            "y_axis_label": "任务数",
            "show_legend": True
        }
        
        return ChartData(
            chart_type=chart_type,
            labels=labels,
            values=datasets,  # 趋势图的values是数据集列表
            title="分类趋势对比",
            options=options
        )
    
    def generate_text_chart(
        self,
        stats: WeeklyStats,
        width: int = 50
    ) -> str:
        """
        生成文本格式的条形图
        
        Args:
            stats: 周统计数据
            width: 图表宽度（字符数）
            
        Returns:
            文本图表字符串
        """
        lines = []
        lines.append(f"\n分类分布 - {stats.week_id}")
        lines.append("=" * width)
        
        # 过滤空分类
        non_empty_stats = [cs for cs in stats.category_stats if cs.task_count > 0]
        
        if not non_empty_stats:
            lines.append("无数据")
            return '\n'.join(lines)
        
        # 计算最大任务数（用于缩放）
        max_count = max(cs.task_count for cs in non_empty_stats)
        bar_max_width = width - 20  # 留出标签空间
        
        for cs in non_empty_stats:
            # 计算条形长度
            bar_length = int((cs.task_count / max_count) * bar_max_width) if max_count > 0 else 0
            bar = '█' * bar_length
            
            # 格式化输出
            label = f"{cs.category_name:<8}"
            count = f"{cs.task_count:>3}"
            percentage = f"({cs.percentage:>5.1f}%)"
            
            lines.append(f"{label} |{bar} {count} {percentage}")
        
        lines.append("=" * width)
        
        return '\n'.join(lines)
    
    def _get_category_name(self, category_id: str) -> str:
        """
        获取分类名称
        
        Args:
            category_id: 分类ID
            
        Returns:
            分类名称
        """
        category = self._category_map.get(category_id)
        if category:
            return category.name
        
        # 特殊分类
        special_names = {
            "uncategorized": "未分类",
            "memory": "内存相关",
            "resource": "资源相关",
            "harmonyos": "鸿蒙支持",
            "ci": "CI相关",
            "audio": "音频相关"
        }
        
        return special_names.get(category_id, category_id)
    
    def _generate_colors(self, count: int) -> List[str]:
        """
        生成图表颜色列表
        
        Args:
            count: 颜色数量
            
        Returns:
            颜色代码列表
        """
        # 预定义颜色
        base_colors = [
            "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF",
            "#FF9F40", "#FF6384", "#C9CBCF", "#4BC0C0", "#FF6384"
        ]
        
        # 循环使用
        colors = []
        for i in range(count):
            colors.append(base_colors[i % len(base_colors)])
        
        return colors
    
    def save_report(
        self,
        content: str,
        output_path: str,
        format_type: str = "markdown"
    ) -> str:
        """
        保存报告到文件
        
        Args:
            content: 报告内容
            output_path: 输出路径
            format_type: 格式类型（markdown, json, csv）
            
        Returns:
            保存的文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        output_file.write_text(content, encoding='utf-8')
        
        logger.info(f"报告已保存: {output_file} ({format_type})")
        
        return str(output_file)


# ============================================================================
# 便捷函数
# ============================================================================

def generate_quick_stats(
    tasks: List[Dict],
    categories: List[Category],
    week_id: str = "unknown"
) -> WeeklyStats:
    """
    快速生成统计的便捷函数
    
    Args:
        tasks: 任务列表
        categories: 分类列表
        week_id: 周次标识
        
    Returns:
        WeeklyStats对象
    """
    generator = CategoryStatsGenerator(categories)
    
    stats = generator.calculate_stats(tasks)
    
    # 计算覆盖率
    total_tasks = len(tasks)
    classified_count = sum(
        cs.task_count for cs in stats
        if cs.category_id != "uncategorized"
    )
    coverage_rate = (classified_count / total_tasks * 100) if total_tasks > 0 else 0.0
    
    # 找出最大分类
    max_category = ""
    for cs in stats:
        if cs.category_id != "uncategorized" and cs.task_count > 0:
            max_category = cs.category_name
            break
    
    return WeeklyStats(
        week_id=week_id,
        total_tasks=total_tasks,
        category_stats=stats,
        coverage_rate=coverage_rate,
        max_category=max_category
    )


# ============================================================================
# 模块测试
# ============================================================================

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    # 模拟分类数据
    test_categories = [
        Category(id="memory", name="内存相关", keywords=["内存", "mmap"], description="内存相关任务"),
        Category(id="resource", name="资源相关", keywords=["资源", "asset"], description="资源相关任务"),
        Category(id="harmonyos", name="鸿蒙支持", keywords=["鸿蒙", "harmony"], description="鸿蒙相关"),
        Category(id="ci", name="CI相关", keywords=["ci", "流水线"], description="CI相关任务"),
        Category(id="audio", name="音频相关", keywords=["音频", "audio"], description="音频相关"),
    ]
    
    # 模拟任务数据
    test_tasks = [
        {"content": "修复内存泄漏问题", "categories": ["memory"], "member": "张三"},
        {"content": "优化资源加载", "categories": ["resource"], "member": "张三"},
        {"content": "支持鸿蒙平台", "categories": ["harmonyos"], "member": "李四"},
        {"content": "修复CI流水线", "categories": ["ci"], "member": "李四"},
        {"content": "优化音频播放", "categories": ["audio"], "member": "王五"},
        {"content": "内存优化", "categories": ["memory"], "member": "张三"},
        {"content": "资源打包优化", "categories": ["resource"], "member": "王五"},
        {"content": "未分类任务1", "categories": [], "member": "李四"},
        {"content": "未分类任务2", "categories": [], "member": "张三"},
    ]
    
    # 创建统计生成器
    generator = CategoryStatsGenerator(test_categories)
    
    # 生成周统计
    stats = generator.calculate_stats(test_tasks)
    weekly_stats = WeeklyStats(
        week_id="2026-W10",
        total_tasks=len(test_tasks),
        category_stats=stats
    )
    
    # 生成Markdown报告
    print("\n" + "="*60)
    print("Markdown报告:")
    print("="*60)
    md_report = generator.generate_markdown_report(weekly_stats)
    print(md_report)
    
    # 生成成员统计
    member_stats = generator.generate_member_stats(test_tasks)
    
    print("\n" + "="*60)
    print("成员统计:")
    print("="*60)
    for ms in member_stats:
        print(f"{ms.member_name}: {ms.total_tasks}个任务, 主要分类: {ms.primary_category}")
    
    # 生成文本图表
    print("\n" + "="*60)
    print("文本图表:")
    print("="*60)
    text_chart = generator.generate_text_chart(weekly_stats)
    print(text_chart)
    
    # 测试多周对比
    print("\n" + "="*60)
    print("多周对比:")
    print("="*60)
    
    # 模拟两周数据
    week1_stats = WeeklyStats(
        week_id="2026-W09",
        total_tasks=30,
        category_stats=[
            CategoryStats("memory", "内存相关", 10, 33.3, []),
            CategoryStats("resource", "资源相关", 8, 26.7, []),
            CategoryStats("harmonyos", "鸿蒙支持", 5, 16.7, []),
            CategoryStats("ci", "CI相关", 4, 13.3, []),
            CategoryStats("audio", "音频相关", 3, 10.0, []),
        ]
    )
    
    week2_stats = WeeklyStats(
        week_id="2026-W10",
        total_tasks=35,
        category_stats=[
            CategoryStats("memory", "内存相关", 12, 34.3, []),
            CategoryStats("resource", "资源相关", 9, 25.7, []),
            CategoryStats("harmonyos", "鸿蒙支持", 6, 17.1, []),
            CategoryStats("ci", "CI相关", 5, 14.3, []),
            CategoryStats("audio", "音频相关", 3, 8.6, []),
        ]
    )
    
    multi_week = generator.compare_weeks([week1_stats, week2_stats])
    
    # 生成带多周对比的Markdown
    md_report_with_trend = generator.generate_markdown_report(
        weekly_stats,
        member_stats=member_stats,
        multi_week_stats=multi_week
    )
    print(md_report_with_trend)
