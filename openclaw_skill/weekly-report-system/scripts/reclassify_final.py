#!/usr/bin/env python3
"""
最终版本 - 从日报重新分类
"""

from pathlib import Path
import re
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# 成员职责映射
MEMBER_RESPONSIBILITIES = {
    "hwl": {"primary": "memory", "secondary": ["resource"]},
    "zsh": {"primary": "ci", "secondary": ["harmonyos"]},
    "yy": {"primary": "ci", "secondary": ["harmonyos"]},
    "alb": {"primary": "resource", "secondary": ["memory", "ci"]},
    "hlq": {"primary": "resource", "secondary": []},
    "dcl": {"primary": "ci", "secondary": []},
    "pgh": {"primary": "audio", "secondary": []},  # 主要负责音频
    "krp": {"primary": "ci", "secondary": ["audio"]},
    "djz": {"primary": "memory", "secondary": []},
    "xzy": {"primary": "ci", "secondary": ["resource"]}
}

# 分类关键词
CATEGORY_KEYWORDS = {
    "memory": ["内存", "mmap", "泄漏", "leak", "缓存池", "asan", "hwasan", "内存峰值", "oom"],
    "resource": ["assetbundle", "ab包", "vfs", "资源加载", "资源卸载", "分包", "引用计数", "hotfix"],
    "audio": ["音频", "audio", "wwise", "音效", "混响", "声音", "枪声", "环境音", "载具系统音频", "辐射值音效"],
    "ci": ["流水线", "蓝盾", "符号服务器", "版本号", "symstore", "svn", "hook", "jenkins"],
    "harmonyos": ["鸿蒙", "harmony"],
    "tools": ["工具", "tool", "查询", "editor", "可视化"]
}

CATEGORY_NAMES = {
    "memory": "内存优化",
    "resource": "资源系统",
    "audio": "音频系统",
    "ci": "CI/构建系统",
    "harmonyos": "鸿蒙平台",
    "tools": "工具开发",
    "uncategorized": "未分类"
}

def extract_tasks_from_daily(base_path: Path, week_dates: List[str]) -> List[Tuple[str, str]]:
    """从日报提取任务"""
    tasks = []
    seen_tasks = set()  # 用于去重
    
    for date in week_dates:
        daily_file = base_path / f"soc_daily_{date}.md"
        if not daily_file.exists():
            continue
        
        content = daily_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        current_member = None
        in_today_section = False
        
        for line in lines:
            member_match = re.match(r'^##\s+([A-Z]{2,3})', line)
            if member_match:
                current_member = member_match.group(1).lower()
                in_today_section = False
                continue
            
            if re.match(r'^###\s+今\s*$', line):
                in_today_section = True
                continue
            
            if re.match(r'^###\s+', line) and not re.match(r'^###\s+今\s*$', line):
                in_today_section = False
                continue
            
            if in_today_section and current_member and line.strip().startswith('- '):
                task = line.strip()[2:].strip()
                if task and not task.startswith('#') and task not in seen_tasks:
                    tasks.append((task, current_member))
                    seen_tasks.add(task)
    
    return tasks

def classify_task(task: str, member_id: str) -> str:
    """分类单个任务"""
    task_lower = task.lower()
    
    # 1. 优先使用成员职责
    if member_id in MEMBER_RESPONSIBILITIES:
        member_info = MEMBER_RESPONSIBILITIES[member_id]
        primary = member_info["primary"]
        
        # PGH特殊处理：几乎所有任务都是音频
        if member_id == "pgh":
            # 除非明确是CI或工具类
            if not any(kw in task_lower for kw in ["流水线", "蓝鉴", "svn工具", "git工具", "查询工具"]):
                return "audio"
        
        # HWL特殊处理：mmap相关主要是内存
        if member_id == "hwl":
            if "mmap" in task_lower or "内存" in task_lower:
                return "memory"
        
        # 默认返回主分类
        return primary
    
    # 2. 关键词匹配
    for cat_id, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in task_lower for kw in keywords):
            return cat_id
    
    # 3. 根据Redmine标签判断
    if "#10" in task:  # Redmine issue
        if any(tag in task for tag in ["【音频", "音频特效"]):
            return "audio"
    
    # 4. 未分类
    return "uncategorized"

def main():
    # 提取任务
    base_path = Path('data/daily')
    week_dates = ['20260302', '20260303', '20260304', '20260305', '20260306']
    
    print('🔍 从日报提取任务...')
    tasks = extract_tasks_from_daily(base_path, week_dates)
    print(f'✅ 提取到 {len(tasks)} 个唯一任务\n')
    
    # 分类
    print('🏷️  开始分类...')
    classified = defaultdict(list)
    
    for task, member_id in tasks:
        category = classify_task(task, member_id)
        classified[category].append((task, member_id))
    
    # 统计
    print('\n📊 分类统计:')
    total = sum(len(tasks) for tasks in classified.values())
    
    for cat_id in sorted(classified.keys(), key=lambda x: len(classified[x]), reverse=True):
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        count = len(classified[cat_id])
        percentage = (count / total * 100) if total > 0 else 0
        print(f'  {cat_name}: {count} ({percentage:.1f}%)')
    
    # 显示音频任务详情
    print('\n🎵 音频系统任务详情:')
    if "audio" in classified:
        for i, (task, member_id) in enumerate(classified["audio"], 1):
            print(f'  {i:2d}. [{member_id.upper()}] {task[:60]}')
    
    # 生成报告
    print('\n📝 生成分类周报...')
    lines = []
    lines.append('# 团队周报 - 20260302（智能分类版 - 最终）')
    lines.append('')
    lines.append('## 📊 分类统计')
    lines.append('')
    lines.append('| 分类 | 任务数 | 占比 |')
    lines.append('|------|--------|------|')
    
    for cat_id in sorted(classified.keys(), key=lambda x: len(classified[x]), reverse=True):
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        count = len(classified[cat_id])
        percentage = (count / total * 100) if total > 0 else 0
        lines.append(f'| {cat_name} | {count} | {percentage:.1f}% |')
    
    lines.append('')
    lines.append(f'**总计**: {total} 个任务')
    lines.append('')
    
    # 详细内容
    lines.append('## 📋 分类任务详情')
    lines.append('')
    
    for cat_id in sorted(classified.keys(), key=lambda x: len(classified[x]), reverse=True):
        cat_name = CATEGORY_NAMES.get(cat_id, cat_id)
        lines.append(f'### {cat_name}')
        lines.append('')
        
        for task, member_id in classified[cat_id]:
            lines.append(f'- {task}')
        
        lines.append('')
    
    lines.append('---')
    lines.append('*此分类周报由智能分类系统生成（基于成员职责）*')
    
    report = '\n'.join(lines)
    
    # 保存
    output_path = Path('data/weekly/team/team_20260302_classified.md')
    output_path.write_text(report, encoding='utf-8')
    print(f'✅ 已保存: {output_path}')
    
    print('\n🎉 完成！')

if __name__ == "__main__":
    main()
