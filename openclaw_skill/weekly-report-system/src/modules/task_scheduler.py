"""
定时任务调度模块

配置和管理定时任务
"""

import logging
import json
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TaskScheduler:
    """定时任务调度器"""

    def __init__(
        self,
        weekly_gen,  # WeeklyGenerator
        email_sender,  # EmailSender
        config  # ConfigManager
    ):
        """
        初始化任务调度器

        Args:
            weekly_gen: 周报生成器
            email_sender: 邮件发送器
            config: 配置管理器
        """
        self.weekly_gen = weekly_gen
        self.email_sender = email_sender
        self.config = config

        logger.info("定时任务调度器初始化完成")

    def setup_weekly_task(self, schedule: str = "0 20 * * 6") -> bool:
        """
        配置每周六20点的周报任务

        Args:
            schedule: cron表达式，默认每周六20:00

        Returns:
            True if 成功, False otherwise

        Note:
            实际实现应该调用OpenClaw的Cron API
        """
        try:
            # 获取配置
            cron_config = self.config.get_cron_config()
            timezone = cron_config.get("timezone", "Asia/Shanghai")

            logger.info(f"配置定时任务: {schedule} ({timezone})")

            # 模拟cron配置
            # 实际应该调用:
            # from cron import cron
            # cron.add(job_spec)

            logger.info(f"定时任务配置成功: {schedule}")
            return True

        except Exception as e:
            logger.error(f"配置定时任务失败: {e}")
            return False

    def execute_weekly_generation(self) -> Dict:
        """
        执行周报生成任务

        Returns:
            执行结果
        """
        from ..core.date_utils import get_week_range, format_date
        from datetime import datetime

        logger.info("开始执行周报生成任务")

        result = {
            "success": True,
            "team_report": None,
            "member_reports": [],
            "errors": []
        }

        try:
            # 获取本周范围
            week_start, week_end = get_week_range()
            week_start_str = format_date(week_start, "YYYYMMDD")

            # 生成团队周报
            logger.info(f"生成团队周报: {week_start_str}")
            team_report_path = self.weekly_gen.generate_team_weekly(
                week_start_str,
                use_llm=True
            )
            result["team_report"] = str(team_report_path)

            # 生成所有成员周报
            logger.info("生成个人周报")
            member_report_paths = self.weekly_gen.generate_all_member_weekly(
                week_start_str,
                use_llm=True
            )
            result["member_reports"] = [str(p) for p in member_report_paths]

            logger.info("周报生成任务完成")

        except Exception as e:
            logger.error(f"周报生成任务失败: {e}")
            result["success"] = False
            result["errors"].append(str(e))

        return result

    def send_team_weekly_to_admin(self, weekly_file: str) -> bool:
        """
        发送团队周报给管理员

        Args:
            weekly_file: 周报文件路径

        Returns:
            True if 成功
        """
        try:
            # 读取周报内容
            with open(weekly_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 获取管理员邮箱
            admin_email = self.config.get_admin_email()
            if not admin_email:
                logger.error("未配置管理员邮箱")
                return False

            # 提取周期信息
            from ..core.date_utils import get_week_range, format_date
            week_start, _ = get_week_range()
            week_range = format_date(week_start, "WYYYY")

            # 发送邮件
            success = self.email_sender.send_team_weekly_to_admin(
                admin_email,
                content,
                week_range
            )

            if success:
                logger.info(f"团队周报已发送给管理员: {admin_email}")
            else:
                logger.error("团队周报发送失败")

            return success

        except Exception as e:
            logger.error(f"发送团队周报失败: {e}")
            return False

    def send_member_weekly_emails(self, weekly_files: list) -> Dict:
        """
        发送个人周报邮件给成员

        Args:
            weekly_files: 周报文件路径列表

        Returns:
            发送结果统计
        """
        result = {
            "total": len(weekly_files),
            "success": 0,
            "failed": 0,
            "errors": []
        }

        for file_path in weekly_files:
            try:
                # 从文件名提取成员ID
                # 文件名格式: soc_weekly_YYYYMMDD_YYYYMMDD_HLQ.md
                import re
                match = re.search(r'_(\w+)\.md$', file_path)
                if not match:
                    logger.warning(f"无法从文件名提取成员ID: {file_path}")
                    result["failed"] += 1
                    continue

                member_id = match.group(1)

                # 获取成员邮箱
                email = self.config.get_member_email(member_id)
                if not email:
                    logger.warning(f"成员 {member_id} 未配置邮箱")
                    result["failed"] += 1
                    result["errors"].append(f"{member_id}: 缺少邮箱")
                    continue

                # 读取周报内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 获取成员姓名
                member_name = self.config.get_member_info(member_id).get("name", member_id)

                # 提取周期信息
                from ..core.date_utils import get_week_range, format_date, get_date_range_description
                week_start, week_end = get_week_range()
                week_range = get_date_range_description(week_start, week_end)

                # 发送邮件
                success = self.email_sender.send_weekly_report(
                    email,
                    member_name,
                    content,
                    week_range
                )

                if success:
                    result["success"] += 1
                    logger.info(f"周报已发送给 {member_name} ({email})")
                else:
                    result["failed"] += 1
                    result["errors"].append(f"{member_id}: 发送失败")

            except Exception as e:
                logger.error(f"发送周报失败 {file_path}: {e}")
                result["failed"] += 1
                result["errors"].append(f"{file_path}: {str(e)}")

        logger.info(
            f"批量发送完成: 总计 {result['total']}, "
            f"成功 {result['success']}, "
            f"失败 {result['failed']}"
        )

        return result

    def run_full_weekly_workflow(self) -> Dict:
        """
        运行完整的周报工作流

        1. 生成团队周报和个人周报
        2. 发送团队周报给管理员
        3. 发送个人周报给成员

        Returns:
            执行结果
        """
        logger.info("开始执行完整周报工作流")

        result = {
            "generation": None,
            "team_email": False,
            "member_emails": None
        }

        # 1. 生成周报
        gen_result = self.execute_weekly_generation()
        result["generation"] = gen_result

        if not gen_result["success"]:
            logger.error("周报生成失败，停止后续操作")
            return result

        # 2. 发送团队周报
        if gen_result["team_report"]:
            result["team_email"] = self.send_team_weekly_to_admin(
                gen_result["team_report"]
            )

        # 3. 发送个人周报
        if gen_result["member_reports"]:
            result["member_emails"] = self.send_member_weekly_emails(
                gen_result["member_reports"]
            )

        logger.info("完整周报工作流执行完成")

        return result

    def get_task_status(self) -> Dict:
        """
        获取定时任务状态

        Returns:
            任务状态信息
        """
        # 模拟返回任务状态
        # 实际应该查询OpenClaw Cron
        return {
            "weekly_task": {
                "enabled": True,
                "schedule": "0 20 * * 6",
                "timezone": "Asia/Shanghai",
                "last_run": None,
                "next_run": None
            }
        }
