# 测试用例编写参考

## 测试框架配置

### Vitest 配置

```typescript
// vitest.config.ts

import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    exclude: ['node_modules', 'dist'],
    testTimeout: 10000,
    hookTimeout: 10000,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.d.ts',
        '**/*.config.*'
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80
      }
    }
  }
});
```

### package.json 脚本

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:unit": "vitest run tests/unit",
    "test:integration": "vitest run tests/integration",
    "test:coverage": "vitest run --coverage"
  }
}
```

---

## 单元测试模式

### 1. 函数测试

```typescript
import { describe, it, expect } from 'vitest';
import { add, subtract } from '../src/core/utils/math-utils';

describe('math-utils', () => {
  describe('add', () => {
    it('应该正确相加两个正数', () => {
      expect(add(2, 3)).toBe(5);
    });

    it('应该正确处理负数', () => {
      expect(add(-1, -2)).toBe(-3);
    });

    it('应该正确处理零', () => {
      expect(add(0, 5)).toBe(5);
      expect(add(5, 0)).toBe(5);
    });
  });

  describe('subtract', () => {
    it('应该正确相减', () => {
      expect(subtract(5, 3)).toBe(2);
    });
  });
});
```

### 2. 类测试

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { UserService } from '../src/modules/user/user-service';

describe('UserService', () => {
  let service: UserService;

  beforeEach(() => {
    service = new UserService();
  });

  describe('create', () => {
    it('应该创建用户', async () => {
      const result = await service.create({
        name: 'John',
        email: 'john@example.com'
      });

      expect(result.success).toBe(true);
      expect(result.data).toMatchObject({
        name: 'John',
        email: 'john@example.com'
      });
    });

    it('应该拒绝无效邮箱', async () => {
      const result = await service.create({
        name: 'John',
        email: 'invalid-email'
      });

      expect(result.success).toBe(false);
      expect(result.error?.code).toBe('INVALID_EMAIL');
    });
  });
});
```

### 3. 异步测试

```typescript
import { describe, it, expect } from 'vitest';
import { fetchData } from '../src/core/utils/http-utils';

describe('异步操作', () => {
  it('应该正确获取数据', async () => {
    const result = await fetchData('https://api.example.com/data');
    expect(result.success).toBe(true);
  });

  it('应该处理网络错误', async () => {
    const result = await fetchData('https://invalid-url');
    expect(result.success).toBe(false);
    expect(result.error?.code).toBe('NETWORK_ERROR');
  });

  it('应该处理超时', async () => {
    await expect(
      fetchData('https://slow-api.example.com', { timeout: 100 })
    ).rejects.toThrow('timeout');
  });
});
```

### 4. Mock 测试

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { OrderService } from '../src/modules/order/order-service';
import * as inventory from '../src/modules/inventory/inventory-service';

describe('OrderService with mocks', () => {
  let service: OrderService;

  beforeEach(() => {
    service = new OrderService();
    vi.clearAllMocks();
  });

  it('应该检查库存', async () => {
    // Mock 库存检查
    const checkStockSpy = vi.spyOn(inventory, 'checkStock')
      .mockResolvedValue({ available: 10, sufficient: true });

    const result = await service.create({
      items: [{ productId: 'P001', quantity: 5 }]
    });

    expect(checkStockSpy).toHaveBeenCalledWith('P001', 5);
    expect(result.success).toBe(true);
  });

  it('应该在库存不足时失败', async () => {
    vi.spyOn(inventory, 'checkStock')
      .mockResolvedValue({ available: 5, sufficient: false });

    const result = await service.create({
      items: [{ productId: 'P001', quantity: 10 }]
    });

    expect(result.success).toBe(false);
    expect(result.error?.code).toBe('OUT_OF_STOCK');
  });
});
```

---

## 集成测试模式

### 1. API 集成测试

```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { createServer } from '../src/server';
import { Server } from 'http';

describe('API 集成测试', () => {
  let server: Server;
  let baseUrl: string;

  beforeAll(async () => {
    server = await createServer(0); // 随机端口
    baseUrl = `http://localhost:${(server.address() as any).port}`;
  });

  afterAll(() => {
    server.close();
  });

  describe('GET /api/users', () => {
    it('应该返回用户列表', async () => {
      const response = await fetch(`${baseUrl}/api/users`);
      expect(response.status).toBe(200);

      const data = await response.json();
      expect(Array.isArray(data)).toBe(true);
    });
  });

  describe('POST /api/users', () => {
    it('应该创建用户', async () => {
      const response = await fetch(`${baseUrl}/api/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'John', email: 'john@example.com' })
      });

      expect(response.status).toBe(201);
      const data = await response.json();
      expect(data.id).toBeDefined();
    });
  });
});
```

### 2. 数据库集成测试

```typescript
import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { Database } from '../src/core/database';
import { UserRepository } from '../src/modules/user/user-repository';

describe('UserRepository 集成测试', () => {
  let db: Database;
  let repository: UserRepository;

  beforeAll(async () => {
    db = new Database(':memory:'); // 使用内存数据库
    await db.connect();
    repository = new UserRepository(db);
  });

  afterAll(async () => {
    await db.disconnect();
  });

  beforeEach(async () => {
    await db.clear(); // 每次测试前清空数据
  });

  it('应该创建并查找用户', async () => {
    const user = await repository.create({
      name: 'John',
      email: 'john@example.com'
    });

    const found = await repository.findById(user.id);
    expect(found).toMatchObject({
      name: 'John',
      email: 'john@example.com'
    });
  });
});
```

### 3. 冒烟测试套件

```typescript
import { describe, it, expect } from 'vitest';

describe('冒烟测试', () => {
  it('应用应该能启动', async () => {
    const { app } = await import('../src/app');
    expect(app).toBeDefined();
  });

  it('数据库应该能连接', async () => {
    const { db } = await import('../src/core/database');
    const connected = await db.ping();
    expect(connected).toBe(true);
  });

  it('配置应该有效', async () => {
    const { config } = await import('../src/core/config');
    expect(config.port).toBeDefined();
    expect(config.database).toBeDefined();
  });
});
```

---

## 测试工具函数

### 测试数据生成器

```typescript
// tests/helpers/fixtures.ts

export function createTestUser(overrides = {}) {
  return {
    id: 'test-user-id',
    name: 'Test User',
    email: 'test@example.com',
    createdAt: new Date().toISOString(),
    ...overrides
  };
}

export function createTestOrder(overrides = {}) {
  return {
    id: 'test-order-id',
    items: [
      { productId: 'P001', quantity: 1, price: 100 }
    ],
    status: 'pending',
    createdAt: new Date().toISOString(),
    ...overrides
  };
}
```

### Mock 工厂

```typescript
// tests/helpers/mocks.ts

import { vi } from 'vitest';

export function createMockLogger() {
  return {
    log: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
    error: vi.fn()
  };
}

export function createMockDatabase() {
  return {
    query: vi.fn(),
    execute: vi.fn(),
    transaction: vi.fn(),
    ping: vi.fn().mockResolvedValue(true)
  };
}
```

### 断言助手

```typescript
// tests/helpers/assertions.ts

import { expect } from 'vitest';

export function assertSuccess<T>(result: Result<T>): asserts result is { success: true; data: T } {
  expect(result.success).toBe(true);
  if (!result.success) {
    throw new Error(`Expected success but got error: ${result.error?.message}`);
  }
}

export function assertFailure<E>(result: Result<any, E>): asserts result is { success: false; error: E } {
  expect(result.success).toBe(false);
  if (result.success) {
    throw new Error('Expected failure but got success');
  }
}

// 使用
it('应该成功创建用户', async () => {
  const result = await service.create({ name: 'John' });
  assertSuccess(result);
  expect(result.data.id).toBeDefined();
});
```

---

## 测试覆盖率

### 覆盖率报告解读

```
 % Stmts   % Branch  % Funcs   % Lines
----------|----------|----------|----------|
   85.71 |    75.00 |   90.00 |    85.71 |
```

- **Statements (Stmts)**: 语句覆盖率
- **Branch**: 分支覆盖率（if/else, switch）
- **Functions**: 函数覆盖率
- **Lines**: 行覆盖率

### 提高覆盖率的技巧

1. **测试所有分支**

```typescript
// 源代码
function process(value: number): string {
  if (value < 0) return 'negative';
  if (value === 0) return 'zero';
  return 'positive';
}

// 测试 - 覆盖所有分支
it('应该处理负数', () => expect(process(-1)).toBe('negative'));
it('应该处理零', () => expect(process(0)).toBe('zero'));
it('应该处理正数', () => expect(process(1)).toBe('positive'));
```

2. **测试异常路径**

```typescript
it('应该在参数无效时抛出错误', () => {
  expect(() => process(null)).toThrow();
});
```

3. **测试边界条件**

```typescript
it('应该处理边界值', () => {
  expect(process(Number.MAX_SAFE_INTEGER)).toBeDefined();
  expect(process(Number.MIN_SAFE_INTEGER)).toBeDefined();
});
```

---

## 常见测试陷阱

### 1. 测试依赖顺序

```typescript
// ❌ 错误：测试依赖顺序
let user: User;

it('创建用户', async () => {
  user = await service.create({ name: 'John' });
});

it('更新用户', async () => {
  // 依赖上一个测试的 user
  await service.update(user.id, { name: 'Jane' });
});

// ✅ 正确：每个测试独立
it('更新用户', async () => {
  const user = await service.create({ name: 'John' });
  await service.update(user.id, { name: 'Jane' });
});
```

### 2. 异步未等待

```typescript
// ❌ 错误：未等待异步
it('应该创建用户', () => {
  service.create({ name: 'John' }); // 没有 await
  expect(database.insert).toHaveBeenCalled();
});

// ✅ 正确：等待异步
it('应该创建用户', async () => {
  await service.create({ name: 'John' });
  expect(database.insert).toHaveBeenCalled();
});
```

### 3. Mock 未清理

```typescript
// ❌ 错误：Mock 污染其他测试
it('测试A', () => {
  vi.spyOn(service, 'fetch').mockResolvedValue({ data: 'A' });
  // 没有清理
});

it('测试B', () => {
  // 可能使用测试A的 Mock
});

// ✅ 正确：使用 beforeEach 清理
beforeEach(() => {
  vi.clearAllMocks();
});
```
