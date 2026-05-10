"""
日报收集模块

收集、解析、存储日报
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..core.parser import (
    parse_daily_report as parse_report,
    validate_report
)
from ..core.git_helper import GitHelper
from ..core.date_utils import format_date
from ..core.data_normalizer import DataNormalizer

logger = logging.getLogger(__name__)


class DailyCollector:
    """日报收集器"""

    def __init__(self, data_dir: str, git_helper: Optional[GitHelper] = None):
        """
        初始化日报收集器

        Args:
            data_dir: 数据存储目录
            git_helper: Git操作辅助类（可选）
        """
        self.data_dir = Path(data_dir)
        self.daily_dir = self.data_dir / "daily"
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        self.git_helper = git_helper

        logger.info(f"日报收集器初始化: {data_dir}")

    def collect_from_markdown(
        self,
        markdown_text: str,
        date: Optional[str] = None
    ) -> Dict:
        """
        从markdown文本收集日报

        Args:
            markdown_text: markdown格式的日报
            date: 日期（YYYYMMDD格式），默认为今天

        Returns:
            收集结果:
            {
                "success": True,
                "file_path": "data/daily/soc_daily_20260307.md",
                "report": {...}
            }
        """
        # 解析日报
        report = parse_report(markdown_text, date)

        # 验证日报
        errors = validate_report(report)
        if errors:
            logger.error(f"日报验证失败: {errors}")
            return {
                "success": False,
                "errors": errors,
                "report": report
            }

        # 保存日报
        file_path = self.save_daily_report(report)

        return {
            "success": True,
            "file_path": str(file_path),
            "report": report
        }

    def save_daily_report(self, report: Dict) -> Path:
        """
        保存日报到文件

        Args:
            report: 日报数据

        Returns:
            文件路径

        Example:
            >>> collector.save_daily_report(report)
            PosixPath('data/daily/soc_daily_20260307.md')
        """
        date = report.get("date", format_date(datetime.now(), "YYYYMMDD"))
        filename = f"soc_daily_{date}.md"
        file_path = self.daily_dir / filename

        # 转换为markdown格式
        markdown_content = self._convert_to_markdown(report)

        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"日报已保存: {file_path}")

        # 提交到Git
        if self.git_helper:
            self.git_helper.commit(
                f"添加日报 {date}",
                [str(file_path.relative_to(self.data_dir.parent))]
            )

        return file_path

    def get_daily_report(self, date: str) -> Optional[Dict]:
        """
        读取指定日期的日报

        Args:
            date: 日期（YYYYMMDD格式）

        Returns:
            日报数据，如果不存在返回None
        """
        filename = f"soc_daily_{date}.md"
        file_path = self.daily_dir / filename

        if not file_path.exists():
            logger.warning(f"日报文件不存在: {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                markdown_text = f.read()

            return parse_report(markdown_text, date)
        except Exception as e:
            logger.error(f"读取日报失败: {e}")
            return None

    def get_week_reports(self, week_start: str) -> List[Dict]:
        """
        获取一周内所有日报

        Args:
            week_start: 周起始日期（YYYYMMDD格式）

        Returns:
            日报列表
        """
        from ..core.date_utils import get_all_dates_in_week, parse_date

        start_date = parse_date(week_start)
        all_dates = get_all_dates_in_week(start_date)

        reports = []
        for date in all_dates:
            date_str = format_date(date, "YYYYMMDD")
            report = self.get_daily_report(date_str)
            if report:
                reports.append(report)

        logger.info(f"获取到 {len(reports)} 份日报")
        return reports

    def _convert_to_markdown(self, report: Dict) -> str:
        """
        转换日报为markdown格式（支持任务描述）
        
        Args:
            report: 日报数据
        
        Returns:
            markdown文本（保留缩进结构）
        """
        lines = [f"# 日报 - {report.get('date', '')}", ""]
        
        for member, data in report.get("members", {}).items():
            lines.append(f"## {member}")
            lines.append("")
            
            # 今日任务
            lines.append("### 今日完成")
            for task in data.get("today", []):
                # 标准化任务（向后兼容）
                task = DataNormalizer.normalize_task(task)
                
                # 任务标题
                lines.append(f"- {task['title']}")
                
                # 任务描述
                for desc in task.get("description", []):
                    if isinstance(desc, str):
                        # 简单描述
                        lines.append(f"    {desc}")
                    else:
                        # 带标签的分组
                        lines.append(f"    {desc['label']}")
                        for item in desc.get("items", []):
                            lines.append(f"        {item}")
            
            lines.append("")
            
            # 明日计划
            lines.append("### 明日计划")
            for task in data.get("tomorrow", []):
                # 标准化任务（向后兼容）
                task = DataNormalizer.normalize_task(task)
                
                # 任务标题
                lines.append(f"- {task['title']}")
                
                # 任务描述（如果有）
                for desc in task.get("description", []):
                    if isinstance(desc, str):
                        lines.append(f"    {desc}")
                    else:
                        lines.append(f"    {desc['label']}")
                        for item in desc.get("items", []):
                            lines.append(f"        {item}")
            
            lines.append("")
        
        return "\n".join(lines)

    def get_statistics(self, date: str) -> Dict:
        """
        获取日报统计信息

        Args:
            date: 日期

        Returns:
            统计信息
        """
        report = self.get_daily_report(date)
        if not report:
            return {}

        members = report.get("members", {})
        stats = {
            "date": date,
            "total_members": len(members),
            "total_tasks": sum(
                len(m.get("today", [])) + len(m.get("tomorrow", []))
                for m in members.values()
            ),
            "details": {}
        }

        for member, data in members.items():
            stats["details"][member] = {
                "today": len(data.get("today", [])),
                "tomorrow": len(data.get("tomorrow", []))
            }

        return stats
