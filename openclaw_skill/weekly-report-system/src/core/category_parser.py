"""
分类规则解析器模块

解析Markdown格式的分类规则配置文件，提取分类信息。
支持热加载配置更新。
"""

import re
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pathlib import Path
import logging
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class Category:
    """分类数据结构"""
    id: str                          # 分类ID，如 "memory"
    name: str                        # 分类名称，如 "内存相关"
    keywords: List[str] = field(default_factory=list)  # 关键词列表
    description: str = ""            # 详细描述
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "keywords": self.keywords,
            "description": self.description
        }


@dataclass
class CategoryConfig:
    """分类配置数据结构"""
    categories: List[Category] = field(default_factory=list)
    version: str = "1.0"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "version": self.version,
            "categories": [cat.to_dict() for cat in self.categories]
        }


class CategoryParser:
    """分类规则解析器"""
    
    # 分类ID映射表：中文分类名 -> 英文ID
    CATEGORY_ID_MAP = {
        "内存相关": "memory",
        "资源相关": "resource",
        "鸿蒙支持相关": "harmonyos",
        "鸿蒙相关": "harmonyos",
        "ci相关": "ci",
        "ci先关任务": "ci",
        "ci任务": "ci",
        "ci先关": "ci",  # 添加这个映射处理typo情况
        "音频相关": "audio",
        "音频相关任务": "audio",
    }
    
    # 常见关键词提取模式
    KEYWORD_PATTERNS = [
        # 技术术语（英文）
        r'\b([a-zA-Z]{2,}[a-zA-Z0-9_-]*)\b',
        # 中英文混合术语
        r'([a-zA-Z]+[a-zA-Z0-9_-]*)',
    ]
    
    # 需要过滤的通用词
    STOP_WORDS = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'shall',
        'can', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
        'to', 'and', 'or', 'but', 'if', 'then', 'else', 'when',
        'up', 'out', 'so', 'than', 'too', 'very', 'just', 'also',
        'we', 'our', 'us', 'this', 'that', 'these', 'those', 'it',
        'its', 'they', 'their', 'them', 'he', 'she', 'his', 'her',
        # 通用中文词
        '我们', '目前', '项目', '任务', '属于', '相关', '问题', '需要',
        '进行', '以及', '或者', '比如', '例如', '因此', '这样', '因为',
        '为了', '由于', '还', '都', '也', '就', '在', '有', '的', '中',
        '和', '与', '等', '所有', '各种', '一些', '这样', '哪些',
    }
    
    def __init__(self, config_path: str):
        """
        初始化分类解析器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self._config: Optional[CategoryConfig] = None
        self._file_hash: Optional[str] = None
        self._category_map: Dict[str, Category] = {}
        
    def _compute_file_hash(self) -> str:
        """计算文件哈希值，用于检测文件变化"""
        if not self.config_path.exists():
            return ""
        
        content = self.config_path.read_text(encoding='utf-8')
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词
        
        Args:
            text: 输入文本
            
        Returns:
            关键词列表
        """
        keywords = set()
        
        # 提取英文关键词
        for pattern in self.KEYWORD_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                word = match.lower()
                # 过滤停用词和短词
                if len(word) >= 2 and word not in self.STOP_WORDS:
                    keywords.add(word)
        
        # 提取中文关键词（简单方法：提取2-4字的中文词组）
        # 从描述中识别技术相关词汇
        chinese_keywords = [
            '内存', '优化', '缓存', '修复', '加载', '卸载',
            '打包', '资源', '平台', '客户端', '流水线', '发布',
            '监控', '数据库', '符号表', '版本号', '环境音',
            '混响', '音效', '性能', '移植', '分包',
        ]
        
        for kw in chinese_keywords:
            if kw in text:
                keywords.add(kw)
        
        return sorted(list(keywords))
    
    def _generate_category_id(self, name: str) -> str:
        """
        根据分类名称生成分类ID
        
        Args:
            name: 分类名称
            
        Returns:
            分类ID
        """
        # 尝试从映射表中查找
        normalized_name = name.strip().lower()
        
        # 先尝试完全匹配
        for cn_name, en_id in self.CATEGORY_ID_MAP.items():
            if cn_name.lower() == normalized_name or cn_name == name:
                return en_id
        
        # 再尝试部分匹配
        for cn_name, en_id in self.CATEGORY_ID_MAP.items():
            if cn_name.lower() in normalized_name or cn_name in name:
                return en_id
            if normalized_name in cn_name.lower() or name in cn_name:
                return en_id
        
        # 如果没有找到映射，生成拼音或使用名称
        # 这里简单使用中文名的拼音首字母或hash
        return normalized_name.replace('相关', '').replace('任务', '')[:10]
    
    def _parse_markdown_config(self, content: str) -> CategoryConfig:
        """
        解析Markdown格式的配置文件
        
        Args:
            content: Markdown内容
            
        Returns:
            CategoryConfig对象
        """
        categories = []
        
        # 按 ## 分割各个分类章节
        # 使用正则匹配 ## 标题行
        section_pattern = r'^##\s+(.+)$'
        lines = content.split('\n')
        
        current_section = None
        current_content = []
        sections = []
        
        for line in lines:
            match = re.match(section_pattern, line, re.MULTILINE)
            if match:
                # 保存之前的section
                if current_section:
                    sections.append((current_section, '\n'.join(current_content)))
                current_section = match.group(1).strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # 添加最后一个section
        if current_section:
            sections.append((current_section, '\n'.join(current_content)))
        
        # 解析每个section
        for section_name, section_content in sections:
            # 生成分类ID
            category_id = self._generate_category_id(section_name)
            
            # 提取关键词
            keywords = self._extract_keywords(section_content)
            
            # 清理描述文本
            description = section_content.strip()
            
            category = Category(
                id=category_id,
                name=section_name,
                keywords=keywords,
                description=description
            )
            categories.append(category)
            logger.debug(f"Parsed category: {category_id} - {section_name}")
        
        # 生成版本号（基于内容hash）
        version = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        
        return CategoryConfig(categories=categories, version=version)
    
    def load_config(self) -> CategoryConfig:
        """
        加载配置文件
        
        Returns:
            CategoryConfig对象
            
        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置文件格式错误
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        content = self.config_path.read_text(encoding='utf-8')
        
        if not content.strip():
            raise ValueError(f"配置文件为空: {self.config_path}")
        
        self._config = self._parse_markdown_config(content)
        self._file_hash = self._compute_file_hash()
        
        # 构建快速查找映射
        self._category_map = {cat.id: cat for cat in self._config.categories}
        
        logger.info(f"成功加载配置文件: {self.config_path}, "
                   f"版本: {self._config.version}, "
                   f"分类数: {len(self._config.categories)}")
        
        return self._config
    
    def reload_config(self) -> CategoryConfig:
        """
        重新加载配置文件（热更新）
        
        检查文件是否有变化，如有变化则重新加载
        
        Returns:
            CategoryConfig对象
        """
        current_hash = self._compute_file_hash()
        
        if self._file_hash is None or current_hash != self._file_hash:
            logger.info("检测到配置文件变化，重新加载...")
            return self.load_config()
        
        logger.debug("配置文件未变化，使用缓存配置")
        return self._config
    
    def get_category(self, category_id: str) -> Optional[Category]:
        """
        根据ID获取分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            Category对象，如未找到返回None
        """
        if self._config is None:
            self.load_config()
        
        return self._category_map.get(category_id)
    
    def get_all_categories(self) -> List[Category]:
        """
        获取所有分类
        
        Returns:
            分类列表
        """
        if self._config is None:
            self.load_config()
        
        return self._config.categories if self._config else []
    
    def get_config_version(self) -> str:
        """
        获取当前配置版本
        
        Returns:
            版本号字符串
        """
        if self._config is None:
            self.load_config()
        
        return self._config.version if self._config else ""
    
    def has_file_changed(self) -> bool:
        """
        检查配置文件是否有变化
        
        Returns:
            True表示文件已变化
        """
        current_hash = self._compute_file_hash()
        return current_hash != self._file_hash
    
    def search_by_keyword(self, keyword: str) -> List[Category]:
        """
        根据关键词搜索分类
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的分类列表
        """
        if self._config is None:
            self.load_config()
        
        keyword_lower = keyword.lower()
        results = []
        
        for category in self._config.categories:
            # 检查关键词列表
            if any(keyword_lower in kw.lower() for kw in category.keywords):
                results.append(category)
            # 检查描述
            elif keyword_lower in category.description.lower():
                results.append(category)
        
        return results


# 便捷函数
def load_categories(config_path: str) -> CategoryConfig:
    """
    快速加载分类配置的便捷函数
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        CategoryConfig对象
    """
    parser = CategoryParser(config_path)
    return parser.load_config()


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "~/Documents/weekly-report-system/data/config/task_category.md"
    
    parser = CategoryParser(config_path)
    config = parser.load_config()
    
    print(f"配置版本: {config.version}")
    print(f"分类数量: {len(config.categories)}")
    print("\n" + "="*50 + "\n")
    
    for cat in config.categories:
        print(f"ID: {cat.id}")
        print(f"名称: {cat.name}")
        print(f"关键词: {', '.join(cat.keywords[:10])}...")
        print(f"描述: {cat.description[:100]}...")
        print("-"*50)
