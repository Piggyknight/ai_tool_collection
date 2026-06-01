/**
 * Redmine Configuration Commands
 *
 * Commands for setting up and managing Redmine integration.
 */

import { Command } from 'commander';
import { confirm, input, password, select } from '@inquirer/prompts';
import ora from 'ora';
import chalk from 'chalk';
import path from 'path';
import { promises as fs } from 'fs';
import yaml from 'yaml';
import { getInstanceManager, RedmineInstance } from '../../core/redmine/instance-manager.js';
import { RedmineCliWrapper } from '../../core/redmine/cli-wrapper.js';

/**
 * Setup Redmine integration interactively
 */
async function setupRedmine(options: { instance?: string }) {
  const manager = getInstanceManager();
  await manager.loadConfig();

  console.log(chalk.cyan('\n🔧 Redmine Integration Setup\n'));

  const instanceName = options.instance || await input({
    message: 'Instance name:',
    default: 'default',
    validate: (value) => value.trim().length > 0 || 'Name is required',
  });

  // Check if instance already exists
  const existing = manager.getInstanceByName(instanceName);
  if (existing) {
    console.log(chalk.yellow(`\nInstance '${instanceName}' already exists.`));
    const action = await select({
      message: 'What would you like to do?',
      choices: [
        { name: 'Update configuration', value: 'Update configuration' },
        { name: 'Remove instance', value: 'Remove instance' },
        { name: 'Cancel', value: 'Cancel' },
      ],
    });

    if (action === 'Cancel') {
      return;
    }

    if (action === 'Remove instance') {
      await manager.removeInstance(instanceName);
      console.log(chalk.green(`\nInstance '${instanceName}' removed.`));
      return;
    }
  }

  // Collect configuration
  const server = await input({
    message: 'Redmine server URL:',
    default: existing?.server || 'https://redmine.example.com',
    validate: (value: string) => {
      try {
        new URL(value);
        return true;
      } catch {
        return 'Please enter a valid URL';
      }
    },
  });
  const apiKey = await password({
    message: 'API key:',
    mask: '*',
    validate: (value: string) => value.trim().length > 0 || 'API key is required',
  });
  const projectIdInput = await input({
    message: 'Project ID:',
    default: existing?.projectId?.toString() || '1',
    validate: (value: string) => !Number.isNaN(Number(value)) || 'Please enter a valid number',
  });
  const cliPathInput = await input({
    message: 'red-cli.exe path (leave empty for PATH):',
    default: existing?.cliPath || '',
  });
  const setWorktree = await confirm({
    message: 'Set this instance for current git worktree?',
    default: !existing?.gitWorktree,
  });

  let gitWorktree: string | undefined;
  if (setWorktree) {
    gitWorktree = await input({
      message: 'Git worktree path:',
      default: process.cwd(),
    });
  }

  const instance: RedmineInstance = {
    name: instanceName,
    server,
    apiKey,
    projectId: Number(projectIdInput),
    cliPath: cliPathInput.trim() || undefined,
    gitWorktree: gitWorktree,
  };

  // Test connection
  const spinner = ora('Testing connection to Redmine...').start();
  const wrapper = new RedmineCliWrapper({
    server: instance.server,
    apiKey: instance.apiKey,
    projectId: instance.projectId,
    cliPath: instance.cliPath,
  });

  const connected = await wrapper.testConnection();
  spinner.stop();

  if (connected) {
    console.log(chalk.green('\n✓ Connection successful!'));
  } else {
    console.log(chalk.red('\n✗ Connection failed. Please check your credentials.'));
    const continueAnyway = await confirm({
      message: 'Save configuration anyway?',
      default: false,
    });
    if (!continueAnyway) {
      return;
    }
  }

  // Save configuration
  await manager.registerInstance(instance);

  // Set as active instance for this worktree if gitWorktree is set
  if (instance.gitWorktree) {
    await manager.setActiveInstance('auto');
    console.log(chalk.cyan(`\nAuto-detection enabled for worktree: ${instance.gitWorktree}`));
  } else {
    const setAsDefault = await confirm({
      message: `Set '${instanceName}' as default instance?`,
      default: true,
    });
    if (setAsDefault) {
      await manager.setActiveInstance(instanceName);
    }
  }

  console.log(chalk.green(`\n✓ Redmine instance '${instanceName}' configured successfully!\n`));
}

/**
 * List configured Redmine instances
 */
async function listInstances() {
  const manager = getInstanceManager();
  await manager.loadConfig();

  const instances = manager.listInstances();

  if (instances.length === 0) {
    console.log(chalk.yellow('\nNo Redmine instances configured.\n'));
    console.log(chalk.gray('Run `openspec redmine setup` to configure an instance.\n'));
    return;
  }

  console.log(chalk.cyan('\n📋 Configured Redmine Instances:\n'));

  for (const instance of instances) {
    const isActive = manager.getActiveInstanceName() === 'auto'
      ? (path.normalize(process.cwd()).toLowerCase() === path.normalize(instance.gitWorktree || '').toLowerCase())
      : manager.getActiveInstanceName() === instance.name;

    const marker = isActive ? chalk.green('★ ') : '  ';
    const name = chalk.bold(instance.name);
    const worktree = instance.gitWorktree ? chalk.gray(` (${instance.gitWorktree})`) : '';

    console.log(`${marker}${name}${worktree}`);
    console.log(`    Server: ${instance.server}`);
    console.log(`    Project: ${instance.projectId}`);
    console.log('');
  }

  console.log(`Active: ${manager.getActiveInstanceName() === 'auto' ? chalk.cyan('auto (worktree-based)') : manager.getActiveInstanceName()}\n`);
}

/**
 * Test Redmine connection
 */
async function testConnection() {
  const manager = getInstanceManager();

  const spinner = ora('Detecting Redmine instance...').start();

  try {
    const wrapper = await manager.createWrapper();
    spinner.text = 'Testing connection...';

    const connected = await wrapper.testConnection();

    if (connected) {
      spinner.succeed(chalk.green('Connection successful!'));
      console.log(chalk.gray('\nYou can now use Redmine integration commands.\n'));
    } else {
      spinner.fail(chalk.red('Connection failed'));
      console.log(chalk.gray('\nPlease check your configuration with `openspec redmine setup`.\n'));
    }
  } catch (error) {
    spinner.fail(chalk.red('Error'));
    console.log(chalk.red(`\n${(error as Error).message}\n`));
  }
}

/**
 * Get current Redmine instance info
 */
async function getCurrentInstance() {
  const manager = getInstanceManager();

  try {
    const instance = await manager.detectInstance();

    if (!instance) {
      console.log(chalk.yellow('\nNo Redmine instance detected for current worktree.\n'));
      console.log(chalk.gray('Run `openspec redmine setup` to configure an instance.\n'));
      return;
    }

    console.log(chalk.cyan('\n📌 Current Redmine Instance:\n'));
    console.log(chalk.bold(`Name: ${instance.name}`));
    console.log(`Server: ${instance.server}`);
    console.log(`Project: ${instance.projectId}`);
    console.log(`CLI: ${instance.cliPath || 'red-cli.exe (from PATH)'}`);
    if (instance.gitWorktree) {
      console.log(`Worktree: ${instance.gitWorktree}`);
    }
    console.log('');
  } catch (error) {
    console.log(chalk.red(`\nError: ${(error as Error).message}\n`));
  }
}

/**
 * Register redmine commands with the CLI
 */
export function registerRedmineCommand(program: Command): void {
  const redmineCmd = program
    .command('redmine')
    .description('Redmine integration configuration');

  redmineCmd
    .command('setup')
    .description('Set up Redmine integration')
    .option('-i, --instance <name>', 'Instance name')
    .action((options) => setupRedmine(options));

  redmineCmd
    .command('list')
    .description('List configured Redmine instances')
    .action(() => listInstances());

  redmineCmd
    .command('test')
    .description('Test connection to Redmine')
    .action(() => testConnection());

  redmineCmd
    .command('current')
    .description('Show current Redmine instance')
    .action(() => getCurrentInstance());
}
