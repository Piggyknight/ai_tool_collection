/**
 * Unit tests for CodeReviewer
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { CodeReviewer, CodeReviewResult, CodeReviewIssue } from '../../../src/core/code-review/reviewer.js';
import { promises as fs } from 'fs';
import path from 'path';

// Mock execa
vi.mock('execa', () => ({
  default: vi.fn()
}));

describe('CodeReviewer', () => {
  let reviewer: CodeReviewer;
  let tempDir: string;

  beforeEach(async () => {
    tempDir = path.join(process.cwd(), 'test-tmp-code-reviewer');
    await fs.mkdir(tempDir, { recursive: true });
    reviewer = new CodeReviewer(tempDir);
  });

  afterEach(async () => {
    // Cleanup temp directory
    try {
      await fs.rm(tempDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  describe('review', () => {
    it('should handle no code changes', async () => {
      const result = await reviewer.review({
        changeName: 'test-change',
        baseBranch: 'main',
      });

      expect(result.status).toBe('passed');
      expect(result.overallScore).toBe(100);
      expect(result.summary).toBe('No code changes to review');
      expect(result.stats.totalLinesChanged).toBe(0);
      expect(result.stats.filesChanged).toBe(0);
    });
  });

  describe('parseDiff', () => {
    it('should parse git diff correctly', () => {
      const diff = `diff --git a/src/test.ts b/src/test.ts
+++ b/src/test.ts
@@ -0,0 +1,2 @@
+const x = 1;
+const y = 2;

diff --git a/src/another.ts b/src/another.ts
+++ b/src/another.ts
@@ -1,1 +1,2 @@
 const a = 1;
+const b = 2;`;

      // Access private method through cast
      const parseDiffMethod = (reviewer as any).parseDiff.bind(reviewer);
      const files = parseDiffMethod(diff);

      expect(files).toHaveLength(2);
      expect(files[0].file).toBe('src/test.ts');
      expect(files[0].addedLines).toHaveLength(2);
      expect(files[1].file).toBe('src/another.ts');
      expect(files[1].addedLines).toHaveLength(1);
    });

    it('should handle empty diff', () => {
      const parseDiffMethod = (reviewer as any).parseDiff.bind(reviewer);
      const files = parseDiffMethod('');

      expect(files).toHaveLength(0);
    });
  });

  describe('calculateScore', () => {
    it('should deduct points for critical issues', () => {
      const stats = {
        filesChanged: 1,
        totalLinesChanged: 0, // No lines, so no bonus
        criticalIssues: 2,
        majorIssues: 0,
        minorIssues: 0,
        infoIssues: 0,
      };

      const calculateScoreMethod = (reviewer as any).calculateScore.bind(reviewer);
      const score = calculateScoreMethod(stats);

      expect(score).toBeLessThan(100);
      expect(score).toBe(60); // 100 - (2 * 20)
    });

    it('should deduct points for major issues', () => {
      const stats = {
        filesChanged: 1,
        totalLinesChanged: 0, // No lines, so no bonus
        criticalIssues: 0,
        majorIssues: 3,
        minorIssues: 0,
        infoIssues: 0,
      };

      const calculateScoreMethod = (reviewer as any).calculateScore.bind(reviewer);
      const score = calculateScoreMethod(stats);

      expect(score).toBeLessThan(100);
      expect(score).toBe(70); // 100 - (3 * 10)
    });

    it('should cap score at 0 and 100', () => {
      const manyCriticalStats = {
        filesChanged: 1,
        totalLinesChanged: 0, // No lines, so no bonus
        criticalIssues: 10,
        majorIssues: 0,
        minorIssues: 0,
        infoIssues: 0,
      };

      const calculateScoreMethod = (reviewer as any).calculateScore.bind(reviewer);
      const score = calculateScoreMethod(manyCriticalStats);

      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(100);
    });

    it('should add bonus for reasonable code size', () => {
      const stats = {
        filesChanged: 1,
        totalLinesChanged: 250, // Reasonable size, bonus applies
        criticalIssues: 0,
        majorIssues: 0,
        minorIssues: 0,
        infoIssues: 0,
      };

      const calculateScoreMethod = (reviewer as any).calculateScore.bind(reviewer);
      const score = calculateScoreMethod(stats);

      // Score should be 105 before capping at 100
      expect(score).toBeGreaterThanOrEqual(100);
      expect(score).toBe(100); // Capped at 100
    });
  });

  describe('checkSecurityIssues', () => {
    it('should detect SQL injection patterns', () => {
      const checkSecurityMethod = (reviewer as any).checkSecurityIssues.bind(reviewer);
      const issues = checkSecurityMethod('test.ts', 'const query = `SELECT * FROM users WHERE id = ${userId}`', 10);

      expect(issues).toHaveLength(1);
      expect(issues[0].type).toBe('security');
      expect(issues[0].severity).toBe('critical');
      expect(issues[0].message).toContain('SQL injection');
    });

    it('should detect eval usage', () => {
      const checkSecurityMethod = (reviewer as any).checkSecurityIssues.bind(reviewer);
      const issues = checkSecurityMethod('test.ts', 'eval(userInput)', 10);

      expect(issues).toHaveLength(1);
      expect(issues[0].type).toBe('security');
      expect(issues[0].severity).toBe('critical');
      expect(issues[0].message).toContain('eval');
    });

    it('should detect hardcoded secrets', () => {
      const checkSecurityMethod = (reviewer as any).checkSecurityIssues.bind(reviewer);
      const issues = checkSecurityMethod('test.ts', 'const apiKey = "secret123"', 10);

      expect(issues).toHaveLength(1);
      expect(issues[0].type).toBe('security');
      expect(issues[0].severity).toBe('critical');
      expect(issues[0].message).toContain('credentials');
    });

    it('should detect console statements', () => {
      const checkSecurityMethod = (reviewer as any).checkSecurityIssues.bind(reviewer);
      const issues = checkSecurityMethod('test.ts', 'console.log("debug info")', 10);

      expect(issues).toHaveLength(1);
      expect(issues[0].type).toBe('best-practice');
      expect(issues[0].severity).toBe('minor');
      expect(issues[0].message).toContain('Console');
    });
  });

  describe('checkErrorHandling', () => {
    it('should detect empty catch blocks', () => {
      const checkErrorMethod = (reviewer as any).checkErrorHandling.bind(reviewer);
      const issues = checkErrorMethod('test.ts', '} catch (e) {}', 10);

      expect(issues).toHaveLength(1);
      expect(issues[0].type).toBe('error');
      expect(issues[0].severity).toBe('major');
      expect(issues[0].message).toContain('catch');
    });
  });

  describe('checkPerformance', () => {
    it('should detect nested loops on same line', () => {
      const checkPerformanceMethod = (reviewer as any).checkPerformance.bind(reviewer);
      const issues = checkPerformanceMethod('test.ts', 'for (let i = 0; i < 10; i++) { for (let j = 0; j < 10; j++) {} }', 10);

      expect(issues).toHaveLength(1);
      expect(issues[0].type).toBe('performance');
      expect(issues[0].severity).toBe('minor');
      expect(issues[0].message.toLowerCase()).toContain('nested');
    });
  });

  describe('checkStyle', () => {
    it('should detect magic numbers', () => {
      const checkStyleMethod = (reviewer as any).checkStyle.bind(reviewer);
      const issues = checkStyleMethod('test.ts', 'if (x > 100) {', 10);

      expect(issues).toHaveLength(1);
      expect(issues[0].type).toBe('best-practice');
      expect(issues[0].severity).toBe('minor');
      expect(issues[0].message).toContain('Magic number');
    });

    it('should detect long lines', () => {
      // Create a line that's actually longer than 120 characters
      const longLine = 'const veryLongVariableName = "this is a very long string that really exceeds 120 characters because it needs to be long enough to trigger the warning";';
      const checkStyleMethod = (reviewer as any).checkStyle.bind(reviewer);
      const issues = checkStyleMethod('test.ts', longLine, 10);

      expect(issues).toHaveLength(1);
      expect(issues[0].type).toBe('style');
      expect(issues[0].severity).toBe('info');
      expect(issues[0].message).toContain('120');
    });

    it('should detect TODO comments', () => {
      const checkStyleMethod = (reviewer as any).checkStyle.bind(reviewer);
      const issues = checkStyleMethod('test.ts', '// TODO: implement this later', 10);

      expect(issues).toHaveLength(1);
      expect(issues[0].type).toBe('best-practice');
      expect(issues[0].severity).toBe('minor');
      expect(issues[0].message).toContain('TODO');
    });
  });

  describe('generateReport', () => {
    it('should generate markdown report correctly', () => {
      const mockResult: CodeReviewResult = {
        changeName: 'test-change',
        overallScore: 85,
        status: 'needs-work',
        summary: 'Found 1 major issue that should be addressed.',
        issues: [
          {
            severity: 'major',
            type: 'error',
            file: 'test.ts',
            line: 10,
            message: 'Empty catch block',
            suggestion: 'Add error handling',
          },
        ],
        stats: {
          filesChanged: 1,
          totalLinesChanged: 20,
          criticalIssues: 0,
          majorIssues: 1,
          minorIssues: 2,
          infoIssues: 1,
        },
        positiveFindings: ['Good code structure'],
      };

      const report = reviewer.generateReport(mockResult);

      expect(report).toContain('# Code Review: test-change');
      expect(report).toContain('85/100');
      expect(report).toContain('needs-work');
      expect(report).toContain('Empty catch block');
      expect(report).toContain('Good code structure');
    });
  });

  describe('saveReport', () => {
    it('should save report to file', async () => {
      const mockResult: CodeReviewResult = {
        changeName: 'test-change',
        overallScore: 100,
        status: 'passed',
        summary: 'No issues found',
        issues: [],
        stats: {
          filesChanged: 0,
          totalLinesChanged: 0,
          criticalIssues: 0,
          majorIssues: 0,
          minorIssues: 0,
          infoIssues: 0,
        },
        positiveFindings: [],
      };

      const outputPath = path.join(tempDir, 'review.md');
      const savedPath = await reviewer.saveReport(mockResult, outputPath);

      expect(savedPath).toBe(outputPath);

      // Verify file exists and has content
      const content = await fs.readFile(outputPath, 'utf-8');
      expect(content).toContain('# Code Review: test-change');
    });
  });
});