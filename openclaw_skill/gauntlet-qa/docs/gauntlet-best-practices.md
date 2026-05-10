# Gauntlet 最佳实践

## 概述

Gauntlet 是 Unreal Engine 5.6 的会话编排框架，用于运行多进程、跨平台、联网的系统级测试。适合端到端验证、性能回归和 CI 集成。

---

## 核心原则

### 1. 编排与断言分离

**原则：** TestNode 负责编排会话，TestController 负责断言验证。

```
TestNode.cs (C#)      → 会话编排（启动进程、配置参数）
TestController.cpp (C++) → 运行时断言（业务逻辑验证）
```

### 2. 状态机驱动

**原则：** 使用状态机管理测试流程，每个状态职责清晰。

```cpp
enum class ETestState
{
    Init,       // 初始化
    Loading,    // 加载中
    Running,    // 执行中
    Verifying,  // 验证中
    Complete    // 完成
};
```

### 3. 超时与心跳

**原则：** 设置合理超时，定期发送心跳防止误判。

```csharp
// TestNode.cs
Configuration.MaxDuration = 600;  // 10 分钟超时

// TestController.cpp
MarkHeartbeatActive();  // 每帧调用
```

### 4. 进程级隔离

**原则：** 每个会话是独立进程，天然隔离全局状态。

---

## TestNode 最佳实践

### 角色配置

```csharp
public override IEnumerator<float> GetConfiguration()
{
    // 配置客户端
    ConfigRole ClientRole = new ConfigRole();
    ClientRole.Type = RoleType.Client;
    ClientRole.Count = 2;  // 2 个客户端
    
    // 配置服务器
    ConfigRole ServerRole = new ConfigRole();
    ServerRole.Type = RoleType.Server;
    ServerRole.Count = 1;  // 1 个服务器
    
    // 添加角色
    Configuration.Roles.Add(ClientRole);
    Configuration.Roles.Add(ServerRole);
    
    // 超时配置
    Configuration.MaxDuration = 600;
    
    // 测试控制器
    Configuration.TestController = "MyTestController";
    
    yield return 0;
}
```

### CI 参数

```csharp
// CI 必需参数
Configuration.Parameters.Add("-nullrhi");      // 无渲染（Headless）
Configuration.Parameters.Add("-unattended");   // 无人值守
Configuration.Parameters.Add("-nopause");      // 不暂停
Configuration.Parameters.Add("-log");          // 启用日志
```

---

## TestController 最佳实践

### 生命周期管理

```cpp
void UMyTestController::OnInit()
{
    // 初始化状态
    SetTestState(ETestState::Loading);
    
    // 加载测试地图
    ServerTravel("/Game/Maps/TestMap");
}

void UMyTestController::OnTick(float DeltaTime)
{
    // 状态机驱动
    switch (CurrentState)
    {
        case ETestState::Loading: TickLoading(); break;
        case ETestState::Running: TickRunning(); break;
        case ETestState::Verifying: TickVerifying(); break;
    }
    
    // 心跳（必需）
    MarkHeartbeatActive();
}

void UMyTestController::OnPostMapChange(UWorld* World)
{
    // 地图加载完成
    SetTestState(ETestState::Running);
}
```

### 状态机实现

```cpp
void UMyTestController::TickRunning()
{
    // 执行测试步骤
    ExecuteTestStep(CurrentStep);
    
    // 检查步骤完成
    if (CheckStepComplete(CurrentStep))
    {
        CurrentStep++;
        
        if (CurrentStep >= TotalSteps)
        {
            SetTestState(ETestState::Verifying);
        }
    }
}

void UMyTestController::TickVerifying()
{
    // 验证结果
    bool bPassed = VerifyTestResults();
    
    // 结束测试
    if (bPassed)
    {
        EndTest(0);  // 通过
    }
    else
    {
        EndTest(1);  // 失败
    }
}
```

---

## 运行命令

### 基础运行

```bash
./Engine/Build/BatchFiles/Linux/RunUAT.sh RunUnreal \
    -project="/home/user/MyGame/MyGame.uproject" \
    -scriptdir="/home/user/MyGame" \
    -platform=Linux \
    -configuration=Development \
    -build=editor \
    -nullrhi -unattended -nopause \
    -test="MyGame.Automation.MyTest"
```

### 带 JUnit 报告

```bash
./Engine/Build/BatchFiles/Linux/RunUAT.sh RunUnreal \
    -project="/home/user/MyGame/MyGame.uproject" \
    -scriptdir="/home/user/MyGame" \
    -platform=Linux \
    -configuration=Development \
    -build=editor \
    -nullrhi -unattended -nopause \
    -test="MyTest(JUnitReportPath=/home/user/MyGame/Saved/Reports/junit.xml)"
```

### 容错恢复

```bash
./Engine/Build/BatchFiles/Linux/RunUAT.sh RunUnreal \
    ... \
    -ResumeOnCriticalFailure=3
```

---

## 参数说明

### RunUAT 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-project` | 项目文件路径 | `-project="/path/to/MyGame.uproject"` |
| `-scriptdir` | 脚本目录 | `-scriptdir="/path/to/MyGame"` |
| `-platform` | 目标平台 | `-platform=Linux` |
| `-configuration` | 构建配置 | `-configuration=Development` |
| `-build` | 构建类型 | `-build=editor` |
| `-nullrhi` | 无渲染（CI 必需） | `-nullrhi` |
| `-unattended` | 无人值守（CI 必需） | `-unattended` |
| `-nopause` | 不暂停（CI 必需） | `-nopause` |
| `-test` | 测试节点+参数 | `-test="TestNode(Param=Value)"` |
| `-ResumeOnCriticalFailure` | 容错恢复 | `-ResumeOnCriticalFailure=3` |

### 测试参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `JUnitReportPath` | JUnit XML 路径 | `JUnitReportPath=/path/to/junit.xml` |
| `ReportPath` | 报告目录 | `ReportPath=/path/to/reports` |
| `TestName` | 测试名称 | `TestName=MyTest` |

---

## CI 集成建议

### PR 阶段（快速冒烟）

```bash
# 单个客户端，快速验证
./Engine/Build/BatchFiles/Linux/RunUAT.sh RunUnreal \
    -platform=Linux \
    -build=editor \
    -nullrhi -unattended -nopause \
    -test="SmokeTest(JUnitReportPath=junit.xml)" \
    MaxDuration=300
```

### Nightly 阶段（完整回归）

```bash
# 多客户端 + 服务器，完整测试
./Engine/Build/BatchFiles/Linux/RunUAT.sh RunUnreal \
    -platform=Linux \
    -build=editor \
    -nullrhi -unattended -nopause \
    -ResumeOnCriticalFailure=3 \
    -test="FullRegression(JUnitReportPath=junit.xml)"
```

### 发布前（性能回归）

```bash
# 性能测试 + 报告
./Engine/Build/BatchFiles/Linux/RunUAT.sh RunUnreal \
    -platform=Linux \
    -nullrhi -unattended \
    -test="PerformanceTest(ReportPath=reports/)"
```

---

## 常见问题

### 问题1：TestNode 未发现

**症状：**
```
Test node not found
```

**解决方案：**
1. 检查 `-scriptdir` 参数是否正确
2. 确保 `.Automation` 目录在 `Build/Scripts` 下
3. 查询知识库：`~/Documents/unreal_rag`

### 问题2：TestController 未加载

**症状：**
```
Test controller not loaded
```

**解决方案：**
1. 检查插件是否正确配置
2. 检查 `Configuration.TestController` 名称
3. 查询知识库：`~/Documents/unreal_rag`

### 问题3：超时误判

**症状：**
```
Test timeout but actually running
```

**解决方案：**
1. 确保每帧调用 `MarkHeartbeatActive()`
2. 增加 `MaxDuration`
3. 查询知识库：`~/Documents/unreal_rag`

---

## 知识库查询

遇到问题时，查询知识库：

```bash
# 编译错误
查询 ~/Documents/unreal_rag → "Gauntlet build error <关键词>"

# 参数问题
查询 ~/Documents/unreal_rag → "RunUAT RunUnreal parameters <参数名>"

# API 使用
查询 ~/Documents/unreal_rag → "UGauntletTestController <方法名>"
```

---

## 检查清单

### TestNode 检查

- [ ] 角色配置正确（Client/Server 数量）
- [ ] 超时设置合理（MaxDuration）
- [ ] CI 参数完整（-nullrhi -unattended -nopause）
- [ ] TestController 名称正确
- [ ] 脚本目录正确（-scriptdir）

### TestController 检查

- [ ] 生命周期回调实现完整
- [ ] 状态机逻辑正确
- [ ] 心跳调用到位（每帧）
- [ ] EndTest 调用正确（0=通过，非0=失败）
- [ ] 日志输出完整

### 运行检查

- [ ] 测试产物生成正确
- [ ] JUnit XML 格式正确
- [ ] 日志文件完整
- [ ] 截图/报告生成（如需）
