/**
 * Code Review Commands
 *
 * Commands for reviewing code changes using local analysis.
 */

import { Command } from 'commander';
import ora from 'ora';
import chalk from 'chalk';
import path from 'path';
import yaml from 'yaml';
import { promises as fs } from 'fs';
import { getInstanceManager } from '../../core/redmine/instance-manager.js';
import { RedmineCliWrapper } from '../../core/redmine/cli-wrapper.js';
import { OneWaySyncManager } from '../../core/redmine/one-way-sync.js';
import { StatusMapper } from '../../core/redmine/status-mapping.js';
import { CodeReviewer, CodeReviewResult } from '../../core/code-review/reviewer.js';

/**
 * Review a change
 */
async function reviewChange(changeName: string, options: {
  branch?: string;
  baseBranch?: string;
  save?: boolean;
  output?: string;
  verbose?: boolean;
  sync?: boolean;
}) {
  const reviewer = new CodeReviewer(process.cwd());

  console.log(chalk.cyan(`\n🔍 Starting code review...\n`));

  const spinner = ora('Running review...').start();

  try {
    const result = await reviewer.review({
      changeName,
      branch: options.branch,
      baseBranch: options.baseBranch,
      verbose: options.verbose,
    });

    spinner.stop();

    // Display results
    displayReviewResult(result, options.verbose);

    // Save report
    if (options.save || options.output) {
      const outputPath = await reviewer.saveReport(result, options.output);
      console.log(chalk.green(`\n✓ Review saved to: ${outputPath}\n`));
    }

    // Sync to Redmine
    if (options.sync && result.status !== 'passed') {
      try {
        await syncToRedmine(changeName, result);
      } catch (error) {
        console.log(chalk.yellow('\nRedmine sync skipped:', (error as Error).message));
      }
    } else if (options.sync) {
      console.log(chalk.gray('\nReview passed, no Redmine sync needed.\n'));
    }
  } catch (error) {
    spinner.fail('Review failed');
    console.log(chalk.red(`\n${(error as Error).message}\n`));
  }
}

/**
 * Review all changes in a sprint
 */
async function reviewSprint(sprintName: string, options: {
  failOnIssues?: boolean;
  verbose?: boolean;
}) {
  const openspecDir = path.join(process.cwd(), 'openspec');
  const sprintPath = path.join(openspecDir, 'sprints', sprintName);
  const metadataPath = path.join(sprintPath, '.openspec.yaml');

  try {
    await fs.access(metadataPath);
  } catch {
    console.log(chalk.red(`\nSprint '${sprintName}' not found.\n`));
    return;
  }

  console.log(chalk.cyan(`\n🔍 Reviewing sprint: ${sprintName}\n`));

  // Get changes in sprint
  let changes: string[] = [];
  try {
    const content = await fs.readFile(metadataPath, 'utf-8');
    const metadata = yaml.parse(content);
    changes = metadata.changes?.map((c: any) => c.name) || [];
  } catch {
    console.log(chalk.yellow('No changes found in sprint.\n'));
    return;
  }

  if (changes.length === 0) {
    console.log(chalk.yellow('No changes to review.\n'));
    return;
  }

  console.log(chalk.gray(`Reviewing ${changes.length} changes:\n`));

  const results: Array<{ change: string; result: CodeReviewResult }> = [];

  for (const change of changes) {
    try {
      const reviewer = new CodeReviewer(process.cwd());
      const result = await reviewer.review({ changeName: change });
      results.push({ change, result });
    } catch (error) {
      console.log(chalk.red(`✗ ${change}: ${(error as Error).message}\n`));
    }
  }

  // Display summary
  console.log(chalk.cyan('\n## Sprint Review Summary\n'));

  const totalScore = results.reduce((sum, r) => sum + r.result.overallScore, 0);
  const avgScore = Math.round(totalScore / results.length);
  const passed = results.filter(r => r.result.status === 'passed').length;
  const needsWork = results.filter(r => r.result.status === 'needs-work').length;
  const failed = results.filter(r => r.result.status === 'failed').length;

  console.log(chalk.bold(`Average Score: ${avgScore}/100`));
  console.log(`Passed: ${chalk.green(passed)} | Needs Work: ${chalk.yellow(needsWork)} | Failed: ${chalk.red(failed)}\n`);

  // Show changes that need attention
  const needsAttention = results.filter(r => r.result.status !== 'passed');
  if (needsAttention.length > 0) {
    console.log(chalk.yellow('Changes needing attention:\n'));
    for (const item of needsAttention) {
      console.log(`  ${item.change} (${item.result.overallScore}/100): ${item.result.summary}`);
    }
    console.log('');
  }

  // Exit with error if failOnIssues and there are issues
  if (options.failOnIssues && (needsWork + failed > 0)) {
    console.log(chalk.red('\nReview failed! Please address the issues above.\n'));
    process.exit(1);
  }
}

/**
 * Display review result
 */
function displayReviewResult(result: CodeReviewResult, verbose: boolean = false): void {
  // Score with color
  let scoreColor: (s: string) => string = chalk.green;
  if (result.overallScore < 60) {
    scoreColor = chalk.red;
  } else if (result.overallScore < 80) {
    scoreColor = chalk.yellow;
  }

  console.log(chalk.bold('Overall Score:'), scoreColor(`${result.overallScore}/100`));

  // Status with icon
  const statusIcons = { passed: '✓', 'needs-work': '⚠', 'failed': '✗' };
  const statusColors = { passed: chalk.green, 'needs-work': chalk.yellow, 'failed': chalk.red };
  console.log(chalk.bold('Status:'), statusColors[result.status](`${statusIcons[result.status]} ${result.status}`));
  console.log('');

  // Summary
  console.log(chalk.bold('Summary:'));
  console.log(`  ${result.summary}\n`);

  // Statistics
  console.log(chalk.bold('Statistics:'));
  console.log(`  Files changed: ${result.stats.filesChanged}`);
  console.log(`  Lines added: ${result.stats.totalLinesChanged}`);
  console.log(`  Issues: ${result.stats.criticalIssues + result.stats.majorIssues + result.stats.minorIssues + result.stats.infoIssues}`);
  if (result.stats.criticalIssues > 0) {
    console.log(`    - Critical: ${chalk.red(result.stats.criticalIssues)}`);
  }
  if (result.stats.majorIssues > 0) {
    console.log(`    - Major: ${chalk.yellow(result.stats.majorIssues)}`);
  }
  if (result.stats.minorIssues > 0) {
    console.log(`    - Minor: ${chalk.blue(result.stats.minorIssues)}`);
  }
  console.log('');

  // Positive findings
  if (result.positiveFindings.length > 0) {
    console.log(chalk.bold('Positive Findings:'));
    result.positiveFindings.forEach(finding => {
      console.log(chalk.green(`  ✓ ${finding}`));
    });
    console.log('');
  }

  // Issues (show all in verbose mode, otherwise only critical/major)
  if (result.issues.length > 0) {
    const issuesToShow = verbose
      ? result.issues
      : result.issues.filter(i => i.severity === 'critical' || i.severity === 'major');

    if (issuesToShow.length > 0) {
      console.log(chalk.bold('Issues:'));
      for (const issue of issuesToShow) {
        const severityColor = {
          'critical': chalk.red,
          'major': chalk.yellow,
          'minor': chalk.blue,
          'info': chalk.gray,
        }[issue.severity];

        console.log(`${severityColor(`[${issue.severity.toUpperCase()}]`)} ${issue.file}${issue.line ? `:${issue.line}` : ''}`);
        console.log(`  ${issue.message}`);
        if (issue.suggestion) {
          console.log(chalk.gray(`  → ${issue.suggestion}`));
        }
        console.log('');
      }
    }
  }
}

/**
 * Sync review result to Redmine
 */
async function syncToRedmine(changeName: string, result: CodeReviewResult): Promise<void> {
  const manager = getInstanceManager();
  const wrapper = await manager.createWrapper();
  const mapper = new StatusMapper();
  const syncManager = new OneWaySyncManager(wrapper, mapper, process.cwd());
  const changePath = path.join(process.cwd(), 'openspec', 'changes', changeName);

  const metadata = await syncManager.getSyncMetadata(changePath);
  if (!metadata?.issueId) {
    console.log(chalk.yellow('No Redmine issue found for this change.\n'));
    return;
  }

  // Update status to code-review
  await wrapper.updateStatus(metadata.issueId, mapper.hermesToRedmine('code-review'));

  // Add review note
  const note = `Code Review completed: ${result.overallScore}/100\n\nStatus: ${result.status}\n\n${result.summary}`;
  await wrapper.addNote(metadata.issueId, note);

  console.log(chalk.green(`✓ Synced to Redmine issue #${metadata.issueId}\n`));
}

/**
 * Register review commands with the CLI
 */
export function registerReviewCommand(program: Command): void {
  const reviewCmd = program
    .command('review')
    .description('Code review');

  reviewCmd
    .command('change <change-name>')
    .description('Review a change')
    .option('-b, --branch <name>', 'Branch to review')
    .option('--base <name>', 'Base branch (default: main)')
    .option('-s, --save', 'Save review report')
    .option('-o, --output <path>', 'Output file path')
    .option('-v, --verbose', 'Show verbose output')
    .option('--sync', 'Sync review result to Redmine')
    .action((changeName, options) => reviewChange(changeName, options));

  reviewCmd
    .command('sprint <sprint-name>')
    .description('Review all changes in a sprint')
    .option('-f, --fail-on-issues', 'Fail on any issues')
    .option('-v, --verbose', 'Show verbose output')
    .action((sprintName, options) => reviewSprint(sprintName, options));
}