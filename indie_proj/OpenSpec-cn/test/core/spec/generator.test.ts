/**
 * Unit tests for SpecGenerator
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { SpecGenerator, SprintSummary } from '../../../src/core/spec/generator.js';
import { promises as fs } from 'fs';
import path from 'path';

// Mock dependencies
vi.mock('execa', () => ({
  default: vi.fn()
}));

describe('SpecGenerator', () => {
  let generator: SpecGenerator;
  let tempDir: string;

  beforeEach(async () => {
    tempDir = path.join(process.cwd(), 'test-tmp-spec-generator');
    await fs.mkdir(tempDir, { recursive: true });
    generator = new SpecGenerator(tempDir);
  });

  afterEach(async () => {
    try {
      await fs.rm(tempDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  describe('generateSprintSummary', () => {
    it('should handle missing sprint directory', async () => {
      await expect(generator.generateSprintSummary({
        sprintName: 'nonexistent-sprint',
      })).rejects.toThrow();
    });

    it('should create minimal summary for empty sprint', async () => {
      // Create sprint directory structure
      const sprintDir = path.join(tempDir, 'openspec', 'sprints', 'test-sprint');
      await fs.mkdir(sprintDir, { recursive: true });

      // Create metadata file
      const metadata = {
        name: 'test-sprint',
        created: '2026-05-17',
        status: 'active',
        redmine: { versionId: 123, projectId: 42 },
        changes: []
      };
      await fs.writeFile(
        path.join(sprintDir, '.openspec.yaml'),
        'name: test-sprint\ncreated: 2026-05-17\nstatus: active\nredmine:\n  versionId: 123\n  projectId: 42\nchanges: []\n',
        'utf-8'
      );

      // Create sprint.md
      await fs.writeFile(
        path.join(sprintDir, 'sprint.md'),
        '# Test Sprint\n\nStart Date: 2026-05-01\nEnd Date: 2026-05-15\n',
        'utf-8'
      );

      const summary = await generator.generateSprintSummary({
        sprintName: 'test-sprint',
      });

      expect(summary.sprintName).toBe('test-sprint');
      expect(summary.sprintId).toBe(123);
      expect(summary.totalStories).toBe(0);
      expect(summary.completedStories).toBe(0);
      expect(summary.totalTasks).toBe(0);
      expect(summary.completedTasks).toBe(0);
    });

    it('should extract dates from sprint.md', async () => {
      const sprintDir = path.join(tempDir, 'openspec', 'sprints', 'date-test');
      await fs.mkdir(sprintDir, { recursive: true });

      await fs.writeFile(
        path.join(sprintDir, '.openspec.yaml'),
        'name: date-test\ncreated: 2026-05-17\nstatus: active\nchanges: []\n',
        'utf-8'
      );

      await fs.writeFile(
        path.join(sprintDir, 'sprint.md'),
        '# Date Test Sprint\n\nStart Date: 2026-05-01\nEnd Date: 2026-05-31\n',
        'utf-8'
      );

      const summary = await generator.generateSprintSummary({
        sprintName: 'date-test',
      });

      expect(summary.startDate).toBe('2026-05-01');
      expect(summary.endDate).toBe('2026-05-31');
    });
  });

  describe('generateSpecDocument', () => {
    it('should generate markdown document', async () => {
      const mockSummary: SprintSummary = {
        sprintName: 'test-sprint',
        sprintId: 123,
        startDate: '2026-05-01',
        endDate: '2026-05-15',
        totalStories: 3,
        completedStories: 3,
        totalTasks: 10,
        completedTasks: 10,
        totalBugs: 2,
        fixedBugs: 2,
        openBugs: 0,
        documents: {
          proposals: ['openspec/changes/story1/proposal.md'],
          specs: ['openspec/changes/story1/specs/spec.md'],
          designs: ['openspec/changes/story1/design.md'],
          tasks: ['openspec/changes/story1/tasks.md'],
        },
        code: {
          filesChanged: 5,
          linesAdded: 100,
          linesDeleted: 20,
          commits: ['abc123', 'def456'],
          branches: ['feature/test'],
          filesChangedList: ['src/test.ts', 'src/test2.ts'],
        },
        timeStats: {
          estimatedHours: 20,
          actualHours: 22,
          perStory: {},
          perTask: {},
        },
        incomplete: {
          stories: [],
          tasks: [],
          blockers: [],
          deferred: [],
          reasons: [],
        },
        lessons: {
          positive: ['Good teamwork', 'On time delivery'],
          improvements: ['Better estimation needed'],
          templates: ['Sprint template created'],
        },
      };

      const outputPath = path.join(tempDir, 'output.md');
      const generatedPath = await generator.generateSpecDocument(mockSummary, outputPath);

      expect(generatedPath).toBe(outputPath);

      const content = await fs.readFile(outputPath, 'utf-8');
      expect(content).toContain('# Sprint test-sprint 总结');
      expect(content).toContain('2026-05-01 ~ 2026-05-15');
      expect(content).toContain('3 / 完成: 3');
      expect(content).toContain('10 / 完成: 10');
      expect(content).toContain('2/2');
    });

    it('should generate correct progress percentage', async () => {
      const mockSummary: SprintSummary = {
        sprintName: 'partial-sprint',
        sprintId: 124,
        startDate: '2026-05-01',
        endDate: '2026-05-15',
        totalStories: 2,
        completedStories: 1,
        totalTasks: 4,
        completedTasks: 2,
        totalBugs: 0,
        fixedBugs: 0,
        openBugs: 0,
        documents: {
          proposals: [],
          specs: [],
          designs: [],
          tasks: [],
        },
        code: {
          filesChanged: 0,
          linesAdded: 0,
          linesDeleted: 0,
          commits: [],
          branches: [],
          filesChangedList: [],
        },
        timeStats: {
          estimatedHours: 0,
          actualHours: 0,
          perStory: {},
          perTask: {},
        },
        incomplete: {
          stories: ['incomplete-story'],
          tasks: [],
          blockers: [],
          deferred: [],
          reasons: [],
        },
        lessons: {
          positive: [],
          improvements: [],
          templates: [],
        },
      };

      const outputPath = path.join(tempDir, 'partial-output.md');
      await generator.generateSpecDocument(mockSummary, outputPath);

      const content = await fs.readFile(outputPath, 'utf-8');
      expect(content).toContain('50%'); // 2/4 tasks = 50%
    });

    it('should include incomplete analysis when items are incomplete', async () => {
      const mockSummary: SprintSummary = {
        sprintName: 'incomplete-sprint',
        sprintId: 125,
        startDate: '2026-05-01',
        endDate: '2026-05-15',
        totalStories: 2,
        completedStories: 1,
        totalTasks: 4,
        completedTasks: 2,
        totalBugs: 1,
        fixedBugs: 0,
        openBugs: 1,
        documents: {
          proposals: [],
          specs: [],
          designs: [],
          tasks: [],
        },
        code: {
          filesChanged: 0,
          linesAdded: 0,
          linesDeleted: 0,
          commits: [],
          branches: [],
          filesChangedList: [],
        },
        timeStats: {
          estimatedHours: 0,
          actualHours: 0,
          perStory: {},
          perTask: {},
        },
        incomplete: {
          stories: ['incomplete-story-1', 'incomplete-story-2'],
          tasks: ['task-1', 'task-2'],
          blockers: ['blocking-issue-1'],
          deferred: ['deferred-feature'],
          reasons: ['有 2 个story未完成', '有 1 个阻塞项'],
        },
        lessons: {
          positive: [],
          improvements: [],
          templates: [],
        },
      };

      const outputPath = path.join(tempDir, 'incomplete-output.md');
      await generator.generateSpecDocument(mockSummary, outputPath);

      const content = await fs.readFile(outputPath, 'utf-8');
      expect(content).toContain('## 未完成分析');
      expect(content).toContain('incomplete-story-1');
      expect(content).toContain('blocking-issue-1');
      // Note: deferred and reasons are not included in the generated markdown
    });

    it('should include lessons learned section', async () => {
      const mockSummary: SprintSummary = {
        sprintName: 'lessons-sprint',
        sprintId: 126,
        startDate: '2026-05-01',
        endDate: '2026-05-15',
        totalStories: 2,
        completedStories: 2,
        totalTasks: 4,
        completedTasks: 4,
        totalBugs: 0,
        fixedBugs: 0,
        openBugs: 0,
        documents: {
          proposals: [],
          specs: [],
          designs: [],
          tasks: [],
        },
        code: {
          filesChanged: 0,
          linesAdded: 0,
          linesDeleted: 0,
          commits: [],
          branches: [],
          filesChangedList: [],
        },
        timeStats: {
          estimatedHours: 0,
          actualHours: 0,
          perStory: {},
          perTask: {},
        },
        incomplete: {
          stories: [],
          tasks: [],
          blockers: [],
          deferred: [],
          reasons: [],
        },
        lessons: {
          positive: ['Excellent communication', 'Quick bug fixes'],
          improvements: ['Need better time estimation', 'Documentation gaps'],
          templates: ['Story template', 'Task template'],
        },
      };

      const outputPath = path.join(tempDir, 'lessons-output.md');
      await generator.generateSpecDocument(mockSummary, outputPath);

      const content = await fs.readFile(outputPath, 'utf-8');
      expect(content).toContain('## 经验总结');
      expect(content).toContain('### 做得好的');
      expect(content).toContain('Excellent communication');
      expect(content).toContain('### 需要改进的');
      expect(content).toContain('Need better time estimation');
      expect(content).toContain('### 可复用模板');
      expect(content).toContain('Story template');
    });
  });

  describe('parseTasks', () => {
    it('should parse completed tasks', async () => {
      const tasksPath = path.join(tempDir, 'tasks.md');
      await fs.writeFile(tasksPath, '- [x] Task 1\n- [x] Task 2\n- [ ] Task 3', 'utf-8');

      // Access private method through cast
      const parseTasksMethod = (generator as any).parseTasks.bind(generator);
      const tasks = await parseTasksMethod(tasksPath);

      expect(tasks).toHaveLength(3);
      expect(tasks[0].name).toBe('Task 1');
      expect(tasks[0].completed).toBe(true);
      expect(tasks[1].name).toBe('Task 2');
      expect(tasks[1].completed).toBe(true);
      expect(tasks[2].name).toBe('Task 3');
      expect(tasks[2].completed).toBe(false);
    });

    it('should handle empty tasks file', async () => {
      const tasksPath = path.join(tempDir, 'empty-tasks.md');
      await fs.writeFile(tasksPath, '', 'utf-8');

      const parseTasksMethod = (generator as any).parseTasks.bind(generator);
      const tasks = await parseTasksMethod(tasksPath);

      expect(tasks).toHaveLength(0);
    });

    it('should handle missing tasks file', async () => {
      const tasksPath = path.join(tempDir, 'nonexistent-tasks.md');

      const parseTasksMethod = (generator as any).parseTasks.bind(generator);
      const tasks = await parseTasksMethod(tasksPath);

      expect(tasks).toHaveLength(0);
    });

    it('should parse tasks with complex names', async () => {
      const tasksPath = path.join(tempDir, 'complex-tasks.md');
      await fs.writeFile(tasksPath, '- [x] Task with special chars: @#$\n- [ ] Task with (parentheses)', 'utf-8');

      const parseTasksMethod = (generator as any).parseTasks.bind(generator);
      const tasks = await parseTasksMethod(tasksPath);

      expect(tasks).toHaveLength(2);
      expect(tasks[0].name).toContain('special chars');
      expect(tasks[1].name).toContain('parentheses');
    });
  });

  describe('fileExists', () => {
    it('should return true for existing file', async () => {
      const filePath = path.join(tempDir, 'existing-file.txt');
      await fs.writeFile(filePath, 'test content', 'utf-8');

      const fileExistsMethod = (generator as any).fileExists.bind(generator);
      const exists = await fileExistsMethod(filePath);

      expect(exists).toBe(true);
    });

    it('should return false for non-existent file', async () => {
      const filePath = path.join(tempDir, 'nonexistent-file.txt');

      const fileExistsMethod = (generator as any).fileExists.bind(generator);
      const exists = await fileExistsMethod(filePath);

      expect(exists).toBe(false);
    });
  });

  describe('extractDate', () => {
    it('should extract date from content with Start Date label', () => {
      const extractDateMethod = (generator as any).extractDate.bind(generator);
      const date = extractDateMethod('# Sprint\nStart Date: 2026-05-01\nEnd Date: 2026-05-15', 'Start Date');

      expect(date).toBe('2026-05-01');
    });

    it('should extract date from content with End Date label', () => {
      const extractDateMethod = (generator as any).extractDate.bind(generator);
      const date = extractDateMethod('# Sprint\nStart Date: 2026-05-01\nEnd Date: 2026-05-15', 'End Date');

      expect(date).toBe('2026-05-15');
    });

    it('should return undefined when date not found', () => {
      const extractDateMethod = (generator as any).extractDate.bind(generator);
      const date = extractDateMethod('# Sprint\nNo dates here', 'Start Date');

      expect(date).toBeUndefined();
    });
  });
});