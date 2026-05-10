#!/usr/bin/env python3
"""
分类统计模块演示脚本

演示如何使用category_stats.py模块生成统计报告。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.category_parser import Category
from src.modules.category_stats import (
    CategoryStats,
    WeeklyStats,
    CategoryStatsGenerator
)


def main():
    """主函数"""
    print("=" * 70)
    print("分类统计模块演示")
    print("=" * 70)
    
    # 1. 创建分类列表
    categories = [
        Category(id="memory", name="内存相关", keywords=["内存", "mmap"], description="内存优化、内存问题修复"),
        Category(id="resource", name="资源相关", keywords=["资源", "asset"], description="资源加载、资源管理"),
        Category(id="harmonyos", name="鸿蒙支持", keywords=["鸿蒙", "harmony"], description="鸿蒙平台适配"),
        Category(id="ci", name="CI相关", keywords=["ci", "流水线"], description="CI流水线、自动化"),
        Category(id="audio", name="音频相关", keywords=["音频", "audio"], description="音频功能、音效"),
    ]
    
    print(f"\n✓ 创建了 {len(categories)} 个分类")
    
    # 2. 创建统计生成器
    generator = CategoryStatsGenerator(categories)
    print("✓ 初始化统计生成器")
    
    # 3. 准备模拟任务数据
    tasks = [
        {"content": "修复Android平台内存泄漏问题", "categories": ["memory"], "member": "张三"},
        {"content": "优化资源加载性能", "categories": ["resource"], "member": "张三"},
        {"content": "支持鸿蒙平台资源打包", "categories": ["harmonyos", "resource"], "member": "李四"},
        {"content": "修复CI流水线打包失败", "categories": ["ci"], "member": "李四"},
        {"content": "优化3D音效播放", "categories": ["audio"], "member": "王五"},
        {"content": "启用ASAN检测内存问题", "categories": ["memory"], "member": "张三"},
        {"content": "优化Asset Bundle分包", "categories": ["resource"], "member": "王五"},
        {"content": "鸿蒙平台音频适配", "categories": ["harmonyos", "audio"], "member": "李四"},
        {"content": "CI流水线增加自动化测试", "categories": ["ci"], "member": "赵六"},
        {"content": "内存池优化", "categories": ["memory"], "member": "张三"},
        {"content": "资源热更新支持", "categories": ["resource"], "member": "王五"},
        {"content": "音频压缩算法优化", "categories": ["audio"], "member": "赵六"},
        {"content": "未分类任务1", "categories": [], "member": "李四"},
        {"content": "未分类任务2", "categories": [], "member": "张三"},
    ]
    
    print(f"✓ 准备了 {len(tasks)} 个模拟任务\n")
    
    # 4. 计算分类统计
    print("-" * 70)
    print("📊 分类统计")
    print("-" * 70)
    
    stats = generator.calculate_stats(tasks)
    
    for s in stats:
        if s.task_count > 0:
            print(f"{s.category_name:12} | {s.task_count:3} 个任务 | {s.percentage:5.1f}%")
    
    # 5. 生成周统计
    weekly_stats = WeeklyStats(
        week_id="2026-W10",
        total_tasks=len(tasks),
        category_stats=stats
    )
    
    # 计算覆盖率
    classified_count = sum(s.task_count for s in stats if s.category_id != "uncategorized")
    coverage_rate = (classified_count / len(tasks) * 100) if tasks else 0
    weekly_stats.coverage_rate = coverage_rate
    
    print(f"\n覆盖率: {coverage_rate:.1f}%")
    print(f"总任务: {len(tasks)}")
    
    # 6. 生成成员统计
    print("\n" + "-" * 70)
    print("👥 成员统计")
    print("-" * 70)
    
    member_stats = generator.generate_member_stats(tasks)
    
    for ms in member_stats:
        print(f"\n{ms.member_name}:")
        print(f"  总任务数: {ms.total_tasks}")
        print(f"  主要分类: {ms.primary_category}")
        print(f"  分类分布: {ms.category_distribution}")
    
    # 7. 多周对比
    print("\n" + "-" * 70)
    print("📈 多周对比")
    print("-" * 70)
    
    # 模拟上周数据
    week1 = WeeklyStats(
        week_id="2026-W09",
        total_tasks=25,
        category_stats=[
            CategoryStats("memory", "内存相关", 8, 32.0, []),
            CategoryStats("resource", "资源相关", 6, 24.0, []),
            CategoryStats("harmonyos", "鸿蒙支持", 4, 16.0, []),
            CategoryStats("ci", "CI相关", 4, 16.0, []),
            CategoryStats("audio", "音频相关", 3, 12.0, []),
        ]
    )
    
    week2 = weekly_stats
    
    multi_week = generator.compare_weeks([week1, week2])
    
    print("\n分类趋势:")
    for cat_name, trends in multi_week.category_trends.items():
        if cat_name != "未分类":
            change = multi_week.trend_changes.get(cat_name, "-")
            print(f"  {cat_name:12} | W09: {trends[0]:2} → W10: {trends[1]:2} | {change}")
    
    # 8. 生成Markdown报告
    print("\n" + "-" * 70)
    print("📄 Markdown报告预览")
    print("-" * 70)
    
    md_report = generator.generate_markdown_report(
        weekly_stats,
        member_stats=member_stats,
        multi_week_stats=multi_week
    )
    
    # 只显示报告的前30行
    lines = md_report.split('\n')
    for line in lines[:30]:
        print(line)
    
    if len(lines) > 30:
        print(f"\n... (还有 {len(lines) - 30} 行)")
    
    # 9. 生成文本图表
    print("\n" + "-" * 70)
    print("📊 文本图表")
    print("-" * 70)
    
    text_chart = generator.generate_text_chart(weekly_stats)
    print(text_chart)
    
    # 10. 生成图表数据
    print("\n" + "-" * 70)
    print("📊 图表数据 (JSON格式)")
    print("-" * 70)
    
    chart_data = generator.generate_chart_data(weekly_stats, "pie")
    print(f"图表类型: {chart_data.chart_type}")
    print(f"标题: {chart_data.title}")
    print(f"标签: {chart_data.labels}")
    print(f"数值: {chart_data.values}")
    
    # 11. 导出示例
    print("\n" + "-" * 70)
    print("💾 导出报告")
    print("-" * 70)
    
    # 生成JSON报告
    json_report = generator.generate_json_report(
        weekly_stats,
        member_stats=member_stats,
        multi_week_stats=multi_week
    )
    
    print(f"✓ JSON报告生成完成 ({len(json_report)} 字节)")
    
    # 生成CSV报告
    csv_report = generator.generate_csv_report(weekly_stats)
    print(f"✓ CSV报告生成完成 ({len(csv_report)} 字节)")
    
    # 12. 保存到文件
    output_dir = Path(__file__).parent.parent / "output" / "stats"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存Markdown
    md_path = output_dir / "report_2026-W10.md"
    generator.save_report(md_report, str(md_path), "markdown")
    print(f"✓ Markdown报告已保存: {md_path}")
    
    # 保存JSON
    json_path = output_dir / "report_2026-W10.json"
    generator.save_report(json_report, str(json_path), "json")
    print(f"✓ JSON报告已保存: {json_path}")
    
    # 保存CSV
    csv_path = output_dir / "report_2026-W10.csv"
    generator.save_report(csv_report, str(csv_path), "csv")
    print(f"✓ CSV报告已保存: {csv_path}")
    
    print("\n" + "=" * 70)
    print("✅ 演示完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
