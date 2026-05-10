# 后端开发 Agent 工作流参考

## 触发条件

当架构师输出的任务包含以下关键词时，触发后端开发 Agent：

- "API"
- "后端"
- "数据库"
- "服务端"
- "RESTful"
- "认证"
- "微服务"

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    后端开发工作流                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 接收任务                                                 │
│     └─ 架构师输出后端 API 任务                               │
│         ↓                                                   │
│  2. 生成 API 架构文档                                        │
│     ├─ RESTful 接口定义                                      │
│     ├─ 数据模型设计                                          │
│     ├─ 安全设计                                              │
│     └─ 任务拆分                                              │
│         ↓                                                   │
│  3. 实现代码                                                 │
│     ├─ 数据模型 (SQLAlchemy)                                │
│     ├─ API 路由 (FastAPI)                                   │
│     ├─ 业务逻辑 (Service)                                   │
│     └─ 数据访问 (Repository)                                │
│         ↓                                                   │
│  4. 单元测试                                                 │
│     └─ pytest + coverage                                    │
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
  "type": "backend_api_task",
  "payload": {
    "task_id": "TASK-BE-001",
    "module": "用户服务",
    "endpoints": ["/api/users", "/api/auth"],
    "database": "PostgreSQL",
    "requirements": "实现用户认证和管理 API"
  }
}
```

### 输出 API 架构

```json
{
  "to": "project-manager",
  "type": "api_architecture",
  "payload": {
    "document": "docs/API架构文档.md",
    "task_breakdown": "docs/后端任务拆分.md",
    "total_tasks": 6,
    "estimated_hours": 16
  }
}
```

## 安全检查清单

### 认证与授权

- [ ] JWT Token 实现
- [ ] 密码 bcrypt 加密
- [ ] 权限验证中间件
- [ ] Token 刷新机制

### 数据安全

- [ ] SQL 注入防护（ORM）
- [ ] XSS 防护
- [ ] CSRF Token
- [ ] 敏感数据加密

### 输入验证

- [ ] 类型检查
- [ ] 长度限制
- [ ] 格式验证
- [ ] 必填字段检查

## 性能优化清单

### 数据库

- [ ] 索引设计
- [ ] 查询优化
- [ ] 连接池配置
- [ ] 事务管理

### 缓存

- [ ] Redis 缓存策略
- [ ] 缓存失效机制
- [ ] 热点数据缓存

### 异步

- [ ] Celery 任务队列
- [ ] 非阻塞 I/O
- [ ] 并发控制
