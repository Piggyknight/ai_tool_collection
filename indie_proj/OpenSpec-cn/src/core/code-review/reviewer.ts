/**
 * Code Reviewer
 *
 * Local code review implementation using git diff to analyze code changes.
 * Supports analysis without external GitHub/GitLab integration.
 */

import { execa } from 'execa';
import path from 'path';
import ora from 'ora';
import chalk from 'chalk';
import { promises as fs } from 'fs';

export interface CodeReviewOptions {
  changeName: string;
  branch?: string;
  baseBranch?: string;
  files?: string[];
  verbose?: boolean;
}

export interface CodeReviewIssue {
  severity: 'critical' | 'major' | 'minor' | 'info';
  type: string; // security, performance, style, error, best-practice
  file?: string;
  line?: number;
  message: string;
  suggestion?: string;
}

export interface CodeReviewResult {
  changeName: string;
  overallScore: number; // 0-100
  status: 'passed' | 'needs-work' | 'failed';
  summary: string;
  issues: CodeReviewIssue[];
  stats: {
    totalLinesChanged: number;
    filesChanged: number;
    criticalIssues: number;
    majorIssues: number;
    minorIssues: number;
    infoIssues: number;
  };
  positiveFindings: string[];
}

export class CodeReviewer {
  private projectRoot: string;
  private changeDir: string = '';

  constructor(private projectPath: string) {
    this.projectRoot = path.resolve(projectPath);
  }

  /**
   * Review a change
   */
  async review(options: CodeReviewOptions): Promise<CodeReviewResult> {
    this.changeDir = path.join(this.projectRoot, 'openspec', 'changes', options.changeName);

    console.log(chalk.cyan(`\n🔍 Code Review: ${options.changeName}\n`));

    const spinner = ora('Analyzing code changes...').start();

    try {
      // Get git diff
      const diff = await this.getGitDiff(options);

      if (!diff.trim()) {
        spinner.warn('No code changes found');
        return {
          changeName: options.changeName,
          overallScore: 100,
          status: 'passed',
          summary: 'No code changes to review',
          issues: [],
          stats: {
            totalLinesChanged: 0,
            filesChanged: 0,
            criticalIssues: 0,
            majorIssues: 0,
            minorIssues: 0,
            infoIssues: 0,
          },
          positiveFindings: [],
        };
      }

      // Parse diff
      const parsedDiff = this.parseDiff(diff);

      spinner.text = 'Analyzing code quality...';

      // Analyze code
      const issues = await this.analyzeCode(parsedDiff);

      spinner.text = 'Calculating review score...';

      // Calculate stats
      const stats = this.calculateStats(parsedDiff, issues);

      // Calculate overall score
      const score = this.calculateScore(stats);

      // Generate summary
      const summary = this.generateSummary(stats);

      // Collect positive findings
      const positiveFindings = this.collectPositiveFindings(parsedDiff);

      const result: CodeReviewResult = {
        changeName: options.changeName,
        overallScore: score,
        status: score >= 80 ? 'passed' : score >= 60 ? 'needs-work' : 'failed',
        summary,
        issues,
        stats,
        positiveFindings,
      };

      spinner.succeed('Review complete');
      return result;
    } catch (error) {
      spinner.fail('Review failed');
      throw error;
    }
  }

  /**
   * Get git diff
   */
  private async getGitDiff(options: CodeReviewOptions): Promise<string> {
    const baseBranch = options.baseBranch || 'main';
    const branch = options.branch || 'HEAD';

    try {
      // Check if git repo exists
      await execa('git', ['rev-parse', '--git-dir'], {
        cwd: this.projectRoot,
        windowsHide: true,
      });
    } catch {
      // Not a git repo, try to read files directly
      return await this.getDiffFromFiles(options.files);
    }

    try {
      // Get diff against base branch
      const { stdout } = await execa('git', [
        'diff',
        `${baseBranch}...${branch}`,
        '--',
        'src/',  // Only review src directory
      ], {
        cwd: this.projectRoot,
        windowsHide: true,
      });

      return stdout;
    } catch {
      // Fallback to uncommitted changes
      try {
        const { stdout } = await execa('git', [
          'diff',
          'HEAD',
          '--',
          'src/',
        ], {
          cwd: this.projectRoot,
          windowsHide: true,
        });

        return stdout;
      } catch {
        // No changes found
        return '';
      }
    }
  }

  /**
   * Get diff from files (when git is not available)
   */
  private async getDiffFromFiles(files?: string[]): Promise<string> {
    if (!files || files.length === 0) {
      return '';
    }

    let diff = '';
    for (const file of files) {
      const filePath = path.join(this.projectRoot, file);
      try {
        const content = await fs.readFile(filePath, 'utf-8');
        diff += `diff --git a/${file} b/${file}\n`;
        diff += `--- a/${file}\n`;
        diff += `+++ b/${file}\n`;
        diff += `@@ -0,0 +1,${content.split('\n').length} @@\n`;
        diff += content.split('\n').map(l => `+${l}`).join('\n');
        diff += '\n';
      } catch {
        // File doesn't exist or can't be read
      }
    }

    return diff;
  }

  /**
   * Parse git diff
   */
  private parseDiff(diff: string): Array<{
    file: string;
    addedLines: string[];
    removedLines: string[];
    lineNumbers: number[];
  }> {
    const files: Array<{
      file: string;
      addedLines: string[];
      removedLines: string[];
      lineNumbers: number[];
    }> = [];

    const lines = diff.split('\n');
    let currentFile = '';
    let addedLines: string[] = [];
    let removedLines: string[] = [];
    let lineNumbers: number[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // New file
      if (line.startsWith('diff --git')) {
        if (currentFile) {
          files.push({ file: currentFile, addedLines, removedLines, lineNumbers });
        }
        currentFile = '';
        addedLines = [];
        removedLines = [];
        lineNumbers = [];
      }

      // File path
      if (line.startsWith('+++')) {
        const match = line.match(/^\+\+\+ b\/(.+)$/);
        if (match) {
          currentFile = match[1];
        }
      }

      // Hunk header (contains line numbers)
      if (line.startsWith('@@')) {
        const match = line.match(/@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@/);
        if (match) {
          const startLine = parseInt(match[1], 10);
          const lineCount = match[2] ? parseInt(match[2], 10) : 1;
          for (let n = startLine; n < startLine + lineCount; n++) {
            lineNumbers.push(n);
          }
        }
      }

      // Added line
      if (line.startsWith('+') && !line.startsWith('+++')) {
        addedLines.push(line.substring(1));
      }

      // Removed line
      if (line.startsWith('-') && !line.startsWith('---')) {
        removedLines.push(line.substring(1));
      }
    }

    // Don't forget the last file
    if (currentFile) {
      files.push({ file: currentFile, addedLines, removedLines, lineNumbers });
    }

    return files;
  }

  /**
   * Analyze code for issues
   */
  private async analyzeCode(diffFiles: Array<{
    file: string;
    addedLines: string[];
    removedLines: string[];
    lineNumbers: number[];
  }>): Promise<CodeReviewIssue[]> {
    const issues: CodeReviewIssue[] = [];

    for (const file of diffFiles) {
      for (let i = 0; i < file.addedLines.length; i++) {
        const line = file.addedLines[i];
        const lineNumber = file.lineNumbers[i];

        // Security checks
        issues.push(...this.checkSecurityIssues(file.file, line, lineNumber));

        // Error handling checks
        issues.push(...this.checkErrorHandling(file.file, line, lineNumber));

        // Performance checks
        issues.push(...this.checkPerformance(file.file, line, lineNumber));

        // Style and best practices
        issues.push(...this.checkStyle(file.file, line, lineNumber));
      }
    }

    return issues;
  }

  /**
   * Check for security issues
   */
  private checkSecurityIssues(file: string, line: string, lineNumber: number): CodeReviewIssue[] {
    const issues: CodeReviewIssue[] = [];

    // SQL injection risk
    if (/`?\$\{[^}]+\}`?/.test(line) && /(SELECT|INSERT|UPDATE|DELETE|DROP)/i.test(line)) {
      issues.push({
        severity: 'critical',
        type: 'security',
        file,
        line: lineNumber,
        message: 'Potential SQL injection',
        suggestion: 'Use parameterized queries or ORM',
      });
    }

    // Eval usage
    if (/eval\s*\(/.test(line)) {
      issues.push({
        severity: 'critical',
        type: 'security',
        file,
        line: lineNumber,
        message: 'Use of eval() is dangerous',
        suggestion: 'Avoid eval() for security reasons',
      });
    }

    // Hardcoded secrets
    if (/password|api[_-]?key|secret|token/i.test(line) &&
        /=\s*['"`][^'"`]+['"`]/.test(line)) {
      issues.push({
        severity: 'critical',
        type: 'security',
        file,
        line: lineNumber,
        message: 'Hardcoded credentials detected',
        suggestion: 'Use environment variables or secret management',
      });
    }

    // console.log in production code
    if (/console\.(log|debug|info|warn|error)/.test(line) &&
        !/\/\/.*console/.test(line) &&
        !line.trim().startsWith('//')) {
      issues.push({
        severity: 'minor',
        type: 'best-practice',
        file,
        line: lineNumber,
        message: 'Console statement found',
        suggestion: 'Remove console statements in production code',
      });
    }

    return issues;
  }

  /**
   * Check for error handling
   */
  private checkErrorHandling(file: string, line: string, lineNumber: number): CodeReviewIssue[] {
    const issues: CodeReviewIssue[] = [];

    // Empty catch block
    if (/catch\s*\([^)]*\)\s*\{\s*\}/.test(line) ||
        (line.includes('catch') && line.includes('{}'))) {
      issues.push({
        severity: 'major',
        type: 'error',
        file,
        line: lineNumber,
        message: 'Empty catch block',
        suggestion: 'Add error handling or logging',
      });
    }

    // No error handling for async operations
    if (/await\s+/.test(line) && !/try|catch/.test(line)) {
      // This is a heuristic, not perfect
    }

    return issues;
  }

  /**
   * Check for performance issues
   */
  private checkPerformance(file: string, line: string, lineNumber: number): CodeReviewIssue[] {
    const issues: CodeReviewIssue[] = [];

    // Inefficient loops
    if (/for\s*\(\s*\w+\s+in\s+.*\.length/.test(line)) {
      issues.push({
        severity: 'minor',
        type: 'performance',
        file,
        line: lineNumber,
        message: 'Length calculation in loop condition',
        suggestion: 'Cache length before loop',
      });
    }

    // Nested loops with complex operations (heuristic)
    if (line.includes('for') && line.match(/for.*for/)) {
      issues.push({
        severity: 'minor',
        type: 'performance',
        file,
        line: lineNumber,
        message: 'Nested loop detected',
        suggestion: 'Consider optimizing algorithm complexity',
      });
    }

    // String concatenation in loop
    if (/\+\s*=.*['"`]/.test(line) && /for|while/.test(line)) {
      issues.push({
        severity: 'minor',
        type: 'performance',
        file,
        line: lineNumber,
        message: 'String concatenation in loop',
        suggestion: 'Use array join or template literals',
      });
    }

    return issues;
  }

  /**
   * Check for style and best practices
   */
  private checkStyle(file: string, line: string, lineNumber: number): CodeReviewIssue[] {
    const issues: CodeReviewIssue[] = [];

    // Magic numbers
    if (/[=!<>]\s*\d{2,}/.test(line) && !/\/\/\s*\d+/.test(line)) {
      issues.push({
        severity: 'minor',
        type: 'best-practice',
        file,
        line: lineNumber,
        message: 'Magic number detected',
        suggestion: 'Extract to a named constant',
      });
    }

    // Long line
    if (line.length > 120) {
      issues.push({
        severity: 'info',
        type: 'style',
        file,
        line: lineNumber,
        message: 'Line exceeds 120 characters',
        suggestion: 'Break line for better readability',
      });
    }

    // TODO comments
    if (/TODO|FIXME|HACK|XXX/i.test(line)) {
      issues.push({
        severity: 'minor',
        type: 'best-practice',
        file,
        line: lineNumber,
        message: 'TODO comment found',
        suggestion: 'Address or create a tracking issue',
      });
    }

    return issues;
  }

  /**
   * Calculate review statistics
   */
  private calculateStats(
    diffFiles: Array<{ file: string; addedLines: string[] }>,
    issues: CodeReviewIssue[]
  ): CodeReviewResult['stats'] {
    const filesChanged = diffFiles.length;
    const totalLinesChanged = diffFiles.reduce((sum, f) => sum + f.addedLines.length, 0);

    const criticalIssues = issues.filter(i => i.severity === 'critical').length;
    const majorIssues = issues.filter(i => i.severity === 'major').length;
    const minorIssues = issues.filter(i => i.severity === 'minor').length;
    const infoIssues = issues.filter(i => i.severity === 'info').length;

    return {
      filesChanged,
      totalLinesChanged,
      criticalIssues,
      majorIssues,
      minorIssues,
      infoIssues,
    };
  }

  /**
   * Calculate overall score (0-100)
   */
  private calculateScore(stats: CodeReviewResult['stats']): number {
    let score = 100;

    // Deduct points for issues
    score -= stats.criticalIssues * 20;
    score -= stats.majorIssues * 10;
    score -= stats.minorIssues * 3;
    score -= stats.infoIssues * 1;

    // Bonus for reasonable code size
    if (stats.totalLinesChanged > 0 && stats.totalLinesChanged < 500) {
      score += 5;
    }

    // Ensure score is between 0 and 100
    return Math.max(0, Math.min(100, score));
  }

  /**
   * Generate review summary
   */
  private generateSummary(stats: CodeReviewResult['stats']): string {
    const totalIssues = stats.criticalIssues + stats.majorIssues + stats.minorIssues + stats.infoIssues;

    if (stats.criticalIssues > 0) {
      return `Found ${stats.criticalIssues} critical issue${stats.criticalIssues > 1 ? 's' : ''} that must be fixed.`;
    } else if (stats.majorIssues > 0) {
      return `Found ${stats.majorIssues} major issue${stats.majorIssues > 1 ? 's' : ''} that should be addressed.`;
    } else if (totalIssues > 0) {
      return `Found ${totalIssues} minor improvement${totalIssues > 1 ? 's' : ''}. Code quality is good.`;
    } else {
      return 'Code review passed! No issues found.';
    }
  }

  /**
   * Collect positive findings
   */
  private collectPositiveFindings(diffFiles: Array<{ file: string; addedLines: string[] }>): string[] {
    const findings: string[] = [];

    const totalLines = diffFiles.reduce((sum, f) => sum + f.addedLines.length, 0);

    if (totalLines > 0) {
      findings.push(`${totalLines} lines of code added across ${diffFiles.length} file${diffFiles.length > 1 ? 's' : ''}`);
    }

    // Check for TypeScript/types
    const hasTypes = diffFiles.some(f =>
      f.addedLines.some(l => /:\s*(string|number|boolean|void|interface|type|enum)/.test(l))
    );
    if (hasTypes) {
      findings.push('Good type usage detected');
    }

    // Check for comments
    const hasComments = diffFiles.some(f =>
      f.addedLines.some(l => /^\s*\/\/\s*\w/.test(l))
    );
    if (hasComments) {
      findings.push('Code includes documentation comments');
    }

    return findings;
  }

  /**
   * Generate markdown review report
   */
  generateReport(result: CodeReviewResult): string {
    const statusIcon = result.status === 'passed' ? '✓' : result.status === 'needs-work' ? '⚠' : '✗';
    const statusColor = result.status === 'passed' ? 'green' : result.status === 'needs-work' ? 'yellow' : 'red';

    let report = `# Code Review: ${result.changeName}\n\n`;
    report += `**Overall Score**: ${result.overallScore}/100\n`;
    report += `**Status**: ${statusIcon} ${result.status}\n\n`;
    report += `## Summary\n\n`;
    report += `${result.summary}\n\n`;
    report += `## Statistics\n\n`;
    report += `- Files changed: ${result.stats.filesChanged}\n`;
    report += `- Lines added: ${result.stats.totalLinesChanged}\n`;
    report += `- Critical issues: ${result.stats.criticalIssues}\n`;
    report += `- Major issues: ${result.stats.majorIssues}\n`;
    report += `- Minor issues: ${result.stats.minorIssues}\n`;
    report += `- Info issues: ${result.stats.infoIssues}\n\n`;

    if (result.issues.length > 0) {
      report += `## Issues\n\n`;
      const grouped = this.groupIssuesByType(result.issues);
      for (const [type, typeIssues] of Object.entries(grouped)) {
        report += `### ${type}\n\n`;
        for (const issue of typeIssues as CodeReviewIssue[]) {
          const severityIcon = issue.severity === 'critical' ? '🔴' : issue.severity === 'major' ? '🟡' : issue.severity === 'minor' ? '🟠' : '🔵';
          report += `${severityIcon} **${issue.file}${issue.line ? `:${issue.line}` : ''}**: ${issue.message}\n`;
          if (issue.suggestion) {
            report += `   Suggestion: ${issue.suggestion}\n`;
          }
          report += '\n';
        }
      }
    }

    if (result.positiveFindings.length > 0) {
      report += `## Positive Findings\n\n`;
      result.positiveFindings.forEach(finding => {
        report += `✓ ${finding}\n`;
      });
      report += '\n';
    }

    report += `---\n\n`;
    report += `*Generated by OpenSpec Code Reviewer*\n`;

    return report;
  }

  /**
   * Group issues by type
   */
  private groupIssuesByType(issues: CodeReviewIssue[]): Record<string, CodeReviewIssue[]> {
    const grouped: Record<string, CodeReviewIssue[]> = {};

    for (const issue of issues) {
      const type = issue.type.charAt(0).toUpperCase() + issue.type.slice(1);
      if (!grouped[type]) {
        grouped[type] = [];
      }
      grouped[type].push(issue);
    }

    return grouped;
  }

  /**
   * Save review report to file
   */
  async saveReport(result: CodeReviewResult, outputPath?: string): Promise<string> {
    const report = this.generateReport(result);

    if (!outputPath) {
      outputPath = path.join(this.changeDir, 'review.md');
    }

    await fs.writeFile(outputPath, report, 'utf-8');
    return outputPath;
  }
}