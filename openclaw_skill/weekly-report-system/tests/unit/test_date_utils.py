"""
日期计算工具单元测试
"""

import pytest
from datetime import datetime, timedelta
from src.core.date_utils import (
    get_week_range,
    get_all_dates_in_week,
    format_date,
    get_week_number,
    get_year_week,
    parse_date,
    get_date_range_description,
    is_weekend,
    get_next_weekday,
)


class TestGetWeekRange:
    """测试 get_week_range 函数"""

    def test_monday(self):
        """测试周一"""
        date = datetime(2026, 3, 2)  # 周一
        start, end = get_week_range(date)
        assert start == datetime(2026, 3, 2, 0, 0, 0)
        assert end == datetime(2026, 3, 8, 23, 59, 59, 999999)

    def test_wednesday(self):
        """测试周三"""
        date = datetime(2026, 3, 4)  # 周三
        start, end = get_week_range(date)
        assert start == datetime(2026, 3, 2, 0, 0, 0)
        assert end == datetime(2026, 3, 8, 23, 59, 59, 999999)

    def test_sunday(self):
        """测试周日"""
        date = datetime(2026, 3, 8)  # 周日
        start, end = get_week_range(date)
        assert start == datetime(2026, 3, 2, 0, 0, 0)
        assert end == datetime(2026, 3, 8, 23, 59, 59, 999999)

    def test_saturday(self):
        """测试周六"""
        date = datetime(2026, 3, 7)  # 周六
        start, end = get_week_range(date)
        assert start == datetime(2026, 3, 2, 0, 0, 0)
        assert end == datetime(2026, 3, 8, 23, 59, 59, 999999)

    def test_no_date_provided(self):
        """测试不提供日期参数"""
        start, end = get_week_range()
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert start.weekday() == 0  # 周一
        assert end.weekday() == 6  # 周日


class TestGetAllDatesInWeek:
    """测试 get_all_dates_in_week 函数"""

    def test_seven_days(self):
        """测试返回7天"""
        dates = get_all_dates_in_week(datetime(2026, 3, 2))
        assert len(dates) == 7

    def test_monday_to_sunday(self):
        """测试周一到周日"""
        dates = get_all_dates_in_week(datetime(2026, 3, 2))
        assert dates[0] == datetime(2026, 3, 2, 0, 0, 0)  # 周一
        assert dates[1] == datetime(2026, 3, 3, 0, 0, 0)  # 周二
        assert dates[2] == datetime(2026, 3, 4, 0, 0, 0)  # 周三
        assert dates[3] == datetime(2026, 3, 5, 0, 0, 0)  # 周四
        assert dates[4] == datetime(2026, 3, 6, 0, 0, 0)  # 周五
        assert dates[5] == datetime(2026, 3, 7, 0, 0, 0)  # 周六
        assert dates[6] == datetime(2026, 3, 8, 0, 0, 0)  # 周日

    def test_from_wednesday(self):
        """测试从周三开始"""
        dates = get_all_dates_in_week(datetime(2026, 3, 4))
        assert dates[0] == datetime(2026, 3, 2, 0, 0, 0)  # 仍然是周一
        assert len(dates) == 7


class TestFormatDate:
    """测试 format_date 函数"""

    def test_yyyymmdd(self):
        """测试 YYYYMMDD 格式"""
        date = datetime(2026, 3, 7)
        assert format_date(date, "YYYYMMDD") == "20260307"
        assert format_date(date, "yyyyMMdd") == "20260307"

    def test_yyyy_mm_dd(self):
        """测试 YYYY-MM-DD 格式"""
        date = datetime(2026, 3, 7)
        assert format_date(date, "YYYY-MM-DD") == "2026-03-07"
        assert format_date(date, "yyyy-MM-dd") == "2026-03-07"

    def test_yyyymm(self):
        """测试 YYYYMM 格式"""
        date = datetime(2026, 3, 7)
        assert format_date(date, "YYYYMM") == "202603"

    def test_wyyyy(self):
        """测试 WYYYY 格式（年-周数）"""
        date = datetime(2026, 3, 7)
        assert format_date(date, "WYYYY") == "2026-W10"

    def test_default(self):
        """测试 DEFAULT 格式"""
        date = datetime(2026, 3, 7)
        assert format_date(date, "DEFAULT") == "2026-03-07"

    def test_custom_format(self):
        """测试自定义格式"""
        date = datetime(2026, 3, 7, 14, 30, 45)
        assert format_date(date, "%Y/%m/%d %H:%M") == "2026/03/07 14:30"


class TestGetWeekNumber:
    """测试 get_week_number 函数"""

    def test_week_10(self):
        """测试第10周"""
        date = datetime(2026, 3, 7)
        assert get_week_number(date) == 10

    def test_week_1(self):
        """测试第1周"""
        date = datetime(2026, 1, 1)
        week = get_week_number(date)
        assert isinstance(week, int)
        assert 1 <= week <= 53


class TestGetYearWeek:
    """测试 get_year_week 函数"""

    def test_year_week(self):
        """测试年份和周数"""
        date = datetime(2026, 3, 7)
        year, week = get_year_week(date)
        assert year == 2026
        assert week == 10


class TestParseDate:
    """测试 parse_date 函数"""

    def test_parse_yyyymmdd(self):
        """测试解析 YYYYMMDD 格式"""
        result = parse_date("20260307")
        assert result == datetime(2026, 3, 7)

    def test_parse_yyyy_mm_dd(self):
        """测试解析 YYYY-MM-DD 格式"""
        result = parse_date("2026-03-07")
        assert result == datetime(2026, 3, 7)

    def test_parse_mm_dd(self):
        """测试解析 MM-DD 格式"""
        result = parse_date("03-07")
        current_year = datetime.now().year
        assert result == datetime(current_year, 3, 7)

    def test_parse_invalid_format(self):
        """测试无效格式"""
        with pytest.raises(ValueError, match="不支持的日期格式"):
            parse_date("invalid")


class TestGetDateRangeDescription:
    """测试 get_date_range_description 函数"""

    def test_date_range(self):
        """测试日期范围描述"""
        start = datetime(2026, 3, 2)
        end = datetime(2026, 3, 7)
        result = get_date_range_description(start, end)
        assert result == "2026-03-02 ~ 2026-03-07"


class TestIsWeekend:
    """测试 is_weekend 函数"""

    def test_saturday(self):
        """测试周六"""
        assert is_weekend(datetime(2026, 3, 7)) is True

    def test_sunday(self):
        """测试周日"""
        assert is_weekend(datetime(2026, 3, 8)) is True

    def test_monday(self):
        """测试周一"""
        assert is_weekend(datetime(2026, 3, 2)) is False

    def test_friday(self):
        """测试周五"""
        assert is_weekend(datetime(2026, 3, 6)) is False


class TestGetNextWeekday:
    """测试 get_next_weekday 函数"""

    def test_from_friday(self):
        """测试从周五"""
        friday = datetime(2026, 3, 6)
        next_day = get_next_weekday(friday)
        assert next_day == datetime(2026, 3, 9)  # 周一

    def test_from_saturday(self):
        """测试从周六"""
        saturday = datetime(2026, 3, 7)
        next_day = get_next_weekday(saturday)
        assert next_day == datetime(2026, 3, 9)  # 周一

    def test_from_sunday(self):
        """测试从周日"""
        sunday = datetime(2026, 3, 8)
        next_day = get_next_weekday(sunday)
        assert next_day == datetime(2026, 3, 9)  # 周一

    def test_from_monday(self):
        """测试从周一"""
        monday = datetime(2026, 3, 2)
        next_day = get_next_weekday(monday)
        assert next_day == datetime(2026, 3, 3)  # 周二
