# API查询指南

## 概述

unreal_rag知识库包含221个Unreal Engine官方文档，支持快速查询API、编码规范、最佳实践等信息。

---

## 查询方式

### 方式1：直接使用Python脚本

```bash
# 交互式查询
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py

# 命令行查询
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py --query "UActorComponent"
```

### 方式2：使用Skill封装脚本

```bash
# 快速查询
~/openclaw/skills/unreal-developer/scripts/query_api.sh "UActorComponent"

# 多关键词查询
~/openclaw/skills/unreal-developer/scripts/query_api.sh "UActorComponent include header"
```

---

## 查询参数

| 参数 | 说明 | 示例 |
|------|------|------|
| --query | 查询关键词（必须） | --query "UActorComponent" |
| --max-results | 最大结果数（可选） | --max-results 5 |

```bash
# 指定返回5个结果
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "UActorComponent" --max-results 5
```

---

## 查询场景

### 场景1：查找类定义

```bash
# 查询UActorComponent
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "UActorComponent class definition"

# 查询结果示例：
# 1. UActorComponent.INT.md
#    相关度: 8
#    路径: ~/Documents/unreal_rag/docs/converted/markdown/UActorComponent.INT.md
#    摘要: UActorComponent is the base class for all Actor components...
```

**返回信息包含：**
- 文档名称
- 相关度评分
- 完整路径
- 内容摘要

### 场景2：查找头文件包含路径

```bash
# 查询正确的包含路径
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "UActorComponent include header"
```

**常见头文件路径：**

| 类 | 包含路径 |
|------|---------|
| AActor | `#include "GameFramework/Actor.h"` |
| UActorComponent | `#include "Components/ActorComponent.h"` |
| USceneComponent | `#include "Components/SceneComponent.h"` |
| UPrimitiveComponent | `#include "Components/PrimitiveComponent.h"` |
| ACharacter | `#include "GameFramework/Character.h"` |
| APlayerController | `#include "GameFramework/PlayerController.h"` |
| UWorld | `#include "Engine/World.h"` |

### 场景3：查找宏使用方法

```bash
# 查询UCLASS宏
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "UCLASS UPROPERTY UFUNCTION macro"

# 查询特定宏错误
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "GENERATED_BODY error fix"
```

### 场景4：查找模块依赖

```bash
# 查询Build.cs配置
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "Build.cs module dependency"

# 查询特定模块
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "GameFramework module"
```

### 场景5：查找容器和智能指针

```bash
# 查询TArray用法
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "TArray usage"

# 查询智能指针
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "TSharedPtr TWeakPtr"
```

---

## 查询技巧

### 技巧1：使用多个关键词

```bash
# 单个关键词可能结果太多
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py --query "component"

# 多个关键词更精确
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "UActorComponent include header path"
```

### 技巧2：查询错误信息

```bash
# 查询编译错误
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "C2065 undeclared identifier"

# 查询链接错误
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "LNK2019 unresolved external"
```

### 技巧3：查询特定功能

```bash
# 查询子系统
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "subsystem WorldSubsystem"

# 查询委托
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "delegate multicast"
```

---

## 结果解析

### 查询成功示例

```
🔎 请输入查询: UActorComponent
🔍 搜索: UActorComponent...
✅ 找到 3 个相关文档

1. UActorComponent.INT.md (相关度: 8)
   📄 /home/kai/Documents/unreal_rag/docs/converted/markdown/UActorComponent.INT.md
   
   摘要:
   UActorComponent is the base class for all Actor components.
   Components are reusable objects that can be added to Actors...

2. UPrimitiveComponent.INT.md (相关度: 6)
   📄 /home/kai/Documents/unreal_rag/docs/converted/markdown/UPrimitiveComponent.INT.md
   
   摘要:
   UPrimitiveComponent is the base class for primitive components
   that have rendering and collision...

3. USceneComponent.INT.md (相关度: 5)
   📄 /home/kai/Documents/unreal_rag/docs/converted/markdown/USceneComponent.INT.md
   
   摘要:
   USceneComponent is a component that has a transform...
```

### 如何使用结果

1. **查看相关度**：优先查看相关度高的文档
2. **阅读摘要**：快速判断是否相关
3. **打开完整文档**：`cat` 或用编辑器打开
4. **提取信息**：
   - 头文件包含路径
   - API使用示例
   - 编码规范要求

```bash
# 查看完整文档
cat ~/Documents/unreal_rag/docs/converted/markdown/UActorComponent.INT.md

# 或用编辑器打开
code ~/Documents/unreal_rag/docs/converted/markdown/UActorComponent.INT.md
```

---

## 知识库结构

```
~/Documents/unreal_rag/
├── docs/                          # 文档目录
│   ├── raw/markdown/             # 49个原始Markdown文档
│   │   ├── Runtime_AIModule_AICodingStandard.md
│   │   ├── CQTest_*.md
│   │   └── ...
│   └── converted/markdown/       # 172个转换后的文档
│       ├── UActorComponent.INT.md
│       ├── ACharacter.INT.md
│       └── ...
├── tools/
│   └── simple_rag_query.py       # ⭐ 主要查询工具
└── README.md                     # 使用说明
```

---

## 常见查询关键词

### 类和组件

- "UActorComponent"
- "USceneComponent"
- "UPrimitiveComponent"
- "ACharacter"
- "APlayerController"
- "APawn"

### 反射系统

- "UCLASS"
- "UPROPERTY"
- "UFUNCTION"
- "GENERATED_BODY"
- "UENUM"

### 容器和类型

- "TArray"
- "TMap"
- "TSet"
- "TSharedPtr"
- "TWeakPtr"
- "FString"

### 模块和依赖

- "Build.cs"
- "module dependency"
- "PublicDependencyModuleNames"
- "PrivateDependencyModuleNames"

### 编码规范

- "coding standard"
- "naming convention"
- "include header"
- "prefix convention"

---

## 与编译验证的集成

在unreal-developer skill中，API查询会自动用于：

1. **代码实现前**
   - 查询API定义
   - 确认头文件包含
   - 查看使用示例

2. **编译错误修复**
   - 查询错误类型
   - 查找解决方案
   - 确认正确的API用法

**示例流程：**

```bash
# 1. 实现UHealthComponent，需要先查询
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "UActorComponent include"

# 2. 得到结果：#include "Components/ActorComponent.h"

# 3. 编译失败，查询错误
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "GENERATED_BODY undeclared"

# 4. 根据查询结果修复代码
```

---

## 高级用法

### PageIndex + GLM（可选）

如果需要更高级的语义查询，可以使用PageIndex系统：

```bash
# 1. 配置GLM API Key
nano ~/Documents/unreal_rag/.env
# 添加: ZAI_API_KEY=your-key-here

# 2. 构建索引
cd ~/Documents/unreal_rag/pageindex/scripts
python3 build_index.py

# 3. 使用高级查询（语义理解更强）
```

**对比：**

| 特性 | 简化RAG | PageIndex + GLM |
|------|---------|-----------------|
| 费用 | 免费 | ¥5左右 |
| 速度 | <1秒 | 较慢 |
| 准确度 | 关键词匹配 | 语义理解 |
| 配置 | 无需配置 | 需API Key |

**推荐：** 日常使用简化RAG即可，复杂问题再用GLM。

---

## 故障排除

### 问题1：查询无结果

```bash
# 可能原因：
# 1. 关键词太具体
# 2. 关键词拼写错误

# 解决方法：
# 1. 使用更通用的关键词
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "component"  # 而不是 "UMyCustomComponent"

# 2. 检查拼写
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py \
  --query "UActorComponent"  # 确保大小写正确
```

### 问题2：Python脚本找不到

```bash
# 检查路径
ls ~/Documents/unreal_rag/tools/simple_rag_query.py

# 如果不存在，检查unreal_rag是否正确安装
cd ~/Documents
ls unreal_rag/
```

---

## 最佳实践

1. **查询前先思考**：明确需要什么信息（类定义、包含路径、使用示例）
2. **使用多个关键词**：提高查询精度
3. **优先查看高相关度结果**：节省时间
4. **保存常用查询**：记录常用API的头文件路径
5. **结合grep使用**：精确搜索时用grep，快速查找用RAG

---

**快速开始：**
```bash
python3 ~/Documents/unreal_rag/tools/simple_rag_query.py
```
