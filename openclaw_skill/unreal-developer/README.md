# Unreal Developer Skill

**Unreal Engine C++开发专家技能**

## 📋 概述

这是一个专门为Unreal Engine 5 C++开发设计的Agent技能，具有以下核心能力：

- ✅ **知识库驱动**：基于221个UE官方文档的知识库查询
- ✅ **自动编译验证**：代码完成后自动编译确保可运行
- ✅ **智能错误修复**：遇到编译错误自动分析并修复（最多3次）
- ✅ **代码规范遵守**：严格遵循UE编码规范

## 🎯 核心特性

### 1. 知识库集成

- 221个UE官方文档
- 快速API查询
- 编码规范参考
- 常见错误解决方案

### 2. 编译验证机制

```
代码实现 → 编译验证 → [失败?] → 错误分析 → 知识库查询 → 修复 → 重试(<3次)
→ [3次失败?] → 通知项目经理
```

### 3. 完整工作流程

1. 接收UE开发任务
2. 查询知识库获取API信息
3. 阅读编码规范
4. 实现C++代码
5. 自动编译验证
6. 智能错误修复（如果需要）
7. 交付已验证的代码

## 📁 文件结构

```
unreal-developer/
├── SKILL.md                    # 主技能文档
├── references/                 # 参考文档
│   ├── coding-standard.md      # UE编码规范
│   ├── api-query-guide.md      # API查询指南
│   ├── common-patterns.md      # UE常用开发模式
│   ├── best-practices.md       # 最佳实践
│   └── compilation-errors.md   # 编译错误处理
└── scripts/                    # 工具脚本
    ├── query_api.sh            # 快速查询API
    ├── compile_project.sh      # 编译UE项目
    ├── analyze_error.sh        # 分析编译错误
    └── validate_code.sh        # 代码规范检查
```

## 🚀 快速开始

### 1. 查询API

```bash
# 使用封装脚本
~/.openclaw/skills/unreal-developer/scripts/query_api.sh "UActorComponent"

# 或直接使用知识库
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py --query "UActorComponent"
```

### 2. 编译项目

```bash
# 编译UE项目
~/.openclaw/skills/unreal-developer/scripts/compile_project.sh MyProject.uproject Development
```

### 3. 分析错误

```bash
# 分析编译错误
~/.openclaw/skills/unreal-developer/scripts/analyze_error.sh build.log
```

### 4. 验证代码

```bash
# 检查代码规范
~/.openclaw/skills/unreal-developer/scripts/validate_code.sh Source/
```

## 📚 参考文档

### 编码规范

- 命名规范（PascalCase、前缀规则）
- 反射宏使用（UCLASS、UPROPERTY、UFUNCTION）
- 头文件包含顺序
- 代码格式要求

**详细文档：** [references/coding-standard.md](references/coding-standard.md)

### API查询

- 查询方式（交互式、命令行）
- 常见查询场景
- 结果解析方法
- 查询技巧

**详细文档：** [references/api-query-guide.md](references/api-query-guide.md)

### 常用模式

- Actor-Component架构
- Subsystem使用
- 委托与事件
- 智能指针
- 定时器
- 数据表
- 接口
- 网络同步

**详细文档：** [references/common-patterns.md](references/common-patterns.md)

### 最佳实践

- 性能优化
- 内存管理
- 线程安全
- 蓝图交互
- 调试技巧
- 常见陷阱

**详细文档：** [references/best-practices.md](references/best-practices.md)

### 错误处理

- 常见编译错误
- 错误分析流程
- 修复方案
- 预防措施

**详细文档：** [references/compilation-errors.md](references/compilation-errors.md)

## 🔄 工作流程

### 完整流程图

```
接收任务
    ↓
查询知识库
    ↓
阅读编码规范
    ↓
实现代码
    ↓
编译验证
    ↓
{编译成功?}
    ↓
是 → 提交Debug Agent
否 → 错误分析 → 知识库查询 → 修复代码
    ↓
{重试次数 < 3?}
    ↓
是 → 返回"编译验证"
否 → 通知项目经理 → 用户介入
```

## 🛠️ 工具脚本说明

### query_api.sh - API查询

快速查询UE API和文档。

```bash
# 查询单个关键词
./scripts/query_api.sh "UActorComponent"

# 查询并限制结果数
./scripts/query_api.sh "UActorComponent include" 5
```

### compile_project.sh - 项目编译

编译UE项目并验证代码。

```bash
# 编译项目（Debug模式）
./scripts/compile_project.sh MyProject.uproject

# 编译项目（Development模式）
./scripts/compile_project.sh MyProject.uproject Development
```

### analyze_error.sh - 错误分析

分析编译错误并生成修复建议。

```bash
# 分析错误日志
./scripts/analyze_error.sh build.log

# 自动生成查询建议和修复报告
```

### validate_code.sh - 代码验证

检查代码是否符合UE编码规范。

```bash
# 验证单个文件
./scripts/validate_code.sh Source/Game/MyCharacter.h

# 验证整个目录
./scripts/validate_code.sh Source/
```

## ⚙️ 配置要求

### 1. 知识库

确保unreal_rag已正确安装：

```bash
~/Documents/unreal_rag/
├── tools/simple_rag_query.py
└── docs/
```

### 2. UE引擎路径

修改 `compile_project.sh` 中的引擎路径：

```bash
UE_PATH="/opt/UnrealEngine"  # 修改为您的UE安装路径
```

### 3. 项目配置

确保项目有正确的Build.cs配置：

```csharp
PublicDependencyModuleNames.AddRange(new string[] { 
    "Core", "CoreUObject", "Engine", "InputCore" 
});
```

## 🎓 使用场景

### 场景1：创建自定义组件

```bash
1. 接收任务：创建生命值组件
2. 查询API：./scripts/query_api.sh "UActorComponent"
3. 阅读规范：references/coding-standard.md
4. 实现代码：HealthComponent.h/.cpp
5. 编译验证：./scripts/compile_project.sh MyProject.uproject
6. [失败?] 分析错误：./scripts/analyze_error.sh error.log
7. [成功?] 提交代码
```

### 场景2：修复编译错误

```bash
1. 编译失败
2. 分析错误：./scripts/analyze_error.sh error.log
3. 查询解决方案：./scripts/query_api.sh "LNK2019 fix"
4. 实施修复
5. 重新编译
6. [成功?] 提交 : [重试<3?] 继续
```

## 📊 与其他Agent的协作

| Agent | 协作方式 |
|-------|---------|
| 项目经理 | 接收任务 / 汇报编译失败（3次后）|
| 架构师 | 遵循架构文档 |
| Debug | 交付代码（已编译验证）→ 接收带日志代码 |
| QA | 等待测试结果 → 接收错误文档 |

## 🔧 故障排除

### 问题1：知识库查询失败

```bash
# 检查知识库路径
ls ~/Documents/unreal_rag/tools/simple_rag_query.py

# 如果不存在，克隆仓库
cd ~/Documents
git clone <unreal_rag仓库地址>
```

### 问题2：编译脚本路径错误

```bash
# 修改compile_project.sh中的UE_PATH
nano ~/.openclaw/skills/unreal-developer/scripts/compile_project.sh
```

### 问题3：权限不足

```bash
# 给脚本添加执行权限
chmod +x ~/.openclaw/skills/unreal-developer/scripts/*.sh
```

## 📝 更新日志

### v1.0.0 (2026-02-20)
- ✅ 初始版本发布
- ✅ 完整的知识库集成
- ✅ 自动编译验证机制
- ✅ 智能错误修复流程
- ✅ 4个工具脚本
- ✅ 5个参考文档

## 📖 相关资源

- **Unreal Engine文档**: https://docs.unrealengine.com/
- **UE编码规范**: ~/Documents/unreal_rag/docs/raw/markdown/Runtime_AIModule_AICodingStandard.md
- **知识库**: ~/Documents/unreal_rag/

## 🤝 贡献

如果您发现bug或有改进建议，请更新相应的文件并记录在更新日志中。

## 📄 许可证

本技能遵循OpenClaw技能系统的许可证。

---

**🎮 Happy Coding with Unreal Developer Skill!**
