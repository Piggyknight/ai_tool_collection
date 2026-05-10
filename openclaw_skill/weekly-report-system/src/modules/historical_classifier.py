"""
历史周报批量分类模块

对已生成的team周报进行批量分类处理，生成按技术领域分组的分类周报。
支持指定周次范围处理，包含分类统计摘要。
"""

import re
import os
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

from ..core.task_classifier import TaskClassifier, TaskToClassify, ClassificationResult
from ..core.category_parser import Category

logger = logging.getLogger(__name__)


# ============================================================================
# 数据结构定义
# ============================================================================

@dataclass
class WeeklyReport:
    """周报数据结构"""
    week_id: str                          # 周次标识，如 "2026-W10"
    year: int                             # 年份
    week_number: int                      # 周数
    tasks: List[Dict[str, Any]] = field(default_factory=list)  # 任务列表
    raw_content: str = ""                 # 原始Markdown内容
    start_date: Optional[str] = None      # 开始日期
    end_date: Optional[str] = None        # 结束日期
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "week_id": self.week_id,
            "year": self.year,
            "week_number": self.week_number,
            "tasks": self.tasks,
            "start_date": self.start_date,
            "end_date": self.end_date
        }


@dataclass
class ClassifiedWeeklyReport:
    """分类后的周报数据结构"""
    week_id: str                                      # 周次标识
    categories: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)  # 按分类组织的任务
    statistics: Dict[str, int] = field(default_factory=dict)  # 分类统计
    markdown_content: str = ""                        # 生成的Markdown内容
    total_tasks: int = 0                              # 总任务数
    classified_tasks: int = 0                         # 已分类任务数
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "week_id": self.week_id,
            "categories": self.categories,
            "statistics": self.statistics,
            "total_tasks": self.total_tasks,
            "classified_tasks": self.classified_tasks
        }


# ============================================================================
# 历史周报分类器
# ============================================================================

class HistoricalClassifier:
    """
    历史周报批量分类器
    
    读取已存在的team周报，解析任务，批量分类，生成分类版周报。
    """
    
    def __init__(
        self,
        classifier: TaskClassifier,
        report_dir: str,
        output_dir: Optional[str] = None
    ):
        """
        初始化历史周报分类器
        
        Args:
            classifier: 任务分类器实例
            report_dir: 周报文件目录
            output_dir: 输出目录（可选，默认与report_dir相同）
        """
        self.classifier = classifier
        self.report_dir = Path(report_dir)
        self.output_dir = Path(output_dir) if output_dir else self.report_dir
        
        # 确保目录存在
        if not self.report_dir.exists():
            raise ValueError(f"周报目录不存在: {self.report_dir}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"初始化历史周报分类器: 输入={self.report_dir}, 输出={self.output_dir}")
    
    def load_weekly_report(self, week_id: str) -> WeeklyReport:
        """
        读取指定周次的周报文件
        
        Args:
            week_id: 周次标识，格式：YYYY-WXX，如 "2026-W10"
                     或日期格式：YYYYMMDD，如 "20260302"
            
        Returns:
            WeeklyReport对象
            
        Raises:
            FileNotFoundError: 周报文件不存在
            ValueError: 文件格式错误
        """
        # 尝试多种文件名格式
        possible_filenames = self._get_possible_filenames(week_id)
        
        report_file = None
        for filename in possible_filenames:
            path = self.report_dir / filename
            if path.exists():
                report_file = path
                break
        
        if not report_file:
            raise FileNotFoundError(
                f"找不到周报文件: {week_id}\n"
                f"尝试的文件名: {possible_filenames}"
            )
        
        logger.info(f"读取周报文件: {report_file}")
        
        # 读取文件内容
        raw_content = report_file.read_text(encoding='utf-8')
        
        # 解析周报
        report = self._parse_weekly_report(raw_content, week_id)
        report.raw_content = raw_content
        
        logger.info(f"成功解析周报: {week_id}, 任务数: {len(report.tasks)}")
        
        return report
    
    def _get_possible_filenames(self, week_id: str) -> List[str]:
        """
        根据week_id生成可能的文件名列表
        
        Args:
            week_id: 周次标识
            
        Returns:
            可能的文件名列表
        """
        filenames = []
        
        # 格式1: YYYY-WXX
        if re.match(r'^\d{4}-W\d{2}$', week_id):
            # team_2026-W10.md
            filenames.append(f"team_{week_id}.md")
            # team_weekly_2026-W10.md
            filenames.append(f"team_weekly_{week_id}.md")
        
        # 格式2: YYYYMMDD（日期格式）
        elif re.match(r'^\d{8}$', week_id):
            # team_weekly_20260302.md
            filenames.append(f"team_weekly_{week_id}.md")
            # team_20260302.md
            filenames.append(f"team_{week_id}.md")
        
        # 格式3: 直接使用week_id作为文件名
        filenames.append(f"{week_id}.md")
        
        return filenames
    
    def _parse_weekly_report(self, content: str, week_id: str) -> WeeklyReport:
        """
        解析周报Markdown内容
        
        Args:
            content: Markdown内容
            week_id: 周次标识
            
        Returns:
            WeeklyReport对象
        """
        # 解析年份和周数
        year, week_number = self._parse_week_id(week_id)
        
        # 解析日期范围
        start_date, end_date = self._extract_date_range(content)
        
        # 提取任务列表
        tasks = self._extract_tasks(content)
        
        return WeeklyReport(
            week_id=week_id,
            year=year,
            week_number=week_number,
            tasks=tasks,
            start_date=start_date,
            end_date=end_date
        )
    
    def _parse_week_id(self, week_id: str) -> Tuple[int, int]:
        """
        解析week_id，提取年份和周数
        
        Args:
            week_id: 周次标识
            
        Returns:
            (年份, 周数)
        """
        # 格式1: YYYY-WXX
        match = re.match(r'^(\d{4})-W(\d{2})$', week_id)
        if match:
            return int(match.group(1)), int(match.group(2))
        
        # 格式2: YYYYMMDD（日期）
        match = re.match(r'^(\d{4})(\d{2})(\d{2})$', week_id)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            # 将日期转换为ISO周
            date = datetime(year, month, day)
            iso_calendar = date.isocalendar()
            return iso_calendar[0], iso_calendar[1]
        
        # 默认值
        logger.warning(f"无法解析week_id: {week_id}，使用默认值")
        return datetime.now().year, 1
    
    def _extract_date_range(self, content: str) -> Tuple[Optional[str], Optional[str]]:
        """
        从周报内容中提取日期范围
        
        Args:
            content: Markdown内容
            
        Returns:
            (开始日期, 结束日期)
        """
        # 模式1: **周期**: 2026-03-02 ~ 2026-03-08
        pattern1 = r'\*\*周期\*\*:\s*(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})'
        match = re.search(pattern1, content)
        if match:
            return match.group(1), match.group(2)
        
        # 模式2: ## 周期：2026-W10 (2026-03-02 ~ 2026-03-08)
        pattern2 = r'(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})'
        match = re.search(pattern2, content)
        if match:
            return match.group(1), match.group(2)
        
        return None, None
    
    def _extract_tasks(self, content: str) -> List[Dict[str, Any]]:
        """
        从周报内容中提取任务列表
        
        Args:
            content: Markdown内容
            
        Returns:
            任务列表，每个任务是一个字典
        """
        tasks = []
        
        # 查找任务章节（多种可能的标题格式）
        task_section_pattern = r'^##\s*[*●]?\s*本周完成的工作.*$'
        
        lines = content.split('\n')
        in_task_section = False
        task_index = 0
        
        for line in lines:
            # 检查是否进入任务章节
            if re.match(task_section_pattern, line, re.IGNORECASE):
                in_task_section = True
                continue
            
            # 检查是否离开任务章节（遇到下一个##标题）
            if in_task_section and line.startswith('##'):
                break
            
            # 提取任务（以 - 开头的行）
            if in_task_section and line.strip().startswith('-'):
                task_content = line.strip()[1:].strip()  # 移除开头的 - 和空格
                
                # 跳过空任务或分隔符
                if not task_content or task_content in ['---', '***', '___']:
                    continue
                
                # 跳过只包含分隔符的行
                if task_content.replace('-', '').replace('*', '').replace('_', '').strip() == '':
                    continue
                
                task = {
                    "index": task_index,
                    "content": task_content,
                    "task_id": f"task-{task_index:04d}"
                }
                tasks.append(task)
                task_index += 1
        
        logger.debug(f"从周报中提取了 {len(tasks)} 个任务")
        return tasks
    
    def classify_report(self, report: WeeklyReport) -> ClassifiedWeeklyReport:
        """
        对周报中的任务进行分类
        
        Args:
            report: 周报对象
            
        Returns:
            ClassifiedWeeklyReport对象
        """
        logger.info(f"开始分类周报: {report.week_id}, 任务数: {len(report.tasks)}")
        
        # 构建待分类任务列表
        tasks_to_classify = [
            TaskToClassify(
                task_id=task["task_id"],
                content=task["content"]
            )
            for task in report.tasks
        ]
        
        # 批量分类
        classification_results = self.classifier.classify_batch(tasks_to_classify)
        
        # 按分类组织任务
        categories: Dict[str, List[Dict[str, Any]]] = {}
        statistics: Dict[str, int] = {}
        classified_count = 0
        
        # 初始化所有分类
        for category in self.classifier.get_all_categories():
            categories[category.id] = []
            statistics[category.id] = 0
        
        # 添加未分类类别
        categories["uncategorized"] = []
        statistics["uncategorized"] = 0
        
        # 组织任务到各个分类
        for task, result in zip(report.tasks, classification_results):
            # 添加原始任务信息到结果
            task_with_classification = {
                **task,
                "categories": result.categories,
                "confidence": result.confidence,
                "method": result.method
            }
            
            # 将任务添加到对应的分类
            if result.categories:
                classified_count += 1
                for category_id in result.categories:
                    if category_id in categories:
                        categories[category_id].append(task_with_classification)
                        statistics[category_id] += 1
            else:
                # 未分类的任务
                categories["uncategorized"].append(task_with_classification)
                statistics["uncategorized"] += 1
        
        # 创建分类周报对象
        classified_report = ClassifiedWeeklyReport(
            week_id=report.week_id,
            categories=categories,
            statistics=statistics,
            total_tasks=len(report.tasks),
            classified_tasks=classified_count
        )
        
        # 生成Markdown内容
        classified_report.markdown_content = self.generate_classified_markdown(classified_report)
        
        logger.info(
            f"周报分类完成: {report.week_id}, "
            f"总任务: {classified_report.total_tasks}, "
            f"已分类: {classified_report.classified_tasks}, "
            f"准确率: {classified_report.classified_tasks / classified_report.total_tasks * 100:.1f}%"
        )
        
        return classified_report
    
    def generate_classified_markdown(self, classified: ClassifiedWeeklyReport) -> str:
        """
        生成分类版周报的Markdown内容
        
        Args:
            classified: 分类后的周报对象
            
        Returns:
            Markdown字符串
        """
        lines = []
        
        # 标题
        lines.append(f"# 团队周报 - {classified.week_id}（分类版）")
        lines.append("")
        
        # 分类统计章节
        lines.append("## 📊 分类统计")
        lines.append("")
        lines.append("| 分类 | 任务数 | 占比 |")
        lines.append("|------|--------|------|")
        
        # 按任务数排序
        sorted_stats = sorted(
            classified.statistics.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for category_id, count in sorted_stats:
            if count > 0:
                percentage = (count / classified.total_tasks * 100) if classified.total_tasks > 0 else 0
                category_name = self._get_category_display_name(category_id)
                lines.append(f"| {category_name} | {count} | {percentage:.1f}% |")
        
        lines.append("")
        lines.append(f"**总计**: {classified.total_tasks} 个任务，已分类 {classified.classified_tasks} 个")
        lines.append("")
        
        # 分类任务详情章节
        lines.append("## 📋 分类任务详情")
        lines.append("")
        
        # 按任务数排序显示各个分类
        for category_id, count in sorted_stats:
            if count > 0 and category_id in classified.categories:
                category_name = self._get_category_display_name(category_id)
                tasks = classified.categories[category_id]
                
                lines.append(f"### {category_name}")
                lines.append("")
                
                for task in tasks:
                    task_line = f"- {task['content']}"
                    # 如果置信度不高，标注分类方法
                    if task.get('confidence', 1.0) < 0.8:
                        task_line += f" _[{task.get('method', 'unknown')}]_"
                    lines.append(task_line)
                
                lines.append("")
        
        # 页脚
        lines.append("---")
        lines.append("*此分类周报由自动化系统生成*")
        
        return '\n'.join(lines)
    
    def _get_category_display_name(self, category_id: str) -> str:
        """
        获取分类的显示名称
        
        Args:
            category_id: 分类ID
            
        Returns:
            分类显示名称
        """
        category = self.classifier.get_category_info(category_id)
        if category:
            return category.name
        
        # 特殊分类的显示名称
        special_names = {
            "uncategorized": "未分类",
            "memory": "内存相关",
            "resource": "资源相关",
            "harmonyos": "鸿蒙支持相关",
            "ci": "CI相关",
            "audio": "音频相关"
        }
        
        return special_names.get(category_id, category_id)
    
    def save_classified_report(
        self,
        classified: ClassifiedWeeklyReport,
        output_path: Optional[str] = None
    ) -> str:
        """
        保存分类后的周报到文件
        
        Args:
            classified: 分类后的周报对象
            output_path: 输出路径（可选，默认自动生成）
            
        Returns:
            保存的文件路径
        """
        if not output_path:
            # 自动生成文件名：team_YYYY-WXX_classified.md
            output_path = self.output_dir / f"team_{classified.week_id}_classified.md"
        else:
            output_path = Path(output_path)
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        output_path.write_text(classified.markdown_content, encoding='utf-8')
        
        logger.info(f"分类周报已保存: {output_path}")
        
        return str(output_path)
    
    def process_week_range(
        self,
        start_week: str,
        end_week: str
    ) -> List[str]:
        """
        处理指定范围的周报
        
        Args:
            start_week: 开始周次，如 "2026-W01"
            end_week: 结束周次，如 "2026-W10"
            
        Returns:
            生成的分类周报文件路径列表
        """
        logger.info(f"开始处理周次范围: {start_week} ~ {end_week}")
        
        # 解析开始和结束周次
        start_year, start_week_num = self._parse_week_id(start_week)
        end_year, end_week_num = self._parse_week_id(end_week)
        
        # 生成周次列表
        week_ids = self._generate_week_range(
            start_year, start_week_num,
            end_year, end_week_num
        )
        
        logger.info(f"需要处理 {len(week_ids)} 个周次")
        
        # 处理每个周次
        output_files = []
        for week_id in week_ids:
            try:
                # 读取周报
                report = self.load_weekly_report(week_id)
                
                # 分类
                classified = self.classify_report(report)
                
                # 保存
                output_path = self.save_classified_report(classified)
                output_files.append(output_path)
                
            except FileNotFoundError as e:
                logger.warning(f"跳过不存在的周报: {week_id} - {e}")
                continue
            except Exception as e:
                logger.error(f"处理周报失败: {week_id} - {e}", exc_info=True)
                continue
        
        logger.info(f"周次范围处理完成，生成 {len(output_files)} 个文件")
        
        return output_files
    
    def _generate_week_range(
        self,
        start_year: int,
        start_week: int,
        end_year: int,
        end_week: int
    ) -> List[str]:
        """
        生成周次范围列表
        
        Args:
            start_year: 开始年份
            start_week: 开始周数
            end_year: 结束年份
            end_week: 结束周数
            
        Returns:
            周次ID列表，如 ["2026-W01", "2026-W02", ...]
        """
        week_ids = []
        
        current_year = start_year
        current_week = start_week
        
        while True:
            # 添加当前周次
            week_ids.append(f"{current_year}-W{current_week:02d}")
            
            # 检查是否到达结束周次
            if current_year == end_year and current_week == end_week:
                break
            
            # 计算下一周
            current_week += 1
            
            # 检查是否超出该年的最大周数（ISO年份有52或53周）
            max_weeks = self._get_max_weeks_in_year(current_year)
            if current_week > max_weeks:
                current_year += 1
                current_week = 1
            
            # 安全检查：防止无限循环
            if current_year > end_year or (current_year == end_year and current_week > end_week):
                break
        
        return week_ids
    
    def _get_max_weeks_in_year(self, year: int) -> int:
        """
        获取指定年份的最大ISO周数
        
        Args:
            year: 年份
            
        Returns:
            最大周数（52或53）
        """
        # ISO年份的最后一周是包含12月28日的那一周
        dec28 = datetime(year, 12, 28)
        _, max_week, _ = dec28.isocalendar()
        return max_week
    
    def process_all_reports(self) -> List[str]:
        """
        处理周报目录中的所有周报文件
        
        Returns:
            生成的分类周报文件路径列表
        """
        logger.info(f"开始处理所有周报: {self.report_dir}")
        
        # 查找所有team周报文件
        report_files = []
        for pattern in ["team_*.md", "team_weekly_*.md"]:
            report_files.extend(self.report_dir.glob(pattern))
        
        # 过滤掉已分类的文件
        report_files = [
            f for f in report_files
            if "_classified" not in f.name
        ]
        
        logger.info(f"找到 {len(report_files)} 个周报文件")
        
        # 处理每个周报
        output_files = []
        for report_file in report_files:
            try:
                # 从文件名提取week_id
                week_id = self._extract_week_id_from_filename(report_file.name)
                
                if not week_id:
                    logger.warning(f"无法从文件名提取周次: {report_file.name}")
                    continue
                
                # 读取周报
                report = self.load_weekly_report(week_id)
                
                # 分类
                classified = self.classify_report(report)
                
                # 保存
                output_path = self.save_classified_report(classified)
                output_files.append(output_path)
                
            except Exception as e:
                logger.error(f"处理周报失败: {report_file} - {e}", exc_info=True)
                continue
        
        logger.info(f"所有周报处理完成，生成 {len(output_files)} 个文件")
        
        return output_files
    
    def _extract_week_id_from_filename(self, filename: str) -> Optional[str]:
        """
        从文件名中提取周次标识
        
        Args:
            filename: 文件名
            
        Returns:
            周次标识，如 "2026-W10" 或 "20260302"
        """
        # 模式1: team_2026-W10.md
        match = re.search(r'team[_\s]*(\d{4}-W\d{2})', filename)
        if match:
            return match.group(1)
        
        # 模式2: team_weekly_20260302.md
        match = re.search(r'team[_\s]*weekly[_\s]*(\d{8})', filename)
        if match:
            return match.group(1)
        
        # 模式3: team_20260302.md
        match = re.search(r'team[_\s]*(\d{8})', filename)
        if match:
            return match.group(1)
        
        return None


# ============================================================================
# 便捷函数
# ============================================================================

def classify_historical_report(
    config_path: str,
    report_dir: str,
    output_dir: Optional[str] = None,
    week_id: Optional[str] = None,
    start_week: Optional[str] = None,
    end_week: Optional[str] = None
) -> List[str]:
    """
    快速分类历史周报的便捷函数
    
    Args:
        config_path: 分类配置文件路径
        report_dir: 周报目录
        output_dir: 输出目录（可选）
        week_id: 单个周次ID（可选）
        start_week: 开始周次（可选）
        end_week: 结束周次（可选）
        
    Returns:
        生成的分类周报文件路径列表
    """
    from ..core.category_parser import CategoryParser
    from ..core.task_classifier import TaskClassifier
    
    # 加载配置
    parser = CategoryParser(config_path)
    config = parser.load_config()
    
    # 创建分类器
    classifier = TaskClassifier(config)
    
    # 创建历史分类器
    historical_classifier = HistoricalClassifier(
        classifier=classifier,
        report_dir=report_dir,
        output_dir=output_dir
    )
    
    # 根据参数选择处理方式
    if week_id:
        # 处理单个周次
        report = historical_classifier.load_weekly_report(week_id)
        classified = historical_classifier.classify_report(report)
        output_path = historical_classifier.save_classified_report(classified)
        return [output_path]
    
    elif start_week and end_week:
        # 处理周次范围
        return historical_classifier.process_week_range(start_week, end_week)
    
    else:
        # 处理所有周报
        return historical_classifier.process_all_reports()


# ============================================================================
# 模块测试
# ============================================================================

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    # 默认路径
    config_path = "~/Documents/weekly-report-system/data/config/task_category.md"
    report_dir = "~/Documents/weekly-report-system/data/weekly/team"
    
    # 命令行参数
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    if len(sys.argv) > 2:
        report_dir = sys.argv[2]
    
    print(f"配置文件: {config_path}")
    print(f"周报目录: {report_dir}")
    
    # 测试：处理单个周报
    try:
        output_files = classify_historical_report(
            config_path=config_path,
            report_dir=report_dir,
            week_id="20260302"
        )
        
        print("\n生成的分类周报:")
        for file in output_files:
            print(f"  - {file}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
