#!/usr/bin/env python3
"""
周报生成入口脚本

用法:
    python scripts/generate_weekly.py --week 2026-W10
    python scripts/generate_weekly.py --week 2026-W10 --send-email
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from src.modules.config_manager import ConfigManager
from src.modules.daily_collector import DailyCollector
from src.modules.weekly_generator import WeeklyGenerator
from src.core.llm_service import LLMService
from src.core.email_sender import EmailSender
from src.core.git_helper import GitHelper
from src.core.date_utils import get_week_range, format_date


def main():
    parser = argparse.ArgumentParser(description="周报生成工具")
    parser.add_argument(
        "--week",
        type=str,
        help="周标识（如2026-W10）或起始日期（如2026-03-02）"
    )
    parser.add_argument(
        "--send-email",
        action="store_true",
        help="发送周报邮件"
    )
    parser.add_argument(
        "--team-only",
        action="store_true",
        help="只生成团队周报"
    )
    parser.add_argument(
        "--members-only",
        action="store_true",
        help="只生成个人周报"
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="不使用LLM润色"
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="不提交到Git"
    )

    args = parser.parse_args()

    if not args.week:
        # 默认使用当前周
        week_start, _ = get_week_range(datetime.now())
        args.week = format_date(week_start, "YYYY-MM-DD")

    # 初始化组件
    data_dir = project_root / "data"
    config_dir = data_dir / "config"

    config = ConfigManager(str(config_dir))
    config.initialize_default_config()

    # 读取输出目录配置
    output_dir = config.load_system_config().get("output_dir")
    if output_dir:
        output_dir = Path(output_dir).expanduser()
    else:
        output_dir = data_dir

    git_helper = GitHelper(str(project_root))
    collector = DailyCollector(str(output_dir), git_helper)
    llm_service = LLMService() if not args.no_llm else None
    email_sender = EmailSender()
    weekly_gen = WeeklyGenerator(collector, llm_service, git_helper)

    print(f"📊 开始生成周报: {args.week}")

    # 生成团队周报
    if not args.members_only:
        print("\n生成团队周报...")
        team_report_path = weekly_gen.generate_team_weekly(args.week)
        print(f"✅ 团队周报已生成: {team_report_path}")

        # 发送团队周报邮件
        if args.send_email:
            admin_email = config.get_admin_email()
            if admin_email:
                with open(team_report_path, 'r', encoding='utf-8') as f:
                    team_content = f.read()

                week_range_desc = args.week
                success = email_sender.send_team_weekly_to_admin(
                    admin_email,
                    team_content,
                    week_range_desc
                )

                if success:
                    print(f"✅ 团队周报已发送到: {admin_email}")
                else:
                    print(f"❌ 团队周报发送失败")
            else:
                print("⚠️ 未配置管理员邮箱，跳过发送")

    # 生成个人周报
    if not args.team_only:
        print("\n生成个人周报...")
        member_report_paths = weekly_gen.generate_all_member_weekly(args.week)
        print(f"✅ 已生成 {len(member_report_paths)} 份个人周报")

        # 发送个人周报邮件
        if args.send_email:
            print("\n发送个人周报邮件...")
            result = weekly_gen.send_member_weekly_emails(member_report_paths, config)

            print(f"\n📊 发送统计:")
            print(f"  总计: {result['total']}")
            print(f"  成功: {result['success']}")
            print(f"  失败: {result['failed']}")

            if result['errors']:
                print(f"\n❌ 错误列表:")
                for error in result['errors']:
                    print(f"  - {error}")

    # Git提交
    if not args.no_git:
        print("\n提交到Git...")
        git_helper.commit(f"生成周报 {args.week}")
        print("✅ 已提交到Git")
    else:
        print("\n跳过Git提交")

    print(f"\n🎉 周报生成完成！")


if __name__ == "__main__":
    main()
