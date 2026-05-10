#!/usr/bin/env python3
"""
日报收集入口脚本

用法:
    python scripts/collect_daily.py --input report.md --date 2026-03-07
    python scripts/collect_daily.py --stdin --date 2026-03-07
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.daily_collector import DailyCollector
from src.modules.config_manager import ConfigManager
from src.core.git_helper import GitHelper


def main():
    parser = argparse.ArgumentParser(description="收集日报")
    parser.add_argument(
        "--input", "-i",
        help="日报文件路径（markdown格式）"
    )
    parser.add_argument(
        "--stdin", "-s",
        action="store_true",
        help="从标准输入读取日报"
    )
    parser.add_argument(
        "--date", "-d",
        help="日期（YYYY-MM-DD或YYYYMMDD格式）"
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="数据存储目录（默认：data）"
    )

    args = parser.parse_args()

    # 读取日报内容
    markdown_text = ""

    if args.stdin:
        # 从标准输入读取
        markdown_text = sys.stdin.read()
    elif args.input:
        # 从文件读取
        with open(args.input, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
    else:
        parser.print_help()
        sys.exit(1)

    # 初始化
    project_root = Path(__file__).parent.parent
    data_dir = project_root / args.data_dir

    config = ConfigManager(str(data_dir / "config"))
    config.initialize_default_config()

    # 读取输出目录配置
    output_dir = config.load_system_config().get("output_dir")
    if output_dir:
        output_dir = Path(output_dir).expanduser()
    else:
        output_dir = data_dir

    git_helper = GitHelper(str(project_root))
    collector = DailyCollector(str(output_dir), git_helper)

    # 收集日报
    result = collector.collect_from_markdown(markdown_text, args.date)

    if result["success"]:
        print(f"✅ 日报收集成功")
        print(f"📄 文件: {result['file_path']}")
        if "report" in result:
            stats = result["report"]
            if "members" in stats:
                print(f"👥 成员数: {len(stats['members'])}")
    else:
        print(f"❌ 日报收集失败")
        if "errors" in result:
            for error in result["errors"]:
                print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
