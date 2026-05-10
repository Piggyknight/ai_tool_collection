# Unreal Engine 常用开发模式

## Actor-Component架构

### 基本概念

- **Actor**: 游戏世界中的对象容器
- **Component**: 实现具体功能的模块化组件
- **组合优于继承**: 通过组合组件实现复杂功能

### 创建自定义Actor

```cpp
// MyActor.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MyActor.generated.h"

UCLASS()
class GAME_API AMyActor : public AActor
{
    GENERATED_BODY()
    
public:
    AMyActor();
    
protected:
    virtual void BeginPlay() override;
    
public:
    virtual void Tick(float DeltaTime) override;
    
private:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
    USceneComponent* RootSceneComponent;
    
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (AllowPrivateAccess = "true"))
    UStaticMeshComponent* MeshComponent;
};
```

```cpp
// MyActor.cpp
#include "MyActor.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"

AMyActor::AMyActor()
{
    PrimaryActorTick.bCanEverTick = true;
    
    // 创建根组件
    RootSceneComponent = CreateDefaultSubobject<USceneComponent>(TEXT("RootComponent"));
    RootComponent = RootSceneComponent;
    
    // 创建网格组件
    MeshComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MeshComponent"));
    MeshComponent->SetupAttachment(RootComponent);
}

void AMyActor::BeginPlay()
{
    Super::BeginPlay();
}

void AMyActor::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
}
```

### 创建自定义Component

```cpp
// HealthComponent.h
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "HealthComponent.generated.h"

UCLASS(ClassGroup = "Health", meta = (BlueprintSpawnableComponent))
class GAME_API UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
    
public:
    UHealthComponent();
    
    UFUNCTION(BlueprintCallable, Category = "Health")
    void TakeDamage(float Damage);
    
    UFUNCTION(BlueprintPure, Category = "Health")
    float GetCurrentHealth() const { return CurrentHealth; }
    
    UFUNCTION(BlueprintPure, Category = "Health")
    bool IsAlive() const { return !bIsDead; }
    
protected:
    virtual void BeginPlay() override;
    
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Health|Config")
    float MaxHealth = 100.0f;
    
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Health|State")
    float CurrentHealth;
    
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Health|State")
    bool bIsDead;
    
private:
    void Die();
};
```

```cpp
// HealthComponent.cpp
#include "HealthComponent.h"

UHealthComponent::UHealthComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UHealthComponent::BeginPlay()
{
    Super::BeginPlay();
    CurrentHealth = MaxHealth;
}

void UHealthComponent::TakeDamage(float Damage)
{
    if (bIsDead) return;
    
    CurrentHealth = FMath::Clamp(CurrentHealth - Damage, 0.0f, MaxHealth);
    
    if (CurrentHealth <= 0.0f)
    {
        Die();
    }
}

void UHealthComponent::Die()
{
    bIsDead = true;
}
```

---

## Subsystem使用模式

### Subsystem简介

- 全局或局部的管理对象
- 生命周期由引擎管理
- 适合单例模式的功能

### 创建WorldSubsystem

```cpp
// HealthSubsystem.h
#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "HealthSubsystem.generated.h"

UCLASS()
class GAME_API UHealthSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()
    
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;
    
    UFUNCTION(BlueprintCallable, Category = "Health")
    void RegisterDamageEvent(AActor* DamagedActor, float Damage);
    
    UFUNCTION(BlueprintPure, Category = "Health")
    float GetTotalDamageDealt() const { return TotalDamageDealt; }
    
private:
    float TotalDamageDealt = 0.0f;
    TArray<TWeakObjectPtr<AActor>> TrackedActors;
};
```

```cpp
// HealthSubsystem.cpp
#include "HealthSubsystem.h"

void UHealthSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    
    // 初始化逻辑
    TotalDamageDealt = 0.0f;
}

void UHealthSubsystem::Deinitialize()
{
    // 清理逻辑
    TrackedActors.Empty();
    
    Super::Deinitialize();
}

void UHealthSubsystem::RegisterDamageEvent(AActor* DamagedActor, float Damage)
{
    TotalDamageDealt += Damage;
    
    // 记录受伤Actor
    if (DamagedActor && !TrackedActors.Contains(DamagedActor))
    {
        TrackedActors.Add(DamagedActor);
    }
}
```

### 使用Subsystem

```cpp
// 在其他代码中访问Subsystem
void AMyCharacter::TakeDamage(float Damage)
{
    Super::TakeDamage(Damage);
    
    // 获取WorldSubsystem
    if (UWorld* World = GetWorld())
    {
        if (UHealthSubsystem* HealthSubsystem = World->GetSubsystem<UHealthSubsystem>())
        {
            HealthSubsystem->RegisterDamageEvent(this, Damage);
        }
    }
}
```

---

## 委托与事件

### 声明委托

```cpp
// HealthComponent.h

// 声明委托类型
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnHealthChanged, float, CurrentHealth, float, Damage);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnDeath);

UCLASS(ClassGroup = "Health", meta = (BlueprintSpawnableComponent))
class GAME_API UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
    
public:
    // 委托属性
    UPROPERTY(BlueprintAssignable, Category = "Health")
    FOnHealthChanged OnHealthChanged;
    
    UPROPERTY(BlueprintAssignable, Category = "Health")
    FOnDeath OnDeath;
    
    UFUNCTION(BlueprintCallable, Category = "Health")
    void TakeDamage(float Damage);
};
```

### 广播委托

```cpp
// HealthComponent.cpp
void UHealthComponent::TakeDamage(float Damage)
{
    if (bIsDead) return;
    
    CurrentHealth = FMath::Clamp(CurrentHealth - Damage, 0.0f, MaxHealth);
    
    // 广播生命值改变事件
    OnHealthChanged.Broadcast(CurrentHealth, Damage);
    
    if (CurrentHealth <= 0.0f)
    {
        Die();
    }
}

void UHealthComponent::Die()
{
    bIsDead = true;
    
    // 广播死亡事件
    OnDeath.Broadcast();
}
```

### 绑定委托

```cpp
// 在其他类中绑定委托
void AMyCharacter::BeginPlay()
{
    Super::BeginPlay();
    
    if (UHealthComponent* HealthComp = FindComponentByClass<UHealthComponent>())
    {
        // C++绑定
        HealthComp->OnHealthChanged.AddDynamic(this, &AMyCharacter::OnHealthChanged);
        HealthComp->OnDeath.AddDynamic(this, &AMyCharacter::OnDeath);
    }
}

void AMyCharacter::OnHealthChanged(float CurrentHealth, float Damage)
{
    UE_LOG(LogTemp, Log, TEXT("Health changed: %f, Damage: %f"), CurrentHealth, Damage);
}

void AMyCharacter::OnDeath()
{
    UE_LOG(LogTemp, Log, TEXT("Character died"));
}
```

---

## 智能指针使用

### UE智能指针类型

- `TSharedPtr` - 共享指针
- `TWeakPtr` - 弱指针
- `TUniquePtr` - 唯一指针
- `TSharedRef` - 共享引用（不能为空）

### 使用示例

```cpp
// 声明智能指针
TSharedPtr<FMyData> SharedData;
TWeakPtr<FMyData> WeakData;
TUniquePtr<FMyData> UniqueData;

// 创建共享指针
SharedData = MakeShareable(new FMyData());

// 创建弱指针
WeakData = SharedData;

// 创建唯一指针
UniqueData = MakeUnique<FMyData>();

// 检查有效性
if (SharedData.IsValid())
{
    SharedData->DoSomething();
}

// 从弱指针提升到共享指针
if (TSharedPtr<FMyData> PinnedData = WeakData.Pin())
{
    PinnedData->DoSomething();
}

// 重置
SharedData.Reset();
UniqueData.Reset();
```

### 与UObject的交互

```cpp
// UObject使用TWeakObjectPtr（不是TWeakPtr）
TWeakObjectPtr<AActor> WeakActor;

// 获取UObject
if (AActor* Actor = WeakActor.Get())
{
    Actor->DoSomething();
}

// 或者使用UPROPERTY的弱引用
UPROPERTY()
TWeakObjectPtr<AActor> WeakActorRef;
```

---

## 定时器使用

### 设置定时器

```cpp
// HealthComponent.h
UCLASS()
class UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
    
public:
    UFUNCTION(BlueprintCallable, Category = "Health")
    void StartRegeneration(float Rate);
    
    UFUNCTION(BlueprintCallable, Category = "Health")
    void StopRegeneration();
    
private:
    FTimerHandle RegenerationTimerHandle;
    
    UFUNCTION()
    void OnRegenerate();
};
```

```cpp
// HealthComponent.cpp
#include "HealthComponent.h"

void UHealthComponent::StartRegeneration(float Rate)
{
    // 设置定时器，每Rate秒调用一次
    GetWorld()->GetTimerManager().SetTimer(
        RegenerationTimerHandle,
        this,
        &UHealthComponent::OnRegenerate,
        Rate,
        true  // 循环
    );
}

void UHealthComponent::StopRegeneration()
{
    GetWorld()->GetTimerManager().ClearTimer(RegenerationTimerHandle);
}

void UHealthComponent::OnRegenerate()
{
    if (bIsDead) return;
    
    CurrentHealth = FMath::Clamp(CurrentHealth + 1.0f, 0.0f, MaxHealth);
    
    if (CurrentHealth >= MaxHealth)
    {
        StopRegeneration();
    }
}
```

---

## 数据表和数据资产

### 使用数据表

```cpp
// 定义结构体
USTRUCT(BlueprintType)
struct FWeaponData : public FTableRowBase
{
    GENERATED_BODY()
    
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FName WeaponName;
    
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float Damage = 10.0f;
    
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float AttackSpeed = 1.0f;
    
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    int32 Cost = 100;
};

// 使用数据表
UCLASS()
class AWeaponManager : public AActor
{
    GENERATED_BODY()
    
public:
    UFUNCTION(BlueprintCallable, Category = "Weapon")
    FWeaponData GetWeaponData(FName WeaponID);
    
private:
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon", meta = (AllowPrivateAccess = "true"))
    UDataTable* WeaponDataTable;
};
```

```cpp
// WeaponManager.cpp
#include "WeaponManager.h"
#include "Engine/DataTable.h"

FWeaponData AWeaponManager::GetWeaponData(FName WeaponID)
{
    if (WeaponDataTable)
    {
        if (FWeaponData* Data = WeaponDataTable->FindRow<FWeaponData>(WeaponID, TEXT("")))
        {
            return *Data;
        }
    }
    
    return FWeaponData();
}
```

---

## 接口使用

### 定义接口

```cpp
// DamageableInterface.h
#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "DamageableInterface.generated.h"

// 必须在.generated.h之前
UINTERFACE(MinimalAPI)
class UDamageableInterface : public UInterface
{
    GENERATED_BODY()
};

class GAME_API IDamageableInterface
{
    GENERATED_BODY()
    
public:
    UFUNCTION(BlueprintNativeEvent, Category = "Damage")
    void TakeDamage(float Damage);
    virtual void TakeDamage_Implementation(float Damage) = 0;
    
    UFUNCTION(BlueprintNativeEvent, Category = "Damage")
    bool IsAlive() const;
    virtual bool IsAlive_Implementation() const = 0;
};
```

### 实现接口

```cpp
// MyCharacter.h
#include "DamageableInterface.h"

UCLASS()
class GAME_API AMyCharacter : public ACharacter, public IDamageableInterface
{
    GENERATED_BODY()
    
public:
    // 接口实现
    virtual void TakeDamage_Implementation(float Damage) override;
    virtual bool IsAlive_Implementation() const override;
    
private:
    float Health = 100.0f;
};
```

```cpp
// MyCharacter.cpp
void AMyCharacter::TakeDamage_Implementation(float Damage)
{
    Health -= Damage;
    
    if (Health <= 0.0f)
    {
        // 死亡处理
    }
}

bool AMyCharacter::IsAlive_Implementation() const
{
    return Health > 0.0f;
}
```

### 使用接口

```cpp
// 检查并调用接口
if (IDamageableInterface* Damageable = Cast<IDamageableInterface>(TargetActor))
{
    Damageable->TakeDamage(10.0f);
    
    if (Damageable->IsAlive())
    {
        // 目标仍然存活
    }
}
```

---

## 网络同步基础

### 复制属性

```cpp
// HealthComponent.h
UCLASS()
class UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
    
public:
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    
private:
    UPROPERTY(Replicated, VisibleAnywhere, BlueprintReadOnly, Category = "Health", meta = (AllowPrivateAccess = "true"))
    float CurrentHealth;
    
    UPROPERTY(ReplicatedUsing = OnRep_IsDead, VisibleAnywhere, BlueprintReadOnly, Category = "Health", meta = (AllowPrivateAccess = "true"))
    bool bIsDead;
    
    UFUNCTION()
    void OnRep_IsDead();
};
```

```cpp
// HealthComponent.cpp
#include "HealthComponent.h"
#include "Net/UnrealNetwork.h"

void UHealthComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    
    // 复制当前生命值
    DOREPLIFETIME(UHealthComponent, CurrentHealth);
    
    // 只复制给所有者
    DOREPLIFETIME_CONDITION(UHealthComponent, bIsDead, COND_OwnerOnly);
}

void UHealthComponent::OnRep_IsDead()
{
    // 当bIsDead在客户端改变时调用
    if (bIsDead)
    {
        // 播放死亡动画等
    }
}
```

### RPC函数

```cpp
// HealthComponent.h
UCLASS()
class UHealthComponent : public UActorComponent
{
    GENERATED_BODY()
    
public:
    // 服务器调用
    UFUNCTION(BlueprintCallable, Category = "Health")
    void TakeDamage(float Damage);
    
    // 在服务器上执行
    UFUNCTION(Server, Reliable)
    void ServerTakeDamage(float Damage);
    
    // 在所有客户端上执行
    UFUNCTION(NetMulticast, Reliable)
    void MulticastOnDeath();
};
```

```cpp
// HealthComponent.cpp
void UHealthComponent::TakeDamage(float Damage)
{
    if (GetOwner()->GetLocalRole() < ROLE_Authority)
    {
        // 客户端调用服务器
        ServerTakeDamage(Damage);
        return;
    }
    
    // 服务器逻辑
    CurrentHealth = FMath::Clamp(CurrentHealth - Damage, 0.0f, MaxHealth);
    
    if (CurrentHealth <= 0.0f)
    {
        MulticastOnDeath();
    }
}

void UHealthComponent::ServerTakeDamage_Implementation(float Damage)
{
    TakeDamage(Damage);
}

void UHealthComponent::MulticastOnDeath_Implementation()
{
    // 在所有客户端上执行
    // 播放死亡动画、音效等
}
```

---

## 总结

| 模式 | 使用场景 |
|------|---------|
| Actor-Component | 模块化功能组合 |
| Subsystem | 全局/局部单例管理 |
| 委托与事件 | 解耦的事件通知 |
| 智能指针 | 非UObject内存管理 |
| 定时器 | 延迟/循环执行 |
| 数据表 | 配置数据管理 |
| 接口 | 多态行为定义 |
| 网络同步 | 多人游戏 |
