"""
日报数据类型定义

定义日报解析系统的核心数据结构
"""

from typing import TypedDict, List, Union, Dict


class DescriptionGroup(TypedDict):
    """描述分组（带标签的嵌套结构）"""
    label: str
    items: List[str]


# 描述项可以是字符串或分组
DescriptionItem = Union[str, DescriptionGroup]


class Task(TypedDict):
    """任务对象"""
    title: str
    description: List[DescriptionItem]


class MemberTasks(TypedDict):
    """成员任务数据"""
    today: List[Task]
    tomorrow: List[Task]


class DailyReport(TypedDict):
    """日报数据结构"""
    date: str
    version: str
    members: Dict[str, MemberTasks]


# 向后兼容：旧格式任务（字符串）
LegacyTask = str


class LegacyMemberTasks(TypedDict):
    """旧格式成员任务数据"""
    today: List[LegacyTask]
    tomorrow: List[LegacyTask]


class LegacyDailyReport(TypedDict):
    """旧格式日报数据结构"""
    date: str
    version: str
    members: Dict[str, LegacyMemberTasks]
