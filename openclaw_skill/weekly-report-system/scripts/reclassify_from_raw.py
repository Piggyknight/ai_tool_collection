#!/usr/bin/env python3
"""
从原始周报重新分类 v3

直接从 team_weekly_20260302.md 读取，利用成员职责进行智能分类

使用方法：
    python scripts/reclassify_from_raw.py --input data/weekly/team/team_weekly_20260302.md --output data/weekly/team/team_20260302_classified.md
"""

import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# 成员职责映射（详细版）
MEMBER_RESPONSIBILITIES = {
    "hwl": {
        "primary": "memory",
        "secondary": ["resource"],
        "keywords": ["mmap", "内存", "缓存", "压缩"],
        "description": "负责mmap相关，主要是内存相关任务"
    },
    "zsh": {
        "primary": "ci",
        "secondary": ["harmonyos"],
        "keywords": ["流水线", "蓝盾", "打包", "符号"],
        "description": "负责CI流水线、鸿蒙支持"
    },
    "yy": {
        "primary": "ci",
        "secondary": ["harmonyos"],
        "keywords": ["流水线", "蓝盾", "打包", "鸿蒙"],
        "description": "负责CI流水线、鸿蒙支持"
    },
    "alb": {
        "primary": "resource",
        "secondary": ["memory", "ci"],
        "keywords": ["热更新", "延迟加载", "表格", "hotfix"],
        "description": "负责热更新、延迟加载、表格生成"
    },
    "hlq": {
        "primary": "resource",
        "secondary": [],
        "keywords": ["打包", "分包", "引用计数", "assetbundle", "资源"],
        "description": "负责资源打包分包规则、引用计数"
    },
    "dcl": {
        "primary": "ci",
        "secondary": [],
        "keywords": ["svn", "hook", "guid", "rename"],
        "description": "负责svn hook相关任务"
    },
    "pgh": {
        "primary": "audio",
        "secondary": [],
        "keywords": ["音频", "audio", "wwise", "音效", "混响", "声音", "枪声", "载具系统音频", "辐射值"],
        "description": "负责音频，基本都是音频相关任务"
    },
    "krp": {
        "primary": "ci",
        "secondary": ["audio"],
        "keywords": ["asan", "hwasan", "crash", "符号"],
        "description": "负责asan相关、部分音频"
    },
    "djz": {
        "primary": "memory",
        "secondary": [],
        "keywords": ["修复", "内存", "泄漏", "texture"],
        "description": "主要负责修复问题，目前主要是内存相关"
    },
    "xzy": {
        "primary": "ci",
        "secondary": ["resource"],
        "keywords": ["shader", "下载", "打包", "psO"],
        "description": "负责shader打包、游戏内下载"
    }
}

# 分类定义
CATEGORIES = {
    "memory": {
        "name": "内存优化",
        "priority": 1,
        "keywords": ["内存", "mmap", "泄漏", "leak", "缓存池", "asan", "hwasan", "内存峰值", "oom"]
    },
    "resource": {
        "name": "资源系统",
        "priority": 1,
        "keywords": ["assetbundle", "ab包", "vfs", "资源加载", "资源卸载", "分包", "asset", "bundle", "mmap文件", "异步加载", "引用计数"]
    },
    "audio": {
        "name": "音频系统",
        "priority": 1,
        "keywords": ["音频", "audio", "wwise", "音效", "混响", "声音", "枪声", "环境音", "载具系统音频", "辐射值音效"]
    },
    "ci": {
        "name": "CI/构建系统",
        "priority": 2,
        "keywords": ["ci", "流水线", "蓝盾", "打包脚本", "构建", "符号服务器", "版本号", "symstore", "jenkins"]
    },
    "harmonyos": {
        "name": "鸿蒙平台",
        "priority": 2,
        "keywords": ["鸿蒙", "harmony", "harmonyos", "华为"]
    },
    "tools": {
        "name": "工具开发",
        "priority": 3,
        "keywords": ["工具", "tool", "查询", "editor", "可视化"]
    }
}

# 分类名称映射
CATEGORY_NAMES = {k: v["name"] for k, v in CATEGORIES.items()}
CATEGORY_NAMES["uncategorized"] = "未分类"

def extract_tasks_from_weekly(content: str) -> List[Tuple[str, Optional[str]]]:
    """
    从周报中提取任务列表
    
    Returns:
        [(task_content, member_id), ...]
    """
    tasks = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        # 匹配任务行
        if line.startswith('- ') and not line.startswith('- [ ]'):
            task = line[2:].strip()
            if task and not task.startswith('#'):  # 跳过标题
                tasks.append((task, None))
    
    return tasks

def extract_tasks_from_daily_reports(base_path: Path, week_dates: List[str]) -> List[Tuple[str, str]]:
    """
    从日报中提取任务（带成员信息）
    
    Args:
        base_path: 日报目录路径
        week_dates: 日期列表，如 ['20260302', '20260303', ...]
    
    Returns:
        [(task_content, member_id), ...]
    """
    tasks = []
    
    for date in week_dates:
        daily_file = base_path / f"soc_daily_{date}.md"
        if not daily_file.exists():
            continue
        
        content = daily_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        current_member = None
        in_today_section = False
        
        for i, line in enumerate(lines):
            # 检测成员标题
            member_match = re.match(r'^##\s+([A-Z]{2,3})', line)
            if member_match:
                current_member = member_match.group(1).lower()
                in_today_section = False
                continue
            
            # 检测"今日完成"部分
            if re.match(r'^###\s+今', line):
                in_today_section = True
                continue
            
            # 检测其他部分（停止收集）
            if re.match(r'^###\s+', line) and not re.match(r'^###\s+今', line):
                in_today_section = False
                continue
            
            # 收集任务
            if in_today_section and current_member and line.strip().startswith('- '):
                task = line.strip()[2:].strip()
                if task and not task.startswith('#'):
                    tasks.append((task, current_member))
    
    return tasks

def classify_task(task: str, member_id: Optional[str] = None) -> str:
    """
    分类单个任务
    
    优先级：
    1. 成员职责
    2. 明确关键词
    3. 分类优先级
    """
    task_lower = task.lower()
    
    # 1. 优先使用成员职责
    if member_id and member_id in MEMBER_RESPONSIBILITIES:
        member_info = MEMBER_RESPONSIBILITIES[member_id]
        primary = member_info["primary"]
        secondary = member_info.get("secondary", [])
        keywords = member_info.get("keywords", [])
        
        # 检查是否匹配成员关键词
        matched = any(kw.lower() in task_lower for kw in keywords)
        
        # PGH特殊处理：几乎所有任务都是音频
        if member_id == "pgh":
            # 除非明确是CI或工具类
            if not any(kw in task_lower for kw in ["流水线", "蓝盾", "svn", "git工具", "查询工具"]):
                return "audio"
        
        # HWL特殊处理：mmap相关主要是内存
        if member_id == "hwl":
            if "mmap" in task_lower or "内存" in task_lower:
                return "memory"
        
        # 如果匹配了关键词，使用主分类
        if matched:
            return primary
        
        # 默认返回主分类
        return primary
    
    # 2. 明确关键词匹配
    # 音频（最高优先级）
    audio_keywords = CATEGORIES["audio"]["keywords"]
    if any(kw in task_lower for kw in audio_keywords):
        return "audio"
    
    # 鸿蒙平台
    if "鸿蒙" in task:
        return "harmonyos"
    
    # CI/构建
    ci_keywords = ["流水线", "蓝盾", "符号服务器", "版本号", "symstore", "svn", "hook"]
    if any(kw in task_lower for kw in ci_keywords):
        return "ci"
    
    # 内存
    if "内存" in task and any(kw in task_lower for kw in ["优化", "泄漏", "峰值"]):
        return "memory"
    
    # 资源
    resource_keywords = ["mmap文件压缩", "资源压缩", "assetbundle", "分包规则", "引用计数"]
    if any(kw in task_lower for kw in resource_keywords):
        return "resource"
    
    # 工具
    if any(kw in task_lower for kw in ["工具", "查询工具", "editor工具"]):
        return "tools"
    
    # 3. 根据Redmine标签判断
    if "#10" in task:  # Redmine issue
        if any(tag in task_lower for tag in ["【音频", "音频特效", "wwise"]):
            return "audio"
        if "【建造" in task or "【领地" in task:
            return "ci"  # bug修复归到CI
    
    # 4. 未分类
    return "uncategorized"

def classify_tasks(tasks: List[Tuple[str, Optional[str]]]) -> Dict[str, List[str]]:
    """批量分类任务"""
    classified = defaultdict(list)
    
    for task, member_id in tasks:
        category = classify_task(task, member_id)
        classified[category].append(task)
    
    return dict(classified)

def generate_classified_report(classified: Dict[str, List[str]], week_id: str) -> str:
    """生成分类后的周报"""
    lines = []
    
    # 标题
    lines.append(f"# 团队周报 - {week_id}（智能分类版）")
    lines.append("")
    
    # 统计
    total = sum(len(tasks) for tasks in classified.values())
    
    lines.append("## 📊 分类统计")
    lines.append("")
    lines.append("| 分类 | 任务数 | 占比 |")
    lines.append("|------|--------|------|")
    
    # 排序
    sorted_cats = sorted(classified.items(), key=lambda x: len(x[1]), reverse=True)
    
    for cat_id, tasks in sorted_cats:
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        count = len(tasks)
        percentage = (count / total * 100) if total > 0 else 0
        lines.append(f"| {cat_name} | {count} | {percentage:.1f}% |")
    
    lines.append("")
    lines.append(f"**总计**: {total} 个任务")
    lines.append("")
    lines.append("**分类说明**: 基于团队成员职责和任务关键词进行智能分类")
    lines.append("")
    
    # 详细内容
    lines.append("## 📋 分类任务详情")
    lines.append("")
    
    for cat_id, tasks in sorted_cats:
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        lines.append(f"### {cat_name}")
        lines.append("")
        
        for task in tasks:
            lines.append(f"- {task}")
        
        lines.append("")
    
    # 页脚
    lines.append("---")
    lines.append("*此分类周报由智能分类系统生成（基于成员职责）*")
    
    return '\n'.join(lines)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='从原始周报重新分类')
    parser.add_argument('--input', required=True, help='原始周报文件')
    parser.add_argument('--output', required=True, help='输出文件')
    parser.add_argument('--use-daily', action='store_true', help='使用日报提取任务（带成员信息）')
    parser.add_argument('--dry-run', action='store_true', help='预览模式')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)
    
    print(f"📖 读取文件: {input_path}")
    
    if args.use_daily:
        # 从日报提取（带成员信息）
        print("🔍 从日报提取任务（带成员信息）...")
        base_path = input_path.parent.parent / "daily"
        week_dates = ['20260302', '20260303', '20260304', '20260305', '20260306']
        tasks = extract_tasks_from_daily_reports(base_path, week_dates)
    else:
        # 从周报提取（无成员信息）
        print("🔍 从周报提取任务...")
        content = input_path.read_text(encoding='utf-8')
        tasks = extract_tasks_from_weekly(content)
    
    print(f"✅ 提取到 {len(tasks)} 个任务")
    
    # 统计成员分布
    if args.use_daily:
        member_stats = defaultdict(int)
        for _, member_id in tasks:
            if member_id:
                member_stats[member_id] += 1
        
        print("\n👥 成员任务分布:")
        for member_id, count in sorted(member_stats.items(), key=lambda x: x[1], reverse=True):
            member_name = member_id.upper()
            print(f"  {member_name}: {count} 个任务")
    
    # 分类
    print("\n🏷️  开始分类...")
    classified = classify_tasks(tasks)
    
    # 显示统计
    print("\n📊 分类统计:")
    total = sum(len(tasks) for tasks in classified.values())
    for cat_id, tasks in sorted(classified.items(), key=lambda x: len(x[1]), reverse=True):
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        count = len(tasks)
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  {cat_name}: {count} ({percentage:.1f}%)")
    
    # 生成报告
    week_id = "20260302"
    print("\n📝 生成分类周报...")
    report = generate_classified_report(classified, week_id)
    
    if args.dry_run:
        print("\n" + "="*60)
        print("预览分类周报:")
        print("="*60)
        print(report[:2000] + "\n... (省略)")
    else:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding='utf-8')
        print(f"\n✅ 已保存分类周报: {output_path}")
    
    print("\n🎉 分类完成！")

if __name__ == "__main__":
    main()
