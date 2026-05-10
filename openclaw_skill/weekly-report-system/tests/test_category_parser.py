"""
分类规则解析器单元测试

测试 category_parser.py 模块的各项功能
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.core.category_parser import (
    Category,
    CategoryConfig,
    CategoryParser,
    load_categories
)


# 测试用的Markdown配置内容
SAMPLE_CONFIG = """# 任务分类规则配置

这份文档主要是用来提供llm任务分类相关规则的文档. 

## 内存相关
主要是项目中涉及内存优化, 内存相关问题修复, 缓存池优化相关任务.
编辑器与打unity的asset bundle包流程中的内存相关问题也属于内存任务.
目前项目中也是用静态数据直接读取操作的方式,由于使用mmap的内存接口, 因此也被称为mmap优化.
后续可能还会有针对代码大小的内存优化, 比如il2cpp代码转换的dll或者so文件大小优化等.
为了查一些内存问题, 我们需要各个平台支持asan功能, 在android上还有硬件支持的HWsan. asan相关任务也属于内存.


## 资源相关
我们使用自定义的vfs文件系统, 将unity的asset bundle文件合并在一起, 以每个100mb左右的文件进行分割, 这样可以解决ab过多, 无法卸载干净等问题.
项目中经常有任务涉及游戏内runt资源异步加载, 异步卸载, 延迟实例化都属于资源相关任务.
另外, 因为仍然使用assetbundle, 我们仍然需要对资源进行各种分包规则优化任务, 以及协助美术修复资源相关问题.
unity引擎内部多进程打包, 搜索资源依赖等存在bug, 也需要修复, 则部分任务也属于资源相关任务.
为了避免unity的guid missing问题, 我们使用svn hook的方式, 在美术提交时检查unity资源引用的正确性. 


## 鸿蒙支持相关
unity默认支持ios, android, pc. 目前项目中正在移植鸿蒙平台, 包括和华为工程师合作完成鸿蒙的客户端生成, 资源生成, 问题修复等. 

## CI先关任务
我们使用腾讯的蓝盾系统来打包所有客户端与资源. 同时为了线上发布, 将包体发布出去, 需要各种各样的工具, 以及资源监控体统. 比如包体大小, 符号表备份, crash符号服务器建设, 版本号数据库.
由于负责流水线是最后一步, 前置各种错误都会在CI打包时发生, 因此CI流水线上的问题修复也都属于CI相关任务.

## 音频相关任务
我们游戏目前使用wwise插件来播放声音, 整体声音游戏runtime的bug修复, 比如枪声, 环境音都都属于音频任务.
wwise的任务涉及环境音, 混响, 各种音效播放, 音频的性能与内存相关, 都划为音频任务.
"""

# 简化的测试配置
MINIMAL_CONFIG = """
## 测试分类
这是测试描述，包含关键词 test keyword。
"""


class TestCategory:
    """测试 Category 数据类"""
    
    def test_category_creation(self):
        """测试创建分类对象"""
        cat = Category(
            id="test",
            name="测试分类",
            keywords=["key1", "key2"],
            description="测试描述"
        )
        
        assert cat.id == "test"
        assert cat.name == "测试分类"
        assert cat.keywords == ["key1", "key2"]
        assert cat.description == "测试描述"
    
    def test_category_to_dict(self):
        """测试转换为字典"""
        cat = Category(
            id="memory",
            name="内存相关",
            keywords=["内存", "mmap"],
            description="内存优化相关"
        )
        
        result = cat.to_dict()
        
        assert result["id"] == "memory"
        assert result["name"] == "内存相关"
        assert "内存" in result["keywords"]
        assert result["description"] == "内存优化相关"
    
    def test_category_default_values(self):
        """测试默认值"""
        cat = Category(id="test", name="测试")
        
        assert cat.keywords == []
        assert cat.description == ""


class TestCategoryConfig:
    """测试 CategoryConfig 数据类"""
    
    def test_config_creation(self):
        """测试创建配置对象"""
        cats = [
            Category(id="cat1", name="分类1"),
            Category(id="cat2", name="分类2")
        ]
        
        config = CategoryConfig(categories=cats, version="1.0.0")
        
        assert len(config.categories) == 2
        assert config.version == "1.0.0"
    
    def test_config_to_dict(self):
        """测试配置转换为字典"""
        cats = [Category(id="test", name="测试", keywords=["k1"])]
        config = CategoryConfig(categories=cats, version="v2")
        
        result = config.to_dict()
        
        assert result["version"] == "v2"
        assert len(result["categories"]) == 1
        assert result["categories"][0]["id"] == "test"
    
    def test_config_default_values(self):
        """测试配置默认值"""
        config = CategoryConfig()
        
        assert config.categories == []
        assert config.version == "1.0"


class TestCategoryParser:
    """测试 CategoryParser 类"""
    
    @pytest.fixture
    def temp_config_file(self):
        """创建临时配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, 
                                         encoding='utf-8') as f:
            f.write(SAMPLE_CONFIG)
            temp_path = f.name
        yield temp_path
        # 清理
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def parser(self, temp_config_file):
        """创建解析器实例"""
        return CategoryParser(temp_config_file)
    
    def test_init(self, temp_config_file):
        """测试初始化"""
        parser = CategoryParser(temp_config_file)
        
        assert parser.config_path == Path(temp_config_file)
        assert parser._config is None
    
    def test_load_config_success(self, parser):
        """测试成功加载配置"""
        config = parser.load_config()
        
        assert config is not None
        assert isinstance(config, CategoryConfig)
        assert len(config.categories) == 5  # 5个分类
    
    def test_load_config_file_not_found(self):
        """测试文件不存在的情况"""
        parser = CategoryParser("/nonexistent/path.md")
        
        with pytest.raises(FileNotFoundError):
            parser.load_config()
    
    def test_load_config_empty_file(self):
        """测试空文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False,
                                         encoding='utf-8') as f:
            f.write("")
            temp_path = f.name
        
        try:
            parser = CategoryParser(temp_path)
            with pytest.raises(ValueError):
                parser.load_config()
        finally:
            os.unlink(temp_path)
    
    def test_parse_five_categories(self, parser):
        """测试正确解析5个分类"""
        config = parser.load_config()
        
        assert len(config.categories) == 5
        
        category_ids = [cat.id for cat in config.categories]
        expected_ids = ["memory", "resource", "harmonyos", "ci", "audio"]
        
        for expected_id in expected_ids:
            assert expected_id in category_ids, f"缺少分类: {expected_id}"
    
    def test_category_names(self, parser):
        """测试分类名称提取"""
        config = parser.load_config()
        
        names = [cat.name for cat in config.categories]
        
        assert "内存相关" in names
        assert "资源相关" in names
        assert "鸿蒙支持相关" in names
    
    def test_keyword_extraction(self, parser):
        """测试关键词提取"""
        config = parser.load_config()
        
        # 检查内存分类的关键词
        memory_cat = parser.get_category("memory")
        assert memory_cat is not None
        
        # 应该包含一些关键词
        assert len(memory_cat.keywords) > 0
        
        # 检查是否包含常见术语
        keywords_str = ' '.join(memory_cat.keywords).lower()
        # 内存相关的常见词
        assert any(kw in keywords_str for kw in ['内存', 'mmap', 'asan', '优化'])
    
    def test_description_extraction(self, parser):
        """测试描述提取"""
        config = parser.load_config()
        
        memory_cat = parser.get_category("memory")
        assert memory_cat is not None
        assert len(memory_cat.description) > 0
        assert "内存" in memory_cat.description
    
    def test_get_category(self, parser):
        """测试获取单个分类"""
        parser.load_config()
        
        # 测试存在的分类
        cat = parser.get_category("memory")
        assert cat is not None
        assert cat.id == "memory"
        
        # 测试不存在的分类
        cat = parser.get_category("nonexistent")
        assert cat is None
    
    def test_get_all_categories(self, parser):
        """测试获取所有分类"""
        parser.load_config()
        
        categories = parser.get_all_categories()
        
        assert len(categories) == 5
        assert all(isinstance(cat, Category) for cat in categories)
    
    def test_reload_config_no_change(self, parser):
        """测试重新加载（文件未变化）"""
        config1 = parser.load_config()
        config2 = parser.reload_config()
        
        # 应该返回同一个配置（缓存）
        assert config1.version == config2.version
    
    def test_reload_config_with_change(self, temp_config_file):
        """测试热更新（文件变化后重新加载）"""
        parser = CategoryParser(temp_config_file)
        config1 = parser.load_config()
        
        # 修改文件
        with open(temp_config_file, 'a', encoding='utf-8') as f:
            f.write("\n\n## 新分类\n这是新分类的描述。\n")
        
        # 重新加载
        config2 = parser.reload_config()
        
        # 版本应该不同
        assert config2.version != config1.version
        # 应该有6个分类
        assert len(config2.categories) == 6
    
    def test_has_file_changed(self, temp_config_file):
        """测试检测文件变化"""
        parser = CategoryParser(temp_config_file)
        parser.load_config()
        
        # 初始未变化
        assert parser.has_file_changed() is False
        
        # 修改文件
        with open(temp_config_file, 'a', encoding='utf-8') as f:
            f.write("\n// comment")
        
        # 应该检测到变化
        assert parser.has_file_changed() is True
    
    def test_search_by_keyword(self, parser):
        """测试关键词搜索"""
        parser.load_config()
        
        # 搜索内存相关
        results = parser.search_by_keyword("内存")
        assert len(results) > 0
        
        # 搜索CI相关
        results = parser.search_by_keyword("ci")
        assert len(results) > 0
        
        # 搜索不存在的关键词
        results = parser.search_by_keyword("zzznonexistent")
        assert len(results) == 0
    
    def test_version_generation(self, parser):
        """测试版本号生成"""
        config = parser.load_config()
        
        # 版本号应该是8位hash
        assert len(config.version) == 8
        assert all(c in '0123456789abcdef' for c in config.version)
    
    def test_lazy_loading(self, temp_config_file):
        """测试延迟加载"""
        parser = CategoryParser(temp_config_file)
        
        # 初始未加载
        assert parser._config is None
        
        # 调用get_all_categories会触发加载
        categories = parser.get_all_categories()
        
        assert parser._config is not None
        assert len(categories) == 5


class TestLoadCategoriesFunction:
    """测试便捷函数"""
    
    def test_load_categories(self):
        """测试便捷加载函数"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False,
                                         encoding='utf-8') as f:
            f.write(SAMPLE_CONFIG)
            temp_path = f.name
        
        try:
            config = load_categories(temp_path)
            
            assert isinstance(config, CategoryConfig)
            assert len(config.categories) == 5
        finally:
            os.unlink(temp_path)


class TestKeywordAccuracy:
    """测试关键词提取准确率"""
    
    @pytest.fixture
    def parser(self):
        """创建解析器"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False,
                                         encoding='utf-8') as f:
            f.write(SAMPLE_CONFIG)
            temp_path = f.name
        
        parser = CategoryParser(temp_path)
        parser.load_config()
        yield parser
        
        os.unlink(temp_path)
    
    def test_memory_keywords_accuracy(self, parser):
        """测试内存分类关键词准确率"""
        cat = parser.get_category("memory")
        
        # 预期应该包含的关键词
        expected_keywords = ["内存", "mmap", "asan", "优化", "缓存"]
        
        found_count = 0
        for kw in expected_keywords:
            if kw in cat.keywords or kw in cat.description:
                found_count += 1
        
        accuracy = found_count / len(expected_keywords)
        assert accuracy >= 0.9, f"关键词准确率 {accuracy:.1%} 低于90%"
    
    def test_resource_keywords_accuracy(self, parser):
        """测试资源分类关键词准确率"""
        cat = parser.get_category("resource")
        
        expected_keywords = ["资源", "vfs", "asset", "bundle", "加载", "卸载"]
        
        found_count = 0
        for kw in expected_keywords:
            if kw in cat.keywords or kw in cat.description:
                found_count += 1
        
        accuracy = found_count / len(expected_keywords)
        assert accuracy >= 0.9, f"关键词准确率 {accuracy:.1%} 低于90%"
    
    def test_ci_keywords_accuracy(self, parser):
        """测试CI分类关键词准确率"""
        cat = parser.get_category("ci")
        
        expected_keywords = ["ci", "流水线", "打包", "蓝盾", "监控", "发布"]
        
        found_count = 0
        for kw in expected_keywords:
            if kw in cat.keywords or kw in cat.description:
                found_count += 1
        
        accuracy = found_count / len(expected_keywords)
        assert accuracy >= 0.9, f"关键词准确率 {accuracy:.1%} 低于90%"
    
    def test_audio_keywords_accuracy(self, parser):
        """测试音频分类关键词准确率"""
        cat = parser.get_category("audio")
        
        expected_keywords = ["音频", "wwise", "声音", "环境音", "混响", "音效"]
        
        found_count = 0
        for kw in expected_keywords:
            if kw in cat.keywords or kw in cat.description:
                found_count += 1
        
        accuracy = found_count / len(expected_keywords)
        assert accuracy >= 0.9, f"关键词准确率 {accuracy:.1%} 低于90%"


class TestEdgeCases:
    """测试边界情况"""
    
    def test_special_characters_in_content(self):
        """测试内容中包含特殊字符"""
        content = """
## 特殊分类
包含特殊字符: @#$%^&*()_+-={}[]|\\:";<>?,./ 
还有中文和English混合。
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False,
                                         encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            parser = CategoryParser(temp_path)
            config = parser.load_config()
            
            assert len(config.categories) == 1
        finally:
            os.unlink(temp_path)
    
    def test_unicode_content(self):
        """测试Unicode内容"""
        content = """
## 表情分类 🎉
这是包含emoji的描述 😀🎉🚀
还有其他Unicode字符：中文 日本語 한국어
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False,
                                         encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            parser = CategoryParser(temp_path)
            config = parser.load_config()
            
            assert len(config.categories) == 1
            assert "🎉" in config.categories[0].name
        finally:
            os.unlink(temp_path)
    
    def test_empty_section(self):
        """测试空章节"""
        content = """
## 空分类


## 有内容分类
这是描述。
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False,
                                         encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            parser = CategoryParser(temp_path)
            config = parser.load_config()
            
            assert len(config.categories) == 2
        finally:
            os.unlink(temp_path)
    
    def test_multiple_reloads(self):
        """测试多次重新加载"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False,
                                         encoding='utf-8') as f:
            f.write(SAMPLE_CONFIG)
            temp_path = f.name
        
        try:
            parser = CategoryParser(temp_path)
            
            for _ in range(5):
                config = parser.reload_config()
                assert len(config.categories) == 5
        finally:
            os.unlink(temp_path)


# 集成测试
class TestIntegration:
    """集成测试 - 使用实际配置文件"""
    
    def test_real_config_file(self):
        """测试使用实际配置文件"""
        config_path = Path.home() / "Documents/weekly-report-system/data/config/task_category.md"
        
        if not config_path.exists():
            pytest.skip(f"配置文件不存在: {config_path}")
        
        parser = CategoryParser(str(config_path))
        config = parser.load_config()
        
        # 验证基本要求
        assert len(config.categories) >= 5, "应该至少有5个分类"
        
        # 验证每个分类都有必要的信息
        for cat in config.categories:
            assert cat.id, f"分类 {cat.name} 缺少ID"
            assert cat.name, f"分类 {cat.id} 缺少名称"
            assert len(cat.keywords) > 0, f"分类 {cat.name} 缺少关键词"
            assert cat.description, f"分类 {cat.id} 缺少描述"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
