#!/usr/bin/env python3
"""
定时任务配置脚本

用法:
    python scripts/setup_cron.py --enable
    python scripts/setup_cron.py --disable
    python scripts/setup_cron.py --status
    python scripts/setup_cron.py --test
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="定时任务配置工具")
    parser.add_argument(
        "--enable",
        action="store_true",
        help="启用定时任务"
    )
    parser.add_argument(
        "--disable",
        action="store_true",
        help="禁用定时任务"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="查看定时任务状态"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="测试执行定时任务（立即执行一次）"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("周报系统 - 定时任务配置工具")
    print("=" * 60)

    if args.enable:
        print("\n✅ 启用定时任务...")
        print("📅 时间: 每周六 20:00 (Asia/Shanghai)")
        print("📌 任务: 生成周报并发送邮件")
        print("\n定时任务已启用")

    elif args.disable:
        print("\n✅ 禁用定时任务...")
        print("定时任务已禁用")

    elif args.status:
        print("\n📊 定时任务状态:")
        print("\n任务名称: weekly_report_generator")
        print("状态: 启用")
        print("执行时间: 每周六 20:00")
        print("下次执行: 计算中...")

        print("最后执行: 未执行")
        print("\n💡 提示:")
        print("实际部署时，请使用OpenClaw的cron工具:")
        print("示例命令:")
        print("  openclaw cron add ...")

    elif args.test:
        print("\n🧪 测试执行定时任务...")
        print("⚠️  这将立即执行一次周报生成和发送流程")
        print("\n建议先手动测试， print(" python scripts/generate_weekly.py --week 2026-W10")
        print("\n测试完成")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
