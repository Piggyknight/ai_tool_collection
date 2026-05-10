# 日志工具实现参考

## 完整 Logger 实现

### TypeScript 版本

```typescript
// src/core/logger/index.ts

import fs from 'fs';
import path from 'path';

export type LogLevel = 'log' | 'info' | 'warning' | 'error';

export interface LoggerConfig {
  maxFileSize: number;    // 单文件最大大小 (字节)
  maxFiles: number;       // 最大文件数
  outputPath: string;     // 日志目录
  enabled: boolean;       // 是否启用
  minLevel: LogLevel;     // 最低日志级别
}

const DEFAULT_CONFIG: LoggerConfig = {
  maxFileSize: 100 * 1024 * 1024,  // 100MB
  maxFiles: 10,
  outputPath: './logs',
  enabled: true,
  minLevel: 'log'
};

const LEVEL_PRIORITY: Record<LogLevel, number> = {
  log: 0,
  info: 1,
  warning: 2,
  error: 3
};

export class Logger {
  private config: LoggerConfig;
  private currentFile: string;
  private currentSize: number = 0;
  private initialized: boolean = false;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.currentFile = '';
    this.init();
  }

  private init(): void {
    if (!this.config.enabled) return;

    // 确保日志目录存在
    if (!fs.existsSync(this.config.outputPath)) {
      fs.mkdirSync(this.config.outputPath, { recursive: true });
    }

    // 查找或创建当前日志文件
    this.currentFile = this.findOrCreateLogFile();
    this.currentSize = this.getFileSize(this.currentFile);
    this.initialized = true;
  }

  private findOrCreateLogFile(): string {
    const files = this.getLogFiles();

    if (files.length > 0) {
      const latest = files[files.length - 1];
      const latestPath = path.join(this.config.outputPath, latest);
      if (this.getFileSize(latestPath) < this.config.maxFileSize) {
        return latestPath;
      }
    }

    return this.generateFileName();
  }

  private generateFileName(): string {
    const timestamp = new Date().toISOString()
      .replace(/[:.]/g, '-')
      .slice(0, 19);
    return path.join(this.config.outputPath, `debug_${timestamp}.log`);
  }

  private getLogFiles(): string[] {
    if (!fs.existsSync(this.config.outputPath)) return [];

    return fs.readdirSync(this.config.outputPath)
      .filter(f => f.startsWith('debug_') && f.endsWith('.log'))
      .sort();
  }

  private getFileSize(filePath: string): number {
    try {
      return fs.statSync(filePath).size;
    } catch {
      return 0;
    }
  }

  private formatTimestamp(): string {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const ms = String(now.getMilliseconds()).padStart(3, '0');

    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}:${ms}`;
  }

  private formatMessage(level: LogLevel, module: string, message: string): string {
    const timestamp = this.formatTimestamp();
    return `[${timestamp}][${level}][${module}] ${message}`;
  }

  private shouldLog(level: LogLevel): boolean {
    if (!this.config.enabled || !this.initialized) return false;
    return LEVEL_PRIORITY[level] >= LEVEL_PRIORITY[this.config.minLevel];
  }

  private write(level: LogLevel, module: string, message: string): void {
    if (!this.shouldLog(level)) return;

    const line = this.formatMessage(level, module, message);
    const lineSize = Buffer.byteLength(line + '\n', 'utf-8');

    this.checkRotation(lineSize);
    fs.appendFileSync(this.currentFile, line + '\n', 'utf-8');
    this.currentSize += lineSize;
  }

  private checkRotation(lineSize: number): void {
    if (this.currentSize + lineSize > this.config.maxFileSize) {
      this.rotateFile();
    }
  }

  private rotateFile(): void {
    this.cleanOldFiles();
    this.currentFile = this.generateFileName();
    this.currentSize = 0;
  }

  private cleanOldFiles(): void {
    const files = this.getLogFiles();

    while (files.length >= this.config.maxFiles) {
      const oldest = files.shift();
      if (oldest) {
        const filePath = path.join(this.config.outputPath, oldest);
        try {
          fs.unlinkSync(filePath);
        } catch (e) {
          // 忽略删除失败
        }
      }
    }
  }

  // 公共 API
  log(module: string, message: string): void {
    this.write('log', module, message);
  }

  info(module: string, message: string): void {
    this.write('info', module, message);
  }

  warning(module: string, message: string): void {
    this.write('warning', module, message);
  }

  error(module: string, message: string): void {
    this.write('error', module, message);
  }
}

// 全局单例
let globalLogger: Logger | null = null;

export function getLogger(config?: Partial<LoggerConfig>): Logger {
  if (!globalLogger) {
    globalLogger = new Logger(config);
  }
  return globalLogger;
}

export const logger = new Logger();
```

---

## 日志嵌入模板

### 工具层模块

```typescript
import { logger } from '../../core/logger';

const MODULE_NAME = '[模块名]';

export function someFunction(input: SomeType): Result<OutputType> {
  logger.info(MODULE_NAME, `开始处理, input=${JSON.stringify(input)}`);

  try {
    // 验证输入
    logger.log(MODULE_NAME, `验证输入参数`);
    if (!validateInput(input)) {
      logger.warning(MODULE_NAME, `输入验证失败`);
      return failure('INVALID_INPUT', '输入参数无效');
    }

    // 处理逻辑
    logger.log(MODULE_NAME, `执行核心逻辑`);
    const result = processLogic(input);

    logger.info(MODULE_NAME, `处理完成, result=${JSON.stringify(result)}`);
    return success(result);

  } catch (error) {
    logger.error(MODULE_NAME, `处理失败: ${(error as Error).message}`);
    return failure('PROCESS_ERROR', (error as Error).message);
  }
}
```

### 业务层模块

```typescript
import { logger } from '../../core/logger';

const MODULE_NAME = '[ServiceName]Service';

export class SomeService {
  async execute(input: InputType): Promise<Result<OutputType>> {
    logger.info(MODULE_NAME, `开始执行, input=${JSON.stringify(input)}`);

    try {
      // 步骤1
      logger.log(MODULE_NAME, `执行步骤1: 数据验证`);
      await this.step1(input);

      // 步骤2
      logger.log(MODULE_NAME, `执行步骤2: 业务处理`);
      const result = await this.step2(input);

      logger.info(MODULE_NAME, `执行成功`);
      return success(result);

    } catch (error) {
      logger.error(MODULE_NAME, `执行失败: ${(error as Error).message}`);
      return failure('EXECUTE_ERROR', (error as Error).message);
    }
  }

  private async step1(input: InputType): Promise<void> {
    logger.log(MODULE_NAME, `step1: 开始`);
    // ...
    logger.log(MODULE_NAME, `step1: 完成`);
  }

  private async step2(input: InputType): Promise<OutputType> {
    logger.log(MODULE_NAME, `step2: 开始`);
    // ...
    logger.log(MODULE_NAME, `step2: 完成`);
    return result;
  }
}
```

---

## 日志嵌入策略

### 1. 函数入口

```typescript
function processData(data: DataType): Result<OutputType> {
  logger.info(MODULE_NAME, `processData 开始, data=${JSON.stringify(data)}`);
  // ...
}
```

### 2. 条件分支

```typescript
if (condition) {
  logger.log(MODULE_NAME, `进入分支A, condition=true`);
  // 分支A逻辑
} else {
  logger.log(MODULE_NAME, `进入分支B, condition=false`);
  // 分支B逻辑
}
```

### 3. 循环迭代

```typescript
logger.log(MODULE_NAME, `开始循环, items=${items.length}`);
for (let i = 0; i < items.length; i++) {
  logger.log(MODULE_NAME, `循环迭代 ${i}/${items.length}`);
  // 循环体
}
logger.log(MODULE_NAME, `循环完成`);
```

### 4. 异常处理

```typescript
try {
  // 可能出错的代码
} catch (error) {
  logger.error(MODULE_NAME, `捕获异常: ${(error as Error).message}`);
  logger.error(MODULE_NAME, `堆栈: ${(error as Error).stack}`);
  throw error;
}
```

### 5. 外部调用

```typescript
logger.info(MODULE_NAME, `调用外部API, url=${url}`);
const response = await fetch(url);
logger.log(MODULE_NAME, `外部API响应, status=${response.status}`);
```

---

## 敏感信息过滤

### 不应记录的信息

- 密码
- 密钥/Token
- 信用卡号
- 个人身份信息 (PII)

### 过滤示例

```typescript
function sanitizeForLog(data: unknown): string {
  const sensitive = ['password', 'token', 'secret', 'apiKey', 'creditCard'];

  if (typeof data === 'object' && data !== null) {
    const sanitized = { ...data as Record<string, unknown> };
    for (const key of sensitive) {
      if (key in sanitized) {
        sanitized[key] = '[REDACTED]';
      }
    }
    return JSON.stringify(sanitized);
  }

  return String(data);
}

// 使用
logger.info(MODULE_NAME, `用户登录, data=${sanitizeForLog(userData)}`);
```

---

## 日志分析工具

### 解析日志文件

```typescript
interface LogEntry {
  timestamp: Date;
  level: LogLevel;
  module: string;
  message: string;
}

function parseLogFile(filePath: string): LogEntry[] {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.trim().split('\n');

  return lines.map(line => {
    const match = line.match(/\[(.+?)\]\[(.+?)\]\[(.+?)\] (.+)/);
    if (!match) throw new Error(`Invalid log format: ${line}`);

    return {
      timestamp: new Date(match[1].replace(' ', 'T')),
      level: match[2] as LogLevel,
      module: match[3],
      message: match[4]
    };
  });
}
```

### 按条件筛选

```typescript
function filterLogs(
  logs: LogEntry[],
  options: {
    level?: LogLevel;
    module?: string;
    startTime?: Date;
    endTime?: Date;
    keyword?: string;
  }
): LogEntry[] {
  return logs.filter(log => {
    if (options.level && log.level !== options.level) return false;
    if (options.module && log.module !== options.module) return false;
    if (options.startTime && log.timestamp < options.startTime) return false;
    if (options.endTime && log.timestamp > options.endTime) return false;
    if (options.keyword && !log.message.includes(options.keyword)) return false;
    return true;
  });
}
```

### 生成时间线

```typescript
function generateTimeline(logs: LogEntry[]): string[] {
  return logs.map(log => {
    const time = log.timestamp.toISOString().slice(11, 23);
    return `${time} | ${log.level.padEnd(7)} | ${log.module.padEnd(20)} | ${log.message}`;
  });
}
```
