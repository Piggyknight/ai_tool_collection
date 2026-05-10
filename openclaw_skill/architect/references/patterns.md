# 架构设计模式参考

## 常用架构模式

### 1. 分层架构（Layered Architecture）

```
┌─────────────────────────────────────┐
│         表现层 (Presentation)        │
├─────────────────────────────────────┤
│         业务层 (Business)            │
├─────────────────────────────────────┤
│         数据层 (Data Access)         │
└─────────────────────────────────────┘
```

**适用场景：** 传统 Web 应用、企业系统

### 2. 两层简化架构（本项目采用）

```
┌─────────────────────────────────────┐
│      业务逻辑层 (Business Layer)     │
│  • 组合工具实现业务流程               │
│  • 处理业务规则                      │
│  • 协调多个工具模块                   │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│      基础工具层 (Tool Layer)         │
│  • 单一职责、碎片化                   │
│  • 可独立单元测试                    │
│  • 与业务逻辑解耦                    │
└─────────────────────────────────────┘
```

**适用场景：** 中小型项目、快速迭代

---

## 目录结构模式

### 模式A：按层级分

```
src/
├── core/           # 下层：工具层
│   ├── utils/
│   ├── types/
│   └── constants/
├── modules/        # 上层：业务层
│   ├── user/
│   ├── order/
│   └── payment/
└── index.ts
```

### 模式B：按功能分

```
src/
├── tools/          # 下层：通用工具
│   ├── logger/
│   ├── validator/
│   └── http/
├── features/       # 上层：业务功能
│   ├── auth/
│   ├── product/
│   └── cart/
└── index.ts
```

### 模式C：混合模式（推荐）

```
src/
├── core/           # 下层：核心工具
│   ├── utils/      # 通用函数
│   ├── types/      # 类型定义
│   ├── errors/     # 错误处理
│   └── config/     # 配置管理
│
├── domain/         # 上层：业务领域
│   ├── shared/     # 共享业务逻辑
│   ├── module-a/   # 业务模块A
│   └── module-b/   # 业务模块B
│
└── index.ts        # 入口
```

---

## 模块设计模式

### 工具层模块模板

```typescript
// src/core/logger/index.ts

// 类型定义
export interface LogEntry {
  timestamp: string;
  level: 'log' | 'info' | 'warning' | 'error';
  module: string;
  message: string;
}

// 配置
export interface LoggerConfig {
  maxSize: number;
  maxFiles: number;
  outputPath: string;
}

// 主函数
export function createLogger(config: LoggerConfig): Logger {
  // 实现...
}

// 辅助类型
export interface Logger {
  log(module: string, message: string): void;
  info(module: string, message: string): void;
  warning(module: string, message: string): void;
  error(module: string, message: string): void;
}
```

### 业务层模块模板

```typescript
// src/domain/user/index.ts

import { createLogger, Logger } from '../../core/logger';
import { validateInput, ValidationResult } from '../../core/validator';

// 业务类型
export interface User {
  id: string;
  name: string;
  email: string;
}

export interface CreateUserInput {
  name: string;
  email: string;
}

// 业务服务
export class UserService {
  private logger: Logger;

  constructor() {
    this.logger = createLogger({ /* config */ });
  }

  async create(input: CreateUserInput): Promise<User> {
    // 1. 验证输入
    const validation = validateInput(input);
    if (!validation.valid) {
      throw new Error(validation.error);
    }

    // 2. 业务逻辑
    this.logger.info('UserService', `Creating user: ${input.name}`);

    // 3. 返回结果
    return { id: 'xxx', ...input };
  }
}
```

---

## 接口协议设计

### RESTful API 示例

```
POST /api/users
Content-Type: application/json

Request:
{
  "name": "string",
  "email": "string"
}

Response (201):
{
  "success": true,
  "data": {
    "id": "string",
    "name": "string",
    "email": "string"
  }
}

Response (400):
{
  "success": false,
  "error": {
    "code": "E001",
    "message": "Invalid email format"
  }
}
```

### 函数接口示例

```typescript
// 输入类型
interface CreateOrderInput {
  userId: string;
  items: Array<{
    productId: string;
    quantity: number;
  }>;
}

// 输出类型
interface CreateOrderOutput {
  orderId: string;
  totalAmount: number;
  status: 'pending' | 'paid' | 'shipped';
}

// 函数签名
function createOrder(input: CreateOrderInput): Promise<CreateOrderOutput>;
```

---

## 错误处理模式

### 错误码设计

```typescript
// src/core/errors/codes.ts

export enum ErrorCode {
  // 通用错误 1xxx
  UNKNOWN = 'E1000',
  INVALID_INPUT = 'E1001',
  NOT_FOUND = 'E1002',

  // 用户相关 2xxx
  USER_NOT_FOUND = 'E2001',
  USER_ALREADY_EXISTS = 'E2002',
  INVALID_EMAIL = 'E2003',

  // 订单相关 3xxx
  ORDER_NOT_FOUND = 'E3001',
  ORDER_ALREADY_PAID = 'E3002',
  OUT_OF_STOCK = 'E3003',
}

export interface AppError {
  code: ErrorCode;
  message: string;
  details?: Record<string, unknown>;
}
```

### 错误处理函数

```typescript
// src/core/errors/handler.ts

export function handleError(error: unknown): AppError {
  if (isAppError(error)) {
    return error;
  }

  return {
    code: ErrorCode.UNKNOWN,
    message: error instanceof Error ? error.message : 'Unknown error',
  };
}
```

---

## 技术选型参考

### 后端技术栈

| 场景 | 推荐技术 | 说明 |
|------|---------|------|
| Node.js 后端 | Express / Fastify | 成熟稳定 |
| TypeScript 后端 | NestJS / tRPC | 类型安全 |
| 数据库 | PostgreSQL / SQLite | 关系型 |
| 缓存 | Redis | 高性能 |
| 消息队列 | BullMQ | Node.js 原生 |

### 前端技术栈

| 场景 | 推荐技术 | 说明 |
|------|---------|------|
| Web 应用 | React / Vue | 主流框架 |
| 跨平台 | Electron / Tauri | 桌面应用 |
| 状态管理 | Zustand / Pinia | 轻量级 |

### 工具库

| 用途 | 推荐库 |
|------|-------|
| 日期处理 | dayjs / date-fns |
| 数据验证 | zod / yup |
| HTTP 客户端 | axios / ky |
| 日志 | pino / winston |
| 测试 | vitest / jest |
