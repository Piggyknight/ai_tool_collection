"""
缩进分析工具

分析文本缩进，支持多种缩进风格
"""

from typing import List
from math import gcd
from functools import reduce


class IndentAnalyzer:
    """缩进分析器"""
    
    @staticmethod
    def calculate_indent_level(line: str, spaces_per_level: int = 4) -> int:
        """
        计算行的缩进级别
        
        Args:
            line: 文本行
            spaces_per_level: 每级缩进的空格数（默认4）
        
        Returns:
            缩进级别（0表示无缩进）
        
        Example:
            >>> IndentAnalyzer.calculate_indent_level("    任务描述")
            1
            >>> IndentAnalyzer.calculate_indent_level("        子项")
            2
            >>> IndentAnalyzer.calculate_indent_level("任务标题")
            0
        """
        stripped = line.lstrip()
        if not stripped:
            return 0
        
        spaces = len(line) - len(stripped)
        return spaces // spaces_per_level
    
    @staticmethod
    def detect_indent_style(lines: List[str]) -> int:
        """
        检测文本使用的缩进风格
        
        通过分析所有缩进行的空格数，计算GCD来判断缩进风格。
        
        Args:
            lines: 文本行列表
        
        Returns:
            每级缩进的空格数（2或4）
        
        Example:
            >>> lines = ["任务", "  描述", "    子项"]
            >>> IndentAnalyzer.detect_indent_style(lines)
            2
        """
        indent_values = []
        
        for line in lines:
            stripped = line.lstrip()
            if stripped and stripped != line:
                spaces = len(line) - len(stripped)
                indent_values.append(spaces)
        
        if not indent_values:
            return 4  # 默认4空格
        
        # 计算GCD
        try:
            gcd_value = reduce(gcd, indent_values)
        except (TypeError, ValueError):
            # 如果无法计算GCD，返回默认值
            return 4
        
        # 判断缩进风格
        if gcd_value == 2:
            return 2
        else:
            return 4
    
    @staticmethod
    def normalize_indent(line: str, from_style: int, to_style: int = 4) -> str:
        """
        规范化缩进风格
        
        Args:
            line: 文本行
            from_style: 原始缩进风格（空格数）
            to_style: 目标缩进风格（空格数）
        
        Returns:
            规范化后的文本行
        
        Example:
            >>> IndentAnalyzer.normalize_indent("  描述", 2, 4)
            "    描述"
        """
        stripped = line.lstrip()
        if not stripped:
            return line
        
        # 计算原始缩进级别
        spaces = len(line) - len(stripped)
        indent_level = spaces // from_style
        
        # 生成新的缩进
        new_indent = " " * (indent_level * to_style)
        
        return new_indent + stripped
    
    @staticmethod
    def get_leading_spaces(line: str) -> int:
        """
        获取行首的空格数
        
        Args:
            line: 文本行
        
        Returns:
            空格数量
        
        Example:
            >>> IndentAnalyzer.get_leading_spaces("    描述")
            4
            >>> IndentAnalyzer.get_leading_spaces("任务")
            0
        """
        stripped = line.lstrip()
        if not stripped:
            return 0
        return len(line) - len(stripped)
