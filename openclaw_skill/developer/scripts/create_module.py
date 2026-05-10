#!/usr/bin/env python3
"""
代码模板生成脚本
根据模块类型生成标准代码模板
"""

import os
import sys
from datetime import datetime
from pathlib import Path


TEMPLATES = {
    'tool': '''/**
 * {module_name} 工具
 * 职责：{description}
 */

/**
 * {pascal_name} 选项
 */
export interface {pascal_name}Options {{
  // TODO: 定义选项
}}

/**
 * {description}
 *
 * @param input - 输入参数
 * @param options - 配置选项
 * @returns 处理结果
 *
 * @example
 * ```typescript
 * const result = {camel_name}(input, {{ /* options */ }});
 * ```
 */
export function {camel_name}(
  input: unknown,
  options?: {pascal_name}Options
): unknown {{
  // TODO: 实现逻辑
  throw new Error('Not implemented');
}}
''',

    'service': '''/**
 * {module_name} 服务
 * 职责：{description}
 */

import {{ Result, success, failure }} from '../../core/types/result';

/**
 * {pascal_name} 输入
 */
export interface {pascal_name}Input {{
  // TODO: 定义输入
}}

/**
 * {pascal_name} 输出
 */
export interface {pascal_name}Output {{
  // TODO: 定义输出
}}

/**
 * {module_name} 服务
 */
export class {pascal_name}Service {{
  /**
   * 执行 {description}
   */
  async execute(input: {pascal_name}Input): Promise<Result<{pascal_name}Output>> {{
    try {{
      // TODO: 实现业务逻辑

      return success({{
        // TODO: 返回数据
      }});
    }} catch (error) {{
      return failure(
        '{pascal_upper}_ERROR',
        (error as Error).message
      );
    }}
  }}
}}
''',

    'types': '''/**
 * {module_name} 类型定义
 */

/**
 * {pascal_name} 类型
 */
export interface {pascal_name} {{
  id: string;
  createdAt: string;
  updatedAt: string;
  // TODO: 添加更多字段
}}

/**
 * 创建 {pascal_name} 输入
 */
export interface Create{pascal_name}Input {{
  // TODO: 定义创建输入
}}

/**
 * 更新 {pascal_name} 输入
 */
export interface Update{pascal_name}Input {{
  id: string;
  // TODO: 定义更新输入
}}
'''
}


def to_camel_case(text: str) -> str:
    """转换为 camelCase"""
    words = text.replace('-', ' ').replace('_', ' ').split()
    if not words:
        return text
    return words[0].lower() + ''.join(w.capitalize() for w in words[1:])


def to_pascal_case(text: str) -> str:
    """转换为 PascalCase"""
    words = text.replace('-', ' ').replace('_', ' ').split()
    return ''.join(w.capitalize() for w in words)


def to_kebab_case(text: str) -> str:
    """转换为 kebab-case"""
    result = []
    for char in text:
        if char.isupper():
            result.append('-')
            result.append(char.lower())
        elif char in (' ', '_'):
            result.append('-')
        else:
            result.append(char)
    return ''.join(result).strip('-')


def create_module(module_type: str, module_name: str, description: str, output_dir: str):
    """创建模块文件"""

    if module_type not in TEMPLATES:
        print(f"错误: 未知的模块类型 '{module_type}'")
        print(f"可用类型: {', '.join(TEMPLATES.keys())}")
        return None

    # 准备变量
    camel_name = to_camel_case(module_name)
    pascal_name = to_pascal_case(module_name)
    kebab_name = to_kebab_case(module_name)
    pascal_upper = pascal_name.upper()

    # 生成代码
    template = TEMPLATES[module_type]
    code = template.format(
        module_name=module_name,
        camel_name=camel_name,
        pascal_name=pascal_name,
        pascal_upper=pascal_upper,
        description=description
    )

    # 确定文件路径
    if module_type == 'tool':
        file_path = os.path.join(output_dir, 'src', 'core', kebab_name, f'{kebab_name}.ts')
    elif module_type == 'service':
        file_path = os.path.join(output_dir, 'src', 'modules', kebab_name, f'{kebab_name}-service.ts')
    elif module_type == 'types':
        file_path = os.path.join(output_dir, 'src', 'modules', kebab_name, 'types.ts')
    else:
        file_path = os.path.join(output_dir, f'{kebab_name}.ts')

    # 创建目录
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(code)

    return file_path


def main():
    if len(sys.argv) < 4:
        print("用法: python create_module.py <类型> <模块名> <描述> [输出目录]")
        print("")
        print("类型:")
        print("  tool    - 工具模块 (src/core/)")
        print("  service - 服务模块 (src/modules/)")
        print("  types   - 类型定义 (src/modules/)")
        print("")
        print("示例:")
        print("  python create_module.py tool date-utils '日期处理工具'")
        print("  python create_module.py service user '用户管理服务'")
        print("  python create_module.py types order '订单类型定义' ./my-project")
        sys.exit(1)

    module_type = sys.argv[1]
    module_name = sys.argv[2]
    description = sys.argv[3]
    output_dir = sys.argv[4] if len(sys.argv) > 4 else '.'

    print(f"🔨 创建 {module_type} 模块: {module_name}")
    print(f"   描述: {description}")

    file_path = create_module(module_type, module_name, description, output_dir)

    if file_path:
        print(f"✅ 已创建: {file_path}")
        print(f"\n📝 下一步:")
        print(f"   1. 实现 TODO 标记的功能")
        print(f"   2. 添加单元测试")
        print(f"   3. 更新 index.ts 导出")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
