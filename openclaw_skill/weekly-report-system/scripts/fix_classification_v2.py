#!/usr/bin/env python3
"""
分类修复脚本 v2 - 基于成员职责的智能分类

改进：
1. 利用成员职责信息辅助分类
2. 优先根据成员职责判断任务分类
3. 保留音频等容易误分类的任务

使用方法：
    python scripts/fix_classification_v2.py --input data/weekly/team/team_20260302_classified.md --output data/weekly/team/team_20260302_classified.md
"""

import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# 成员职责映射
MEMBER_RESPONSIBILITIES = {
    "hwl": {
        "primary": "memory",      # 主要是内存相关
        "secondary": ["resource"], # 次要：资源
        "keywords": ["mmap", "内存", "缓存"]
    },
    "zsh": {
        "primary": "ci",          # 主要是CI相关
        "secondary": ["harmonyos"], # 次要：鸿蒙
        "keywords": ["流水线", "蓝盾", "打包"]
    },
    "yy": {
        "primary": "ci",          # 主要是CI相关
        "secondary": ["harmonyos"], # 次要：鸿蒙
        "keywords": ["流水线", "蓝盾", "打包"]
    },
    "alb": {
        "primary": "resource",    # 主要是资源相关
        "secondary": ["memory", "ci"], # 次要：内存、CI
        "keywords": ["热更新", "延迟加载", "表格生成"]
    },
    "hlq": {
        "primary": "resource",    # 主要是资源相关
        "secondary": [],          # 资源打包、引用计数
        "keywords": ["打包", "分包", "引用计数", "assetbundle"]
    },
    "dcl": {
        "primary": "ci",          # 主要是CI相关
        "secondary": [],          # svn hook
        "keywords": ["svn", "hook", "guid"]
    },
    "pgh": {
        "primary": "audio",       # 主要是音频相关
        "secondary": [],          # 基本都是音频
        "keywords": ["音频", "audio", "wwise", "音效", "混响", "声音"]
    },
    "krp": {
        "primary": "ci",          # 主要是CI相关
        "secondary": ["audio"],   # 次要：音频
        "keywords": ["asan", "hwasan", "crash"]
    },
    "djz": {
        "primary": "memory",      # 主要是内存相关
        "secondary": [],          # 修复问题
        "keywords": ["修复", "内存", "泄漏"]
    },
    "xzy": {
        "primary": "ci",          # 主要是CI相关
        "secondary": ["resource"], # 次要：资源
        "keywords": ["shader", "下载", "打包"]
    }
}

# 分类优先级
CATEGORY_PRIORITY = {
    "audio": 1,       # 音频 - 高优先级（避免被CI误分类）
    "memory": 1,      # 内存 - 高优先级
    "resource": 1,    # 资源 - 高优先级
    "ci": 2,          # CI - 中优先级
    "harmonyos": 2,   # 鸿蒙 - 中优先级
    "tools": 3,       # 工具 - 低优先级
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

def extract_member_from_task(task: str) -> str:
    """从任务中提取成员ID"""
    # 尝试多种格式
    patterns = [
        r'([a-z]{2,3})\s*[:：]',           # hwl: 任务
        r'\((\w{2,3})\)',                  # (hwl)
        r'[-—]\s*(\w{2,3})\s*[-—]',        # - hwl -
        r'^([a-z]{2,3})\s+',               # hwl 任务
    ]
    
    for pattern in patterns:
        match = re.search(pattern, task, re.IGNORECASE)
        if match:
            member_id = match.group(1).lower()
            if member_id in MEMBER_RESPONSIBILITIES:
                return member_id
    
    return None

def classify_by_member_priority(task: str, member_id: str = None) -> str:
    """根据成员职责优先分类"""
    
    # 如果能提取到成员信息
    if member_id and member_id in MEMBER_RESPONSIBILITIES:
        member_info = MEMBER_RESPONSIBILITIES[member_id]
        primary = member_info["primary"]
        secondary = member_info.get("secondary", [])
        keywords = member_info.get("keywords", [])
        
        # 检查是否匹配成员的关键词
        task_lower = task.lower()
        matched_keywords = [kw for kw in keywords if kw.lower() in task_lower]
        
        # 如果匹配了关键词，优先使用主分类
        if matched_keywords:
            return primary
        
        # 如果任务明确提到次分类的关键领域
        if primary == "audio":
            # pgh的任务默认归到音频（除非明确是其他）
            if not any(kw in task_lower for kw in ["流水线", "蓝盾", "svn", "git", "工具"]):
                return "audio"
        
        if primary == "memory":
            # hwl/djz的任务默认归到内存
            if not any(kw in task_lower for kw in ["音频", "wwise", "音效"]):
                return "memory"
        
        # 默认返回主分类
        return primary
    
    return None

def select_primary_category_v2(
    task: str, 
    matched_categories: List[str],
    member_id: str = None
) -> str:
    """
    为任务选择主分类 v2
    
    优先级：
    1. 成员职责
    2. 明确的关键词
    3. 分类优先级
    """
    if not matched_categories:
        return "uncategorized"
    
    task_lower = task.lower()
    
    # 1. 优先使用成员职责判断
    member_category = classify_by_member_priority(task, member_id)
    if member_category:
        return member_category
    
    # 2. 特殊规则：明确的核心目标优先
    
    # 音频相关（优先级最高，避免被CI误分类）
    if any(kw in task_lower for kw in ["音频", "wwise", "音效", "混响", "声音播放", "枪声", "环境音"]):
        return "audio"
    
    # 鸿蒙平台特定任务
    if "鸿蒙" in task and any(kw in task_lower for kw in ["打包", "引擎", "适配", "apk"]):
        return "harmonyos"
    
    # CI流水线相关
    if any(kw in task_lower for kw in ["流水线", "蓝盾", "符号服务器", "版本号", "symstore"]):
        return "ci"
    
    # 内存优化
    if "内存" in task and any(kw in task_lower for kw in ["优化", "泄漏", "峰值", "asan", "hwasan"]):
        return "memory"
    
    # 资源系统
    if any(kw in task_lower for kw in ["mmap文件压缩", "资源压缩", "assetbundle", "分包规则"]):
        return "resource"
    
    # svn hook
    if "svn" in task_lower or "hook" in task_lower:
        return "ci"
    
    # 工具开发
    if any(kw in task_lower for kw in ["工具", "查询工具", "editor", "可视化"]):
        return "tools"
    
    # 3. 默认：按分类优先级选择
    sorted_cats = sorted(matched_categories, key=lambda x: CATEGORY_PRIORITY.get(x, 2))
    return sorted_cats[0]

def parse_classified_report_v2(content: str) -> Tuple[Dict[str, List[Tuple[str, str]]], Dict]:
    """
    解析分类周报 v2
    
    Returns:
        (分类任务字典[task, member_id], 统计信息)
    """
    categories = defaultdict(list)
    stats = {}
    
    lines = content.split('\n')
    current_category = None
    
    for line in lines:
        # 解析分类标题
        if line.startswith('### '):
            cat_name = line[4:].strip()
            # 提取分类ID
            current_category = None
            for cat_id, name in CATEGORY_NAMES.items():
                if name in cat_name or cat_name in name:
                    current_category = cat_id
                    break
            
            if not current_category:
                for cat_id in CATEGORY_PRIORITY.keys():
                    if cat_id in cat_name.lower():
                        current_category = cat_id
                        break
        
        # 解析任务
        elif line.startswith('- ') and current_category:
            task = line[2:].strip()
            # 移除标记
            task = re.sub(r' _\[.*?\]_$', '', task)
            
            # 提取成员信息
            member_id = extract_member_from_task(task)
            
            categories[current_category].append((task, member_id))
    
    return categories, stats

def fix_classification_v2(categories: Dict[str, List[Tuple[str, str]]]) -> Dict[str, List[str]]:
    """
    修复分类重叠问题 v2 - 利用成员职责
    """
    # 1. 收集所有任务及其出现的分类和成员
    task_info = defaultdict(lambda: {"categories": [], "member_id": None})
    
    for cat_id, tasks in categories.items():
        for task, member_id in tasks:
            task_info[task]["categories"].append(cat_id)
            if member_id and not task_info[task]["member_id"]:
                task_info[task]["member_id"] = member_id
    
    # 2. 为每个任务选择主分类
    fixed_categories = defaultdict(list)
    
    for task, info in task_info.items():
        matched_cats = info["categories"]
        member_id = info["member_id"]
        
        primary_cat = select_primary_category_v2(task, matched_cats, member_id)
        fixed_categories[primary_cat].append(task)
    
    # 3. 移除空分类
    fixed_categories = {
        cat_id: tasks 
        for cat_id, tasks in fixed_categories.items() 
        if tasks
    }
    
    return fixed_categories

def generate_fixed_report_v2(
    categories: Dict[str, List[str]], 
    original_stats: Dict
) -> str:
    """生成修复后的周报 v2"""
    lines = []
    
    # 标题
    lines.append("# 团队周报 - 20260302（分类修复版 v2）")
    lines.append("")
    
    # 统计信息
    total_tasks = sum(len(tasks) for tasks in categories.values())
    
    lines.append("## 📊 分类统计（修复后 v2）")
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
    lines.append("**改进说明**: 基于团队成员职责进行智能分类，优先保护音频等易误分类任务")
    lines.append("")
    
    # 详细内容
    lines.append("## 📋 分类任务详情")
    lines.append("")
    
    for cat_id, tasks in sorted_categories:
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        lines.append(f"### {cat_name}")
        lines.append("")
        
        for task in tasks:
            lines.append(f"- {task} _[fixed-v2]_")
        
        lines.append("")
    
    # 页脚
    lines.append("---")
    lines.append("*此分类周报由自动化系统生成（修复版 v2 - 基于成员职责）*")
    
    return '\n'.join(lines)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='修复周报分类重叠问题 v2 - 基于成员职责')
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
    categories, stats = parse_classified_report_v2(content)
    
    # 显示原始统计
    print("\n📊 原始分类统计:")
    total_original = sum(len(tasks) for tasks in categories.values())
    for cat_id, tasks in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        count = len(tasks)
        percentage = (count / total_original * 100) if total_original > 0 else 0
        print(f"  {cat_name}: {count} ({percentage:.1f}%)")
    print(f"  总计: {total_original} 个任务（含重复）")
    
    # 修复
    print("\n🔧 修复分类重叠（v2 - 基于成员职责）...")
    fixed_categories = fix_classification_v2(categories)
    
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
    
    # 显示关键改进
    print("\n📈 关键改进:")
    for cat_id in ["audio", "memory", "ci", "resource"]:
        before = sum(len(tasks) for cat, tasks in categories.items() if cat == cat_id)
        after = len(fixed_categories.get(cat_id, []))
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        if before != after:
            print(f"  {cat_name}: {before} → {after} ({after - before:+d})")
    
    # 生成报告
    print("\n📝 生成修复后周报...")
    report = generate_fixed_report_v2(fixed_categories, stats)
    
    if args.dry_run:
        print("\n" + "="*60)
        print("预览修复后周报:")
        print("="*60)
        print(report[:1500] + "\n... (省略)")
    else:
        # 保存
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding='utf-8')
        print(f"\n✅ 已保存修复后周报: {output_path}")
    
    print("\n🎉 修复完成！")

if __name__ == "__main__":
    main()
