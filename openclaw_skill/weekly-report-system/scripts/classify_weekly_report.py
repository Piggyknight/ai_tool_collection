#!/usr/bin/env python3
"""
周报分类命令行工具

使用方法：
    python scripts/classify_weekly_report.py --week 2026-W10
    python scripts/classify_weekly_report.py --range 2026-W01 2026-W10
    python scripts/classify_weekly_report.py --all
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.category_parser import CategoryParser
from src.core.task_classifier import TaskClassifier, SimpleLLMClient, CacheManager
from src.modules.historical_classifier import HistoricalClassifier


def main():
    parser = argparse.ArgumentParser(description='周报分类工具')
    parser.add_argument('--week', type=str, help='指定周次，如 2026-W10')
    parser.add_argument('--range', nargs=2, metavar=('START', 'END'), 
                       help='指定周次范围，如 2026-W01 2026-W10')
    parser.add_argument('--all', action='store_true', help='处理所有周报')
    parser.add_argument('--report-dir', type=str, 
                       default='data/weekly/team',
                       help='周报目录（默认：data/weekly/team）')
    parser.add_argument('--config', type=str,
                       default='data/config/task_category.md',
                       help='分类配置文件（默认：data/config/task_category.md）')
    parser.add_argument('--use-llm', action='store_true',
                       help='使用LLM分类（默认使用关键词匹配）')
    
    args = parser.parse_args()
    
    # 初始化分类器
    print("📁 加载分类配置...")
    category_parser = CategoryParser(args.config)
    config = category_parser.load_config()
    
    # 选择分类方式
    if args.use_llm:
        print("🤖 使用LLM分类模式")
        llm_client = SimpleLLMClient()  # 可替换为实际LLM客户端
        cache_manager = CacheManager()
    else:
        print("🔍 使用关键词匹配模式（推荐）")
        llm_client = None
        cache_manager = None
    
    classifier = TaskClassifier(
        config=config,
        llm_client=llm_client,
        cache_manager=cache_manager
    )
    
    # 创建历史周报分类器
    historical_classifier = HistoricalClassifier(
        classifier=classifier,
        report_dir=args.report_dir
    )
    
    # 处理周报
    output_files = []
    
    if args.week:
        print(f"\n📊 处理周报: {args.week}")
        output_file = historical_classifier.process_single_week(args.week)
        output_files.append(output_file)
        
    elif args.range:
        start, end = args.range
        print(f"\n📊 处理周次范围: {start} 到 {end}")
        output_files = historical_classifier.process_week_range(start, end)
        
    elif args.all:
        print(f"\n📊 处理所有周报")
        output_files = historical_classifier.process_all_reports()
        
    else:
        parser.print_help()
        return
    
    # 输出结果
    if output_files:
        print(f"\n✅ 完成！生成 {len(output_files)} 个分类周报：")
        for file in output_files:
            print(f"   - {file}")
    else:
        print("\n⚠️  未找到可处理的周报文件")


if __name__ == '__main__':
    main()
