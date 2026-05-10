# Unreal Engine 最佳实践

## 性能优化

### 1. 组件优化

#### 减少不必要的Tick

```cpp
// ✅ 关闭不需要的Tick
AMyActor::AMyActor()
{
    PrimaryActorTick.bCanEverTick = false;  // 如果不需要每帧更新
}

// ✅ 使用定时器代替Tick
void AMyActor::BeginPlay()
{
    Super::BeginPlay();
    
    // 每0.5秒检查一次，而不是每帧
    GetWorld()->GetTimerManager().SetTimer(
        CheckTimerHandle,
        this,
        &AMyActor::OnPeriodicCheck,
        0.5f,
        true
    );
}
```

#### 按需启用Tick

```cpp
// ✅ 只在需要时启用Tick
void AMyActor::StartAction()
{
    SetActorTickEnabled(true);
}

void AMyActor::StopAction()
{
    SetActorTickEnabled(false);
}

void AMyActor::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    
    // 执行动作
    
    if (IsActionComplete())
    {
        SetActorTickEnabled(false);
    }
}
```

### 2. 内存优化

#### 使用弱引用避免循环引用

```cpp
// ✅ 使用弱引用
UPROPERTY()
TWeakObjectPtr<AActor> TargetActor;

// ❌ 避免强引用导致的循环引用
UPROPERTY()
AActor* TargetActor;  // 可能导致无法垃圾回收
```

#### 及时释放资源

```cpp
// ✅ 清空数组时使用Empty
void AMyActor::Cleanup()
{
    Actors.Empty();       // 清空并释放内存
    Actors.Reset();       // 清空但不释放内存（可能重用）
}

// ✅ 使用Shrink释放多余内存
TArray<int32> Numbers;
Numbers.Add(1);
Numbers.Add(2);
Numbers.Empty();  // 清空元素
Numbers.Shrink(); // 释放内存
```

### 3. 对象池

```cpp
// 对象池管理器
UCLASS()
class UObjectPool : public UObject
{
    GENERATED_BODY()
    
public:
    AActor* GetActor();
    void ReturnActor(AActor* Actor);
    
private:
    TArray<TWeakObjectPtr<AActor>> ActiveActors;
    TArray<TWeakObjectPtr<AActor>> InactiveActors;
};

AActor* UObjectPool::GetActor()
{
    // 从池中获取
    for (int32 i = InactiveActors.Num() - 1; i >= 0; --i)
    {
        if (AActor* Actor = InactiveActors[i].Get())
        {
            InactiveActors.RemoveAtSwap(i);
            ActiveActors.Add(Actor);
            Actor->SetActorHiddenInGame(false);
            return Actor;
        }
    }
    
    // 池中没有，创建新的
    return nullptr;
}

void UObjectPool::ReturnActor(AActor* Actor)
{
    Actor->SetActorHiddenInGame(true);
    
    ActiveActors.Remove(Actor);
    InactiveActors.Add(Actor);
}
```

---

## 内存管理

### 1. UObject生命周期

```cpp
// ✅ 让UE管理UObject生命周期
UPROPERTY()
UObject* MyObject;

// ✅ 使用NewObject创建
MyObject = NewObject<UMyObject>(this);

// ❌ 不要手动delete
delete MyObject;  // 错误！
```

### 2. 智能指针

```cpp
// ✅ 非UObject使用智能指针
TSharedPtr<FMyStruct> SharedData = MakeShareable(new FMyStruct());

// ✅ 使用弱指针避免循环引用
TWeakPtr<FMyStruct> WeakData = SharedData;

// ✅ 提升到共享指针后使用
if (TSharedPtr<FMyStruct> PinnedData = WeakData.Pin())
{
    PinnedData->DoSomething();
}
```

### 3. 避免内存泄漏

```cpp
// ✅ 绑定委托时记录句柄
FDelegateHandle Handle;
Handle = Component->OnEvent.AddUObject(this, &AMyActor::OnEvent);

// ✅ 销毁时移除委托
void AMyActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    Component->OnEvent.Remove(Handle);
    Super::EndPlay(EndPlayReason);
}
```

---

## 线程安全

### 1. 主线程限制

```cpp
// ⚠️ 大多数UE函数只能在游戏线程调用
void AMyActor::DoSomething()
{
    check(IsInGameThread());  // 断言在游戏线程
    
    // 安全操作
}
```

### 2. 异步操作

```cpp
// ✅ 使用AsyncTask
AsyncTask(ENamedThreads::GameThread, [this]()
{
    // 在游戏线程执行
    UpdateUI();
});

// ✅ 使用Async
TFuture<int32> Result = Async(EAsyncExecution::ThreadPool, []()
{
    // 在线程池执行
    return ExpensiveCalculation();
});

// 等待结果（会阻塞）
int32 Value = Result.Get();
```

### 3. 多线程安全

```cpp
// ✅ 使用FCriticalSection保护数据
FCriticalSection DataLock;
TArray<int32> SharedData;

void AddData(int32 Value)
{
    FScopeLock Lock(&DataLock);
    SharedData.Add(Value);
}
```

---

## 蓝图交互

### 1. 暴露给蓝图

```cpp
// ✅ 使用BlueprintCallable
UFUNCTION(BlueprintCallable, Category = "Health")
void TakeDamage(float Damage);

// ✅ 使用BlueprintPure（无副作用）
UFUNCTION(BlueprintPure, Category = "Health")
float GetCurrentHealth() const { return CurrentHealth; }

// ✅ 使用BlueprintImplementableEvent
UFUNCTION(BlueprintImplementableEvent, Category = "Health")
void OnDeath();

// ✅ 使用BlueprintNativeEvent
UFUNCTION(BlueprintNativeEvent, Category = "Health")
void OnDamageTaken(float Damage);
```

### 2. 分类组织

```cpp
// ✅ 使用Category组织
UCLASS()
class UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
    
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Health|Config")
    float MaxHealth;
    
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Health|Config")
    float Armor;
    
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Health|State")
    float CurrentHealth;
    
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Health|State")
    bool bIsDead;
};
```

### 3. 元数据提示

```cpp
// ✅ 使用meta提供额外信息
UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Health",
    meta = (ClampMin = "0.0", ClampMax = "1000.0", UIMin = "0.0", UIMax = "100.0"))
float MaxHealth;

// ✅ 条件显示
UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Health",
    meta = (EditCondition = "bIsRegenerating"))
float RegenerationRate;

UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Health")
bool bIsRegenerating;
```

---

## 调试技巧

### 1. 日志输出

```cpp
// ✅ 使用UE_LOG
UE_LOG(LogTemp, Log, TEXT("Health: %f"), CurrentHealth);
UE_LOG(LogTemp, Warning, TEXT("Low health warning!"));
UE_LOG(LogTemp, Error, TEXT("Character is dead!"));

// ✅ 定义日志类别
DECLARE_LOG_CATEGORY_EXTERN(LogHealth, Log, All);
DEFINE_LOG_CATEGORY(LogHealth);

UE_LOG(LogHealth, Log, TEXT("Health changed to %f"), CurrentHealth);
```

### 2. 可视化调试

```cpp
// ✅ 绘制调试线
DrawDebugLine(GetWorld(), Start, End, FColor::Red, true, 5.0f);

// ✅ 绘制调试球
DrawDebugSphere(GetWorld(), Center, Radius, 12, FColor::Green, true);

// ✅ 绘制调试文本
DrawDebugString(GetWorld(), Location, TEXT("Debug Text"), nullptr, FColor::White, 5.0f);
```

### 3. 断言

```cpp
// ✅ 使用check断言
check(Health >= 0.0f);  // 如果false，程序停止

// ✅ 使用ensure警告
ensure(Health <= MaxHealth);  // 如果false，继续运行但输出警告

// ✅ 使用ensureMsgf输出信息
ensureMsgf(Health > 0.0f, TEXT("Health should be positive! Current: %f"), Health);
```

---

## 常见陷阱

### 1. 空指针检查

```cpp
// ❌ 危险：可能空指针
AActor* Owner = GetOwner();
Owner->DoSomething();  // 可能崩溃！

// ✅ 安全：检查空指针
if (AActor* Owner = GetOwner())
{
    Owner->DoSomething();
}
```

### 2. 组件初始化顺序

```cpp
// ❌ 错误：在构造函数中访问其他组件
AMyActor::AMyActor()
{
    HealthComponent = CreateDefaultSubobject<UHealthComponent>(TEXT("Health"));
    
    // ❌ 错误！可能在构造函数中其他组件还未创建
    UActorComponent* Comp = FindComponentByClass<UActorComponent>();
}

// ✅ 正确：在BeginPlay中访问其他组件
void AMyActor::BeginPlay()
{
    Super::BeginPlay();
    
    // ✅ 现在所有组件都已创建
    UActorComponent* Comp = FindComponentByClass<UActorComponent>();
}
```

### 3. 依赖注入顺序

```cpp
// ❌ 错误：在构造函数中设置依赖
AMyActor::AMyActor()
{
    HealthComponent = CreateDefaultSubobject<UHealthComponent>(TEXT("Health"));
    HealthComponent->SetOwner(this);  // ❌ 此时this可能未完全构造
}

// ✅ 正确：在BeginPlay中设置依赖
void AMyActor::BeginPlay()
{
    Super::BeginPlay();
    
    if (HealthComponent)
    {
        HealthComponent->SetOwner(this);
    }
}
```

---

## 代码组织

### 1. 文件结构

```
Source/
├── Game/
│   ├── Public/              # 头文件
│   │   ├── Characters/
│   │   ├── Components/
│   │   └── Game/
│   └── Private/             # 实现文件
│       ├── Characters/
│       ├── Components/
│       └── Game/
```

### 2. 头文件包含顺序

```cpp
// 1. 预编译头文件（.cpp中）
#include "Game.h"

// 2. 对应的头文件
#include "MyCharacter.h"

// 3. 项目头文件
#include "Components/HealthComponent.h"
#include "GameFramework/PlayerController.h"

// 4. 引擎头文件
#include "Engine/World.h"
#include "DrawDebugHelpers.h"

// 5. .generated.h（头文件中，必须最后）
#include "MyCharacter.generated.h"
```

### 3. 命名空间

```cpp
// ✅ 使用命名空间组织工具类
namespace HealthUtils
{
    float CalculateDamage(float BaseDamage, float Armor);
    bool IsFatal(float CurrentHealth, float Damage);
}

// 使用
float Damage = HealthUtils::CalculateDamage(10.0f, 5.0f);
```

---

## 性能分析

### 1. 使用STAT组

```cpp
// 定义统计组
DECLARE_STATS_GROUP(TEXT("HealthSystem"), STATGROUP_Health, STATCAT_Advanced);

// 定义统计项
DECLARE_CYCLE_STAT(TEXT("TakeDamage"), STAT_TakeDamage, STATGROUP_Health);

void UHealthComponent::TakeDamage(float Damage)
{
    SCOPE_CYCLE_COUNTER(STAT_TakeDamage);
    
    // 伤害计算逻辑
}
```

### 2. 使用分析工具

```bash
# UE4分析工具
stat unit
stat fps
stat game
stat physics

# 内存分析
stat memory
obj list
memreport
```

---

## 总结清单

### 性能
- [ ] 关闭不必要的Tick
- [ ] 使用定时器代替高频Tick
- [ ] 使用对象池管理频繁创建/销毁的对象
- [ ] 避免每帧分配内存

### 内存
- [ ] 使用UPROPERTY防止垃圾回收
- [ ] 使用弱引用避免循环引用
- [ ] 及时释放不需要的资源
- [ ] 检查委托绑定是否正确移除

### 线程
- [ ] 确保在游戏线程操作UObject
- [ ] 使用AsyncTask处理异步操作
- [ ] 使用锁保护共享数据

### 蓝图
- [ ] 正确标记BlueprintCallable/BlueprintPure
- [ ] 使用Category组织属性和函数
- [ ] 使用meta提供编辑器提示

### 调试
- [ ] 使用UE_LOG输出日志
- [ ] 使用DrawDebug可视化
- [ ] 使用check/ensure断言

### 安全
- [ ] 检查所有指针是否为空
- [ ] 注意组件初始化顺序
- [ ] 避免构造函数中的依赖
