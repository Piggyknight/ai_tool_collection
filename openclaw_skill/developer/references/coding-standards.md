# 开发者编码规范参考

## TypeScript 编码规范

### 1. 类型定义

```typescript
// ✅ 推荐：使用 interface 定义对象类型
interface User {
  id: string;
  name: string;
  email: string;
}

// ✅ 推荐：使用 type 定义联合类型、工具类型
type Status = 'pending' | 'active' | 'completed';
type PartialUser = Partial<User>;

// ✅ 推荐：泛型约束
interface Result<T, E = Error> {
  success: boolean;
  data?: T;
  error?: E;
}

// ❌ 避免：过度使用 any
function process(data: any): any { } // 不要这样
```

### 2. 函数设计

```typescript
// ✅ 推荐：纯函数，无副作用
export function add(a: number, b: number): number {
  return a + b;
}

// ✅ 推荐：单一职责
export function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function validatePassword(password: string): boolean {
  return password.length >= 8;
}

// ✅ 推荐：参数对象化（超过3个参数时）
interface CreateOrderOptions {
  userId: string;
  items: OrderItem[];
  couponCode?: string;
}

export function createOrder(options: CreateOrderOptions): Order {
  // ...
}

// ❌ 避免：参数过多
export function createOrder(
  userId: string,
  items: OrderItem[],
  couponCode: string,
  shippingAddress: Address,
  billingAddress: Address,
  notes: string
): Order { } // 不要这样
```

### 3. 错误处理

```typescript
// ✅ 推荐：Result 模式
export function parseJson<T>(text: string): Result<T> {
  try {
    const data = JSON.parse(text) as T;
    return { success: true, data };
  } catch (error) {
    return {
      success: false,
      error: {
        code: 'PARSE_ERROR',
        message: (error as Error).message
      }
    };
  }
}

// ✅ 推荐：自定义错误类
export class AppError extends Error {
  constructor(
    public code: string,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'AppError';
  }
}

// 使用
throw new AppError('USER_NOT_FOUND', 'User does not exist', { userId: '123' });

// ❌ 避免：捕获后不处理
try {
  doSomething();
} catch (e) {
  // 什么都不做 - 隐藏了错误
}
```

### 4. 异步处理

```typescript
// ✅ 推荐：async/await
export async function fetchUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) {
    throw new AppError('FETCH_FAILED', `HTTP ${response.status}`);
  }
  return response.json();
}

// ✅ 推荐：Promise 并行
export async function fetchUsers(ids: string[]): Promise<User[]> {
  const promises = ids.map(id => fetchUser(id));
  return Promise.all(promises);
}

// ✅ 推荐：错误边界
export async function safeFetchUser(id: string): Promise<Result<User>> {
  try {
    const user = await fetchUser(id);
    return { success: true, data: user };
  } catch (error) {
    return {
      success: false,
      error: {
        code: 'FETCH_ERROR',
        message: (error as Error).message
      }
    };
  }
}
```

### 5. 模块导出

```typescript
// ✅ 推荐：命名导出
export function formatDate(date: Date): string { }
export function parseDate(str: string): Date { }
export type DateFormat = 'iso' | 'locale';

// ✅ 推荐：index.ts 统一导出
// src/core/utils/index.ts
export * from './date-utils';
export * from './id-utils';
export * from './string-utils';

// ✅ 推荐：类型与实现分离
// types.ts
export interface User { }

// user-service.ts
import { User } from './types';
export class UserService { }
```

---

## 目录结构规范

### 工具层目录结构

```
src/core/
├── utils/
│   ├── date-utils.ts      # 日期工具
│   ├── id-utils.ts        # ID生成工具
│   ├── string-utils.ts    # 字符串工具
│   └── index.ts           # 统一导出
├── types/
│   ├── result.ts          # Result 类型
│   ├── common.ts          # 通用类型
│   └── index.ts
├── errors/
│   ├── codes.ts           # 错误码定义
│   ├── app-error.ts       # 错误类
│   └── index.ts
└── config/
    ├── constants.ts       # 常量定义
    └── index.ts
```

### 业务层目录结构

```
src/modules/
├── shared/                # 共享业务逻辑
│   └── auth/
├── user/                  # 用户模块
│   ├── types.ts
│   ├── user-service.ts
│   ├── user-repository.ts
│   └── index.ts
├── order/                 # 订单模块
│   ├── types.ts
│   ├── order-service.ts
│   ├── order-repository.ts
│   └── index.ts
└── index.ts
```

---

## 注释规范

### 函数注释

```typescript
/**
 * 格式化日期为指定格式
 *
 * @param date - 要格式化的日期对象
 * @param options - 格式化选项
 * @param options.format - 格式类型：'iso' | 'locale' | 'custom'
 * @param options.pattern - 自定义格式模式（当 format 为 'custom' 时使用）
 * @returns 格式化后的日期字符串
 * @throws {TypeError} 当 date 为 null 或 undefined 时
 *
 * @example
 * ```typescript
 * formatDate(new Date(), { format: 'iso' });
 * // => '2026-02-20T08:30:00.000Z'
 *
 * formatDate(new Date(), { format: 'custom', pattern: 'YYYY-MM-DD' });
 * // => '2026-02-20'
 * ```
 */
export function formatDate(date: Date, options: FormatOptions): string {
  // ...
}
```

### 类注释

```typescript
/**
 * 用户服务
 *
 * 负责用户相关的业务逻辑，包括创建、查询、更新用户等操作。
 *
 * @example
 * ```typescript
 * const userService = new UserService(userRepository);
 * const user = await userService.create({ name: 'John', email: 'john@example.com' });
 * ```
 */
export class UserService {
  // ...
}
```

### 行内注释

```typescript
export function calculateTotal(items: OrderItem[]): number {
  let total = 0;

  for (const item of items) {
    // 计算单品小计：单价 × 数量
    const subtotal = item.price * item.quantity;
    total += subtotal;
  }

  // 应用折扣：总价 × 0.9（10% off）
  return total * 0.9;
}
```

---

## 常见代码模式

### 单例模式

```typescript
// 推荐使用模块级别的单例
let instance: Logger | null = null;

export function getLogger(): Logger {
  if (!instance) {
    instance = new Logger();
  }
  return instance;
}
```

### 工厂模式

```typescript
export interface Storage {
  get(key: string): unknown;
  set(key: string, value: unknown): void;
}

export function createStorage(type: 'memory' | 'file'): Storage {
  switch (type) {
    case 'memory':
      return new MemoryStorage();
    case 'file':
      return new FileStorage();
    default:
      throw new Error(`Unknown storage type: ${type}`);
  }
}
```

### 策略模式

```typescript
export type PaymentStrategy = {
  pay(amount: number): Promise<PaymentResult>;
};

export class PaymentService {
  constructor(private strategy: PaymentStrategy) {}

  async processPayment(amount: number): Promise<PaymentResult> {
    return this.strategy.pay(amount);
  }
}

// 使用
const creditCardStrategy: PaymentStrategy = {
  async pay(amount) {
    // 信用卡支付逻辑
  }
};

const service = new PaymentService(creditCardStrategy);
```

### 观察者模式

```typescript
type EventCallback<T> = (data: T) => void;

export class EventEmitter<T extends Record<string, unknown>> {
  private listeners = new Map<keyof T, Set<EventCallback<unknown>>>();

  on<K extends keyof T>(event: K, callback: EventCallback<T[K]>): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback as EventCallback<unknown>);
  }

  emit<K extends keyof T>(event: K, data: T[K]): void {
    const callbacks = this.listeners.get(event);
    callbacks?.forEach(cb => cb(data));
  }
}
```

---

## 性能优化建议

### 1. 避免不必要的计算

```typescript
// ❌ 避免：每次调用都重新计算
function getConfig() {
  return JSON.parse(fs.readFileSync('config.json', 'utf-8'));
}

// ✅ 推荐：缓存结果
let cachedConfig: Config | null = null;

function getConfig(): Config {
  if (!cachedConfig) {
    cachedConfig = JSON.parse(fs.readFileSync('config.json', 'utf-8'));
  }
  return cachedConfig;
}
```

### 2. 批量操作

```typescript
// ❌ 避免：循环中单独操作
for (const user of users) {
  await database.insert(user);
}

// ✅ 推荐：批量操作
await database.insertMany(users);
```

### 3. 懒加载

```typescript
// ✅ 推荐：按需加载
let heavyModule: HeavyModule | null = null;

export async function getHeavyModule(): Promise<HeavyModule> {
  if (!heavyModule) {
    const module = await import('./heavy-module');
    heavyModule = new module.HeavyModule();
  }
  return heavyModule;
}
```
