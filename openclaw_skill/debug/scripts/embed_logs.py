#!/usr/bin/env python3
"""
日志嵌入脚本
自动在代码中嵌入标准格式的调试日志
"""

import os
import sys
import re
from pathlib import Path


def embed_logs_in_file(file_path: str, module_name: str) -> str:
    """在文件中嵌入日志语句"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经导入了 logger
    has_logger_import = "import { logger }" in content or "from '../../core/logger'" in content

    # 添加 logger 导入
    if not has_logger_import:
        # 找到第一个 import 语句的位置
        import_match = re.search(r"^import\s+", content, re.MULTILINE)
        if import_match:
            insert_pos = import_match.start()
            import_statement = "import { logger } from '../../core/logger';\n"
            content = content[:insert_pos] + import_statement + content[insert_pos:]

    # 添加 MODULE_NAME 常量
    if 'MODULE_NAME' not in content:
        # 找到类定义或第一个函数定义的位置
        class_match = re.search(r"^export\s+(class|function|const)", content, re.MULTILINE)
        if class_match:
            insert_pos = class_match.start()
            module_constant = f"\nconst MODULE_NAME = '{module_name}';\n\n"
            content = content[:insert_pos] + module_constant + content[insert_pos:]

    # 在函数入口添加日志
    content = add_function_entry_logs(content, module_name)

    # 在条件分支添加日志
    content = add_condition_logs(content, module_name)

    # 在 try-catch 添加日志
    content = add_error_logs(content, module_name)

    return content


def add_function_entry_logs(content: str, module_name: str) -> str:
    """在函数入口添加日志"""

    # 匹配 async function 或普通 function
    pattern = r'(async\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{\n]+))?\s*\{'

    def add_log(match):
        full_match = match.group(0)
        is_async = match.group(1)
        func_name = match.group(2)
        params = match.group(3)

        # 跳过已有日志的函数
        if 'logger.info' in content[max(0, match.end()-100):match.end()+200]:
            return full_match

        # 跳过私有方法（以_开头）
        if func_name.startswith('_'):
            return full_match

        # 添加入口日志
        param_display = params.strip() if params and params.strip() else "无参数"
        log_statement = f'\n    logger.info(MODULE_NAME, `{func_name} 开始`);'

        return full_match + log_statement

    return re.sub(pattern, add_log, content)


def add_condition_logs(content: str, module_name: str) -> str:
    """在条件分支添加日志"""

    # 匹配 if 语句
    pattern = r'(\s*)(if\s*\([^)]+\)\s*\{)'

    def add_log(match):
        indent = match.group(1)
        if_statement = match.group(2)

        # 提取条件
        condition_match = re.search(r'if\s*\(([^)]+)\)', if_statement)
        condition = condition_match.group(1) if condition_match else '条件'

        # 添加分支日志
        log_statement = f"\n{indent}    logger.log(MODULE_NAME, `条件分支: {condition}`);"

        return if_statement + log_statement

    # 只在简单的 if 语句中添加（避免过度嵌入）
    # 这里简化处理，实际应用中需要更智能的判断
    return content


def add_error_logs(content: str, module_name: str) -> str:
    """在 catch 块添加错误日志"""

    # 匹配 catch 块
    pattern = r'(\s*)catch\s*\((\w+)\)\s*\{'

    def add_log(match):
        indent = match.group(1)
        error_var = match.group(2)
        catch_statement = match.group(0)

        # 检查是否已有日志
        next_200_chars = content[match.end():match.end()+200]
        if 'logger.error' in next_200_chars:
            return catch_statement

        # 添加错误日志
        log_statement = f"\n{indent}    logger.error(MODULE_NAME, `捕获异常: ${{{error_var}.message}}`);"

        return catch_statement + log_statement

    return re.sub(pattern, add_log, content)


def generate_log_report(file_path: str, module_name: str) -> dict:
    """生成日志嵌入报告"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 统计日志数量
    log_count = len(re.findall(r'logger\.(log|info|warning|error)', content))

    # 统计各等级数量
    log_levels = {
        'log': len(re.findall(r'logger\.log', content)),
        'info': len(re.findall(r'logger\.info', content)),
        'warning': len(re.findall(r'logger\.warning', content)),
        'error': len(re.findall(r'logger\.error', content))
    }

    return {
        'file': file_path,
        'module': module_name,
        'total_logs': log_count,
        'levels': log_levels
    }


def main():
    if len(sys.argv) < 2:
        print("用法: python embed_logs.py <文件路径> [模块名]")
        print("")
        print("示例:")
        print("  python embed_logs.py src/modules/order/order-service.ts OrderService")
        print("")
        print("如果不提供模块名，将从文件名自动推断")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 {file_path}")
        sys.exit(1)

    # 推断模块名
    if len(sys.argv) > 2:
        module_name = sys.argv[2]
    else:
        # 从文件名推断
        file_name = os.path.basename(file_path)
        module_name = file_name.replace('.ts', '').replace('-', ' ').title().replace(' ', '')

    print(f"🔍 分析文件: {file_path}")
    print(f"📦 模块名: {module_name}")

    # 嵌入日志
    new_content = embed_logs_in_file(file_path, module_name)

    # 备份原文件
    backup_path = file_path + '.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        with open(file_path, 'r', encoding='utf-8') as original:
            f.write(original.read())
    print(f"💾 已备份原文件到: {backup_path}")

    # 写入新内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"✅ 已嵌入日志到: {file_path}")

    # 生成报告
    report = generate_log_report(file_path, module_name)
    print(f"\n📊 日志统计:")
    print(f"   总计: {report['total_logs']} 条日志")
    print(f"   - log: {report['levels']['log']}")
    print(f"   - info: {report['levels']['info']}")
    print(f"   - warning: {report['levels']['warning']}")
    print(f"   - error: {report['levels']['error']}")

    print(f"\n⚠️  注意:")
    print(f"   1. 请检查自动生成的日志是否合理")
    print(f"   2. 如有问题可从备份恢复: {backup_path}")
    print(f"   3. 确保已创建 src/core/logger/index.ts")


if __name__ == "__main__":
    main()
