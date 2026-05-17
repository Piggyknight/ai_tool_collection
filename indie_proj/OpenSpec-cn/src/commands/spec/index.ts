/**
 * Sprint Spec Commands
 *
 * Commands for generating and managing sprint specification documentation.
 */

import { Command } from 'commander';
import inquirer from 'inquirer';
import ora from 'ora';
import chalk from 'chalk';
import path from 'path';
import { SpecGenerator, SprintSummary } from '../../core/spec/generator.js';
import yaml from 'yaml';
import { promises as fs } from 'fs';
import { getInstanceManager } from '../../core/redmine/instance-manager.js';
import { RedmineCliWrapper } from '../../core/redmine/cli-wrapper.js';
import { OneWaySyncManager } from '../../core/redmine/one-way-sync.js';
import { StatusMapper } from '../../core/redmine/status-mapping.js';

/**
 * Generate spec for a sprint
 */
async function generateSpec(sprintName: string, options: {
  includeCodeStats?: boolean;
  includeTimeStats?: boolean;
  output?: string;
  verbose?: boolean;
}) {
  const generator = new SpecGenerator(process.cwd());

  console.log(chalk.cyan(`\n📄 Generating spec: ${sprintName}\n`));

  const spinner = ora('Analyzing sprint data...').start();

  try {
    const summary = await generator.generateSprintSummary({
      sprintName,
      includeCodeStats: options.includeCodeStats,
      includeTimeStats: options.includeTimeStats,
    });

    spinner.text = 'Generating spec document...';

    const outputPath = await generator.generateSpecDocument(summary, options.output);

    spinner.succeed(chalk.green('Spec generated successfully!'));

    if (options.verbose) {
      displaySummary(summary);
    }

    console.log(chalk.gray(`\n  Output: ${outputPath}\n`));
  } catch (error) {
    spinner.fail('Failed to generate spec');
    console.log(chalk.red(`\n${(error as Error).message}\n`));
  }
}

/**
 * Upload spec to Redmine Wiki
 */
async function uploadSpec(sprintName: string, options: {
  format?: string;
  page?: string;
}) {
  const specPath = path.join(process.cwd(), 'openspec', 'sprints', sprintName, 'summary.md');

  try {
    await fs.access(specPath);
  } catch {
    console.log(chalk.red(`\nSpec file not found: ${specPath}\n`));
    console.log(chalk.gray('Run `openspec sprint-spec generate <sprint-name>` first.\n'));
    return;
  }

  console.log(chalk.cyan(`\n📤 Uploading spec to Redmine: ${sprintName}\n`));

  const spinner = ora('Uploading to Redmine Wiki...').start();

  try {
    const specContent = await fs.readFile(specPath, 'utf-8');

    const manager = getInstanceManager();
    const wrapper = await manager.createWrapper();
    const mapper = new StatusMapper();
    const syncManager = new OneWaySyncManager(wrapper, mapper, process.cwd());

    const sprintPath = path.join(process.cwd(), 'openspec', 'sprints', sprintName);
    const metadataPath = path.join(sprintPath, '.openspec.yaml');

    const metadata = yaml.parse(await fs.readFile(metadataPath, 'utf-8'));
    const versionId = metadata.redmine?.versionId;

    if (!versionId) {
      spinner.warn('No Redmine version ID found');
      console.log(chalk.yellow('\nSkipping upload to Redmine Wiki.\n'));
      return;
    }

    // TODO: Implement Redmine Wiki API upload
    // This requires the Redmine API as CLI may not support wiki uploads

    spinner.succeed(chalk.green('Spec ready for upload'));
    console.log(chalk.gray('\nNote: Redmine Wiki upload requires API integration.\n'));
    console.log(chalk.gray(`Spec saved at: ${specPath}\n`));
  } catch (error) {
    spinner.fail('Upload failed');
    console.log(chalk.red(`\n${(error as Error).message}\n`));
  }
}

/**
 * List all specs
 */
async function listSpecs(): Promise<void> {
  const sprintsPath = path.join(process.cwd(), 'openspec', 'sprints');
  const specsPath = path.join(process.cwd(), 'openspec', 'specs');

  console.log(chalk.cyan('\n📄 Available Specs\n'));

  // Sprint summaries
  try {
    const entries = await fs.readdir(sprintsPath, { withFileTypes: true });
    const sprintDirs = entries.filter(e => e.isDirectory());

    for (const dir of sprintDirs) {
      const summaryPath = path.join(sprintsPath, dir.name, 'summary.md');
      if (await fileExists(summaryPath)) {
        console.log(chalk.bold(`Sprint: ${dir.name}`));
        console.log(chalk.gray(`  ${summaryPath}\n`));
      }
    }
  } catch {
    console.log(chalk.gray('No sprint summaries found.\n'));
  }

  // Main specs
  try {
    const entries = await fs.readdir(specsPath, { withFileTypes: true });
    const specFiles = entries.filter(e => e.isFile() && e.name.endsWith('.md'));

    if (specFiles.length > 0) {
      console.log(chalk.bold('Main Specs:\n'));
      for (const file of specFiles) {
        console.log(`  ${file.name}`);
      }
      console.log('');
    }
  } catch {
    console.log(chalk.gray('No main specs found.\n'));
  }
}

/**
 * Display sprint summary
 */
function displaySummary(summary: SprintSummary): void {
  console.log(chalk.bold('📊 Sprint Summary\n'));

  // Statistics
  const progress = Math.round((summary.completedTasks / Math.max(summary.totalTasks, 1)) * 100);
  const progressColor = progress === 100 ? chalk.green : progress >= 80 ? chalk.yellow : chalk.red;

  console.log('Statistics:');
  console.log(`  Stories: ${summary.completedStories}/${summary.totalStories}`);
  console.log(`  Tasks: ${summary.completedTasks}/${summary.totalTasks}`);
  console.log(`  Progress: ${progressColor(`${progress}%`)}`);
  console.log(`  Bugs: ${summary.fixedBugs}/${summary.totalBugs} (${summary.openBugs} open)\n`);

  // Documents
  if (Object.values(summary.documents).some(d => d.length > 0)) {
    console.log(chalk.bold('Documents:'));
    if (summary.documents.proposals.length > 0) {
      console.log(`  Proposals: ${summary.documents.proposals.length}`);
    }
    if (summary.documents.specs.length > 0) {
      console.log(`  Specs: ${summary.documents.specs.length}`);
    }
    if (summary.documents.designs.length > 0) {
      console.log(`  Designs: ${summary.documents.designs.length}`);
    }
    console.log('');
  }

  // Code
  if (summary.code.filesChanged > 0) {
    console.log(chalk.bold('Code Changes:'));
    console.log(`  Files: ${summary.code.filesChanged}`);
    console.log(`  Lines: +${summary.code.linesAdded} -${summary.code.linesDeleted}`);
    console.log(`  Commits: ${summary.code.commits.length}`);
    console.log('');
  }

  // Time
  if (summary.timeStats.actualHours > 0) {
    console.log(chalk.bold('Time:'));
    console.log(`  Estimated: ${summary.timeStats.estimatedHours}h`);
    console.log(`  Actual: ${summary.timeStats.actualHours}h`);
    const variance = summary.timeStats.actualHours - summary.timeStats.estimatedHours;
    const varianceColor = variance < 0 ? chalk.green : chalk.red;
    console.log(`  Variance: ${varianceColor(`${variance >= 0 ? '+' : ''}${variance}h`)}\n`);
  }

  // Incomplete
  if (summary.incomplete.stories.length > 0) {
    console.log(chalk.bold('Incomplete:'));
    console.log(chalk.red(`  Stories: ${summary.incomplete.stories.length}`));
  }
  if (summary.incomplete.blockers.length > 0) {
    console.log(chalk.red(`  Blockers: ${summary.incomplete.blockers.length}`));
  }
  if (summary.incomplete.blockers.length > 0 || summary.incomplete.stories.length > 0) {
    console.log('');
  }

  // Lessons
  if (summary.lessons.positive.length > 0) {
    console.log(chalk.green('✓ Positives:'));
    summary.lessons.positive.forEach(l => {
      console.log(chalk.green(`  ${l}`));
    });
    console.log('');
  }

  if (summary.lessons.improvements.length > 0) {
    console.log(chalk.yellow('⚠ Improvements:'));
    summary.lessons.improvements.forEach(l => {
      console.log(chalk.yellow(`  ${l}`));
    });
    console.log('');
  }
}

/**
 * Check if file exists
 */
async function fileExists(filePath: string): Promise<boolean> {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

/**
 * Register spec commands with the CLI
 */
export function registerSpecCommand(program: Command): void {
  const specCmd = program
    .command('sprint-spec')
    .description('Sprint specification documentation');

  specCmd
    .command('generate <sprint-name>')
    .description('Generate spec document for a sprint')
    .option('--code-stats', 'Include code statistics')
    .option('--time-stats', 'Include time statistics')
    .option('-o, --output <path>', 'Output file path')
    .option('-v, --verbose', 'Show verbose output')
    .action((sprintName, options) => generateSpec(sprintName, options));

  specCmd
    .command('upload <sprint-name>')
    .description('Upload spec to Redmine Wiki')
    .option('-f, --format <type>', 'Document format (markdown)')
    .option('-p, --page <name>', 'Wiki page name')
    .action((sprintName, options) => uploadSpec(sprintName, options));

  specCmd
    .command('list')
    .description('List all spec documents')
    .action(() => listSpecs());
}