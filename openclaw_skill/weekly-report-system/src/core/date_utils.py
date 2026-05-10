"""
日期计算工具

提供周报相关的日期计算功能
"""

from datetime import datetime, timedelta
from typing import List, Tuple, Optional


def get_week_range(date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """
    获取指定日期所在周的范围

    Args:
        date: 指定日期，默认为今天

    Returns:
        (week_start, week_end): 周起始日期和结束日期

    Example:
        >>> start, end = get_week_range(datetime(2026, 3, 7))
        >>> print(start)  # 2026-03-02 (周一)
        >>> print(end)    # 2026-03-08 (周日)
    """
    if date is None:
        date = datetime.now()

    # 周一为一周的起始 (weekday() 返回 0-6, 0=周一)
    weekday = date.weekday()
    week_start = date - timedelta(days=weekday)
    week_end = week_start + timedelta(days=6)

    # 重置时间为00:00:00
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_end.replace(hour=23, minute=59, second=59, microsecond=999999)

    return week_start, week_end


def get_all_dates_in_week(week_start: Optional[datetime] = None) -> List[datetime]:
    """
    获取一周内所有日期（周一到周日）

    Args:
        week_start: 周起始日期，默认为本周一

    Returns:
        一周内所有日期列表 [周一, 周二, ..., 周日]

    Example:
        >>> dates = get_all_dates_in_week(datetime(2026, 3, 2))
        >>> len(dates)  # 7
        >>> dates[0]    # 2026-03-02 (周一)
        >>> dates[6]    # 2026-03-08 (周日)
    """
    if week_start is None:
        week_start, _ = get_week_range()

    # 确保week_start是周一
    if week_start.weekday() != 0:
        week_start, _ = get_week_range(week_start)

    dates = []
    for i in range(7):
        date = week_start + timedelta(days=i)
        dates.append(date.replace(hour=0, minute=0, second=0, microsecond=0))

    return dates


def format_date(date: datetime, fmt: str = "YYYYMMDD") -> str:
    """
    格式化日期

    Args:
        date: 日期对象
        fmt: 格式字符串，支持以下格式：
            - "YYYYMMDD" 或 "yyyyMMdd": 20260307
            - "YYYY-MM-DD" 或 "yyyy-MM-dd": 2026-03-07
            - "YYYYMM" 或 "yyyyMM": 202603
            - "WYYYY" 或 "Wyyyy": 2026-W10 (年-周数)
            - "DEFAULT": 2026-03-07

    Returns:
        格式化后的日期字符串

    Example:
        >>> format_date(datetime(2026, 3, 7), "YYYYMMDD")
        '20260307'
        >>> format_date(datetime(2026, 3, 7), "YYYY-MM-DD")
        '2026-03-07'
        >>> format_date(datetime(2026, 3, 7), "WYYYY")
        '2026-W10'
    """
    fmt_upper = fmt.upper()

    if fmt_upper in ["YYYYMMDD", "YYYYMMDD"]:
        return date.strftime("%Y%m%d")
    elif fmt_upper in ["YYYY-MM-DD", "YYYY-MM-DD"]:
        return date.strftime("%Y-%m-%d")
    elif fmt_upper in ["YYYYMM", "YYYYMM"]:
        return date.strftime("%Y%m")
    elif fmt_upper in ["WYYYY", "WYYYY"]:
        iso_calendar = date.isocalendar()
        return f"{iso_calendar[0]}-W{iso_calendar[1]:02d}"
    elif fmt_upper == "DEFAULT":
        return date.strftime("%Y-%m-%d")
    else:
        # 使用自定义格式
        return date.strftime(fmt)


def get_week_number(date: Optional[datetime] = None) -> int:
    """
    获取周数（ISO标准）

    Args:
        date: 指定日期，默认为今天

    Returns:
        周数 (1-53)

    Example:
        >>> get_week_number(datetime(2026, 3, 7))
        10
    """
    if date is None:
        date = datetime.now()

    iso_calendar = date.isocalendar()
    return iso_calendar[1]


def get_year_week(date: Optional[datetime] = None) -> Tuple[int, int]:
    """
    获取年份和周数（ISO标准）

    Args:
        date: 指定日期，默认为今天

    Returns:
        (year, week_number): 年份和周数

    Example:
        >>> get_year_week(datetime(2026, 3, 7))
        (2026, 10)
    """
    if date is None:
        date = datetime.now()

    iso_calendar = date.isocalendar()
    return iso_calendar[0], iso_calendar[1]


def parse_date(date_str: str) -> datetime:
    """
    解析日期字符串

    支持以下格式：
    - "YYYYMMDD": "20260307"
    - "YYYY-MM-DD": "2026-03-07"
    - "MM-DD": "03-07" (默认年份为当前年)

    Args:
        date_str: 日期字符串

    Returns:
        datetime 对象

    Raises:
        ValueError: 日期格式不支持

    Example:
        >>> parse_date("20260307")
        datetime(2026, 3, 7)
        >>> parse_date("2026-03-07")
        datetime(2026, 3, 7)
        >>> parse_date("03-07")
        datetime(2026, 3, 7)  # 假设当前是2026年
    """
    # 尝试 YYYYMMDD 格式
    if len(date_str) == 8 and date_str.isdigit():
        return datetime.strptime(date_str, "%Y%m%d")

    # 尝试 YYYY-MM-DD 格式
    if len(date_str) == 10 and "-" in date_str:
        return datetime.strptime(date_str, "%Y-%m-%d")

    # 尝试 MM-DD 格式
    if len(date_str) == 5 and "-" in date_str:
        current_year = datetime.now().year
        return datetime.strptime(f"{current_year}-{date_str}", "%Y-%m-%d")

    raise ValueError(f"不支持的日期格式: {date_str}")


def get_date_range_description(start_date: datetime, end_date: datetime) -> str:
    """
    生成日期范围描述

    Args:
        start_date: 起始日期
        end_date: 结束日期

    Returns:
        日期范围描述字符串

    Example:
        >>> get_date_range_description(
        ...     datetime(2026, 3, 2),
        ...     datetime(2026, 3, 7)
        ... )
        '2026-03-02 ~ 2026-03-07'
    """
    return f"{format_date(start_date, 'YYYY-MM-DD')} ~ {format_date(end_date, 'YYYY-MM-DD')}"


def is_weekend(date: datetime) -> bool:
    """
    判断是否为周末

    Args:
        date: 日期

    Returns:
        True if 周六或周日，False otherwise

    Example:
        >>> is_weekend(datetime(2026, 3, 7))  # 周六
        True
        >>> is_weekend(datetime(2026, 3, 2))  # 周一
        False
    """
    return date.weekday() >= 5  # 5=周六, 6=周日


def get_next_weekday(date: datetime) -> datetime:
    """
    获取下一个工作日（周一到周五）

    Args:
        date: 当前日期

    Returns:
        下一个工作日

    Example:
        >>> get_next_weekday(datetime(2026, 3, 7))  # 周六
        datetime(2026, 3, 9)  # 周一
    """
    next_day = date + timedelta(days=1)
    while is_weekend(next_day):
        next_day += timedelta(days=1)
    return next_day
