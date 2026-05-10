#!/usr/bin/env python3
"""
Git 操作脚本
提供标准化的 Git 操作接口
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path


def run_command(cmd: list, cwd: str = None) -> dict:
    """执行命令并返回结果"""

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode
        }

    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }


def is_git_repo(path: str = None) -> bool:
    """检查是否是 Git 仓库"""

    result = run_command(['git', 'rev-parse', '--git-dir'], cwd=path)
    return result['success']


def get_current_branch(path: str = None) -> str:
    """获取当前分支名"""

    result = run_command(['git', 'branch', '--show-current'], cwd=path)
    if result['success']:
        return result['stdout']
    return ''


def get_status(path: str = None) -> dict:
    """获取仓库状态"""

    result = run_command(['git', 'status', '--porcelain'], cwd=path)

    status = {
        'clean': result['success'] and not result['stdout'],
        'modified': [],
        'added': [],
        'deleted': [],
        'untracked': []
    }

    if result['stdout']:
        for line in result['stdout'].split('\n'):
            if not line:
                continue

            code = line[:2]
            file_path = line[3:]

            if 'M' in code:
                status['modified'].append(file_path)
            elif 'A' in code or '?' in code:
                status['added'].append(file_path)
            elif 'D' in code:
                status['deleted'].append(file_path)
            elif '??' in code:
                status['untracked'].append(file_path)

    return status


def add_files(files: list = None, path: str = None) -> dict:
    """暂存文件"""

    if files:
        cmd = ['git', 'add'] + files
    else:
        cmd = ['git', 'add', '.']

    return run_command(cmd, cwd=path)


def commit(message: str, body: str = None, path: str = None) -> dict:
    """提交更改"""

    cmd = ['git', 'commit', '-m', message]

    if body:
        cmd.extend(['-m', body])

    result = run_command(cmd, cwd=path)

    if result['success']:
        # 获取提交 hash
        hash_result = run_command(['git', 'rev-parse', 'HEAD'], cwd=path)
        result['commit_hash'] = hash_result['stdout'][:7] if hash_result['success'] else ''

    return result


def push(remote: str = 'origin', branch: str = None, path: str = None) -> dict:
    """推送到远程"""

    if not branch:
        branch = get_current_branch(path)

    cmd = ['git', 'push', remote, branch]
    return run_command(cmd, cwd=path)


def pull(remote: str = 'origin', branch: str = None, path: str = None) -> dict:
    """从远程拉取"""

    if not branch:
        branch = get_current_branch(path)

    cmd = ['git', 'pull', remote, branch]
    return run_command(cmd, cwd=path)


def create_branch(branch_name: str, path: str = None) -> dict:
    """创建分支"""

    cmd = ['git', 'checkout', '-b', branch_name]
    return run_command(cmd, cwd=path)


def switch_branch(branch_name: str, path: str = None) -> dict:
    """切换分支"""

    cmd = ['git', 'checkout', branch_name]
    return run_command(cmd, cwd=path)


def merge_branch(branch_name: str, path: str = None) -> dict:
    """合并分支"""

    cmd = ['git', 'merge', branch_name]
    return run_command(cmd, cwd=path)


def get_log(count: int = 10, path: str = None) -> list:
    """获取提交历史"""

    cmd = ['git', 'log', f'-{count}', '--oneline', '--format=%H|%s|%an|%ad']
    result = run_command(cmd, cwd=path)

    logs = []
    if result['success'] and result['stdout']:
        for line in result['stdout'].split('\n'):
            if not line:
                continue
            parts = line.split('|', 3)
            if len(parts) >= 4:
                logs.append({
                    'hash': parts[0][:7],
                    'message': parts[1],
                    'author': parts[2],
                    'date': parts[3]
                })

    return logs


def has_conflicts(path: str = None) -> bool:
    """检查是否有冲突"""

    result = run_command(['git', 'diff', '--name-only', '--diff-filter=U'], cwd=path)
    return bool(result['stdout'])


def commit_and_push(
    task_id: str,
    task_name: str,
    files: list = None,
    message: str = None,
    path: str = None
) -> dict:
    """提交并推送（主操作）"""

    result = {
        'task_id': task_id,
        'success': False,
        'steps': []
    }

    # 1. 检查是否是 Git 仓库
    if not is_git_repo(path):
        result['error'] = '不是 Git 仓库'
        return result
    result['steps'].append({'step': 'check_repo', 'success': True})

    # 2. 检查状态
    status = get_status(path)
    if status['clean']:
        result['error'] = '没有更改需要提交'
        result['already_committed'] = True
        return result
    result['steps'].append({'step': 'check_status', 'success': True})

    # 3. 暂存文件
    add_result = add_files(files, path)
    if not add_result['success']:
        result['error'] = f"暂存失败: {add_result['stderr']}"
        return result
    result['steps'].append({'step': 'add', 'success': True})

    # 4. 提交
    if not message:
        message = f"feat: 完成 {task_name}"

    commit_result = commit(message, f"Task: {task_id}", path)
    if not commit_result['success']:
        result['error'] = f"提交失败: {commit_result['stderr']}"
        return result
    result['commit_hash'] = commit_result.get('commit_hash', '')
    result['steps'].append({'step': 'commit', 'success': True})

    # 5. 推送
    push_result = push(path=path)
    if not push_result['success']:
        result['error'] = f"推送失败: {push_result['stderr']}"
        return result
    result['branch'] = get_current_branch(path)
    result['steps'].append({'step': 'push', 'success': True})

    result['success'] = True
    return result


def main():
    if len(sys.argv) < 2:
        print("用法: python git_operations.py <操作> [参数...]")
        print("")
        print("操作:")
        print("  status                    查看状态")
        print("  branch                    查看当前分支")
        print("  log [count]               查看提交历史")
        print("  commit <task_id> <name>   提交并推送")
        print("")
        print("示例:")
        print("  python git_operations.py status")
        print("  python git_operations.py log 5")
        print("  python git_operations.py commit TASK-001 '实现工具模块'")
        sys.exit(1)

    operation = sys.argv[1]

    if operation == 'status':
        status = get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif operation == 'branch':
        branch = get_current_branch()
        print(f"当前分支: {branch}")

    elif operation == 'log':
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        logs = get_log(count)
        for log in logs:
            print(f"{log['hash']} - {log['message']} ({log['author']})")

    elif operation == 'commit':
        if len(sys.argv) < 4:
            print("用法: python git_operations.py commit <task_id> <task_name>")
            sys.exit(1)

        task_id = sys.argv[2]
        task_name = sys.argv[3]

        result = commit_and_push(task_id, task_name)

        if result['success']:
            print(f"✅ 备份成功")
            print(f"   提交: {result.get('commit_hash', 'N/A')}")
            print(f"   分支: {result.get('branch', 'N/A')}")
        else:
            print(f"❌ 备份失败: {result.get('error', '未知错误')}")

    else:
        print(f"未知操作: {operation}")
        sys.exit(1)


if __name__ == "__main__":
    main()
