# LLT (Low-Level Tests) 最佳实践

## 概述

Low-Level Tests (LLT) 是 Unreal Engine 5.6 的轻量级单元测试框架，使用 Catch2 作为测试框架，无需启动 Editor，适合快速迭代和 CI 集成。

---

## 核心原则

### 1. 依赖最小化

**原则：** 只依赖必要的模块，优先仅依赖 Core。

```csharp
// ✅ 推荐：最小依赖
PrivateDependencyModuleNames.AddRange(new string[] { "Core" });

// ⚠️ 谨慎使用：必要时添加
PrivateDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject" });

// ❌ 避免：重量级依赖
PrivateDependencyModuleNames.AddRange(new string[] { "Engine", "Editor" });
```

### 2. 隔离测试

**原则：** 使用 Stub/Mock 隔离外部依赖。

```csharp
// Target.cs
bUsePlatformFileStub = true;      // 文件系统 Stub
bMockEngineDefaults = true;        // Mock 引擎默认值
```

### 3. 快速反馈

**原则：** 测试应在秒级完成，适合每次提交运行。

```cpp
// 使用标签区分测试速度
TEST_CASE("Fast test", "[unit][fast]") { ... }
TEST_CASE("Slow test", "[unit][slow]") { ... }

// PR 阶段只运行 fast 测试
./Test "[fast]"
```

---

## 测试用例设计

### AAA 模式

```cpp
TEST_CASE("Example", "[unit]")
{
    SECTION("Normal flow")
    {
        // Arrange - 准备
        int32 Input = 5;
        int32 Expected = 10;
        
        // Act - 执行
        int32 Result = Function(Input);
        
        // Assert - 断言
        REQUIRE(Result == Expected);
    }
}
```

### 等价类划分

```cpp
TEST_CASE("Validate input", "[unit]")
{
    SECTION("Valid input") { /* 有效等价类 */ }
    SECTION("Invalid input") { /* 无效等价类 */ }
    SECTION("Edge cases") { /* 边界情况 */ }
}
```

### 边界值测试

```cpp
TEST_CASE("Boundary test", "[unit]")
{
    SECTION("Min value") { REQUIRE(Function(0) == 0); }
    SECTION("Max value") { REQUIRE(Function(MAX) > 0); }
    SECTION("Below min") { REQUIRE(Function(-1) == 0); }
    SECTION("Above max") { /* 溢出处理 */ }
}
```

---

## 断言选择

| 断言 | 失败行为 | 使用场景 |
|------|---------|---------|
| `REQUIRE` | 中止当前测试 | 关键断言，失败后无意义继续 |
| `CHECK` | 继续执行 | 非关键断言，收集所有失败 |
| `REQUIRE_FALSE` | 中止当前测试 | 断言为假 |
| `CHECK_FALSE` | 继续执行 | 检查为假 |
| `REQUIRE_THROWS` | 中止当前测试 | 期望抛出异常 |

```cpp
// 关键断言：失败后无意义继续
REQUIRE(Pointer != nullptr);

// 非关键断言：收集所有失败
CHECK(Value1 == Expected1);
CHECK(Value2 == Expected2);
CHECK(Value3 == Expected3);
```

---

## 标签策略

### 标签分类

| 标签 | 说明 | 运行策略 |
|------|------|---------|
| `[unit]` | 单元测试 | PR 阶段 |
| `[fast]` | 快速测试 (<1s) | PR 阶段 |
| `[slow]` | 慢速测试 (>1s) | Nightly |
| `[integration]` | 模块级集成 | Nightly |
| `[network]` | 网络协议（无实际网络）| Nightly |

### 标签过滤

```bash
# 仅运行 fast 测试
./Test "[fast]"

# 排除 slow 测试
./Test "~[slow]"

# 运行 unit 且非 slow
./Test "[unit]~[slow]"

# 运行特定标签组合
./Test "[unit][fast]"
```

---

## 构建配置

### Build.cs 最佳实践

```csharp
public class MyTests : TestModuleRules
{
    static MyTests()
    {
        if (!InTestMode) return;

        TestMetadata = new Metadata();
        TestMetadata.TestName = "MyModule";
        TestMetadata.UsesCatch2 = true;
        
        // ✅ 限制平台
        TestMetadata.SupportedPlatforms.Clear();
        TestMetadata.SupportedPlatforms.Add(UnrealTargetPlatform.Linux);
    }

    public MyTests(ReadOnlyTargetRules Target) : base(Target)
    {
        // ✅ 禁用优化（便于调试）
        OptimizeCode = CodeOptimization.Never;

        // ✅ 最小依赖
        PrivateDependencyModuleNames.AddRange(new string[] { "Core" });
    }
}
```

### Target.cs 最佳实践

```csharp
public class MyTestsTarget : TestTargetRules
{
    public MyTestsTarget(TargetInfo Target) : base(Target)
    {
        // ✅ 隔离策略
        bUsePlatformFileStub = true;
        bMockEngineDefaults = true;
    }
}
```

---

## 运行命令

### 基础运行

```bash
# 构建
./Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool \
    MyTestsTarget Development Linux

# 运行
./MyTests --log --timeout=30 -r junit -o report.xml
```

### 调试模式

```bash
# 失败时断进调试器
./MyTests -b

# 详细日志
./MyTests --log --debug
```

### CI 集成

```bash
# JUnit XML 输出（CI 消费）
./MyTests -r junit -o junit.xml

# 标签过滤
./MyTests -r junit "[fast]" -o junit.xml

# 传递 UE 参数
./MyTests --extra-args -stdout
```

---

## 常见问题

### 问题1：编译错误 - 缺少 include

**症状：**
```
error: 'TestHarness.h' file not found
```

**解决方案：**
1. 检查 Build.cs 是否继承 `TestModuleRules`
2. 检查 `UsesCatch2 = true` 是否设置
3. 查询知识库：`~/Documents/unreal_rag`

### 问题2：链接错误 - 符号未定义

**症状：**
```
undefined reference to `Symbol`
```

**解决方案：**
1. 检查模块依赖是否完整
2. 检查头文件是否包含
3. 查询知识库：`~/Documents/unreal_rag`

### 问题3：Editor 依赖问题

**症状：**
```
Editor subsystem not available
```

**解决方案：**
1. LLT 不适合 Editor 深度测试
2. 改用 Automation Framework (Specs)
3. 查询知识库：`~/Documents/unreal_rag`

---

## 知识库查询

遇到问题时，查询知识库：

```bash
# 编译错误
查询 ~/Documents/unreal_rag → "LLT compile error <关键词>"

# 参数问题
查询 ~/Documents/unreal_rag → "LLT runner parameters <参数名>"

# API 使用
查询 ~/Documents/unreal_rag → "Catch2 API <函数名>"
```

---

## 检查清单

### 测试文件检查

- [ ] 包含 `TestHarness.h`
- [ ] 使用正确的标签
- [ ] 遵循 AAA 模式
- [ ] 使用正确的断言
- [ ] 测试描述清晰

### 构建配置检查

- [ ] Build.cs 继承 `TestModuleRules`
- [ ] Target.cs 继承 `TestTargetRules`
- [ ] `UsesCatch2 = true` 已设置
- [ ] 依赖最小化
- [ ] 隔离配置正确

### 运行检查

- [ ] 所有测试通过
- [ ] 覆盖率 ≥ 80%
- [ ] JUnit XML 生成正确
- [ ] 日志文件完整
