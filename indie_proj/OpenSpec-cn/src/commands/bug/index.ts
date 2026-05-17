/**
 * Bug Management Commands
 *
 * Commands for managing bug reports including creation, updates, and listing.
 */

import { Command } from 'commander';
import inquirer from 'inquirer';
import ora from 'ora';
import chalk from 'chalk';
import path from 'path';
import { promises as fs } from 'fs';
import yaml from 'yaml';
import { getInstanceManager } from '../../core/redmine/instance-manager.js';
import { RedmineCliWrapper } from '../../core/redmine/cli-wrapper.js';
import { OneWaySyncManager } from '../../core/redmine/one-way-sync.js';
import { StatusMapper, BUG_STATES } from '../../core/redmine/status-mapping.js';
import { BugMetadata } from '../../core/artifact-graph/types.js';

const OPENSPEC_DIR = 'openspec';
const BUGS_DIR = path.join(OPENSPEC_DIR, 'bugs');

/**
 * Create a new bug report
 */
async function createBug(title: string, options: {
  severity?: string;
  relatedStory?: string;
  relatedTask?: string;
  description?: string;
  interactive?: boolean;
}) {
  console.log(chalk.cyan(`\n🐛 Creating bug report: ${title}\n`));

  let severity = options.severity || 'major';
  let description = options.description || '';
  let relatedStory = options.relatedStory;
  let relatedTask = options.relatedTask;
  const validSeverities = ['critical', 'major', 'minor', 'trivial'];

  if (!validSeverities.includes(severity)) {
    console.log(chalk.red(`\nInvalid severity: ${severity}`));
    console.log(chalk.gray(`Valid severities: ${validSeverities.join(', ')}\n`));
    return;
  }

  if (options.interactive) {
    const answers = await inquirer.prompt([
      {
        type: 'list',
        name: 'severity',
        message: 'Bug severity:',
        choices: ['critical', 'major', 'minor', 'trivial'],
        default: 'major',
      },
      {
        type: 'input',
        name: 'description',
        message: 'Bug description:',
      },
      {
        type: 'input',
        name: 'relatedStory',
        message: 'Related story (optional):',
        default: relatedStory,
      },
      {
        type: 'input',
        name: 'relatedTask',
        message: 'Related task (optional):',
        default: relatedTask,
      },
    ]);

    severity = answers.severity;
    description = answers.description;
    relatedStory = answers.relatedStory || undefined;
    relatedTask = answers.relatedTask || undefined;
  }

  const bugId = generateBugId();
  const bugPath = path.join(process.cwd(), BUGS_DIR, bugId);

  // Create bugs directory if it doesn't exist
  await fs.mkdir(bugPath, { recursive: true });

  // Generate bug.md content
  const bugContent = generateBugContent(bugId, title, severity, description, relatedStory);

  await fs.writeFile(path.join(bugPath, 'bug.md'), bugContent, 'utf-8');

  // Create metadata
  const today = new Date().toISOString().split('T')[0];
  const metadata: BugMetadata = {
    title,
    severity: severity as 'critical' | 'major' | 'minor' | 'trivial',
    status: 'new' as 'new' | 'in-progress' | 'fixed' | 'verified',
    created: today,
    relatedChange: relatedStory,
    relatedTask,
  };

  await fs.writeFile(
    path.join(bugPath, '.openspec.yaml'),
    yaml.stringify(metadata),
    'utf-8'
  );

  console.log(chalk.green(`✓ Bug report created: ${bugId}`));
  console.log(chalk.gray(`  Location: ${bugPath}\n`));

  // Sync to Redmine
  try {
    const manager = getInstanceManager();
    const wrapper = await manager.createWrapper();
    const mapper = new StatusMapper();
    const syncManager = new OneWaySyncManager(wrapper, mapper, process.cwd());

    const relatedIssueId = relatedStory ? await getIssueIdForChange(relatedStory) : undefined;
    await syncManager.syncBug(bugPath, title, severity, relatedIssueId);

    console.log(chalk.green(`✓ Synced to Redmine`));
  } catch (error) {
    console.log(chalk.yellow('\nRedmine sync skipped:', (error as Error).message));
  }
}

/**
 * Update a bug
 */
async function updateBug(bugId: string, options: {
  status?: string;
  severity?: string;
  addNote?: string;
}) {
  const bugPath = path.join(process.cwd(), BUGS_DIR, bugId);

  // Check if bug exists
  try {
    await fs.access(bugPath);
  } catch {
    console.log(chalk.red(`\nBug '${bugId}' not found.\n`));
    console.log(chalk.gray('Run `openspec bug list` to see available bugs.\n'));
    return;
  }

  const metadataPath = path.join(bugPath, '.openspec.yaml');
  let metadata: BugMetadata;

  try {
    const content = await fs.readFile(metadataPath, 'utf-8');
    metadata = yaml.parse(content) as BugMetadata;
  } catch {
    console.log(chalk.red(`\nBug metadata not found for '${bugId}'.\n`));
    return;
  }

  console.log(chalk.cyan(`\n🔧 Updating bug: ${bugId} (${metadata.title})\n`));

  let updated = false;

  if (options.status) {
    const validStatuses = ['new', 'in-progress', 'fixed', 'verified'];
    if (!validStatuses.includes(options.status)) {
      console.log(chalk.red(`Invalid status: ${options.status}`));
      console.log(chalk.gray(`Valid statuses: ${validStatuses.join(', ')}\n`));
      return;
    }

    const previousStatus = metadata.status;
    metadata.status = options.status as 'new' | 'in-progress' | 'fixed' | 'verified';

    if (options.status === 'verified' || options.status === 'fixed') {
      metadata.resolved = new Date().toISOString().split('T')[0];
    }

    console.log(chalk.green(`✓ Status updated: ${previousStatus} → ${options.status}`));
    updated = true;
  }

  if (options.severity) {
    const previousSeverity = metadata.severity;
    metadata.severity = options.severity as 'critical' | 'major' | 'minor' | 'trivial';
    console.log(chalk.green(`✓ Severity updated: ${previousSeverity} → ${options.severity}`));
    updated = true;
  }

  if (options.addNote) {
    const bugMdPath = path.join(bugPath, 'bug.md');
    let bugContent = await fs.readFile(bugMdPath, 'utf-8');

    // Add note to Resolution section
    if (bugContent.includes('## Resolution')) {
      bugContent = bugContent.replace(
        '## Resolution',
        `## Resolution\n\n**${new Date().toISOString()}**: ${options.addNote}\n\n### Previous:`
      );
    } else {
      bugContent += `\n\n## Resolution\n\n${options.addNote}`;
    }

    await fs.writeFile(bugMdPath, bugContent, 'utf-8');
    console.log(chalk.green(`✓ Note added to bug report`));
    updated = true;
  }

  if (updated) {
    await fs.writeFile(metadataPath, yaml.stringify(metadata), 'utf-8');

    // Sync to Redmine
    try {
      const manager = getInstanceManager();
      const wrapper = await manager.createWrapper();
      const mapper = new StatusMapper();
      const syncManager = new OneWaySyncManager(wrapper, mapper, process.cwd());

      const syncMeta = await syncManager.getSyncMetadata(bugPath);
      if (syncMeta?.issueId) {
        // Update status in Redmine
        const statusMapping: Record<string, string> = {
          'new': '待修复',
          'in-progress': '修复中',
          'fixed': '修复完成',
          'verified': '验证完成'
        };

        await wrapper.updateStatus(syncMeta.issueId, statusMapping[metadata.status]);
        console.log(chalk.green(`✓ Redmine issue #${syncMeta.issueId} updated`));
      }
    } catch (error) {
      console.log(chalk.yellow('\nRedmine sync skipped:', (error as Error).message));
    }

    console.log('');
  } else {
    console.log(chalk.gray('No changes to apply.\n'));
  }
}

/**
 * List bugs with optional filter
 */
async function listBugs(options: { status?: string; severity?: string }) {
  const bugsPath = path.join(process.cwd(), BUGS_DIR);

  try {
    await fs.access(bugsPath);
  } catch {
    console.log(chalk.yellow('\nNo bugs found.\n'));
    console.log(chalk.gray('Run `openspec bug create <title>` to create a bug report.\n'));
    return;
  }

  const entries = await fs.readdir(bugsPath, { withFileTypes: true });
  const bugDirs = entries.filter(e => e.isDirectory());

  if (bugDirs.length === 0) {
    console.log(chalk.yellow('\nNo bugs found.\n'));
    return;
  }

  const bugs: Array<{
    id: string;
    title: string;
    status: string;
    severity: string;
    created: string;
    relatedChange?: string;
    issueId?: number;
  }> = [];

  for (const dir of bugDirs) {
    const bugPath = path.join(bugsPath, dir.name);
    const metadataPath = path.join(bugPath, '.openspec.yaml');

    try {
      const content = await fs.readFile(metadataPath, 'utf-8');
      const metadata = yaml.parse(content) as BugMetadata;

      // Get issue ID from .openspec.yaml redmine section
      const parsed = yaml.parse(content) as any;
      const issueId = parsed.redmine?.issueId;

      bugs.push({
        id: dir.name,
        title: metadata.title,
        status: metadata.status,
        severity: metadata.severity,
        created: metadata.created || '',
        relatedChange: metadata.relatedChange,
        issueId,
      });
    } catch {
      // Skip invalid bugs
    }
  }

  // Apply filters
  let filtered = bugs;
  if (options.status) {
    filtered = filtered.filter(b => b.status === options.status);
  }
  if (options.severity) {
    filtered = filtered.filter(b => b.severity === options.severity);
  }

  if (filtered.length === 0) {
    console.log(chalk.yellow('\nNo bugs match the criteria.\n'));
    return;
  }

  console.log(chalk.cyan('\n🐛 Bug Reports:\n'));

  // Severity colors
  const severityColors: Record<string, (s: string) => string> = {
    'critical': chalk.red,
    'major': chalk.yellow,
    'minor': chalk.blue,
    'trivial': chalk.gray,
  };

  // Status colors
  const statusColors: Record<string, (s: string) => string> = {
    'new': chalk.red,
    'in-progress': chalk.yellow,
    'fixed': chalk.blue,
    'verified': chalk.green,
  };

  for (const bug of filtered) {
    const severityColor = severityColors[bug.severity] || chalk.white;
    const statusColor = statusColors[bug.status] || chalk.white;

    console.log(chalk.bold(`${bug.id}: ${bug.title}`));
    console.log(`  Status: ${statusColor(bug.status)}`);
    console.log(`  Severity: ${severityColor(bug.severity)}`);
    if (bug.relatedChange) {
      console.log(`  Related: ${bug.relatedChange}`);
    }
    if (bug.issueId) {
      console.log(chalk.gray(`  Redmine: Issue #${bug.issueId}`));
    }
    console.log(`  Created: ${bug.created}`);
    console.log('');
  }
}

/**
 * Generate a unique bug ID
 */
function generateBugId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 7);
  return `BUG-${timestamp}-${random}`.toUpperCase();
}

/**
 * Generate bug.md content
 */
function generateBugContent(
  bugId: string,
  title: string,
  severity: string,
  description: string,
  relatedStory?: string
): string {
  const today = new Date().toISOString().split('T')[0];

  let content = `# Bug Report: ${title}\n\n`;
  content += `**ID**: ${bugId}\n`;
  content += `**Severity**: ${severity}\n`;
  content += `**Status**: new\n`;
  content += `**Created**: ${today}\n`;
  if (relatedStory) {
    content += `**Related Story**: ${relatedStory}\n`;
  }
  content += '\n## Description\n\n';
  content += description || `<!-- Describe the bug in detail -->`;
  content += '\n\n## Steps to Reproduce\n\n';
  content += '1. <!-- Step 1 -->\n';
  content += '2. <!-- Step 2 -->\n';
  content += '3. <!-- Step 3 -->\n';
  content += '\n## Expected Behavior\n\n';
  content += '<!-- What should happen -->\n\n';
  content += '## Actual Behavior\n\n';
  content += '<!-- What actually happens -->\n\n';
  content += '## Environment\n\n';
  content += '- **OS**: Windows\n';
  content += '- **Version**: <!-- Version -->\n';
  content += '- **Browser/Environment**: <!-- Environment -->\n';
  content += '\n## Screenshots\n\n';
  content += '<!-- Add screenshots if applicable -->\n\n';
  content += '## Additional Notes\n\n';
  content += '<!-- Any additional context about the bug -->\n\n';
  content += '## Resolution\n\n';
  content += '<!-- How the bug was resolved -->\n\n';
  content += '---\n\n';
  content += `*Last updated: ${today}*\n`;

  return content;
}

/**
 * Get Redmine issue ID for a change
 */
async function getIssueIdForChange(changeName: string): Promise<number | undefined> {
  try {
    const metadataPath = path.join(
      process.cwd(),
      OPENSPEC_DIR,
      'changes',
      changeName,
      '.openspec.yaml'
    );
    const content = await fs.readFile(metadataPath, 'utf-8');
    const metadata = yaml.parse(content);
    return metadata.redmine?.issueId;
  } catch {
    return undefined;
  }
}

/**
 * Register bug commands with the CLI
 */
export function registerBugCommand(program: Command): void {
  const bugCmd = program
    .command('bug')
    .description('Bug management');

  bugCmd
    .command('create <title>')
    .description('Create a new bug report')
    .option('-s, --severity <level>', 'Bug severity (critical|major|minor|trivial)')
    .option('--related-story <name>', 'Related story name')
    .option('--related-task <name>', 'Related task name')
    .option('-d, --description <text>', 'Bug description')
    .option('-i, --interactive', 'Interactive mode')
    .action((title, options) => createBug(title, options));

  bugCmd
    .command('update <bug-id>')
    .description('Update a bug')
    .option('--status <status>', 'New status (new|in-progress|fixed|verified)')
    .option('--severity <level>', 'New severity (critical|major|minor|trivial)')
    .option('--note <text>', 'Add a note')
    .action((bugId, options) => updateBug(bugId, options));

  bugCmd
    .command('list')
    .description('List bugs')
    .option('--status <status>', 'Filter by status')
    .option('--severity <level>', 'Filter by severity')
    .action((options) => listBugs(options));
}