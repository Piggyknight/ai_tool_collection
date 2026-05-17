/**
 * Spec Generator
 *
 * Generates sprint summaries and spec documentation with statistics and analysis.
 */

import path from 'path';
import { promises as fs } from 'fs';
import yaml from 'yaml';
import chalk from 'chalk';
import { execa } from 'execa';
import { getInstanceManager } from '../redmine/instance-manager.js';
import { RedmineCliWrapper } from '../redmine/cli-wrapper.js';
import { OneWaySyncManager } from '../redmine/one-way-sync.js';
import { StatusMapper } from '../redmine/status-mapping.js';

export interface SprintSummaryOptions {
  sprintName: string;
  includeCodeStats?: boolean;
  includeTimeStats?: boolean;
}

export interface SprintSummary {
  sprintName: string;
  sprintId: number;
  startDate: string;
  endDate: string;

  // Completion statistics
  totalStories: number;
  completedStories: number;
  totalTasks: number;
  completedTasks: number;
  totalBugs: number;
  fixedBugs: number;
  openBugs: number;

  // Documents
  documents: {
    proposals: string[];
    specs: string[];
    designs: string[];
    tasks: string[];
  };

  // Code statistics
  code: {
    filesChanged: number;
    linesAdded: number;
    linesDeleted: number;
    commits: string[];
    branches: string[];
    filesChangedList: string[];
  };

  // Time statistics
  timeStats: {
    estimatedHours: number;
    actualHours: number;
    perStory: Record<string, { estimated: number; actual: number }>;
    perTask: Record<string, { estimated: number; actual: number }>;
  };

  // Incomplete analysis
  incomplete: {
    stories: string[];
    tasks: string[];
    blockers: string[];
    deferred: string[];
    reasons: string[];
  };

  // Lessons learned
  lessons: {
    positive: string[];
    improvements: string[];
    templates: string[];
  };
}

export interface ChangeTask {
  name: string;
  completed: boolean;
  estimatedHours?: number;
}

export interface BugInfo {
  id: string;
  title: string;
  severity: string;
  status: string;
  relatedStory?: string;
}

export class SpecGenerator {
  private projectRoot: string;
  private openspecDir: string;

  constructor(projectPath: string) {
    this.projectRoot = path.resolve(projectPath);
    this.openspecDir = path.join(this.projectRoot, 'openspec');
  }

  /**
   * Generate sprint summary
   */
  async generateSprintSummary(options: SprintSummaryOptions): Promise<SprintSummary> {
    const sprintPath = path.join(this.openspecDir, 'sprints', options.sprintName);
    const metadataPath = path.join(sprintPath, '.openspec.yaml');
    const sprintMdPath = path.join(sprintPath, 'sprint.md');

    console.log(chalk.cyan(`\n📊 Generating sprint summary: ${options.sprintName}\n`));

    // Read sprint metadata
    const metadata = await this.readSprintMetadata(metadataPath);
    const sprintContent = await fs.readFile(sprintMdPath, 'utf-8');

    // Extract dates
    const startDate = this.extractDate(sprintContent, 'Start Date') || metadata.created || '';
    const endDate = this.extractDate(sprintContent, 'End Date') || this.extractDate(sprintContent, 'Due Date') || '';

    // Get stories in sprint
    const stories = metadata.changes || [];

    // Analyze each story
    const storiesData = await this.analyzeStories(stories);

    // Get bugs
    const bugsData = await this.analyzeBugs();

    // Collect documents
    const documents = await this.collectDocuments(stories);

    // Get code statistics
    const codeStats = await this.getCodeStatistics(options.sprintName);

    // Get time statistics from Redmine
    const timeStats = await this.getTimeStatistics(stories);

    // Analyze incomplete items
    const incomplete = await this.analyzeIncomplete(storiesData, bugsData);

    // Generate lessons learned
    const lessons = await this.generateLessons(storiesData, bugsData);

    const summary: SprintSummary = {
      sprintName: options.sprintName,
      sprintId: metadata.redmine?.versionId || 0,
      startDate,
      endDate,
      totalStories: stories.length,
      completedStories: storiesData.filter(s => s.completed).length,
      totalTasks: storiesData.reduce((sum, s) => sum + s.totalTasks, 0),
      completedTasks: storiesData.reduce((sum, s) => sum + s.completedTasks, 0),
      totalBugs: bugsData.length,
      fixedBugs: bugsData.filter(b => b.status === 'fixed' || b.status === 'verified').length,
      openBugs: bugsData.filter(b => b.status === 'new' || b.status === 'in-progress').length,
      documents,
      code: codeStats,
      timeStats,
      incomplete,
      lessons,
    };

    return summary;
  }

  /**
   * Generate spec document
   */
  async generateSpecDocument(summary: SprintSummary, outputPath?: string): Promise<string> {
    let content = `# Sprint ${summary.sprintName} 总结\n\n`;

    // Overview
    content += `## 概览\n\n`;
    content += `- **期间**: ${summary.startDate} ~ ${summary.endDate}\n`;
    content += `- **总Story**: ${summary.totalStories} / 完成: ${summary.completedStories}\n`;
    content += `- **总Task**: ${summary.totalTasks} / 完成: ${summary.completedTasks}\n`;
    content += `- **Bug**: ${summary.fixedBugs}/${summary.totalBugs}\n`;
    content += `- **进度**: ${Math.round((summary.completedTasks / Math.max(summary.totalTasks, 1)) * 100)}%\n\n`;

    // Stories
    content += `## Stories\n\n`;
    for (const storyName of summary.documents.proposals) {
      const storyFile = path.basename(storyName);
      content += `- **[${storyFile}](${storyName})**\n`;
    }
    content += '\n';

    // Tasks
    if (summary.documents.tasks.length > 0) {
      content += `## Tasks\n\n`;
      for (const taskFile of summary.documents.tasks) {
        content += `- [${taskFile}](${taskFile})\n`;
      }
      content += '\n';
    }

    // Bug修复
    if (summary.fixedBugs > 0 || summary.openBugs > 0) {
      content += `## Bug修复\n\n`;
      content += `- **已修复**: ${summary.fixedBugs}\n`;
      content += `- **未修复**: ${summary.openBugs}\n\n`;
    }

    // 文档位置
    content += `## 文档位置\n\n`;
    content += `### Proposals\n`;
    for (const doc of summary.documents.proposals) {
      content += `- [${path.basename(doc)}](${doc})\n`;
    }
    content += '\n';

    if (summary.documents.specs.length > 0) {
      content += `### Specs\n`;
      for (const doc of summary.documents.specs) {
        content += `- [${path.basename(doc)}](${doc})\n`;
      }
      content += '\n';
    }

    if (summary.documents.designs.length > 0) {
      content += `### Designs\n`;
      for (const doc of summary.documents.designs) {
        content += `- [${path.basename(doc)}](${doc})\n`;
      }
      content += '\n';
    }

    // 相关代码
    content += `## 相关代码\n\n`;
    if (summary.code.filesChangedList && summary.code.filesChangedList.length > 0) {
      content += `### 修改的文件\n`;
      for (const file of summary.code.filesChangedList) {
        content += `- ${file}\n`;
      }
      content += '\n';
    }

    if (summary.code.commits.length > 0) {
      content += `### 相关提交\n`;
      for (const commit of summary.code.commits) {
        content += `- ${commit}\n`;
      }
      content += '\n';
    }

    // 时间统计
    if (summary.timeStats.actualHours > 0) {
      content += `## 时间统计\n\n`;
      content += `| Story/Task | 预估工时 | 实际工时 | 偏差 |\n`;
      content += `|-----------|---------|---------|------|\n`;
      for (const [name, times] of Object.entries(summary.timeStats.perTask)) {
        const diff = (times.actual - times.estimated).toFixed(1);
        const diffColor = diff.includes('-') ? diff : `+${diff}`;
        content += `| ${name} | ${times.estimated}h | ${times.actual}h | ${diffColor}h |\n`;
      }
      content += '\n';
    }

    // 未完成分析
    if (summary.incomplete.stories.length > 0 || summary.incomplete.tasks.length > 0) {
      content += `## 未完成分析\n\n`;
      if (summary.incomplete.stories.length > 0) {
        content += `### 未完成的Stories\n`;
        for (const story of summary.incomplete.stories) {
          content += `- ${story}\n`;
        }
        content += '\n';
      }
      if (summary.incomplete.tasks.length > 0) {
        content += `### 未完成的Tasks\n`;
        for (const task of summary.incomplete.tasks) {
          content += `- ${task}\n`;
        }
        content += '\n';
      }
      if (summary.incomplete.blockers.length > 0) {
        content += `### 阻塞项\n`;
        for (const blocker of summary.incomplete.blockers) {
          content += `- ${blocker}\n`;
        }
        content += '\n';
      }
    }

    // 经验总结
    if (summary.lessons.positive.length > 0 || summary.lessons.improvements.length > 0) {
      content += `## 经验总结\n\n`;
      if (summary.lessons.positive.length > 0) {
        content += `### 做得好的\n`;
        for (const item of summary.lessons.positive) {
          content += `- ${item}\n`;
        }
        content += '\n';
      }
      if (summary.lessons.improvements.length > 0) {
        content += `### 需要改进的\n`;
        for (const item of summary.lessons.improvements) {
          content += `- ${item}\n`;
        }
        content += '\n';
      }
      if (summary.lessons.templates.length > 0) {
        content += `### 可复用模板\n`;
        for (const template of summary.lessons.templates) {
          content += `- ${template}\n`;
        }
        content += '\n';
      }
    }

    content += `---\n\n`;
    content += `*生成时间: ${new Date().toISOString()}*\n`;

    if (!outputPath) {
      outputPath = path.join(this.openspecDir, 'sprints', summary.sprintName, 'summary.md');
    }

    await fs.writeFile(outputPath, content, 'utf-8');
    return outputPath;
  }

  /**
   * Read sprint metadata
   */
  private async readSprintMetadata(metadataPath: string): Promise<any> {
    try {
      const content = await fs.readFile(metadataPath, 'utf-8');
      return yaml.parse(content);
    } catch {
      return {};
    }
  }

  /**
   * Extract date from content
   */
  private extractDate(content: string, label: string): string | undefined {
    const match = content.match(new RegExp(`${label}:\\s*(\\d{4}-\\d{2}-\\d{2})`, 'i'));
    return match?.[1];
  }

  /**
   * Analyze stories
   */
  private async analyzeStories(stories: Array<{ name: string }>): Promise<Array<{
    name: string;
    completed: boolean;
    totalTasks: number;
    completedTasks: number;
  }>> {
    const results = [];

    for (const story of stories) {
      const changePath = path.join(this.openspecDir, 'changes', story.name);
      const tasksPath = path.join(changePath, 'tasks.md');
      const metadataPath = path.join(changePath, '.openspec.yaml');

      const tasks = await this.parseTasks(tasksPath);

      // Check if story is completed (all tasks done and synced)
      let completed = false;
      try {
        const metadata = yaml.parse(await fs.readFile(metadataPath, 'utf-8'));
        completed = metadata.redmine?.syncStatus === 'synced' &&
                     tasks.filter(t => t.completed).length === tasks.length;
      } catch {
        completed = tasks.filter(t => t.completed).length === tasks.length;
      }

      results.push({
        name: story.name,
        completed,
        totalTasks: tasks.length,
        completedTasks: tasks.filter(t => t.completed).length,
      });
    }

    return results;
  }

  /**
   * Analyze bugs
   */
  private async analyzeBugs(): Promise<BugInfo[]> {
    const bugsPath = path.join(this.openspecDir, 'bugs');
    const bugs: BugInfo[] = [];

    try {
      const entries = await fs.readdir(bugsPath, { withFileTypes: true });
      const bugDirs = entries.filter(e => e.isDirectory());

      for (const dir of bugDirs) {
        const bugPath = path.join(bugsPath, dir.name);
        const metadataPath = path.join(bugPath, '.openspec.yaml');

        try {
          const metadata = yaml.parse(await fs.readFile(metadataPath, 'utf-8'));
          bugs.push({
            id: dir.name,
            title: metadata.title || 'Unknown',
            severity: metadata.severity || 'unknown',
            status: metadata.status || 'unknown',
            relatedStory: metadata.relatedChange,
          });
        } catch {
          // Skip invalid bugs
        }
      }
    } catch {
      // No bugs directory
    }

    return bugs;
  }

  /**
   * Collect document paths
   */
  private async collectDocuments(stories: Array<{ name: string }>): Promise<SprintSummary['documents']> {
    const documents = {
      proposals: [] as string[],
      specs: [] as string[],
      designs: [] as string[],
      tasks: [] as string[],
    };

    for (const story of stories) {
      const changePath = path.join(this.openspecDir, 'changes', story.name);

      // Proposal
      const proposalPath = path.join(changePath, 'proposal.md');
      if (await this.fileExists(proposalPath)) {
        documents.proposals.push(proposalPath);
      }

      // Specs
      const specsPath = path.join(changePath, 'specs');
      try {
        const entries = await fs.readdir(specsPath);
        for (const entry of entries) {
          if (entry.endsWith('.md')) {
            documents.specs.push(path.join(specsPath, entry));
          }
        }
      } catch {
        // No specs
      }

      // Design
      const designPath = path.join(changePath, 'design.md');
      if (await this.fileExists(designPath)) {
        documents.designs.push(designPath);
      }

      // Tasks
      const tasksPath = path.join(changePath, 'tasks.md');
      if (await this.fileExists(tasksPath)) {
        documents.tasks.push(tasksPath);
      }
    }

    return documents;
  }

  /**
   * Get code statistics
   */
  private async getCodeStatistics(sprintName: string): Promise<SprintSummary['code']> {
    // Try to get git stats
    try {
      // Get branch for sprint
      const branchName = `sprint/${sprintName}`;

      // Get commits
      const { stdout: commits } = await this.execGit(['log', branchName, '--pretty=format:%h - %s', '--']);
      const commitList = commits.trim().split('\n').filter(c => c);

      // Get files changed
      const { stdout: files } = await this.execGit(['diff', 'main...'+branchName, '--name-only']);
      const fileList = files.trim().split('\n').filter(f => f);

      // Get line counts
      const { stdout: stats } = await this.execGit(['diff', 'main...'+branchName, '--stat']);
      const linesAddedMatch = stats.match(/(\d+) insertion/);
      const linesDeletedMatch = stats.match(/(\d+) deletion/);

      return {
        filesChanged: fileList.length,
        linesAdded: linesAddedMatch ? parseInt(linesAddedMatch[1], 10) : 0,
        linesDeleted: linesDeletedMatch ? parseInt(linesDeletedMatch[1], 10) : 0,
        commits: commitList,
        branches: [branchName],
        filesChangedList: fileList,
      };
    } catch {
      // Git not available or no stats
      return {
        filesChanged: 0,
        linesAdded: 0,
        linesDeleted: 0,
        commits: [],
        branches: [],
        filesChangedList: [],
      };
    }
  }

  /**
   * Get time statistics from Redmine
   */
  private async getTimeStatistics(stories: Array<{ name: string }>): Promise<SprintSummary['timeStats']> {
    let estimatedHours = 0;
    let actualHours = 0;
    const perStory: Record<string, { estimated: number; actual: number }> = {};
    const perTask: Record<string, { estimated: number; actual: number }> = {};

    try {
      const manager = getInstanceManager();
      const wrapper = await manager.createWrapper();
      const mapper = new StatusMapper();

      for (const story of stories) {
        const changePath = path.join(this.openspecDir, 'changes', story.name);
        const metadataPath = path.join(changePath, '.openspec.yaml');
        const metadata = yaml.parse(await fs.readFile(metadataPath, 'utf-8'));

        if (metadata.redmine?.issueId) {
          const issue = await wrapper.getIssue(metadata.redmine.issueId);
          const est = issue.estimated_hours || 0;
          const act = issue.spent_hours || 0;

          estimatedHours += est;
          actualHours += act;

          perStory[story.name] = { estimated: est, actual: act };

          // Parse tasks for per-task time
          const tasksPath = path.join(changePath, 'tasks.md');
          const tasks = await this.parseTasks(tasksPath);
          for (const task of tasks) {
            perTask[task.name] = {
              estimated: Math.round(est / tasks.length * 10) / 10,
              actual: Math.round(act / tasks.length * 10) / 10,
            };
          }
        }
      }
    } catch {
      // Redmine not available
    }

    return {
      estimatedHours,
      actualHours,
      perStory,
      perTask,
    };
  }

  /**
   * Analyze incomplete items
   */
  private async analyzeIncomplete(
    storiesData: Array<{ name: string; completed: boolean }>,
    bugsData: BugInfo[]
  ): Promise<SprintSummary['incomplete']> {
    const incomplete: SprintSummary['incomplete'] = {
      stories: [],
      tasks: [],
      blockers: [],
      deferred: [],
      reasons: [],
    };

    // Incomplete stories
    for (const story of storiesData) {
      if (!story.completed) {
        incomplete.stories.push(story.name);
      }
    }

    // Open bugs
    for (const bug of bugsData) {
      if (bug.status === 'new' || bug.status === 'in-progress') {
        incomplete.blockers.push(`Bug: ${bug.title}`);
      }
    }

    // Generate reasons based on analysis
    if (incomplete.stories.length > 0) {
      incomplete.reasons.push(`有 ${incomplete.stories.length} 个story未完成`);
    }
    if (incomplete.blockers.length > 0) {
      incomplete.reasons.push(`有 ${incomplete.blockers.length} 个阻塞项`);
    }

    return incomplete;
  }

  /**
   * Generate lessons learned
   */
  private async generateLessons(
    storiesData: Array<{ name: string; completed: boolean }>,
    bugsData: BugInfo[]
  ): Promise<SprintSummary['lessons']> {
    const lessons: SprintSummary['lessons'] = {
      positive: [],
      improvements: [],
      templates: [],
    };

    // Positive findings
    const completedCount = storiesData.filter(s => s.completed).length;
    if (completedCount > 0 && completedCount === storiesData.length) {
      lessons.positive.push('所有story按时完成');
    }

    if (bugsData.filter(b => b.status === 'verified').length > 0) {
      lessons.positive.push('Bug修复和验证流程良好');
    }

    // Improvements
    const openCriticalBugs = bugsData.filter(b => b.status === 'new' && b.severity === 'critical').length;
    if (openCriticalBugs > 0) {
      lessons.improvements.push('需要优先处理critical级别bug');
    }

    const incompleteCount = storiesData.length - completedCount;
    if (incompleteCount > 0) {
      lessons.improvements.push('需要优化story估算，避免延期');
    }

    // Templates
    if (storiesData.length > 0) {
      lessons.templates.push('Sprint规划模板');
    }

    return lessons;
  }

  /**
   * Parse tasks from tasks.md
   */
  private async parseTasks(tasksPath: string): Promise<ChangeTask[]> {
    const tasks: ChangeTask[] = [];

    try {
      const content = await fs.readFile(tasksPath, 'utf-8');
      const lines = content.split('\n');

      for (const line of lines) {
        const match = line.match(/^\s*-\s*\[([ x])\]\s+(.+)$/);
        if (match) {
          const [, checked, name] = match;
          tasks.push({
            name: name.trim(),
            completed: checked === 'x',
          });
        }
      }
    } catch {
      // File doesn't exist
    }

    return tasks;
  }

  /**
   * Check if file exists
   */
  private async fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Execute git command
   */
  private async execGit(args: string[]): Promise<{ stdout: string; stderr: string }> {
    return execa('git', args, {
      cwd: this.projectRoot,
      windowsHide: true,
    });
  }
}