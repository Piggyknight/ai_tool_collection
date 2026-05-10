# 前端开发 Agent 工作流参考

## 触发条件

当架构师输出的任务包含以下关键词时，触发前端开发 Agent：

- "Web UI"
- "React"
- "前端页面"
- "组件"
- "用户界面"
- "Dashboard"
- "表单"

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    前端开发工作流                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 接收任务                                                 │
│     └─ 架构师输出 Web UI 任务                                │
│         ↓                                                   │
│  2. 生成 UI/UX 组件架构文档                                   │
│     ├─ 页面结构                                              │
│     ├─ 组件层级                                              │
│     ├─ 状态管理                                              │
│     └─ 任务拆分                                              │
│         ↓                                                   │
│  3. 实现组件                                                 │
│     ├─ 通用组件 (Button, Input, Modal...)                   │
│     ├─ 布局组件 (Header, Footer, Sidebar...)                │
│     └─ 业务组件 (具体功能)                                    │
│         ↓                                                   │
│  4. 单元测试                                                 │
│     └─ 使用 Jest + Testing Library                          │
│         ↓                                                   │
│  5. 交付 QA                                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 与项目经理的通信

### 接收任务

```json
{
  "from": "architect-agent",
  "type": "web_ui_task",
  "payload": {
    "task_id": "TASK-FE-001",
    "module": "用户管理",
    "pages": ["用户列表", "用户详情", "用户编辑"],
    "api_endpoints": ["/api/users", "/api/users/:id"],
    "requirements": "实现用户管理 CRUD 界面"
  }
}
```

### 输出组件架构

```json
{
  "to": "project-manager",
  "type": "ui_architecture",
  "payload": {
    "document": "docs/前端组件架构.md",
    "task_breakdown": "docs/前端任务拆分.md",
    "total_tasks": 8,
    "estimated_hours": 24
  }
}
```

## 代码规范

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件 | PascalCase | `Button`, `UserList` |
| Hook | camelCase + use | `useCounter`, `useAuth` |
| 工具函数 | camelCase | `formatDate`, `parseQuery` |
| 常量 | UPPER_SNAKE_CASE | `API_BASE_URL` |
| 类型 | PascalCase | `User`, `ButtonProps` |
| 文件 | PascalCase | `Button.tsx` |

### 文件组织

```
ComponentName/
├── ComponentName.tsx       # 组件实现
├── ComponentName.test.tsx  # 单元测试
├── ComponentName.styles.ts # 样式（如需要）
├── types.ts                # 类型定义（如需要）
├── hooks.ts                # 局部 Hooks（如需要）
└── index.ts                # 导出
```

## 测试规范

### 单元测试模板

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click event', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByText('Click me')).toBeDisabled();
  });
});
```
