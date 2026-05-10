"""
任务解析器

解析任务及其描述结构
"""

from typing import List, Tuple, Union, Dict
from .indent_analyzer import IndentAnalyzer
from .types import Task, DescriptionGroup, DescriptionItem


class TaskParser:
    """任务解析器"""
    
    def __init__(self, indent_analyzer: IndentAnalyzer = None):
        """
        初始化任务解析器
        
        Args:
            indent_analyzer: 缩进分析器实例（可选）
        """
        self.indent_analyzer = indent_analyzer or IndentAnalyzer()
    
    def parse_task_with_description(
        self,
        lines: List[str],
        start_idx: int,
        spaces_per_level: int = 4
    ) -> Tuple[Task, int]:
        """
        解析任务及其描述
        
        Args:
            lines: 所有文本行
            start_idx: 任务标题所在的行索引
            spaces_per_level: 每级缩进的空格数
        
        Returns:
            (task_dict, next_index)
            - task_dict: {"title": str, "description": List}
            - next_index: 下一个任务的起始索引
        
        Example:
            >>> lines = ["任务标题", "    描述1", "    描述2"]
            >>> task, idx = parser.parse_task_with_description(lines, 0)
            >>> task["title"]
            "任务标题"
            >>> len(task["description"])
            2
        """
        task: Task = {
            "title": lines[start_idx].strip(),
            "description": []
        }
        
        idx = start_idx + 1
        
        while idx < len(lines):
            line = lines[idx]
            
            # 跳过空行
            if not line.strip():
                idx += 1
                continue
            
            # 计算缩进级别
            indent = self.indent_analyzer.calculate_indent_level(
                line, spaces_per_level
            )
            
            # 缩进级别0，任务结束
            if indent == 0:
                break
            
            # 解析描述项
            desc_item, idx = self.parse_description_item(
                lines, idx, indent, spaces_per_level
            )
            task["description"].append(desc_item)
        
        return task, idx
    
    def parse_description_item(
        self,
        lines: List[str],
        idx: int,
        current_indent: int,
        spaces_per_level: int = 4
    ) -> Tuple[DescriptionItem, int]:
        """
        解析单个描述项
        
        Args:
            lines: 所有文本行
            idx: 当前行索引
            current_indent: 当前缩进级别
            spaces_per_level: 每级缩进的空格数
        
        Returns:
            (description_item, next_index)
            - description_item: 字符串或 {"label": str, "items": List}
            - next_index: 下一个描述项的索引
        """
        content = lines[idx].strip()
        
        # 检查是否有子项（下一行缩进更深）
        if self._has_child_items(lines, idx, current_indent, spaces_per_level):
            # 当前项是标签，构建分组
            group: DescriptionGroup = {
                "label": content,
                "items": []
            }
            
            idx += 1
            child_indent = current_indent + 1
            
            # 收集所有直接子项
            while idx < len(lines):
                line = lines[idx]
                
                # 跳过空行
                if not line.strip():
                    idx += 1
                    continue
                
                line_indent = self.indent_analyzer.calculate_indent_level(
                    line, spaces_per_level
                )
                
                # 缩进减少或为0，子项结束
                if line_indent <= current_indent:
                    break
                
                # 只收集直接子项（缩进级别 = current_indent + 1）
                if line_indent == child_indent:
                    group["items"].append(line.strip())
                
                idx += 1
            
            return group, idx
        
        # 简单文本描述
        return content, idx + 1
    
    def _has_child_items(
        self,
        lines: List[str],
        idx: int,
        current_indent: int,
        spaces_per_level: int
    ) -> bool:
        """
        判断当前行是否有子项
        
        Args:
            lines: 所有文本行
            idx: 当前行索引
            current_indent: 当前缩进级别
            spaces_per_level: 每级缩进的空格数
        
        Returns:
            True 如果下一行缩进更深
        """
        if idx + 1 >= len(lines):
            return False
        
        next_line = lines[idx + 1]
        if not next_line.strip():
            # 如果下一行是空行，继续向后查找
            for i in range(idx + 2, len(lines)):
                if lines[i].strip():
                    next_line = lines[i]
                    break
                if i - idx > 3:  # 最多查找3行
                    return False
            else:
                return False
        
        next_indent = self.indent_analyzer.calculate_indent_level(
            next_line, spaces_per_level
        )
        
        return next_indent > current_indent
