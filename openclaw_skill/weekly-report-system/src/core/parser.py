"""
Markdown日报解析器

解析markdown格式的团队日报，提取成员任务

Version Changes:
    v2.0: 支持任务描述和嵌套结构
    v1.0: 仅支持简单任务列表
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
from .indent_analyzer import IndentAnalyzer
from .task_parser import TaskParser
from .data_normalizer import DataNormalizer
from .types import Task, DailyReport
from .date_utils import parse_date as parse_date_str


def parse_daily_report(markdown_text: str, date: Optional[str] = None) -> DailyReport:
    """
    解析markdown格式日报（支持任务描述）
    
    Args:
        markdown_text: markdown格式的日报文本
        date: 日期字符串（YYYYMMDD格式），默认为今天
    
    Returns:
        解析后的日报数据结构（版本2.0）：
        {
            "date": "20260307",
            "version": "2.0",
            "members": {
                "HLQ": {
                    "today": [
                        {
                            "title": "任务标题",
                            "description": ["描述1", {"label": "效果", "items": ["子项1"]}]
                        }
                    ],
                    "tomorrow": []
                }
            }
        }
    
    Example:
        >>> report = parse_daily_report("HLQ: 今: 任务1\\n明: 任务2")
        >>> report["members"]["HLQ"]["today"][0]["title"]
        "任务1"
    
    Version Changes:
        v2.0: 支持任务描述和嵌套结构
        v1.0: 仅支持简单任务列表
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    else:
        # 统一转换为 YYYYMMDD 格式
        parsed = parse_date_str(date)
        date = parsed.strftime("%Y%m%d")
    
    # 初始化工具
    indent_analyzer = IndentAnalyzer()
    task_parser = TaskParser(indent_analyzer)
    
    # 初始化结果
    result: DailyReport = {
        "date": date,
        "version": "2.0",
        "members": {}
    }
    
    # 按行分割（保留原始缩进！）
    lines = markdown_text.split('\n')
    
    # 检测缩进风格
    spaces_per_level = indent_analyzer.detect_indent_style(lines)
    
    current_member = None
    current_section = None  # "today" or "tomorrow"
    
    idx = 0
    while idx < len(lines):
        original_line = lines[idx]
        stripped_line = original_line.strip()
        
        # 跳过空行
        if not stripped_line:
            idx += 1
            continue
        
        # 检查是否是成员行（格式1：成员名: 或 格式2：## 成员名）
        member_match = re.match(r'^([A-Z]{2,4})\s*:', stripped_line)
        if not member_match:
            # 尝试匹配 Markdown 标题格式：## HLQ
            member_match = re.match(r'^##\s*([A-Z]{2,4})\s*$', stripped_line)
        if member_match:
            current_member = member_match.group(1)
            if current_member not in result["members"]:
                result["members"][current_member] = {"today": [], "tomorrow": []}
            current_section = None
            idx += 1
            continue
        
        # 检查是否是"今"或"明"标记（格式1：今: 或 格式2：### 今）
        is_today = ('今' in stripped_line and ':' in stripped_line) or re.match(r'^###\s*今\s*$', stripped_line)
        is_tomorrow = ('明' in stripped_line and ':' in stripped_line) or re.match(r'^###\s*明\s*$', stripped_line)
        
        if is_today:
            current_section = "today"
            # 检查是否后面有任务标题（例如："今: 任务标题"）
            parts = stripped_line.split(':', 1)
            if len(parts) > 1 and parts[1].strip() and current_member:
                # 有任务标题，创建临时行列表
                task_title = parts[1].strip()
                temp_lines = [task_title] + lines[idx + 1:]
                
                # 解析任务及描述
                task, consumed = task_parser.parse_task_with_description(
                    temp_lines, 0, spaces_per_level
                )
                
                result["members"][current_member][current_section].append(task)
                # consumed 是 temp_lines 中的索引偏移，映射回 lines 就是 idx + consumed
                idx = idx + consumed
            else:
                idx += 1
            continue
        
        if is_tomorrow:
            current_section = "tomorrow"
            # 检查是否后面有任务标题
            parts = stripped_line.split(':', 1)
            if len(parts) > 1 and parts[1].strip() and current_member:
                task_title = parts[1].strip()
                temp_lines = [task_title] + lines[idx + 1:]
                
                task, consumed = task_parser.parse_task_with_description(
                    temp_lines, 0, spaces_per_level
                )
                
                result["members"][current_member][current_section].append(task)
                idx = idx + consumed
            else:
                idx += 1
            continue
        
        # 计算缩进级别
        indent = indent_analyzer.calculate_indent_level(
            original_line, spaces_per_level
        )
        
        # 缩进级别0，可能是任务标题
        if indent == 0 and current_member and current_section:
            # 检查是否是标题行（跳过markdown标题，但保留 #123 这种 issue 编号）
            if stripped_line.startswith('#') and re.match(r'^#\s+\S', stripped_line):
                idx += 1
                continue
            
            # 去除任务标记符（- • 等）
            task_match = re.match(r'^[-•]\s*(.+)', stripped_line)
            if task_match:
                task_title = task_match.group(1).strip()
            else:
                task_title = stripped_line
            
            if task_title:
                # 创建临时行列表，从当前位置开始
                temp_lines = [task_title] + lines[idx + 1:]
                
                # 解析任务及描述
                task, _ = task_parser.parse_task_with_description(
                    temp_lines, 0, spaces_per_level
                )
                
                # 计算实际消耗的行数
                consumed = len(task["description"])
                for desc in task["description"]:
                    if isinstance(desc, dict):
                        consumed += len(desc.get("items", []))
                
                result["members"][current_member][current_section].append(task)
                idx += consumed + 1
            else:
                idx += 1
        else:
            idx += 1
    
    return result


def extract_member_name(line: str) -> Optional[str]:
    """
    从行中提取成员名称

    Args:
        line: 文本行

    Returns:
        成员名称（如"HLQ"），如果无法提取则返回None

    Example:
        >>> extract_member_name("HLQ: 今: 任务列表")
        'HLQ'
        >>> extract_member_name("这是一行普通文本")
        None
    """
    match = re.match(r'^([A-Z]{2,4})\s*:', line)
    return match.group(1) if match else None


def extract_tasks(section_text: str, task_type: str = "all") -> List[str]:
    """
    提取指定类型的任务列表

    Args:
        section_text: 文本段落（包含今/明任务）
        task_type: "today" | "tomorrow" | "all"

    Returns:
        任务列表

    Example:
        >>> text = "今: - 任务1\\n明: - 任务2"
        >>> extract_tasks(text, "today")
        ['任务1']
    """
    tasks = []
    lines = section_text.strip().split('\n')

    in_section = False
    section_marker = "今" if task_type == "today" else "明" if task_type == "tomorrow" else None

    for line in lines:
        line = line.strip()

        # 检查是否进入指定区域
        if section_marker and section_marker in line and ':' in line:
            in_section = True
            continue

        # 检查是否离开指定区域
        if in_section and ('今' in line or '明' in line) and ':' in line:
            if section_marker not in line:
                in_section = False
                continue

        # 提取任务
        if (task_type == "all" or in_section):
            task_match = re.match(r'^[-•]\s*(.+)', line)
            if task_match:
                task = task_match.group(1).strip()
                if task:
                    tasks.append(task)

    return tasks


def validate_report(report: Dict) -> List[str]:
    """
    验证日报数据格式

    Args:
        report: 日报数据结构

    Returns:
        错误消息列表，空列表表示验证通过

    Example:
        >>> errors = validate_report({"date": "20260307", "members": {}})
        >>> len(errors) == 0
        True
    """
    errors = []

    # 检查必需字段
    if "date" not in report:
        errors.append("缺少date字段")

    if "members" not in report:
        errors.append("缺少members字段")
    elif not isinstance(report["members"], dict):
        errors.append("members字段必须是字典")
    elif len(report["members"]) == 0:
        errors.append("members字段不能为空")

    # 检查每个成员的数据
    for member, data in report.get("members", {}).items():
        if "today" not in data:
            errors.append(f"成员{member}缺少today字段")
        if "tomorrow" not in data:
            errors.append(f"成员{member}缺少tomorrow字段")

    return errors


def merge_reports(reports: List[Dict]) -> Dict:
    """
    合并多个日报（用于处理多日数据）

    Args:
        reports: 日报列表

    Returns:
        合并后的日报

    Example:
        >>> report1 = {"date": "20260307", "members": {"HLQ": {"today": ["任务1"], "tomorrow": []}}}
        >>> report2 = {"date": "20260308", "members": {"HLQ": {"today": ["任务2"], "tomorrow": []}}}
        >>> merged = merge_reports([report1, report2])
    """
    if not reports:
        return {"date": "", "version": "1.0", "members": {}}

    merged = {
        "date": reports[0].get("date", ""),
        "version": "1.0",
        "members": {}
    }

    for report in reports:
        for member, data in report.get("members", {}).items():
            if member not in merged["members"]:
                merged["members"][member] = {"today": [], "tomorrow": []}

            merged["members"][member]["today"].extend(data.get("today", []))
            merged["members"][member]["tomorrow"].extend(data.get("tomorrow", []))

    return merged


def get_member_statistics(report: Dict) -> Dict[str, int]:
    """
    统计每个成员的任务数量

    Args:
        report: 日报数据

    Returns:
        成员任务统计 {成员: 任务总数}

    Example:
        >>> report = {"members": {"HLQ": {"today": ["任务1", "任务2"], "tomorrow": ["任务3"]}}}
        >>> get_member_statistics(report)
        {'HLQ': 3}
    """
    stats = {}

    for member, data in report.get("members", {}).items():
        today_count = len(data.get("today", []))
        tomorrow_count = len(data.get("tomorrow", []))
        stats[member] = today_count + tomorrow_count

    return stats
