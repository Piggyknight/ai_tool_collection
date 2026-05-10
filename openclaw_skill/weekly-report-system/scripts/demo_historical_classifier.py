#!/usr/bin/env python3
"""
历史周报批量分类演示脚本

演示如何使用historical_classifier模块对历史周报进行批量分类。
"""

import sys
import logging
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.category_parser import CategoryParser
from src.core.task_classifier import TaskClassifier
from src.modules.historical_classifier import HistoricalClassifier

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_single_report():
    """演示：处理单个周报"""
    print("\n" + "="*70)
    print("演示1：处理单个周报")
    print("="*70)
    
    # 配置路径
    config_path = Path.home() / "Documents/weekly-report-system/data/config/task_category.md"
    report_dir = Path.home() / "Documents/weekly-report-system/data/weekly/team"
    output_dir = report_dir
    
    # 1. 加载分类配置
    print(f"\n1. 加载分类配置: {config_path}")
    parser = CategoryParser(str(config_path))
    config = parser.load_config()
    print(f"   ✓ 成功加载 {len(config.categories)} 个分类")
    
    # 2. 创建分类器
    print(f"\n2. 创建任务分类器")
    classifier = TaskClassifier(config)
    print(f"   ✓ 分类器创建成功")
    
    # 3. 创建历史周报分类器
    print(f"\n3. 创建历史周报分类器")
    historical_classifier = HistoricalClassifier(
        classifier=classifier,
        report_dir=str(report_dir),
        output_dir=str(output_dir)
    )
    print(f"   ✓ 历史周报分类器创建成功")
    print(f"   输入目录: {report_dir}")
    print(f"   输出目录: {output_dir}")
    
    # 4. 处理单个周报
    week_id = "20260302"
    print(f"\n4. 处理周报: {week_id}")
    
    try:
        # 加载周报
        report = historical_classifier.load_weekly_report(week_id)
        print(f"   ✓ 成功加载周报")
        print(f"   - 周次: {report.week_id}")
        print(f"   - 年份: {report.year}, 周数: {report.week_number}")
        print(f"   - 日期: {report.start_date} ~ {report.end_date}")
        print(f"   - 任务数: {len(report.tasks)}")
        
        # 分类周报
        classified = historical_classifier.classify_report(report)
        print(f"\n   ✓ 分类完成")
        print(f"   - 总任务数: {classified.total_tasks}")
        print(f"   - 已分类: {classified.classified_tasks}")
        print(f"   - 分类准确率: {classified.classified_tasks / classified.total_tasks * 100:.1f}%")
        
        # 显示统计
        print(f"\n   分类统计:")
        for category_id, count in sorted(classified.statistics.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                percentage = count / classified.total_tasks * 100
                category_name = historical_classifier._get_category_display_name(category_id)
                print(f"   - {category_name}: {count} ({percentage:.1f}%)")
        
        # 保存分类周报
        output_path = historical_classifier.save_classified_report(classified)
        print(f"\n   ✓ 分类周报已保存: {output_path}")
        
    except FileNotFoundError as e:
        print(f"   ✗ 错误: {e}")
        return False
    
    return True


def demo_week_range():
    """演示：处理周次范围"""
    print("\n" + "="*70)
    print("演示2：处理周次范围")
    print("="*70)
    
    # 配置路径
    config_path = Path.home() / "Documents/weekly-report-system/data/config/task_category.md"
    report_dir = Path.home() / "Documents/weekly-report-system/data/weekly/team"
    
    # 创建分类器
    parser = CategoryParser(str(config_path))
    config = parser.load_config()
    classifier = TaskClassifier(config)
    
    historical_classifier = HistoricalClassifier(
        classifier=classifier,
        report_dir=str(report_dir)
    )
    
    # 处理周次范围
    start_week = "2026-W09"
    end_week = "2026-W10"
    print(f"\n处理周次范围: {start_week} ~ {end_week}")
    
    try:
        output_files = historical_classifier.process_week_range(start_week, end_week)
        print(f"\n✓ 处理完成，生成 {len(output_files)} 个分类周报:")
        for file in output_files:
            print(f"  - {file}")
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False
    
    return True


def demo_all_reports():
    """演示：处理所有周报"""
    print("\n" + "="*70)
    print("演示3：处理所有周报")
    print("="*70)
    
    # 配置路径
    config_path = Path.home() / "Documents/weekly-report-system/data/config/task_category.md"
    report_dir = Path.home() / "Documents/weekly-report-system/data/weekly/team"
    
    # 创建分类器
    parser = CategoryParser(str(config_path))
    config = parser.load_config()
    classifier = TaskClassifier(config)
    
    historical_classifier = HistoricalClassifier(
        classifier=classifier,
        report_dir=str(report_dir)
    )
    
    # 处理所有周报
    print(f"\n处理所有周报...")
    
    try:
        output_files = historical_classifier.process_all_reports()
        print(f"\n✓ 处理完成，生成 {len(output_files)} 个分类周报:")
        for file in output_files:
            print(f"  - {file}")
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False
    
    return True


def main():
    """主函数"""
    print("\n" + "#"*70)
    print("# 历史周报批量分类模块 - 功能演示")
    print("#"*70)
    
    # 演示1：处理单个周报
    success1 = demo_single_report()
    
    # 演示2：处理周次范围（可选）
    # success2 = demo_week_range()
    
    # 演示3：处理所有周报（可选）
    # success3 = demo_all_reports()
    
    print("\n" + "="*70)
    print("演示完成")
    print("="*70)
    
    # 显示生成的分类周报示例
    output_file = Path.home() / "Documents/weekly-report-system/data/weekly/team/team_20260302_classified.md"
    if output_file.exists():
        print(f"\n生成的分类周报示例 ({output_file.name}):")
        print("-"*70)
        content = output_file.read_text(encoding='utf-8')
        # 只显示前50行
        lines = content.split('\n')
        print('\n'.join(lines[:50]))
        if len(lines) > 50:
            total_lines = len(lines)
            print(f"\n... (共 {total_lines} 行)")
        print("-"*70)


if __name__ == "__main__":
    main()
