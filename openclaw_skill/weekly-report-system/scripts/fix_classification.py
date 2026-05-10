#!/usr/bin/env python3
"""
分类修复脚本
立即修复当前周报的分类重叠问题

使用方法：
    python scripts/fix_classification.py --input data/weekly/team/team_20260302_classified.md --output data/weekly/team/team_20260302_classified_fixed.md
"""

import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# 分类优先级（数字越小优先级越高）
CATEGORY_PRIORITY = {
    "memory": 1,      # 内存优化 - 高优先级
    "resource": 1,    # 资源系统 - 高优先级
    "ci": 2,          # CI/构建 - 中优先级
    "harmonyos": 2,   # 鸿蒙平台 - 中优先级
    "audio": 2,       # 音频系统 - 中优先级
    "tools": 3,       # 工具开发 - 低优先级
    "uncategorized": 0  # 未分类 - 兜底
}

# 分类名称映射
CATEGORY_NAMES = {
    "memory": "内存优化",
    "resource": "资源系统",
    "ci": "CI/构建系统",
    "harmonyos": "鸿蒙平台",
    "audio": "音频系统",
    "tools": "工具开发",
    "uncategorized": "未分类"
}

def parse_classified_report(content: str) -> Tuple[Dict[str, List[str]], Dict]:
    """
    解析分类周报
    
    Returns:
        (分类任务字典, 统计信息)
    """
    categories = defaultdict(list)
    stats = {}
    
    lines = content.split('\n')
    current_category = None
    
    for line in lines:
        # 解析分类标题
        if line.startswith('### '):
            cat_name = line[4:].strip()
            # 提取分类ID（中文名称 -> ID）
            current_category = None
            for cat_id, name in CATEGORY_NAMES.items():
                if name in cat_name or cat_name in name:
                    current_category = cat_id
                    break
            
            if not current_category:
                # 尝试从英文匹配
                for cat_id in CATEGORY_PRIORITY.keys():
                    if cat_id in cat_name.lower():
                        current_category = cat_id
                        break
        
        # 解析任务
        elif line.startswith('- ') and current_category:
            task = line[2:].strip()
            # 移除标记
            task = re.sub(r' _\[.*?\]_$', '', task)
            categories[current_category].append(task)
    
    return categories, stats

def select_primary_category(task: str, matched_categories: List[str]) -> str:
    """
    为任务选择主分类
    
    规则：
    1. 按优先级排序
    2. 基于任务核心内容判断
    """
    if not matched_categories:
        return "uncategorized"
    
    # 任务内容分析（基于核心目标）
    task_lower = task.lower()
    
    # 特殊规则：明确的核心目标优先
    if "mmap文件压缩" in task or "资源压缩" in task:
        return "resource"
    
    if "鸿蒙" in task and ("打包" in task or "引擎" in task or "适配" in task):
        return "harmonyos"
    
    if "音频" in task or "wwise" in task or "音效" in task:
        return "audio"
    
    if "流水线" in task or "蓝盾" in task or "符号服务器" in task:
        return "ci"
    
    if "内存" in task and ("优化" in task or "泄漏" in task or "峰值" in task):
        return "memory"
    
    if "打包" in task and "内存" in task:
        return "memory"
    
    if "工具" in task or "查询" in task:
        return "tools"
    
    # 默认：按优先级选择
    sorted_cats = sorted(matched_categories, key=lambda x: CATEGORY_PRIORITY.get(x, 2))
    return sorted_cats[0]

def fix_classification(categories: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    修复分类重叠问题
    
    策略：
    1. 收集所有任务
    2. 去重
    3. 为每个任务选择主分类
    4. 重新组织
    """
    # 1. 收集所有任务及其出现的分类
    task_categories = defaultdict(list)
    
    for cat_id, tasks in categories.items():
        for task in tasks:
            task_categories[task].append(cat_id)
    
    # 2. 为每个任务选择主分类
    fixed_categories = defaultdict(list)
    
    for task, matched_cats in task_categories.items():
        primary_cat = select_primary_category(task, matched_cats)
        fixed_categories[primary_cat].append(task)
    
    # 3. 移除空分类
    fixed_categories = {
        cat_id: tasks 
        for cat_id, tasks in fixed_categories.items() 
        if tasks
    }
    
    return fixed_categories

def generate_fixed_report(
    categories: Dict[str, List[str]], 
    original_stats: Dict
) -> str:
    """
    生成修复后的周报
    """
    lines = []
    
    # 标题
    lines.append("# 团队周报 - 20260302（分类修复版）")
    lines.append("")
    
    # 统计信息
    total_tasks = sum(len(tasks) for tasks in categories.values())
    
    lines.append("## 📊 分类统计（修复后）")
    lines.append("")
    lines.append("| 分类 | 任务数 | 占比 |")
    lines.append("|------|--------|------|")
    
    # 按任务数排序
    sorted_categories = sorted(
        categories.items(), 
        key=lambda x: len(x[1]), 
        reverse=True
    )
    
    for cat_id, tasks in sorted_categories:
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        count = len(tasks)
        percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
        lines.append(f"| {cat_name} | {count} | {percentage:.1f}% |")
    
    lines.append("")
    lines.append(f"**总计**: {total_tasks} 个任务")
    lines.append("")
    
    # 详细内容
    lines.append("## 📋 分类任务详情")
    lines.append("")
    
    for cat_id, tasks in sorted_categories:
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        lines.append(f"### {cat_name}")
        lines.append("")
        
        for task in tasks:
            lines.append(f"- {task} _[fixed]_")
        
        lines.append("")
    
    # 页脚
    lines.append("---")
    lines.append("*此分类周报由自动化系统生成（修复版）*")
    
    return '\n'.join(lines)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='修复周报分类重叠问题')
    parser.add_argument('--input', required=True, help='输入文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不保存')
    
    args = parser.parse_args()
    
    # 读取文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)
    
    print(f"📖 读取文件: {input_path}")
    content = input_path.read_text(encoding='utf-8')
    
    # 解析
    print("🔍 解析分类周报...")
    categories, stats = parse_classified_report(content)
    
    # 显示原始统计
    print("\n📊 原始分类统计:")
    total_original = sum(len(tasks) for tasks in categories.values())
    for cat_id, tasks in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        count = len(tasks)
        percentage = (count / total_original * 100) if total_original > 0 else 0
        print(f"  {cat_name}: {count} ({percentage:.1f}%)")
    print(f"  总计: {total_original} 个任务（含重复）")
    print(f"  ⚠️  分类总数超过100%，存在重复归类")
    
    # 修复
    print("\n🔧 修复分类重叠...")
    fixed_categories = fix_classification(categories)
    
    # 显示修复后统计
    print("\n✅ 修复后统计:")
    total_fixed = sum(len(tasks) for tasks in fixed_categories.values())
    for cat_id, tasks in sorted(fixed_categories.items(), key=lambda x: len(x[1]), reverse=True):
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        count = len(tasks)
        percentage = (count / total_fixed * 100) if total_fixed > 0 else 0
        print(f"  {cat_name}: {count} ({percentage:.1f}%)")
    print(f"  总计: {total_fixed} 个任务（去重后）")
    print(f"  ✅ 分类总数 = 100%")
    
    # 生成报告
    print("\n📝 生成修复后周报...")
    report = generate_fixed_report(fixed_categories, stats)
    
    if args.dry_run:
        print("\n" + "="*60)
        print("预览修复后周报:")
        print("="*60)
        print(report[:1000] + "\n... (省略)")
    else:
        # 保存
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding='utf-8')
        print(f"\n✅ 已保存修复后周报: {output_path}")
    
    print("\n🎉 修复完成！")

if __name__ == "__main__":
    main()
