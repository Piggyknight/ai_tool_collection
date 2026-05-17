/**
 * Sprint Management Commands
 *
 * Commands for managing sprints including creation, planning, and closing.
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
import { StatusMapper } from '../../core/redmine/status-mapping.js';
import { SprintMetadata } from '../../core/artifact-graph/types.js';

const OPENSPEC_DIR = 'openspec';
const SPRINTS_DIR = path.join(OPENSPEC_DIR, 'sprints');

/**
 * Create a new sprint
 */
async function createSprint(name: string, options: { dueDate?: string; description?: string }) {
  const manager = getInstanceManager();
  const sprintPath = path.join(process.cwd(), SPRINTS_DIR, name);

  // Check if sprint already exists
  try {
    await fs.access(sprintPath);
    console.log(chalk.yellow(`\nSprint '${name}' already exists.\n`));
    return;
  } catch {
    // Directory doesn't exist, proceed
  }

  // Get Redmine configuration
  let wrapper: RedmineCliWrapper | null = null;
  const spinner = ora('Creating sprint...').start();

  try {
    wrapper = await manager.createWrapper();
  } catch (error) {
    spinner.warn('Redmine not configured, creating sprint without sync');
  }

  // Create sprint directory
  await fs.mkdir(sprintPath, { recursive: true });

  // Generate sprint metadata
  const today = new Date().toISOString().split('T')[0];
  const metadata: SprintMetadata = {
    name,
    created: today,
    status: 'active',
    dueDate: options.dueDate,
    redmine: {},
  };

  // Create sprint.md from template
  const templatePath = path.join(
    process.cwd(),
    'openspec',
    'schemas',
    'spec-driven',
    'templates',
    'sprint.md'
  );

  let sprintContent = `# Sprint: ${name}\n\n`;
  sprintContent += `**Created**: ${today}\n`;
  sprintContent += `**Status**: active\n`;
  if (options.dueDate) {
    sprintContent += `**Due Date**: ${options.dueDate}\n`;
  }
  sprintContent += '\n## Sprint Goal\n\n';
  sprintContent += options.description || `<!-- Describe the main goal of this sprint -->`;
  sprintContent += '\n\n## Scope\n\n';
  sprintContent += 'This sprint includes the following stories:\n\n';
  sprintContent += '<!-- Stories will be populated by openspec sprint plan command -->\n';
  sprintContent += '\n## Timeline\n\n';
  sprintContent += `- **Start Date**: ${today}\n`;
  if (options.dueDate) {
    sprintContent += `- **End Date**: ${options.dueDate}\n`;
  }
  sprintContent += '\n## Success Criteria\n\n';
  sprintContent += '- [ ] All stories completed\n';
  sprintContent += '- [ ] All acceptance criteria met\n';
  sprintContent += '- [ ] No critical bugs remaining\n';
  sprintContent += '- [ ] Documentation updated\n';
  sprintContent += '\n## Risks & Dependencies\n\n';
  sprintContent += '<!-- List any risks or dependencies that could affect the sprint -->\n';
  sprintContent += '\n## Notes\n\n';
  sprintContent += '<!-- Any additional notes about the sprint -->\n';

  // Write sprint.md
  await fs.writeFile(path.join(sprintPath, 'sprint.md'), sprintContent, 'utf-8');

  // Write .openspec.yaml
  await fs.writeFile(
    path.join(sprintPath, '.openspec.yaml'),
    yaml.stringify(metadata),
    'utf-8'
  );

  // Sync to Redmine if available
  if (wrapper) {
    const mapper = new StatusMapper();
    const syncManager = new OneWaySyncManager(wrapper, mapper, process.cwd());
    await syncManager.syncSprint(sprintPath, name);
  }

  spinner.succeed(chalk.green(`Sprint '${name}' created successfully!`));
  console.log(chalk.gray(`\n  Location: ${sprintPath}\n`));
}

/**
 * List all sprints
 */
async function listSprints() {
  const sprintsPath = path.join(process.cwd(), SPRINTS_DIR);

  try {
    const entries = await fs.readdir(sprintsPath, { withFileTypes: true });
    const sprintDirs = entries.filter(e => e.isDirectory());

    if (sprintDirs.length === 0) {
      console.log(chalk.yellow('\nNo sprints found.\n'));
      console.log(chalk.gray('Run `openspec sprint create <name>` to create a sprint.\n'));
      return;
    }

    console.log(chalk.cyan('\n📋 Sprints:\n'));

    for (const dir of sprintDirs) {
      const sprintPath = path.join(sprintsPath, dir.name);
      const metadataPath = path.join(sprintPath, '.openspec.yaml');

      let status = 'unknown';
      let dueDate = '';

      try {
        const content = await fs.readFile(metadataPath, 'utf-8');
        const metadata = yaml.parse(content) as SprintMetadata;
        status = metadata.status || 'unknown';
        dueDate = metadata.dueDate || '';
      } catch {
        // Metadata doesn't exist
      }

      const statusColor = status === 'active' ? chalk.green : status === 'closed' ? chalk.gray : chalk.yellow;

      console.log(chalk.bold(dir.name));
      console.log(`  Status: ${statusColor(status)}`);
      if (dueDate) {
        console.log(`  Due: ${dueDate}`);
      }
      console.log('');
    }
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      console.log(chalk.yellow('\nNo sprints directory found.\n'));
      console.log(chalk.gray('Run `openspec sprint create <name>` to create your first sprint.\n'));
    } else {
      console.log(chalk.red(`\nError: ${(error as Error).message}\n`));
    }
  }
}

/**
 * Plan a sprint (break down proposals into stories)
 */
async function planSprint(sprintName: string, options: { auto?: boolean }) {
  const sprintPath = path.join(process.cwd(), SPRINTS_DIR, sprintName);

  // Check if sprint exists
  try {
    await fs.access(sprintPath);
  } catch {
    console.log(chalk.red(`\nSprint '${sprintName}' not found.\n`));
    console.log(chalk.gray('Run `openspec sprint list` to see available sprints.\n'));
    return;
  }

  console.log(chalk.cyan(`\n🎯 Planning Sprint: ${sprintName}\n`));

  // Look for proposals in changes directory
  const changesPath = path.join(process.cwd(), OPENSPEC_DIR, 'changes');
  let proposals: string[] = [];

  try {
    const entries = await fs.readdir(changesPath, { withFileTypes: true });
    const changeDirs = entries.filter(e => e.isDirectory());

    for (const dir of changeDirs) {
      const proposalPath = path.join(changesPath, dir.name, 'proposal.md');
      try {
        await fs.access(proposalPath);
        proposals.push(dir.name);
      } catch {
        // No proposal
      }
    }
  } catch {
    console.log(chalk.yellow('No changes directory found.\n'));
  }

  if (proposals.length === 0) {
    console.log(chalk.yellow('No proposals found to break down into stories.\n'));
    console.log(chalk.gray('Run `openspec new change <name>` to create a change with a proposal.\n'));
    return;
  }

  console.log(chalk.gray('Found proposals:\n'));
  proposals.forEach(p => console.log(`  - ${p}`));
  console.log('');

  if (!options.auto) {
    const { selected } = await inquirer.prompt([
      {
        type: 'checkbox',
        name: 'selected',
        message: 'Select proposals to include in this sprint:',
        choices: proposals,
        default: proposals,
      },
    ]);

    if (selected.length === 0) {
      console.log(chalk.yellow('\nNo proposals selected. Sprint planning cancelled.\n'));
      return;
    }

    proposals = selected;
  }

  // Update sprint metadata with stories
  const metadataPath = path.join(sprintPath, '.openspec.yaml');
  let metadata: SprintMetadata;

  try {
    const content = await fs.readFile(metadataPath, 'utf-8');
    metadata = yaml.parse(content) as SprintMetadata;
  } catch {
    metadata = {
      name: sprintName,
      created: new Date().toISOString().split('T')[0],
      status: 'active',
    };
  }

  metadata.changes = proposals.map(name => ({ name }));

  await fs.writeFile(
    metadataPath,
    yaml.stringify(metadata),
    'utf-8'
  );

  // Update sprint.md
  const sprintMdPath = path.join(sprintPath, 'sprint.md');
  let sprintContent = await fs.readFile(sprintMdPath, 'utf-8');

  // Replace stories section
  const storiesSection = '## Scope\n\nThis sprint includes the following stories:\n\n';
  const storiesList = proposals.map(p => `- **[${p}](../../changes/${p}/proposal.md)**`).join('\n');
  const replacement = storiesSection + storiesList + '\n';

  const scopeRegex = /## Scope[\s\S]*?(?=\n##|\n*$)/;
  if (scopeRegex.test(sprintContent)) {
    sprintContent = sprintContent.replace(scopeRegex, replacement.trim());
  } else {
    // Insert after Sprint Goal
    const goalRegex = /## Sprint Goal[\s\S]*?(?=\n##|\n*$)/;
    sprintContent = sprintContent.replace(goalRegex, (match) => match + '\n\n' + replacement.trim());
  }

  await fs.writeFile(sprintMdPath, sprintContent, 'utf-8');

  console.log(chalk.green(`\n✓ Sprint planned with ${proposals.length} stories!\n`));

  // Sync to Redmine
  try {
    const manager = getInstanceManager();
    const wrapper = await manager.createWrapper();
    const mapper = new StatusMapper();
    const syncManager = new OneWaySyncManager(wrapper, mapper, process.cwd());

    const spinner = ora('Syncing to Redmine...').start();

    for (const proposal of proposals) {
      const changePath = path.join(changesPath, proposal);
      await syncManager.syncStory(changePath, proposal, metadata.redmine?.versionId || 0);
    }

    spinner.succeed(chalk.green('Sprint synced to Redmine!'));
  } catch (error) {
    console.log(chalk.yellow('\nRedmine sync skipped:', (error as Error).message));
  }

  console.log('');
}

/**
 * Close a sprint
 */
async function closeSprint(sprintName: string, options: { yes?: boolean }) {
  const sprintPath = path.join(process.cwd(), SPRINTS_DIR, sprintName);

  // Check if sprint exists
  try {
    await fs.access(sprintPath);
  } catch {
    console.log(chalk.red(`\nSprint '${sprintName}' not found.\n`));
    return;
  }

  if (!options.yes) {
    const { confirmed } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'confirmed',
        message: `Are you sure you want to close sprint '${sprintName}'?`,
        default: false,
      },
    ]);

    if (!confirmed) {
      console.log(chalk.yellow('\nSprint close cancelled.\n'));
      return;
    }
  }

  const spinner = ora('Closing sprint...').start();

  try {
    // Update metadata
    const metadataPath = path.join(sprintPath, '.openspec.yaml');
    let metadata: SprintMetadata;

    try {
      const content = await fs.readFile(metadataPath, 'utf-8');
      metadata = yaml.parse(content) as SprintMetadata;
    } catch {
      metadata = {
        name: sprintName,
        created: new Date().toISOString().split('T')[0],
        status: 'active',
      };
    }

    metadata.status = 'closed';

    await fs.writeFile(
      metadataPath,
      yaml.stringify(metadata),
      'utf-8'
    );

    // Move to archived
    const archivedPath = path.join(process.cwd(), OPENSPEC_DIR, 'archived', 'sprints', sprintName);
    await fs.mkdir(path.dirname(archivedPath), { recursive: true });

    // Move files
    const files = await fs.readdir(sprintPath);
    for (const file of files) {
      await fs.rename(
        path.join(sprintPath, file),
        path.join(archivedPath, file)
      );
    }

    // Remove empty directory
    await fs.rmdir(sprintPath);

    spinner.succeed(chalk.green(`Sprint '${sprintName}' closed and archived!`));
    console.log(chalk.gray(`\n  Archived to: ${archivedPath}\n`));
  } catch (error) {
    spinner.fail(chalk.red('Failed to close sprint'));
    console.log(chalk.red(`\n${(error as Error).message}\n`));
  }
}

/**
 * Register sprint commands with the CLI
 */
export function registerSprintCommand(program: Command): void {
  const sprintCmd = program
    .command('sprint')
    .description('Sprint planning and management');

  sprintCmd
    .command('create <name>')
    .description('Create a new sprint')
    .option('-d, --due-date <date>', 'Sprint due date (YYYY-MM-DD)')
    .option('--description <text>', 'Sprint goal description')
    .action((name, options) => createSprint(name, options));

  sprintCmd
    .command('list')
    .description('List all sprints')
    .action(() => listSprints());

  sprintCmd
    .command('plan <name>')
    .description('Plan sprint stories from existing proposals')
    .option('-a, --auto', 'Auto-select all proposals')
    .action((name, options) => planSprint(name, options));

  sprintCmd
    .command('close <name>')
    .description('Close and archive a sprint')
    .option('-y, --yes', 'Skip confirmation')
    .action((name, options) => closeSprint(name, options));
}