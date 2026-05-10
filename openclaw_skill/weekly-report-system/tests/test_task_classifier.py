"""
任务分类器单元测试

测试 task_classifier.py 模块的功能
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import time

from src.core.task_classifier import (
    TaskToClassify,
    ClassificationResult,
    CacheManager,
    SimpleLLMClient,
    TaskClassifier,
    create_classifier
)
from src.core.category_parser import Category, CategoryConfig


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_categories():
    """创建示例分类列表"""
    return [
        Category(
            id="memory",
            name="内存相关",
            keywords=["内存", "mmap", "asan", "cache", "内存优化"],
            description="内存优化、内存问题修复、缓存池优化等"
        ),
        Category(
            id="resource",
            name="资源相关",
            keywords=["资源", "asset", "bundle", "vfs", "分包"],
            description="资源加载、卸载、分包规则优化等"
        ),
        Category(
            id="harmonyos",
            name="鸿蒙支持相关",
            keywords=["鸿蒙", "harmony", "华为"],
            description="鸿蒙平台移植和问题修复"
        ),
        Category(
            id="ci",
            name="CI相关",
            keywords=["ci", "流水线", "打包", "蓝盾", "发布"],
            description="CI流水线和发布相关任务"
        ),
        Category(
            id="audio",
            name="音频相关",
            keywords=["音频", "wwise", "音效", "声音"],
            description="音频播放和音效相关"
        )
    ]


@pytest.fixture
def sample_config(sample_categories):
    """创建示例配置"""
    return CategoryConfig(categories=sample_categories)


@pytest.fixture
def mock_llm_client():
    """创建模拟的LLM客户端"""
    client = MagicMock()
    client.call = MagicMock(return_value=None)
    return client


@pytest.fixture
def cache_manager():
    """创建缓存管理器"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield CacheManager(cache_dir=tmpdir)


@pytest.fixture
def classifier(sample_config, mock_llm_client, cache_manager):
    """创建分类器实例"""
    return TaskClassifier(
        config=sample_config,
        llm_client=mock_llm_client,
        cache_manager=cache_manager
    )


# ============================================================================
# 数据结构测试
# ============================================================================

class TestTaskToClassify:
    """TaskToClassify 数据结构测试"""
    
    def test_create_task(self):
        """测试创建任务"""
        task = TaskToClassify(
            task_id="test-001",
            content="测试任务内容",
            context="测试上下文"
        )
        assert task.task_id == "test-001"
        assert task.content == "测试任务内容"
        assert task.context == "测试上下文"
    
    def test_create_task_without_context(self):
        """测试创建无上下文的任务"""
        task = TaskToClassify(
            task_id="test-002",
            content="测试任务"
        )
        assert task.task_id == "test-002"
        assert task.context is None
    
    def test_to_dict(self):
        """测试转换为字典"""
        task = TaskToClassify(
            task_id="test-003",
            content="测试",
            context="上下文"
        )
        d = task.to_dict()
        assert d["task_id"] == "test-003"
        assert d["content"] == "测试"
        assert d["context"] == "上下文"
    
    def test_get_cache_key(self):
        """测试缓存键生成"""
        task1 = TaskToClassify(task_id="t1", content="相同内容")
        task2 = TaskToClassify(task_id="t2", content="相同内容")
        task3 = TaskToClassify(task_id="t3", content="不同内容")
        
        # 相同内容应该生成相同的缓存键
        assert task1.get_cache_key() == task2.get_cache_key()
        # 不同内容应该生成不同的缓存键
        assert task1.get_cache_key() != task3.get_cache_key()


class TestClassificationResult:
    """ClassificationResult 数据结构测试"""
    
    def test_create_result(self):
        """测试创建分类结果"""
        result = ClassificationResult(
            task_id="test-001",
            categories=["memory", "resource"],
            confidence=0.9,
            method="llm"
        )
        assert result.task_id == "test-001"
        assert result.categories == ["memory", "resource"]
        assert result.confidence == 0.9
        assert result.method == "llm"
        assert result.error is None
    
    def test_create_result_with_error(self):
        """测试创建带错误的分类结果"""
        result = ClassificationResult(
            task_id="test-002",
            categories=[],
            confidence=0.0,
            method="llm",
            error="LLM调用超时"
        )
        assert result.error == "LLM调用超时"
    
    def test_to_dict(self):
        """测试转换为字典"""
        result = ClassificationResult(
            task_id="test-003",
            categories=["ci"],
            confidence=0.85,
            method="keyword"
        )
        d = result.to_dict()
        assert d["task_id"] == "test-003"
        assert d["categories"] == ["ci"]
        assert d["confidence"] == 0.85
        assert d["method"] == "keyword"


# ============================================================================
# 缓存管理器测试
# ============================================================================

class TestCacheManager:
    """CacheManager 测试"""
    
    def test_set_and_get(self):
        """测试设置和获取缓存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(cache_dir=tmpdir)
            
            result = ClassificationResult(
                task_id="test",
                categories=["memory"],
                confidence=0.9,
                method="llm"
            )
            
            cache.set("key1", result)
            cached = cache.get("key1")
            
            assert cached is not None
            assert cached.task_id == "test"
            assert cached.categories == ["memory"]
    
    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = CacheManager()
        cached = cache.get("nonexistent")
        assert cached is None
    
    def test_cache_stats(self):
        """测试缓存统计"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(cache_dir=tmpdir)
            
            result = ClassificationResult(
                task_id="test",
                categories=["memory"],
                confidence=0.9,
                method="llm"
            )
            
            cache.set("key1", result)
            cache.get("key1")  # hit
            cache.get("key1")  # hit
            cache.get("nonexistent")  # miss
            
            stats = cache.get_stats()
            assert stats["hits"] == 2
            assert stats["misses"] == 1
            assert stats["size"] == 1
    
    def test_cache_clear(self):
        """测试清空缓存"""
        cache = CacheManager()
        result = ClassificationResult(
            task_id="test",
            categories=["memory"],
            confidence=0.9,
            method="llm"
        )
        
        cache.set("key1", result)
        assert cache.get("key1") is not None
        
        cache.clear()
        assert cache.get("key1") is None
    
    def test_max_size_limit(self):
        """测试缓存大小限制"""
        cache = CacheManager(max_size=3)
        
        for i in range(5):
            result = ClassificationResult(
                task_id=f"test-{i}",
                categories=["memory"],
                confidence=0.9,
                method="llm"
            )
            cache.set(f"key{i}", result)
        
        stats = cache.get_stats()
        assert stats["size"] <= 3


# ============================================================================
# 任务分类器测试
# ============================================================================

class TestTaskClassifier:
    """TaskClassifier 测试"""
    
    def test_init(self, sample_config, mock_llm_client):
        """测试初始化"""
        classifier = TaskClassifier(
            config=sample_config,
            llm_client=mock_llm_client
        )
        assert len(classifier.config.categories) == 5
    
    def test_build_prompt(self, classifier):
        """测试构建提示词"""
        task = TaskToClassify(
            task_id="test",
            content="修复内存问题",
            context="本周工作"
        )
        
        prompt = classifier._build_prompt(task, classifier.config.categories)
        
        assert "内存问题" in prompt
        assert "本周工作" in prompt
        assert "memory" in prompt
        assert "resource" in prompt
    
    def test_parse_llm_response_single(self, classifier):
        """测试解析单个分类响应"""
        response = "memory"
        categories = classifier._parse_llm_response(response)
        assert categories == ["memory"]
    
    def test_parse_llm_response_multiple(self, classifier):
        """测试解析多个分类响应"""
        response = "memory, resource"
        categories = classifier._parse_llm_response(response)
        assert set(categories) == {"memory", "resource"}
    
    def test_parse_llm_response_with_noise(self, classifier):
        """测试解析带噪声的响应"""
        response = "分类结果是：memory, resource\n其他说明"
        categories = classifier._parse_llm_response(response)
        assert set(categories) == {"memory", "resource"}
    
    def test_parse_llm_response_invalid(self, classifier):
        """测试解析无效响应"""
        response = "这是一个无效的分类"
        categories = classifier._parse_llm_response(response)
        assert categories == []
    
    def test_fallback_keyword_match_memory(self, classifier):
        """测试关键词匹配 - 内存"""
        task = TaskToClassify(
            task_id="test",
            content="修复Android平台上的内存泄漏问题，优化mmap缓存策略"
        )
        
        categories = classifier._fallback_keyword_match(task)
        assert "memory" in categories
    
    def test_fallback_keyword_match_resource(self, classifier):
        """测试关键词匹配 - 资源"""
        task = TaskToClassify(
            task_id="test",
            content="优化asset bundle分包规则，解决资源加载问题"
        )
        
        categories = classifier._fallback_keyword_match(task)
        assert "resource" in categories
    
    def test_fallback_keyword_match_ci(self, classifier):
        """测试关键词匹配 - CI"""
        task = TaskToClassify(
            task_id="test",
            content="修复CI流水线打包失败问题"
        )
        
        categories = classifier._fallback_keyword_match(task)
        assert "ci" in categories
    
    def test_fallback_keyword_match_audio(self, classifier):
        """测试关键词匹配 - 音频"""
        task = TaskToClassify(
            task_id="test",
            content="优化音频播放性能，修复wwise音效问题"
        )
        
        categories = classifier._fallback_keyword_match(task)
        assert "audio" in categories
    
    def test_fallback_keyword_match_harmonyos(self, classifier):
        """测试关键词匹配 - 鸿蒙"""
        task = TaskToClassify(
            task_id="test",
            content="支持鸿蒙平台，与华为工程师合作"
        )
        
        categories = classifier._fallback_keyword_match(task)
        assert "harmonyos" in categories
    
    def test_fallback_keyword_match_multiple(self, classifier):
        """测试关键词匹配 - 多个分类"""
        task = TaskToClassify(
            task_id="test",
            content="优化鸿蒙平台的内存和资源加载性能"
        )
        
        categories = classifier._fallback_keyword_match(task)
        assert "harmonyos" in categories
        assert "memory" in categories or "resource" in categories
    
    def test_classify_task_with_llm(self, sample_config, cache_manager):
        """测试使用LLM分类"""
        # 创建模拟LLM客户端
        mock_client = MagicMock()
        mock_client.call = MagicMock(return_value="memory, resource")
        
        classifier = TaskClassifier(
            config=sample_config,
            llm_client=mock_client,
            cache_manager=cache_manager
        )
        
        task = TaskToClassify(
            task_id="test",
            content="修复内存和资源相关的问题"
        )
        
        result = classifier.classify_task(task)
        
        assert result.method == "llm"
        assert set(result.categories) == {"memory", "resource"}
        assert result.confidence >= 0.9
        mock_client.call.assert_called_once()
    
    def test_classify_task_fallback(self, classifier):
        """测试LLM失败后降级到关键词匹配"""
        # LLM客户端返回None表示失败
        classifier.llm_client.call = MagicMock(return_value=None)
        
        task = TaskToClassify(
            task_id="test",
            content="修复CI流水线打包问题"
        )
        
        result = classifier.classify_task(task)
        
        assert result.method == "keyword"
        assert "ci" in result.categories
        assert result.confidence >= 0.5
    
    def test_classify_task_uncategorized(self, classifier):
        """测试无法分类的任务"""
        classifier.llm_client.call = MagicMock(return_value=None)
        
        task = TaskToClassify(
            task_id="test",
            content="这是一条无法分类的任务内容"
        )
        
        result = classifier.classify_task(task)
        
        # 应该标记为未分类或使用关键词匹配
        assert result.categories is not None
        assert result.confidence >= 0
    
    def test_classify_task_cache_hit(self, sample_config):
        """测试缓存命中"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(cache_dir=tmpdir)
            
            # 使用 MagicMock 并正确配置 call 方法
            mock_client = MagicMock()
            mock_client.call = MagicMock(return_value="memory")
            
            classifier = TaskClassifier(
                config=sample_config,
                llm_client=mock_client,
                cache_manager=cache
            )
            
            task = TaskToClassify(
                task_id="test",
                content="测试缓存"
            )
            
            # 第一次分类
            result1 = classifier.classify_task(task)
            
            # 第二次分类应该命中缓存
            result2 = classifier.classify_task(task)
            
            # LLM应该只被调用一次
            assert mock_client.call.call_count == 1
            
            # 结果应该一致
            assert result1.categories == result2.categories
    
    def test_classify_batch(self, classifier):
        """测试批量分类"""
        classifier.llm_client.call = MagicMock(return_value=None)  # 强制使用关键词匹配
        
        tasks = [
            TaskToClassify(task_id="t1", content="修复内存泄漏"),
            TaskToClassify(task_id="t2", content="优化资源加载"),
            TaskToClassify(task_id="t3", content="支持鸿蒙平台"),
            TaskToClassify(task_id="t4", content="修复CI打包问题"),
            TaskToClassify(task_id="t5", content="音频播放优化"),
        ]
        
        results = classifier.classify_batch(tasks)
        
        assert len(results) == 5
        for result in results:
            assert isinstance(result, ClassificationResult)
            assert result.categories is not None
    
    def test_classify_batch_large(self, sample_config, cache_manager):
        """测试大批量分类（性能测试）"""
        mock_client = MagicMock()
        mock_client.call = MagicMock(return_value=None)
        
        classifier = TaskClassifier(
            config=sample_config,
            llm_client=mock_client,
            cache_manager=cache_manager
        )
        
        # 创建100个任务
        tasks = [
            TaskToClassify(
                task_id=f"task-{i}",
                content=f"任务{i}: 修复内存和资源相关问题"
            )
            for i in range(100)
        ]
        
        start_time = time.time()
        results = classifier.classify_batch(tasks, batch_size=20)
        elapsed = time.time() - start_time
        
        assert len(results) == 100
        # 平均每个任务应该小于2秒（这里用更宽松的限制）
        avg_time = elapsed / 100
        assert avg_time < 0.5, f"平均分类时间过长: {avg_time:.2f}s"
    
    def test_classify_batch_response_time(self, sample_config, cache_manager):
        """测试响应时间要求 < 2秒/任务"""
        mock_client = MagicMock()
        mock_client.call = MagicMock(return_value="memory")
        
        classifier = TaskClassifier(
            config=sample_config,
            llm_client=mock_client,
            cache_manager=cache_manager,
            timeout_seconds=2.0
        )
        
        task = TaskToClassify(
            task_id="perf-test",
            content="性能测试任务"
        )
        
        start_time = time.time()
        result = classifier.classify_task(task)
        elapsed = time.time() - start_time
        
        assert elapsed < 2.0, f"响应时间超过2秒: {elapsed:.2f}s"
    
    def test_llm_retry_mechanism(self, sample_config, cache_manager):
        """测试LLM重试机制"""
        mock_client = MagicMock()
        # 前两次失败，第三次成功
        mock_client.call = MagicMock(side_effect=[None, None, "memory"])
        
        classifier = TaskClassifier(
            config=sample_config,
            llm_client=mock_client,
            cache_manager=cache_manager,
            max_retries=3
        )
        
        task = TaskToClassify(
            task_id="retry-test",
            content="重试测试"
        )
        
        result = classifier.classify_task(task)
        
        # 应该调用3次
        assert mock_client.call.call_count == 3
        # 最终应该成功
        assert result.method == "llm"
        assert "memory" in result.categories
    
    def test_llm_max_retries_exceeded(self, sample_config, cache_manager):
        """测试超过最大重试次数后降级"""
        mock_client = MagicMock()
        mock_client.call = MagicMock(return_value=None)  # 总是失败
        
        classifier = TaskClassifier(
            config=sample_config,
            llm_client=mock_client,
            cache_manager=cache_manager,
            max_retries=3
        )
        
        task = TaskToClassify(
            task_id="fail-test",
            content="内存优化"  # 包含关键词，确保降级后能匹配
        )
        
        result = classifier.classify_task(task)
        
        # 应该调用3次
        assert mock_client.call.call_count == 3
        # 应该降级到关键词匹配
        assert result.method == "keyword"
    
    def test_get_category_info(self, classifier):
        """测试获取分类信息"""
        category = classifier.get_category_info("memory")
        assert category is not None
        assert category.id == "memory"
        assert category.name == "内存相关"
    
    def test_get_category_info_not_found(self, classifier):
        """测试获取不存在的分类"""
        category = classifier.get_category_info("nonexistent")
        assert category is None
    
    def test_get_all_categories(self, classifier):
        """测试获取所有分类"""
        categories = classifier.get_all_categories()
        assert len(categories) == 5
        category_ids = [cat.id for cat in categories]
        assert "memory" in category_ids
        assert "resource" in category_ids
        assert "harmonyos" in category_ids
        assert "ci" in category_ids
        assert "audio" in category_ids


# ============================================================================
# 便捷函数测试
# ============================================================================

class TestCreateClassifier:
    """create_classifier 便捷函数测试"""
    
    def test_create_classifier_with_file(self):
        """测试从配置文件创建分类器"""
        # 使用项目中的实际配置文件
        config_path = Path("~/Documents/weekly-report-system/data/config/task_category.md")
        config_path = config_path.expanduser()
        
        if not config_path.exists():
            pytest.skip("配置文件不存在")
        
        classifier = create_classifier(str(config_path))
        assert classifier is not None
        assert len(classifier.config.categories) >= 5


# ============================================================================
# 集成测试
# ============================================================================

class TestIntegration:
    """集成测试"""
    
    def test_full_classification_flow(self, sample_config):
        """测试完整的分类流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CacheManager(cache_dir=tmpdir)
            mock_client = MagicMock()
            mock_client.call = MagicMock(return_value="memory,resource")
            
            classifier = TaskClassifier(
                config=sample_config,
                llm_client=mock_client,
                cache_manager=cache
            )
            
            # 创建多个任务
            tasks = [
                TaskToClassify(task_id=f"task-{i}", content=f"任务{i}内容")
                for i in range(10)
            ]
            
            # 批量分类
            results = classifier.classify_batch(tasks)
            
            # 验证结果
            assert len(results) == 10
            for result in results:
                assert isinstance(result, ClassificationResult)
                assert result.categories is not None
            
            # 验证缓存
            stats = cache.get_stats()
            assert stats["size"] > 0


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
