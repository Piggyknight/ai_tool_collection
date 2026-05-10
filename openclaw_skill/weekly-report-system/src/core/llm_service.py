"""
LLM润色服务

调用OpenClaw的GLM模型进行文本润色
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class LLMService:
    """LLM润色服务"""

    def __init__(self, model: str = "zai/glm-5"):
        """
        初始化LLM服务

        Args:
            model: 模型名称
        """
        self.model = model
        logger.info(f"初始化LLM服务，模型: {model}")

    def polish_text(self, text: str, style: str = "concise") -> str:
        """
        使用LLM润色文本

        Args:
            text: 待润色的文本
            style: 润色风格
                - "concise": 简洁（默认）
                - "formal": 正式
                - "detailed": 详细

        Returns:
            润色后的文本

        Example:
            >>> service = LLMService()
            >>> polished = service.polish_text("修复了很多BUG", "concise")
        """
        if not text or not text.strip():
            return text

        # 构造润色提示词
        prompt = self._build_polish_prompt(text, style)

        # 调用OpenClaw的GLM模型（模拟实现）
        # 实际实现应该调用sessions_spawn或其他OpenClaw API
        polished = self._call_llm(prompt)

        return polished if polished else text

    def summarize_tasks(self, tasks: List[str]) -> str:
        """
        汇总并精简任务列表

        Args:
            tasks: 任务列表

        Returns:
            汇总后的文本

        Example:
            >>> tasks = ["修复BUG1", "修复BUG2", "新增功能"]
            >>> summary = service.summarize_tasks(tasks)
        """
        if not tasks:
            return ""

        # 构造汇总提示词
        prompt = self._build_summarize_prompt(tasks)

        # 调用LLM
        summary = self._call_llm(prompt)

        return summary if summary else "\n".join(f"- {task}" for task in tasks)

    def deduplicate_similar(self, tasks: List[str]) -> List[str]:
        """
        识别相似任务并去重（使用LLM辅助）

        Args:
            tasks: 任务列表

        Returns:
            去重后的任务列表

        Example:
            >>> tasks = ["修复登录BUG", "修复登录页面BUG", "新增功能"]
            >>> deduped = service.deduplicate_similar(tasks)
        """
        if not tasks:
            return []

        # 对于LLM去重，我们构造一个提示词让LLM识别相似任务
        prompt = self._build_deduplicate_prompt(tasks)

        # 调用LLM
        result = self._call_llm(prompt)

        if result:
            # 解析LLM返回的任务列表
            deduped = [
                line.strip().lstrip('- ')
                for line in result.strip().split('\n')
                if line.strip() and not line.startswith('#')
            ]
            return deduped if deduped else tasks

        return tasks

    def _build_polish_prompt(self, text: str, style: str) -> str:
        """构造润色提示词"""
        style_guide = {
            "concise": "简洁明了，突出重点，去除冗余",
            "formal": "正式专业，使用规范的技术术语",
            "detailed": "详细完整，保留所有细节信息"
        }

        guide = style_guide.get(style, style_guide["concise"])

        prompt = f"""请润色以下工作汇报文本，要求：
1. {guide}
2. 保持核心信息不变
3. 使用清晰的业务语言
4. 保留关键的技术细节和数据
5. 如果有多项工作，用分号分隔

原文：
{text}

润色后的文本："""

        return prompt

    def _build_summarize_prompt(self, tasks: List[str]) -> str:
        """构造汇总提示词"""
        tasks_text = "\n".join(f"- {task}" for task in tasks)

        prompt = f"""请将以下工作内容汇总整理，要求：
1. 按工作类型分类（如：功能开发、BUG修复、性能优化等）
2. 合并同类项，去除重复
3. 使用简洁的专业术语
4. 保留关键的技术细节和成果
5. 使用Markdown格式输出

工作内容：
{tasks_text}

汇总后的周报："""

        return prompt

    def _build_deduplicate_prompt(self, tasks: List[str]) -> str:
        """构造去重提示词"""
        tasks_text = "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))

        prompt = f"""以下工作列表中可能存在相似或重复的内容，请识别并合并相似的任务：

{tasks_text}

要求：
1. 合并内容相似或重复的任务
2. 保留最完整、最准确的描述
3. 去重后用列表形式输出（每行一个任务，格式：- 任务描述）

去重后的任务列表："""

        return prompt

    def _call_llm(self, prompt: str) -> Optional[str]:
        """
        调用LLM模型

        Args:
            prompt: 提示词

        Returns:
            LLM返回的文本，失败返回None

        Note:
            这是一个模拟实现。实际实现应该：
            1. 使用sessions_spawn调用OpenClaw的子会话
            2. 或直接调用GLM模型API
            3. 处理超时和错误
        """
        try:
            # 模拟LLM调用
            # 在实际项目中，这里应该调用OpenClaw的API
            logger.info(f"调用LLM模型: {self.model}, 提示词长度: {len(prompt)}")

            # 简单的模拟：返回优化后的文本
            # 实际应该返回LLM的真实结果
            if "润色" in prompt:
                # 简单的润色逻辑
                lines = prompt.split('\n\n原文：\n')[-1].split('\n\n润色后的文本：')[0]
                # 去除多余的空格和标点
                polished = lines.strip()
                return polished

            return None

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return None

    def generate_weekly_report(
        self,
        member: str,
        tasks: List[str],
        week_range: str
    ) -> str:
        """
        生成个人周报

        Args:
            member: 成员名称
            tasks: 任务列表
            week_range: 周期描述（如"2026-03-02 ~ 2026-03-07"）

        Returns:
            格式化的周报文本

        Example:
            >>> report = service.generate_weekly_report(
            ...     "HLQ",
            ...     ["修复登录BUG", "优化性能"],
            ...     "2026-03-02 ~ 2026-03-07"
            ... )
        """
        # 使用LLM汇总任务
        summary = self.summarize_tasks(tasks)

        # 构造周报
        report = f"""# {member} 周报

**周期**: {week_range}

## ● 本周完成的工作:

{summary}

---
*此周报由自动化系统生成*
"""
        return report
