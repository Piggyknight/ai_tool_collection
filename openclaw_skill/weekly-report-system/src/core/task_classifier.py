"""
任务分类器模块

使用LLM对任务进行智能分类，支持单任务分类和批量分类。
包含降级策略（关键词匹配）和分类结果缓存。
"""

import logging
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Protocol
from pathlib import Path

from .category_parser import Category, CategoryConfig

logger = logging.getLogger(__name__)


# ============================================================================
# 数据结构定义
# ============================================================================

@dataclass
class TaskToClassify:
    """待分类任务数据结构"""
    task_id: str                          # 任务唯一标识
    content: str                          # 任务内容
    context: Optional[str] = None         # 可选的上下文信息
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "content": self.content,
            "context": self.context
        }
    
    def get_cache_key(self) -> str:
        """生成缓存键"""
        # 使用任务内容生成hash作为缓存键
        content_hash = hashlib.md5(self.content.encode('utf-8')).hexdigest()
        return f"task_classify:{content_hash}"


@dataclass
class ClassificationResult:
    """分类结果数据结构"""
    task_id: str                          # 任务ID
    categories: List[str] = field(default_factory=list)  # 分类ID列表
    confidence: float = 0.0               # 置信度 (0.0 - 1.0)
    method: str = "unknown"               # 分类方法: "llm" or "keyword"
    error: Optional[str] = None           # 错误信息（如果有）
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "categories": self.categories,
            "confidence": self.confidence,
            "method": self.method,
            "error": self.error
        }


# ============================================================================
# 缓存管理器
# ============================================================================

class CacheManager:
    """
    分类结果缓存管理器
    
    使用内存缓存 + 可选的文件持久化
    """
    
    def __init__(self, cache_dir: Optional[str] = None, max_size: int = 10000):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存文件目录（可选）
            max_size: 最大缓存条目数
        """
        self._cache: Dict[str, ClassificationResult] = {}
        self._cache_dir = Path(cache_dir) if cache_dir else None
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        
        if self._cache_dir:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_from_disk()
    
    def _get_cache_file(self) -> Path:
        """获取缓存文件路径"""
        return self._cache_dir / "classification_cache.json" if self._cache_dir else None
    
    def _load_from_disk(self):
        """从磁盘加载缓存"""
        cache_file = self._get_cache_file()
        if cache_file and cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        self._cache[key] = ClassificationResult(**value)
                logger.info(f"从磁盘加载缓存: {len(self._cache)} 条记录")
            except Exception as e:
                logger.warning(f"加载缓存失败: {e}")
    
    def _save_to_disk(self):
        """保存缓存到磁盘"""
        cache_file = self._get_cache_file()
        if cache_file:
            try:
                data = {k: v.to_dict() for k, v in self._cache.items()}
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"保存缓存失败: {e}")
    
    def get(self, key: str) -> Optional[ClassificationResult]:
        """获取缓存"""
        result = self._cache.get(key)
        if result:
            self._hits += 1
        else:
            self._misses += 1
        return result
    
    def set(self, key: str, result: ClassificationResult):
        """设置缓存"""
        # 如果缓存已满，删除最旧的条目
        if len(self._cache) >= self._max_size:
            # 简单的LRU：删除第一个条目
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"缓存已满，删除旧条目: {oldest_key}")
        
        self._cache[key] = result
        
        # 定期保存到磁盘
        if len(self._cache) % 100 == 0 and self._cache_dir:
            self._save_to_disk()
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        if self._cache_dir:
            cache_file = self._get_cache_file()
            if cache_file and cache_file.exists():
                cache_file.unlink()
        logger.info("缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate
        }


# ============================================================================
# LLM客户端协议
# ============================================================================

class LLMClientProtocol(Protocol):
    """LLM客户端协议定义"""
    
    def call(self, prompt: str) -> Optional[str]:
        """
        调用LLM模型
        
        Args:
            prompt: 提示词
            
        Returns:
            模型返回的文本，失败返回None
        """
        ...


class SimpleLLMClient:
    """
    简单的LLM客户端实现
    
    可以被替换为实际的LLM API调用实现
    """
    
    def __init__(self, model: str = "zai/glm-5", max_retries: int = 3):
        """
        初始化LLM客户端
        
        Args:
            model: 模型名称
            max_retries: 最大重试次数
        """
        self.model = model
        self.max_retries = max_retries
        logger.info(f"初始化LLM客户端，模型: {model}")
    
    def call(self, prompt: str) -> Optional[str]:
        """
        调用LLM模型（模拟实现）
        
        实际实现应该：
        1. 使用OpenClaw的sessions_spawn调用子会话
        2. 或直接调用GLM模型API
        3. 处理超时和错误
        
        Args:
            prompt: 提示词
            
        Returns:
            模型返回的文本
        """
        # 这是一个模拟实现
        # 在实际项目中应该调用真实的LLM API
        logger.info(f"调用LLM模型: {self.model}, 提示词长度: {len(prompt)}")
        
        # 模拟：返回None表示需要降级
        return None


# ============================================================================
# 任务分类器
# ============================================================================

class TaskClassifier:
    """
    任务分类器
    
    使用LLM进行智能分类，支持降级到关键词匹配
    """
    
    # 分类ID的有效集合
    VALID_CATEGORY_IDS = {
        "memory", "resource", "harmonyos", "ci", "audio"
    }
    
    def __init__(
        self,
        config: CategoryConfig,
        llm_client: Optional[LLMClientProtocol] = None,
        cache_manager: Optional[CacheManager] = None,
        max_retries: int = 3,
        timeout_seconds: float = 2.0
    ):
        """
        初始化任务分类器
        
        Args:
            config: 分类配置
            llm_client: LLM客户端（可选，默认使用SimpleLLMClient）
            cache_manager: 缓存管理器（可选）
            max_retries: LLM调用最大重试次数
            timeout_seconds: 单任务超时时间（秒）
        """
        self.config = config
        self.llm_client = llm_client or SimpleLLMClient()
        self.cache_manager = cache_manager
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        
        # 构建分类ID到Category的映射
        self._category_map: Dict[str, Category] = {
            cat.id: cat for cat in config.categories
        }
        
        logger.info(f"初始化任务分类器，分类数: {len(config.categories)}")
    
    def classify_task(self, task: TaskToClassify) -> ClassificationResult:
        """
        对单个任务进行分类
        
        Args:
            task: 待分类的任务
            
        Returns:
            分类结果
        """
        start_time = time.time()
        
        # 1. 检查缓存
        if self.cache_manager:
            cache_key = task.get_cache_key()
            cached_result = self.cache_manager.get(cache_key)
            if cached_result:
                logger.debug(f"缓存命中: {task.task_id}")
                return ClassificationResult(
                    task_id=task.task_id,
                    categories=cached_result.categories,
                    confidence=cached_result.confidence,
                    method=cached_result.method
                )
        
        # 2. 尝试LLM分类（带重试）
        categories = []
        confidence = 0.0
        method = "llm"
        error = None
        
        try:
            categories, confidence = self._classify_with_llm(task)
        except Exception as e:
            logger.warning(f"LLM分类失败: {e}")
            error = str(e)
        
        # 3. 如果LLM失败，降级到关键词匹配
        if not categories:
            categories = self._fallback_keyword_match(task)
            confidence = 0.6  # 关键词匹配的默认置信度
            method = "keyword"
            logger.debug(f"降级到关键词匹配: {task.task_id} -> {categories}")
        
        # 4. 如果仍然没有匹配，标记为未分类
        if not categories:
            categories = ["uncategorized"]
            confidence = 0.0
            method = "fallback"
        
        # 5. 构建结果
        result = ClassificationResult(
            task_id=task.task_id,
            categories=categories,
            confidence=confidence,
            method=method,
            error=error
        )
        
        # 6. 缓存结果
        if self.cache_manager:
            self.cache_manager.set(task.get_cache_key(), result)
        
        elapsed = time.time() - start_time
        logger.debug(f"分类完成: {task.task_id} -> {categories}, 耗时: {elapsed:.2f}s")
        
        return result
    
    def classify_batch(
        self,
        tasks: List[TaskToClassify],
        batch_size: int = 10
    ) -> List[ClassificationResult]:
        """
        批量分类任务
        
        Args:
            tasks: 任务列表
            batch_size: 批处理大小
            
        Returns:
            分类结果列表
        """
        results = []
        total = len(tasks)
        
        logger.info(f"开始批量分类，任务数: {total}, 批大小: {batch_size}")
        
        start_time = time.time()
        
        for i, task in enumerate(tasks):
            # 进度日志
            if (i + 1) % batch_size == 0 or (i + 1) == total:
                logger.info(f"分类进度: {i+1}/{total}")
            
            result = self.classify_task(task)
            results.append(result)
        
        elapsed = time.time() - start_time
        avg_time = elapsed / total if total > 0 else 0
        
        logger.info(f"批量分类完成，总耗时: {elapsed:.2f}s, 平均: {avg_time:.2f}s/任务")
        
        return results
    
    def _classify_with_llm(
        self,
        task: TaskToClassify
    ) -> tuple[List[str], float]:
        """
        使用LLM进行分类（带重试）
        
        Args:
            task: 待分类任务
            
        Returns:
            (分类ID列表, 置信度)
            
        Raises:
            RuntimeError: LLM调用失败
        """
        prompt = self._build_prompt(task, self.config.categories)
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.llm_client.call(prompt)
                if response:
                    categories = self._parse_llm_response(response)
                    if categories:
                        # LLM返回结果置信度较高
                        return categories, 0.9
            except Exception as e:
                last_error = e
                logger.warning(f"LLM调用失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
        
        raise RuntimeError(f"LLM调用失败: {last_error}")
    
    def _build_prompt(
        self,
        task: TaskToClassify,
        categories: List[Category]
    ) -> str:
        """
        构建LLM提示词
        
        Args:
            task: 待分类任务
            categories: 分类列表
            
        Returns:
            提示词字符串
        """
        # 构建分类规则描述
        categories_desc = []
        for cat in categories:
            desc = f"- {cat.id}: {cat.name}"
            if cat.keywords:
                desc += f" (关键词: {', '.join(cat.keywords[:5])})"
            categories_desc.append(desc)
        
        categories_text = "\n".join(categories_desc)
        
        # 构建任务内容
        task_content = task.content
        if task.context:
            task_content = f"[上下文: {task.context}]\n{task.content}"
        
        prompt = f"""你是一个任务分类专家。根据以下分类规则，判断任务属于哪个分类。

分类规则：
{categories_text}

任务内容：
{task_content}

请返回分类ID（可以属于多个分类，用逗号分隔）。
只返回分类ID，不要解释。例如：memory,resource"""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> List[str]:
        """
        解析LLM返回的分类结果
        
        Args:
            response: LLM返回的文本
            
        Returns:
            分类ID列表
        """
        # 清理响应文本
        response = response.strip()
        
        # 尝试多种解析模式
        categories = []
        
        # 模式1：逗号分隔
        if ',' in response:
            parts = response.split(',')
        # 模式2：空格分隔
        elif ' ' in response:
            parts = response.split()
        # 模式3：单个分类
        else:
            parts = [response]
        
        # 清理和验证每个分类ID
        for part in parts:
            cat_id = part.strip().lower()
            
            # 移除可能的解释文字（取最后一个冒号后的内容）
            cat_id = cat_id.split('\n')[0].strip()
            
            # 处理中英文冒号：取最后一个冒号后的内容
            if '：' in cat_id:
                cat_id = cat_id.split('：')[-1].strip()
            if ':' in cat_id:
                cat_id = cat_id.split(':')[-1].strip()
            
            # 验证是否是有效的分类ID
            if cat_id in self._category_map:
                categories.append(cat_id)
            elif cat_id in self.VALID_CATEGORY_IDS:
                categories.append(cat_id)
            else:
                logger.debug(f"忽略无效的分类ID: {cat_id}")
        
        # 去重
        categories = list(dict.fromkeys(categories))
        
        return categories
    
    def _fallback_keyword_match(self, task: TaskToClassify) -> List[str]:
        """
        降级策略：关键词匹配
        
        Args:
            task: 待分类任务
            
        Returns:
            分类ID列表
        """
        content = task.content.lower()
        if task.context:
            content = f"{task.context} {content}".lower()
        
        matched_categories = []
        
        for category in self.config.categories:
            # 检查关键词
            for keyword in category.keywords:
                if keyword.lower() in content:
                    if category.id not in matched_categories:
                        matched_categories.append(category.id)
                    break
            
            # 检查描述中的关键词（次要匹配）
            if category.id not in matched_categories:
                # 从描述中提取更多关键词
                desc_keywords = self._extract_keywords_from_description(category.description)
                for kw in desc_keywords:
                    if kw.lower() in content and kw.lower() not in ['任务', '相关', '问题']:
                        matched_categories.append(category.id)
                        break
        
        return matched_categories
    
    def _extract_keywords_from_description(self, description: str) -> List[str]:
        """
        从描述中提取关键词
        
        Args:
            description: 分类描述
            
        Returns:
            关键词列表
        """
        # 简单的关键词提取：提取中文词汇和英文术语
        import re
        
        keywords = []
        
        # 提取中文关键词（2-4个字符）
        chinese_pattern = r'[\u4e00-\u9fa5]{2,4}'
        chinese_matches = re.findall(chinese_pattern, description)
        keywords.extend(chinese_matches)
        
        # 提取英文术语
        english_pattern = r'[a-zA-Z][a-zA-Z0-9_-]*'
        english_matches = re.findall(english_pattern, description)
        keywords.extend([m.lower() for m in english_matches if len(m) >= 2])
        
        return keywords
    
    def get_category_info(self, category_id: str) -> Optional[Category]:
        """
        获取分类信息
        
        Args:
            category_id: 分类ID
            
        Returns:
            Category对象，未找到返回None
        """
        return self._category_map.get(category_id)
    
    def get_all_categories(self) -> List[Category]:
        """
        获取所有分类
        
        Returns:
            分类列表
        """
        return self.config.categories


# ============================================================================
# 便捷函数
# ============================================================================

def create_classifier(
    config_path: str,
    llm_client: Optional[LLMClientProtocol] = None,
    cache_dir: Optional[str] = None
) -> TaskClassifier:
    """
    快速创建分类器的便捷函数
    
    Args:
        config_path: 分类配置文件路径
        llm_client: LLM客户端（可选）
        cache_dir: 缓存目录（可选）
        
    Returns:
        TaskClassifier实例
    """
    from .category_parser import CategoryParser
    
    parser = CategoryParser(config_path)
    config = parser.load_config()
    
    cache_manager = CacheManager(cache_dir) if cache_dir else None
    
    return TaskClassifier(
        config=config,
        llm_client=llm_client,
        cache_manager=cache_manager
    )


# ============================================================================
# 模块测试
# ============================================================================

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG)
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else \
        "~/Documents/weekly-report-system/data/config/task_category.md"
    
    # 创建分类器
    classifier = create_classifier(config_path)
    
    # 测试单个任务
    test_task = TaskToClassify(
        task_id="test-001",
        content="修复Android平台上的内存泄漏问题，优化mmap缓存策略",
        context="本周工作"
    )
    
    result = classifier.classify_task(test_task)
    print(f"\n任务: {test_task.content}")
    print(f"分类结果: {result.categories}")
    print(f"置信度: {result.confidence}")
    print(f"方法: {result.method}")
    
    # 批量测试
    test_tasks = [
        TaskToClassify(task_id="t1", content="优化音频播放性能"),
        TaskToClassify(task_id="t2", content="修复CI流水线打包失败问题"),
        TaskToClassify(task_id="t3", content="支持鸿蒙平台资源加载"),
        TaskToClassify(task_id="t4", content="优化asset bundle分包规则"),
        TaskToClassify(task_id="t5", content="启用asan检测内存问题"),
    ]
    
    print("\n" + "="*50)
    print("批量分类测试:")
    
    results = classifier.classify_batch(test_tasks)
    for task, result in zip(test_tasks, results):
        print(f"  {task.content[:30]}... -> {result.categories} ({result.method})")
