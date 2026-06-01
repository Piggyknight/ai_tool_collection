/**
 * Task Management Commands with Redmine Sync
 *
 * Commands for managing tasks and syncing progress to Redmine.
 */

import { Command } from 'commander';
import ora from 'ora';
import chalk from 'chalk';
import path from 'path';
import { promises as fs } from 'fs';
import yaml from 'yaml';
import { getInstanceManager } from '../../core/redmine/instance-manager.js';
import { RedmineCliWrapper } from '../../core/redmine/cli-wrapper.js';
import { OneWaySyncManager } from '../../core/redmine/one-way-sync.js';
import { StatusMapper, HermesState } from '../../core/redmine/status-mapping.js';

const OPENSPEC_DIR = 'openspec';
const CHANGES_DIR = path.join(OPENSPEC_DIR, 'changes');

/**
 * Break down a story into tasks
 */
async function breakdownTasks(storyName: string, options: {
  parentIssueId?: number;
  interactive?: boolean;
  dryRun?: boolean;
}) {
  const changePath = path.join(process.cwd(), CHANGES_DIR, storyName);
  const tasksPath = path.join(changePath, 'tasks.md');

  // Check if change exists
  try {
    await fs.access(changePath);
  } catch {
    console.log(chalk.red(`\nStory '${storyName}' not found.\n`));
    console.log(chalk.gray('Run `openspec new change <name>` to create a change.\n'));
    return;
  }

  console.log(chalk.cyan(`\n📋 Breaking down tasks for: ${storyName}\n`));

  // Read proposal.md and story.md for context
  const proposalPath = path.join(changePath, 'proposal.md');
  const storyPath = path.join(changePath, 'story.md');

  let proposalContent = '';
  let storyContent = '';

  try {
    proposalContent = await fs.readFile(proposalPath, 'utf-8');
  } catch {
    console.log(chalk.yellow('No proposal.md found, using minimal template.\n'));
  }

  try {
    storyContent = await fs.readFile(storyPath, 'utf-8');
  } catch {
    console.log(chalk.yellow('No story.md found, using minimal template.\n'));
  }

  // Generate tasks.md content
  const tasksContent = generateTasksContent(storyName, proposalContent, storyContent);

  if (options.dryRun) {
    console.log(chalk.cyan('[Dry Run] Generated tasks.md:\n'));
    console.log(tasksContent);
    return;
  }

  await fs.writeFile(tasksPath, tasksContent, 'utf-8');

  console.log(chalk.green('✓ Tasks.md created successfully!\n'));
  console.log(chalk.gray(`  Location: ${tasksPath}\n`));

  // Sync to Redmine
  try {
    const manager = getInstanceManager();
    const wrapper = await manager.createWrapper();
    const mapper = new StatusMapper();
    const syncManager = new OneWaySyncManager(wrapper, mapper, process.cwd());

    const spinner = ora('Syncing to Redmine...').start();

    // Get parent issue ID from story or use provided parent
    let parentId = options.parentIssueId;
    if (!parentId) {
      const metadata = await syncManager.getSyncMetadata(changePath);
      parentId = metadata?.issueId;
    }

    // Create Redmine issues for each task
    const tasks = parseTasks(tasksContent);
    for (const task of tasks) {
      const taskName = `${storyName}: ${task.text}`;
      await syncManager.syncTask(changePath, task.text, parentId || 0);
    }

    spinner.succeed(chalk.green('Tasks synced to Redmine!'));
  } catch (error) {
    console.log(chalk.yellow('\nRedmine sync skipped:', (error as Error).message));
  }
}

/**
 * Sync task progress to Redmine
 */
async function syncTasks(changeName: string, options: {
  dryRun?: boolean;
  verbose?: boolean;
}) {
  const changePath = path.join(process.cwd(), CHANGES_DIR, changeName);
  const tasksPath = path.join(changePath, 'tasks.md');

  // Check if change exists
  try {
    await fs.access(changePath);
  } catch {
    console.log(chalk.red(`\nChange '${changeName}' not found.\n`));
    return;
  }

  console.log(chalk.cyan(`\n🔄 Syncing tasks for: ${changeName}\n`));

  // Parse tasks.md
  const tasks = parseTasks(tasksPath);
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter(t => t.checked).length;
  const progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  console.log(chalk.gray(`Progress: ${completedTasks}/${totalTasks} (${progress}%)\n`));

  if (options.dryRun) {
    console.log(chalk.cyan('[Dry Run] Would update Redmine with:'));
    console.log(chalk.gray(`  Progress: ${progress}%`));
    console.log(chalk.gray(`  Status: ${getHermesStateFromProgress(progress)}\n`));
    return;
  }

  // Sync to Redmine
  try {
    const manager = getInstanceManager();
    const wrapper = await manager.createWrapper();
    const mapper = new StatusMapper();
    const syncManager = new OneWaySyncManager(wrapper, mapper, process.cwd());

    const result = await syncManager.syncProgress(changePath, options);

    if (result.success) {
      console.log(chalk.green('✓ Progress synced to Redmine!'));

      if (options.verbose) {
        const metadata = await syncManager.getSyncMetadata(changePath);
        if (metadata?.issueId) {
          console.log(chalk.gray(`  Issue #${metadata.issueId}`));
        }
      }

      // Show completed tasks
      if (completedTasks > 0) {
        console.log(chalk.cyan('\n✓ Completed tasks:'));
        tasks.filter(t => t.checked).forEach(t => {
          console.log(chalk.green(`  ✓ ${t.text}`));
        });
        console.log('');
      }

      // Show remaining tasks
      const remaining = tasks.filter(t => !t.checked);
      if (remaining.length > 0) {
        console.log(chalk.cyan('○ Remaining tasks:'));
        remaining.forEach(t => {
          console.log(chalk.gray(`  ○ ${t.text}`));
        });
        console.log('');
      }
    } else {
      console.log(chalk.yellow('\nNo Redmine issue found for this change.\n'));
    }
  } catch (error) {
    console.log(chalk.red('\nSync failed:'));
    console.log(chalk.red((error as Error).message));
  }
}

/**
 * Show task status
 */
async function showStatus(changeName: string) {
  const changePath = path.join(process.cwd(), CHANGES_DIR, changeName);
  const tasksPath = path.join(changePath, 'tasks.md');

  // Check if change exists
  try {
    await fs.access(changePath);
  } catch {
    console.log(chalk.red(`\nChange '${changeName}' not found.\n`));
    return;
  }

  console.log(chalk.cyan(`\n📊 Task Status: ${changeName}\n`));

  // Parse tasks.md
  const tasks = parseTasks(tasksPath);
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter(t => t.checked).length;
  const progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  // Show progress bar
  const filled = Math.floor(progress / 10);
  const empty = 10 - filled;
  const bar = '█'.repeat(filled) + '░'.repeat(empty);
  const barColor = progress === 100 ? chalk.green : progress > 50 ? chalk.yellow : chalk.red;

  console.log(barColor(`${bar} ${progress}%`));
  console.log(chalk.gray(`${completedTasks}/${totalTasks} tasks completed\n`));

  // Group by section
  const sections = new Map<string, typeof tasks>();
  let currentSection = 'General';

  for (const task of tasks) {
    if (task.section) {
      currentSection = task.section;
    }
    if (!sections.has(currentSection)) {
      sections.set(currentSection, []);
    }
    sections.get(currentSection)!.push(task);
  }

  // Display tasks by section
  for (const [section, sectionTasks] of sections) {
    console.log(chalk.bold(`\n## ${section}`));
    for (const task of sectionTasks) {
      if (task.checked) {
        console.log(chalk.green(`  ✓ ${task.text}`));
      } else {
        console.log(chalk.gray(`  ○ ${task.text}`));
      }
    }
  }

  // Show Redmine sync status
  try {
    const manager = getInstanceManager();
    const wrapper = await manager.createWrapper();
    const mapper = new StatusMapper();
    const syncManager = new OneWaySyncManager(wrapper, mapper, process.cwd());

    const metadata = await syncManager.getSyncMetadata(changePath);
    if (metadata?.issueId) {
      console.log(chalk.cyan('\n📌 Redmine:'));
      console.log(chalk.gray(`  Issue #${metadata.issueId}`));
      console.log(chalk.gray(`  Sync Status: ${metadata.syncStatus}`));
      console.log(chalk.gray(`  Last Sync: ${metadata.lastSync}`));
    } else {
      console.log(chalk.yellow('\n📌 Redmine: Not synced'));
    }
  } catch {
    console.log(chalk.yellow('\n📌 Redmine: Not configured'));
  }

  console.log('');
}

/**
 * Parse tasks from tasks.md
 */
interface ParsedTask {
  text: string;
  checked: boolean;
  section?: string;
  order: number;
}

function parseTasks(content: string): ParsedTask[] {
  const tasks: ParsedTask[] = [];
  const lines = content.split('\n');
  let currentSection = '';
  let order = 0;

  for (const line of lines) {
    // Check for section headers (##)
    const sectionMatch = line.match(/^##\s+(.+)$/);
    if (sectionMatch) {
      currentSection = sectionMatch[1].trim();
      continue;
    }

    // Check for task items (- [ ] or - [x])
    const taskMatch = line.match(/^\s*-\s*\[([ x])\]\s*(.+)$/);
    if (taskMatch) {
      const [, checked, text] = taskMatch;
      tasks.push({
        text: text.trim(),
        checked: checked === 'x',
        section: currentSection || undefined,
        order: order++,
      });
    }
  }

  return tasks;
}

/**
 * Generate tasks.md content
 */
function generateTasksContent(storyName: string, proposal: string, story: string): string {
  const today = new Date().toISOString().split('T')[0];

  let content = `# Tasks: ${storyName}\n\n`;
  content += `**Created**: ${today}\n\n`;
  content += `## Setup\n\n`;
  content += `- [ ] 1.1 Initialize project structure\n`;
  content += `- [ ] 1.2 Configure development environment\n`;
  content += `- [ ] 1.3 Set up dependencies\n\n`;
  content += `## Implementation\n\n`;
  content += `- [ ] 2.1 Implement core functionality\n`;
  content += `- [ ] 2.2 Add error handling\n`;
  content += `- [ ] 2.3 Integrate with Redmine\n`;
  content += `- [ ] 2.4 Write unit tests\n\n`;
  content += `## Testing\n\n`;
  content += `- [ ] 3.1 Manual testing\n`;
  content += `- [ ] 3.2 Automated testing\n`;
  content += `- [ ] 3.3 Edge case testing\n\n`;
  content += `## Documentation\n\n`;
  content += `- [ ] 4.1 Update API documentation\n`;
  content += `- [ ] 4.2 Write user guide\n`;
  content += `- [ ] 4.3 Update README\n\n`;
  content += `---\n\n`;
  content += `*Last updated: ${today}*\n`;

  return content;
}

/**
 * Get Hermes state from progress percentage
 */
function getHermesStateFromProgress(progress: number): string {
  if (progress === 100) {
    return 'done';
  } else if (progress > 50) {
    return 'applying';
  } else if (progress > 0) {
    return 'propose';
  } else {
    return 'plan';
  }
}

/**
 * Register task commands with the CLI
 */
export function registerTaskCommand(program: Command): void {
  const taskCmd = program
    .command('task')
    .description('Task management with Redmine sync');

  taskCmd
    .command('breakdown <story-name>')
    .description('Break down a story into tasks')
    .option('-p, --parent <id>', 'Parent Redmine issue ID')
    .option('-i, --interactive', 'Interactive mode (not yet implemented)')
    .option('--dry-run', 'Preview without creating')
    .action((storyName, options) => breakdownTasks(storyName, options));

  taskCmd
    .command('sync <change-name>')
    .description('Sync task progress to Redmine')
    .option('--dry-run', 'Preview without syncing')
    .option('-v, --verbose', 'Show verbose output')
    .action((changeName, options) => syncTasks(changeName, options));

  taskCmd
    .command('status <change-name>')
    .description('Show task status')
    .action((changeName) => showStatus(changeName));
}