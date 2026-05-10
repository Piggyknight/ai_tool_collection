"""
周报生成模块

生成团队周报和个人周报
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .daily_collector import DailyCollector
from ..core.llm_service import LLMService
from ..core.git_helper import GitHelper
from ..core.task_dedup import deduplicate_tasks, merge_similar_tasks
from ..core.date_utils import (
    get_week_range,
    get_all_dates_in_week,
    format_date,
    get_date_range_description
)

logger = logging.getLogger(__name__)


class WeeklyGenerator:
    """周报生成器"""

    def __init__(
        self,
        collector: DailyCollector,
        llm_service: LLMService,
        git_helper: Optional[GitHelper] = None
    ):
        """
        初始化周报生成器

        Args:
            collector: 日报收集器
            llm_service: LLM服务
            git_helper: Git操作辅助类（可选）
        """
        self.collector = collector
        self.llm_service = llm_service
        self.git_helper = git_helper

        # 周报存储目录
        self.weekly_dir = collector.data_dir / "weekly"
        self.team_dir = self.weekly_dir / "team"
        self.members_dir = self.weekly_dir / "members"

        self.team_dir.mkdir(parents=True, exist_ok=True)
        self.members_dir.mkdir(parents=True, exist_ok=True)

        logger.info("周报生成器初始化完成")

    def generate_team_weekly(
        self,
        week_start: str,
        use_llm: bool = True
    ) -> str:
        """
        生成团队汇总周报

        Args:
            week_start: 周起始日期（YYYYMMDD格式）
            use_llm: 是否使用LLM润色

        Returns:
            周报文件路径

        Example:
            >>> path = generator.generate_team_weekly("20260302")
        """
        logger.info(f"开始生成团队周报: {week_start}")

        # 获取一周内所有日报
        reports = self.collector.get_week_reports(week_start)

        if not reports:
            logger.warning("没有找到任何日报")
            return ""

        # 收集所有"今日完成"任务
        all_tasks = []
        for report in reports:
            for member, data in report.get("members", {}).items():
                for task in data.get("today", []):
                    # 支持新旧格式：v2.0 是字典，v1.0 是字符串
                    if isinstance(task, dict):
                        all_tasks.append(task.get("title", ""))
                    else:
                        all_tasks.append(task)

        logger.info(f"共收集到 {len(all_tasks)} 条任务")

        # 去重
        unique_tasks = deduplicate_tasks(all_tasks, threshold=0.7)
        logger.info(f"去重后剩余 {len(unique_tasks)} 条任务")

        # 使用LLM润色（可选）
        if use_llm and unique_tasks:
            try:
                polished_tasks = self.llm_service.summarize_tasks(unique_tasks)
            except Exception as e:
                logger.error(f"LLM润色失败: {e}")
                polished_tasks = "\n".join(f"- {task}" for task in unique_tasks)
        else:
            polished_tasks = "\n".join(f"- {task}" for task in unique_tasks)

        # 生成周报内容
        week_start_date = datetime.strptime(week_start, "%Y%m%d")
        week_end_date = get_week_range(week_start_date)[1]
        week_range_str = get_date_range_description(
            week_start_date,
            week_end_date
        )

        content = f"""# 团队周报汇总

**周期**: {week_range_str}

## ● 本周完成的工作:

{polished_tasks}

---
*此周报由自动化系统生成*
"""

        # 保存周报
        filename = f"team_weekly_{week_start}.md"
        file_path = self.team_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"团队周报已保存: {file_path}")

        # Git提交
        if self.git_helper:
            self.git_helper.commit(f"添加团队周报 {week_start}")

        return str(file_path)

    def generate_member_weekly(
        self,
        week_start: str,
        member: str,
        use_llm: bool = True
    ) -> str:
        """
        生成个人周报

        Args:
            week_start: 周起始日期
            member: 成员ID
            use_llm: 是否使用LLM润色

        Returns:
            周报文件路径
        """
        logger.info(f"开始生成个人周报: {member} - {week_start}")

        # 获取一周内所有日报
        reports = self.collector.get_week_reports(week_start)

        # 收集该成员的任务
        member_tasks = []
        member_name = member

        for report in reports:
            data = report.get("members", {}).get(member, {})
            if data:
                member_name = data.get("name", member)
                for task in data.get("today", []):
                    # 支持新旧格式：v2.0 是字典，v1.0 是字符串
                    if isinstance(task, dict):
                        member_tasks.append(task.get("title", ""))
                    else:
                        member_tasks.append(task)

        if not member_tasks:
            logger.warning(f"成员 {member} 本周没有任务")
            return ""

        # 去重
        unique_tasks = deduplicate_tasks(member_tasks, threshold=0.7)
        logger.info(f"成员 {member} 去重后剩余 {len(unique_tasks)} 条任务")

        # 生成周报
        week_start_date = datetime.strptime(week_start, "%Y%m%d")
        week_end_date = get_week_range(week_start_date)[1]
        week_range_str = get_date_range_description(week_start_date, week_end_date)

        content = self.llm_service.generate_weekly_report(
            member_name,
            unique_tasks,
            week_range_str
        )

        # 保存周报
        filename = f"soc_weekly_{week_start}_{format_date(week_end_date, 'YYYYMMDD')}_{member}.md"
        file_path = self.members_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"个人周报已保存: {file_path}")

        return str(file_path)

    def generate_all_member_weekly(
        self,
        week_start: str,
        use_llm: bool = True
    ) -> List[str]:
        """
        生成所有成员的个人周报

        Args:
            week_start: 周起始日期
            use_llm: 是否使用LLM润色

        Returns:
            文件路径列表
        """
        logger.info(f"开始生成所有成员周报: {week_start}")

        # 获取所有活跃成员
        from .config_manager import ConfigManager
        config = ConfigManager(str(self.collector.data_dir / "config"))
        active_members = config.get_all_active_members()

        file_paths = []
        for member_id in active_members:
            path = self.generate_member_weekly(
                week_start,
                member_id,
                use_llm
            )
            if path:
                file_paths.append(path)

        logger.info(f"已生成 {len(file_paths)} 份个人周报")

        # Git提交
        if self.git_helper:
            self.git_helper.commit(f"添加个人周报 {week_start}")

        return file_paths

    def get_weekly_statistics(self, week_start: str) -> Dict:
        """
        获取周报统计信息

        Args:
            week_start: 周起始日期

        Returns:
            统计信息
        """
        reports = self.collector.get_week_reports(week_start)

        stats = {
            "week_start": week_start,
            "total_reports": len(reports),
            "total_members": 0,
            "total_tasks": 0,
            "members": {}
        }

        seen_members = set()
        for report in reports:
            for member, data in report.get("members", {}).items():
                seen_members.add(member)
                task_count = len(data.get("today", [])) + len(data.get("tomorrow", []))
                stats["total_tasks"] += task_count

                if member not in stats["members"]:
                    stats["members"][member] = 0
                stats["members"][member] += task_count

        stats["total_members"] = len(seen_members)

        return stats
