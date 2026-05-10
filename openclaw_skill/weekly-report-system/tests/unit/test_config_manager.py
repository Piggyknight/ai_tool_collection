"""
配置管理模块单元测试
"""

import pytest
import tempfile
import shutil
from src.modules.config_manager import ConfigManager


class TestConfigManager:
    """测试 ConfigManager 类"""

    @pytest.fixture
    def temp_config_dir(self):
        """创建临时配置目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_init(self, temp_config_dir):
        """测试初始化"""
        manager = ConfigManager(temp_config_dir)
        assert manager.config_dir.exists()

    def test_initialize_default_config(self, temp_config_dir):
        """测试初始化默认配置"""
        manager = ConfigManager(temp_config_dir)
        manager.initialize_default_config()

        assert manager.members_file.exists()
        assert manager.system_file.exists()

    def test_load_members(self, temp_config_dir):
        """测试加载成员配置"""
        manager = ConfigManager(temp_config_dir)
        manager.initialize_default_config()

        members = manager.load_members()
        assert "HLQ" in members
        assert members["HLQ"]["email"] == "hlqiang@wooduan.com"

    def test_get_member_email(self, temp_config_dir):
        """测试获取成员邮箱"""
        manager = ConfigManager(temp_config_dir)
        manager.initialize_default_config()

        email = manager.get_member_email("HLQ")
        assert email == "hlqiang@wooduan.com"

    def test_get_admin_email(self, temp_config_dir):
        """测试获取管理员邮箱"""
        manager = ConfigManager(temp_config_dir)
        manager.initialize_default_config()

        email = manager.get_admin_email()
        assert email == "kai@wooduan.com"

    def test_get_all_active_members(self, temp_config_dir):
        """测试获取所有活跃成员"""
        manager = ConfigManager(temp_config_dir)
        manager.initialize_default_config()

        members = manager.get_all_active_members()
        assert isinstance(members, list)
        assert len(members) > 0
        assert all(m["active"] for m in members)

    def test_get_llm_config(self, temp_config_dir):
        """测试获取LLM配置"""
        manager = ConfigManager(temp_config_dir)
        manager.initialize_default_config()

        llm_config = manager.get_llm_config()
        assert "model" in llm_config
        assert llm_config["model"] == "zai/glm-5"

    def test_get_cron_config(self, temp_config_dir):
        """测试获取定时任务配置"""
        manager = ConfigManager(temp_config_dir)
        manager.initialize_default_config()

        cron_config = manager.get_cron_config()
        assert "weekly_time" in cron_config
        assert cron_config["weekly_time"] == "0 20 * * 6"

    def test_load_members_cache(self, temp_config_dir):
        """测试成员配置缓存"""
        manager = ConfigManager(temp_config_dir)
        manager.initialize_default_config()

        # 第一次加载
        members1 = manager.load_members()
        # 第二次加载（应使用缓存）
        members2 = manager.load_members()

        assert members1 is members2  # 应该是同一个对象
