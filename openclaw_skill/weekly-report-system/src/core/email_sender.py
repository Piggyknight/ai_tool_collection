"""
邮件发送封装

封装OpenClaw邮件发送功能
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class EmailSender:
    """邮件发送器"""

    def __init__(self, smtp_config: Optional[Dict] = None):
        """
        初始化邮件发送器

        Args:
            smtp_config: SMTP配置（可选）
        """
        self.smtp_config = smtp_config or {}
        logger.info("初始化邮件发送器")

    def send_email(
        self,
        to: str,
        subject: str,
        content: str,
        attachment: Optional[str] = None
    ) -> bool:
        """
        发送邮件

        Args:
            to: 收件人邮箱
            subject: 邮件主题
            content: 邮件内容
            attachment: 附件路径（可选）

        Returns:
            True if 发送成功, False otherwise

        Example:
            >>> sender = EmailSender()
            >>> sender.send_email(
            ...     "user@example.com",
            ...     "周报通知",
            ...     "这是您的周报"
            ... )
            True

        Note:
            实际实现应该使用OpenClaw的send_email工具
        """
        try:
            logger.info(f"准备发送邮件到: {to}")
            logger.info(f"主题: {subject}")
            logger.info(f"内容长度: {len(content)}")

            if attachment:
                logger.info(f"附件: {attachment}")

            # 模拟邮件发送
            # 实际实现应该调用OpenClaw的send_email工具
            # from send_email import send_email
            # send_email(to=to, subject=subject, text=content, ...)

            logger.info(f"邮件发送成功: {to}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    def send_batch(
        self,
        recipients: List[Dict[str, str]],
        subject: str,
        content_generator
    ) -> Dict:
        """
        批量发送邮件

        Args:
            recipients: 收件人列表，每项包含:
                {
                    "name": "姓名",
                    "email": "邮箱",
                    "data": {}  # 附加数据（用于生成内容）
                }
            subject: 邮件主题
            content_generator: 内容生成函数
                def generator(recipient: dict) -> str:
                    return "邮件内容"

        Returns:
            发送结果统计:
            {
                "total": 10,
                "success": 8,
                "failed": 2,
                "errors": ["错误信息"]
            }

        Example:
            >>> recipients = [
            ...     {"name": "张三", "email": "zhangsan@example.com"},
            ...     {"name": "李四", "email": "lisi@example.com"}
            ... ]
            >>> def gen_content(r):
            ...     return f"你好 {r['name']}"
            >>> result = sender.send_batch(recipients, "通知", gen_content)
        """
        result = {
            "total": len(recipients),
            "success": 0,
            "failed": 0,
            "errors": []
        }

        for recipient in recipients:
            email = recipient.get("email")
            if not email:
                logger.warning(f"收件人缺少邮箱: {recipient.get('name')}")
                result["failed"] += 1
                result["errors"].append(f"缺少邮箱: {recipient.get('name')}")
                continue

            # 生成个性化内容
            try:
                content = content_generator(recipient)
            except Exception as e:
                logger.error(f"生成内容失败: {email}, 错误: {e}")
                result["failed"] += 1
                result["errors"].append(f"生成内容失败: {email}")
                continue

            # 发送邮件
            success = self.send_email(email, subject, content)

            if success:
                result["success"] += 1
            else:
                result["failed"] += 1
                result["errors"].append(f"发送失败: {email}")

        logger.info(
            f"批量发送完成: 总计 {result['total']}, "
            f"成功 {result['success']}, "
            f"失败 {result['failed']}"
        )

        return result

    def send_weekly_report(
        self,
        to: str,
        member_name: str,
        report_content: str,
        week_range: str
    ) -> bool:
        """
        发送周报邮件

        Args:
            to: 收件人邮箱
            member_name: 成员姓名
            report_content: 周报内容
            week_range: 周期描述

        Returns:
            True if 发送成功, False otherwise

        Example:
            >>> sender.send_weekly_report(
            ...     "hlqiang@wooduan.com",
            ...     "黄良强",
            ...     "# 周报内容...",
            ...     "2026-03-02 ~ 2026-03-07"
            ... )
        """
        subject = f"【周报】{member_name} {week_range} 工作总结"

        # 构造完整的邮件内容
        full_content = f"""{report_content}

---
此邮件由周报自动化系统生成
如有疑问，请联系管理员
"""

        return self.send_email(to, subject, full_content)

    def send_team_weekly_to_admin(
        self,
        admin_email: str,
        report_content: str,
        week_range: str
    ) -> bool:
        """
        发送团队周报给管理员

        Args:
            admin_email: 管理员邮箱
            report_content: 团队周报内容
            week_range: 周期描述

        Returns:
            True if 发送成功, False otherwise

        Example:
            >>> sender.send_team_weekly_to_admin(
            ...     "admin@example.com",
            ...     "# 团队周报...",
            ...     "2026-W10"
            ... )
        """
        subject = f"【团队周报】{week_range} 工作汇总"

        full_content = f"""{report_content}

---
此邮件由周报自动化系统生成
"""

        return self.send_email(admin_email, subject, full_content)

    def validate_email(self, email: str) -> bool:
        """
        验证邮箱格式

        Args:
            email: 邮箱地址

        Returns:
            True if 格式正确, False otherwise

        Example:
            >>> sender.validate_email("user@example.com")
            True
            >>> sender.validate_email("invalid-email")
            False
        """
        import re

        # 简单的邮箱格式验证
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def format_html_email(
        self,
        title: str,
        content: str,
        style: str = "default"
    ) -> str:
        """
        格式化HTML邮件

        Args:
            title: 邮件标题
            content: 邮件内容（Markdown格式）
            style: 样式风格

        Returns:
            HTML格式的邮件内容

        Example:
            >>> html = sender.format_html_email(
            ...     "周报",
            ...     "# 标题\\n内容",
            ...     "default"
            ... )
        """
        """
        格式化HTML邮件

        Args:
            title: 邮件标题
            content: 邮件内容（Markdown格式）
            style: 样式风格

        Returns:
            HTML格式的邮件内容

        Example:
            >>> html = sender.format_html_email(
            ...     "周报",
            ...     "# 标题\\n内容",
            ...     "default"
            ... )
        """
        # 简单的Markdown转HTML（实际应使用markdown库）
        html_content = content.replace('\n', '<br>')

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 20px;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 5px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
            color: #888;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="content">
        {html_content}
    </div>
    <div class="footer">
        此邮件由周报自动化系统生成
    </div>
</body>
</html>"""

        return html
