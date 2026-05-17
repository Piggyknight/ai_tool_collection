# OpenSpec-cn v1.4.0 本地部署包

## 📦 包内容

```
openspec-cn-1.4.0/
├── bin/                    # 可执行文件
│   └── openspec.js        # 主程序入口
├── dist/                   # 编译输出
│   ├── *.js              # JavaScript文件
│   └── *.d.ts            # TypeScript类型定义
├── schemas/               # Schema定义
├── node_modules/          # 依赖包
├── package.json          # 包配置
├── package-lock.json     # 依赖锁定
├── README.md             # 使用说明
└── LICENSE               # 许可证
```

## 🚀 快速开始

### 方法1: 直接使用 (推荐)

```bash
# 进入部署包目录
cd openspec-cn-1.4.0

# 测试安装
node bin/openspec.js --version
# 应该输出: 1.4.0

# 测试新命令
node bin/openspec.js redmine --help
node bin/openspec.js sprint --help
```

### 方法2: 全局安装 (可选)

```bash
# 在项目根目录安装
npm install -g ./openspec-cn-1.4.0

# 现在可以在任何地方使用
openspec-cn --version
openspec-cn redmine --help
```

### 方法3: 作为项目依赖

```bash
# 在你的项目中安装
cd your-project
npm install ../openspec-cn-1.4.0

# 在package.json中添加脚本
{
  "scripts": {
    "review": "openspec-cn review change",
    "sprint": "openspec-cn sprint",
    "redmine": "openspec-cn redmine"
  }
}
```

## 🆕 新功能说明

### Redmine集成

#### 1. 配置Redmine
```bash
node bin/openspec.js redmine setup
```

#### 2. Sprint管理
```bash
# 创建Sprint
node bin/openspec.js sprint create sprint-v1.4 --due-date 2026-06-30

# 规划Sprint
node bin/openspec.js sprint plan sprint-v1.4

# 列出所有Sprint
node bin/openspec.js sprint list

# 关闭Sprint
node bin/openspec.js sprint close sprint-v1.4
```

#### 3. Story管理
```bash
# 拆分Story
node bin/openspec.js story breakdown sprint-v1.4 user-auth

# 完善Story
node bin/openspec.js story refine user-auth

# 列出Story
node bin/openspec.js story list
```

#### 4. Bug管理
```bash
# 创建Bug
node bin/openspec.js bug create "登录失败" --severity critical

# 更新Bug状态
node bin/openspec.js bug update 123 --status fixed

# 列出Bug
node bin/openspec.js bug list
```

#### 5. 任务同步
```bash
# 拆分任务
node bin/openspec.js task breakdown user-auth

# 同步进度
node bin/openspec.js task sync user-auth

# 显示状态
node bin/openspec.js task status user-auth
```

#### 6. 代码审查
```bash
# 审查单个变更
node bin/openspec.js review change user-auth --save

# 审查整个Sprint
node bin/openspec.js review sprint sprint-v1.4

# 同步审查结果到Redmine
node bin/openspec.js review change user-auth --sync
```

#### 7. Sprint总结生成
```bash
# 生成Sprint总结
node bin/openspec.js sprint-spec generate sprint-v1.4

# 上传到Redmine Wiki
node bin/openspec.js sprint-spec upload sprint-v1.4

# 列出所有spec
node bin/openspec.js sprint-spec list
```

## 🔧 环境要求

- **Node.js**: >=20.19.0
- **redmine-cli**: 需要在PATH中可用 (用于Redmine功能)
- **Git**: 用于版本控制和工作流

## 📋 配置文件

### 全局配置
```bash
# 查看配置
node bin/openspec.js config

# 修改配置
node bin/openspec.js config set ai-tool "claude"
```

### Redmine配置
```bash
# 设置Redmine
node bin/openspec.js redmine setup

# 测试连接
node bin/openspec.js redmine test

# 查看当前实例
node bin/openspec.js redmine current
```

## 🧪 测试

### 运行测试
```bash
# 在项目根目录
cd openspec-cn-1.4.0
npm test

# 特定模块测试
npm test -- test/core/redmine/
npm test -- test/core/code-review/
npm test -- test/core/spec/
```

### 功能测试
```bash
# 测试所有新命令
node bin/openspec.js redmine --help
node bin/openspec.js sprint --help
node bin/openspec.js story --help
node bin/openspec.js bug --help
node bin/openspec.js task --help
node bin/openspec.js review --help
node bin/openspec.js sprint-spec --help
```

## 📚 命令参考

### Redmine命令
```bash
openspec-cn redmine setup          # 设置Redmine集成
openspec-cn redmine list            # 列出配置的实例
openspec-cn redmine test            # 测试连接
openspec-cn redmine current         # 显示当前实例
```

### Sprint命令
```bash
openspec-cn sprint create <name>    # 创建Sprint
openspec-cn sprint list             # 列出Sprint
openspec-cn sprint plan <name>      # 规划Sprint
openspec-cn sprint close <name>     # 关闭Sprint
```

### Story命令
```bash
openspec-cn story breakdown <sprint> <change>  # 拆分Story
openspec-cn story refine <name>     # 完善Story
openspec-cn story list             # 列出Story
```

### Bug命令
```bash
openspec-cn bug create <title>      # 创建Bug
openspec-cn bug update <id>         # 更新Bug
openspec-cn bug list               # 列出Bug
```

### Task命令
```bash
openspec-cn task breakdown <name>  # 拆分任务
openspec-cn task sync <name>        # 同步进度
openspec-cn task status <name>      # 显示状态
```

### Review命令
```bash
openspec-cn review change <name>    # 审查变更
openspec-cn review sprint <name>    # 审查Sprint
```

### Sprint Spec命令
```bash
openspec-cn sprint-spec generate <sprint>  # 生成总结
openspec-cn sprint-spec upload <sprint>    # 上传到Redmine
openspec-cn sprint-spec list                # 列出所有spec
```

## 🎯 使用示例

### 完整的Sprint工作流

```bash
# 1. 配置Redmine
node bin/openspec.js redmine setup

# 2. 创建Sprint
node bin/openspec.js sprint create sprint-v1.4 --due-date 2026-06-30

# 3. 规划Sprint
node bin/openspec.js sprint plan sprint-v1.4

# 4. 开发过程中的任务同步
node bin/openspec.js task sync user-auth

# 5. 代码审查
node bin/openspec.js review change user-auth --sync

# 6. 生成Sprint总结
node bin/openspec.js sprint-spec generate sprint-v1.4

# 7. 关闭Sprint
node bin/openspec.js sprint close sprint-v1.4
```

### Bug管理工作流

```bash
# 1. 发现Bug
node bin/openspec.js bug create "用户无法登录" --severity critical

# 2. 修复Bug
# (代码开发过程...)

# 3. 更新Bug状态
node bin/openspec.js bug update 123 --status fixed

# 4. 验证Bug
node bin/openspec.js bug update 123 --status verified
```

## 🔍 故障排除

### 常见问题

1. **命令找不到**
   ```bash
   # 确保在正确的目录
   cd openspec-cn-1.4.0
   node bin/openspec.js --help
   ```

2. **依赖缺失**
   ```bash
   # 重新安装依赖
   npm install
   ```

3. **Redmine连接失败**
   ```bash
   # 检查redmine-cli是否可用
   red-cli --version
   
   # 测试连接
   node bin/openspec.js redmine test
   ```

4. **构建错误**
   ```bash
   # 重新构建
   npm run build
   ```

## 📞 支持

如遇问题，请查看：
- `README.md` - 完整使用说明
- `REDMINE_INTEGRATION_PROGRESS.md` - 功能开发进度
- 项目GitHub: https://github.com/studyzy/OpenSpec-cn

## 📝 更新日志

### v1.4.0 (2026-05-17)

**新增功能**:
- ✅ 完整的Redmine集成系统
- ✅ Sprint规划和管理
- ✅ Story管理
- ✅ Bug管理
- ✅ 任务同步
- ✅ 本地Code Review
- ✅ Sprint文档生成
- ✅ 多实例Redmine支持

**改进**:
- 🔄 扩展工作流支持Hermes 7状态模型
- 🔄 新增Sprint数据结构
- 🎯 72个单元测试覆盖核心功能

**修复**:
- 🐛 修复CLI命令注册冲突
- 🐛 修复构建依赖问题

---

*版本: 1.4.0*  
*发布日期: 2026-05-17*  
*包大小: ~200MB*