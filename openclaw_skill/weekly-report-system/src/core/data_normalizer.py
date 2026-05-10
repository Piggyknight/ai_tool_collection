"""
数据标准化器

标准化日报数据格式，支持向后兼容
"""

from typing import Dict, Union, List
from .types import (
    Task, DailyReport, LegacyDailyReport,
    DescriptionItem
)


class DataNormalizer:
    """数据标准化器"""
    
    @staticmethod
    def normalize_task(task: Union[str, Task]) -> Task:
        """
        将任务标准化为新格式
        
        Args:
            task: 旧格式（字符串）或新格式（字典）
        
        Returns:
            标准化后的任务字典
        
        Example:
            >>> DataNormalizer.normalize_task("简单任务")
            {"title": "简单任务", "description": []}
        """
        if isinstance(task, str):
            return {
                "title": task,
                "description": []
            }
        
        # 已经是新格式，验证结构
        if "title" not in task:
            raise ValueError("任务对象缺少title字段")
        
        if "description" not in task:
            task["description"] = []
        
        return task
    
    @staticmethod
    def normalize_member_tasks(member_data: Dict) -> Dict:
        """
        标准化成员任务数据
        
        Args:
            member_data: 成员任务数据
        
        Returns:
            标准化后的成员任务数据
        """
        normalized = {
            "today": [],
            "tomorrow": []
        }
        
        for section in ["today", "tomorrow"]:
            if section in member_data:
                tasks = member_data[section]
                normalized[section] = [
                    DataNormalizer.normalize_task(task)
                    for task in tasks
                ]
        
        return normalized
    
    @staticmethod
    def normalize_report(report: Union[DailyReport, LegacyDailyReport]) -> DailyReport:
        """
        标准化整个日报
        
        Args:
            report: 原始日报数据
        
        Returns:
            标准化后的日报（版本2.0）
        """
        normalized: DailyReport = {
            "date": report.get("date", ""),
            "version": "2.0",
            "members": {}
        }
        
        for member, member_data in report.get("members", {}).items():
            normalized["members"][member] = DataNormalizer.normalize_member_tasks(
                member_data
            )
        
        return normalized
    
    @staticmethod
    def is_legacy_format(report: Dict) -> bool:
        """
        判断是否是旧版格式
        
        Args:
            report: 日报数据
        
        Returns:
            True 如果任务使用字符串格式
        """
        members = report.get("members", {})
        
        for member_data in members.values():
            for section in ["today", "tomorrow"]:
                tasks = member_data.get(section, [])
                if tasks and isinstance(tasks[0], str):
                    return True
        
        return False
    
    @staticmethod
    def to_legacy_task(task: Task) -> str:
        """
        将新格式任务转换为旧格式（丢弃描述）
        
        Args:
            task: 新格式任务对象
        
        Returns:
            任务标题字符串
        """
        return task.get("title", "")
    
    @staticmethod
    def to_legacy_report(report: DailyReport) -> LegacyDailyReport:
        """
        将新格式日报转换为旧格式（丢弃描述）
        
        Args:
            report: 新格式日报
        
        Returns:
            旧格式日报
        """
        legacy: LegacyDailyReport = {
            "date": report.get("date", ""),
            "version": "1.0",
            "members": {}
        }
        
        for member, member_data in report.get("members", {}).items():
            legacy["members"][member] = {
                "today": [
                    DataNormalizer.to_legacy_task(task)
                    for task in member_data.get("today", [])
                ],
                "tomorrow": [
                    DataNormalizer.to_legacy_task(task)
                    for task in member_data.get("tomorrow", [])
                ]
            }
        
        return legacy
