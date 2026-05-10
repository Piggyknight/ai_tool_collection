"""
LLM润色服务单元测试
"""

import pytest
from src.core.llm_service import LLMService


class TestLLMService:
    """测试 LLMService 类"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return LLMService()

    def test_init(self, service):
        """测试初始化"""
        assert service.model == "zai/glm-5"

    def test_init_custom_model(self):
        """测试自定义模型"""
        service = LLMService(model="custom-model")
        assert service.model == "custom-model"

    def test_polish_text_empty(self, service):
        """测试润色空文本"""
        assert service.polish_text("") == ""
        assert service.polish_text("   ") == "   "

    def test_polish_text_concise(self, service):
        """测试简洁风格润色"""
        text = "修复了很多BUG，新增了一些功能"
        result = service.polish_text(text, "concise")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_polish_text_formal(self, service):
        """测试正式风格润色"""
        text = "修好了BUG"
        result = service.polish_text(text, "formal")
        assert isinstance(result, str)

    def test_polish_text_detailed(self, service):
        """测试详细风格润色"""
        text = "修复BUG"
        result = service.polish_text(text, "detailed")
        assert isinstance(result, str)

    def test_summarize_tasks_empty(self, service):
        """测试汇总空任务列表"""
        result = service.summarize_tasks([])
        assert result == ""

    def test_summarize_tasks(self, service):
        """测试汇总任务列表"""
        tasks = ["修复登录BUG", "优化性能", "新增功能"]
        result = service.summarize_tasks(tasks)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_deduplicate_similar_empty(self, service):
        """测试去重空列表"""
        result = service.deduplicate_similar([])
        assert result == []

    def test_deduplicate_similar(self, service):
        """测试去重相似任务"""
        tasks = ["修复登录BUG", "修复登录页BUG", "新增功能"]
        result = service.deduplicate_similar(tasks)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_build_polish_prompt(self, service):
        """测试构造润色提示词"""
        prompt = service._build_polish_prompt("修复BUG", "concise")
        assert "修复BUG" in prompt
        assert "简洁" in prompt

    def test_build_summarize_prompt(self, service):
        """测试构造汇总提示词"""
        tasks = ["任务1", "任务2"]
        prompt = service._build_summarize_prompt(tasks)
        assert "任务1" in prompt
        assert "任务2" in prompt

    def test_build_deduplicate_prompt(self, service):
        """测试构造去重提示词"""
        tasks = ["任务1", "任务2"]
        prompt = service._build_deduplicate_prompt(tasks)
        assert "任务1" in prompt
        assert "任务2" in prompt

    def test_generate_weekly_report(self, service):
        """测试生成周报"""
        report = service.generate_weekly_report(
            "HLQ",
            ["修复登录BUG", "优化性能"],
            "2026-03-02 ~ 2026-03-07"
        )

        assert "HLQ" in report
        assert "2026-03-02 ~ 2026-03-07" in report
        assert "本周完成的工作" in report


class TestLLMServiceIntegration:
    """集成测试"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return LLMService()

    def test_full_workflow(self, service):
        """测试完整工作流"""
        # 1. 润色文本
        text = "修复了很多很多的BUG"
        polished = service.polish_text(text)
        assert isinstance(polished, str)

        # 2. 汇总任务
        tasks = ["修复BUG1", "修复BUG2", "新增功能"]
        summary = service.summarize_tasks(tasks)
        assert isinstance(summary, str)

        # 3. 生成周报
        report = service.generate_weekly_report("DJZ", tasks, "2026-W10")
        assert "DJZ" in report
        assert "2026-W10" in report
