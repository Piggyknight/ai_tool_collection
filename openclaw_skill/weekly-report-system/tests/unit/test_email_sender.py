"""
邮件发送封装单元测试
"""

import pytest
from src.core.email_sender import EmailSender


class TestEmailSender:
    """测试 EmailSender 类"""

    @pytest.fixture
    def sender(self):
        """创建发送器实例"""
        return EmailSender()

    def test_init(self, sender):
        """测试初始化"""
        assert sender.smtp_config is not None

    def test_init_with_config(self):
        """测试带配置初始化"""
        config = {"host": "smtp.example.com", "port": 587}
        sender = EmailSender(smtp_config=config)
        assert sender.smtp_config == config

    def test_send_email_basic(self, sender):
        """测试基本邮件发送"""
        result = sender.send_email(
            to="user@example.com",
            subject="测试邮件",
            content="这是测试内容"
        )
        assert result is True

    def test_send_email_with_attachment(self, sender):
        """测试带附件的邮件发送"""
        result = sender.send_email(
            to="user@example.com",
            subject="带附件的邮件",
            content="内容",
            attachment="/path/to/file.pdf"
        )
        assert result is True

    def test_send_batch_empty(self, sender):
        """测试批量发送空列表"""
        result = sender.send_batch([], "主题", lambda r: "内容")
        assert result["total"] == 0
        assert result["success"] == 0
        assert result["failed"] == 0

    def test_send_batch_success(self, sender):
        """测试批量发送成功"""
        recipients = [
            {"name": "张三", "email": "zhangsan@example.com"},
            {"name": "李四", "email": "lisi@example.com"}
        ]

        def content_gen(r):
            return f"你好 {r['name']}"

        result = sender.send_batch(recipients, "通知", content_gen)

        assert result["total"] == 2
        assert result["success"] == 2
        assert result["failed"] == 0

    def test_send_batch_missing_email(self, sender):
        """测试批量发送时缺少邮箱"""
        recipients = [
            {"name": "张三", "email": "zhangsan@example.com"},
            {"name": "李四"}  # 缺少邮箱
        ]

        result = sender.send_batch(recipients, "通知", lambda r: "内容")

        assert result["total"] == 2
        assert result["success"] == 1
        assert result["failed"] == 1
        assert len(result["errors"]) > 0

    def test_send_weekly_report(self, sender):
        """测试发送周报"""
        result = sender.send_weekly_report(
            to="user@example.com",
            member_name="张三",
            report_content="# 周报内容",
            week_range="2026-03-02 ~ 2026-03-07"
        )
        assert result is True

    def test_send_team_weekly_to_admin(self, sender):
        """测试发送团队周报给管理员"""
        result = sender.send_team_weekly_to_admin(
            admin_email="admin@example.com",
            report_content="# 团队周报",
            week_range="2026-W10"
        )
        assert result is True

    def test_validate_email_valid(self, sender):
        """测试验证有效邮箱"""
        assert sender.validate_email("user@example.com") is True
        assert sender.validate_email("user.name@subdomain.example.com") is True
        assert sender.validate_email("user+tag@example.co.uk") is True

    def test_validate_email_invalid(self, sender):
        """测试验证无效邮箱"""
        assert sender.validate_email("invalid-email") is False
        assert sender.validate_email("@example.com") is False
        assert sender.validate_email("user@") is False
        assert sender.validate_email("") is False

    def test_format_html_email(self, sender):
        """测试格式化HTML邮件"""
        html = sender.format_html_email(
            title="周报",
            content="# 标题\n内容",
            style="default"
        )

        assert "<!DOCTYPE html>" in html
        assert "周报" in html
        assert "标题" in html

    def test_format_html_email_structure(self, sender):
        """测试HTML邮件结构"""
        html = sender.format_html_email("测试", "内容")

        assert "<html>" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "<style>" in html


class TestEmailSenderEdgeCases:
    """测试边界情况"""

    @pytest.fixture
    def sender(self):
        """创建发送器实例"""
        return EmailSender()

    def test_send_email_empty_content(self, sender):
        """测试发送空内容"""
        result = sender.send_email("user@example.com", "主题", "")
        assert result is True

    def test_send_batch_content_generator_error(self, sender):
        """测试内容生成器抛出异常"""
        recipients = [{"name": "张三", "email": "user@example.com"}]

        def bad_generator(r):
            raise Exception("生成错误")

        result = sender.send_batch(recipients, "主题", bad_generator)

        assert result["failed"] == 1
        assert len(result["errors"]) > 0
