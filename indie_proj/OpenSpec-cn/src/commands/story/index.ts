/**
 * Story Management Commands
 *
 * Commands for managing user stories including breakdown, refinement, and listing.
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
import { StatusMapper, HermesState } from '../../core/redmine/status-mapping.js';
import { ChangeMetadata } from '../../core/artifact-graph/types.js';

const OPENSPEC_DIR = 'openspec';
const CHANGES_DIR = path.join(OPENSPEC_DIR, 'changes');

/**
 * Break down a proposal into a story
 */
async function breakdownStory(sprintName: string, changeName: string, options: { interactive?: boolean }) {
  const changePath = path.join(process.cwd(), CHANGES_DIR, changeName);
  const proposalPath = path.join(changePath, 'proposal.md');

  // Check if change exists
  try {
    await fs.access(changePath);
  } catch {
    console.log(chalk.red(`\nChange '${changeName}' not found.\n`));
    console.log(chalk.gray('Run `openspec new change <name>` to create a change.\n'));
    return;
  }

  // Check if proposal exists
  try {
    await fs.access(proposalPath);
  } catch {
    console.log(chalk.yellow(`\nNo proposal found for '${changeName}'.\n`));
    return;
  }

  console.log(chalk.cyan(`\n📖 Breaking down story: ${changeName}\n`));

  const spinner = ora('Reading proposal...').start();

  let proposalContent = '';
  try {
    proposalContent = await fs.readFile(proposalPath, 'utf-8');
  } catch (error) {
    spinner.fail('Failed to read proposal');
    console.log(chalk.red(`\n${(error as Error).message}\n`));
    return;
  }

  spinner.succeed('Proposal loaded');

  // Parse proposal to extract capabilities
  const capabilities = extractCapabilities(proposalContent);

  console.log(chalk.gray('\nExtracted capabilities:\n'));
  capabilities.forEach((cap, i) => {
    console.log(`  ${i + 1}. ${cap}`);
  });
  console.log('');

  // Extract summary from proposal
  const summary = extractSummary(proposalContent);

  // Generate story.md
  const storyContent = generateStoryContent(changeName, summary, capabilities);

  const storyPath = path.join(changePath, 'story.md');
  await fs.writeFile(storyPath, storyContent, 'utf-8');

  console.log(chalk.green(`✓ Story document created: story.md`));

  // Update or create .openspec.yaml with redmine sync info
  const metadataPath = path.join(changePath, '.openspec.yaml');
  let metadata: ChangeMetadata;

  try {
    const content = await fs.readFile(metadataPath, 'utf-8');
    metadata = yaml.parse(content) as ChangeMetadata;
  } catch {
    metadata = {
      schema: 'spec-driven',
      created: new Date().toISOString().split('T')[0],
    };
  }

  // Sync to Redmine
  let issueId: number | undefined;
  try {
    const manager = getInstanceManager();
    const wrapper = await manager.createWrapper();
    const mapper = new StatusMapper();
    const syncManager = new OneWaySyncManager(wrapper, mapper, process.cwd());

    // Get sprint version ID if specified
    let sprintId = 0;
    if (sprintName) {
      const sprintPath = path.join(process.cwd(), OPENSPEC_DIR, 'sprints', sprintName);
      const sprintMetadataPath = path.join(sprintPath, '.openspec.yaml');
      try {
        const sprintContent = await fs.readFile(sprintMetadataPath, 'utf-8');
        const sprintMetadata = yaml.parse(sprintContent);
        sprintId = sprintMetadata.redmine?.versionId || 0;
      } catch {
        // Sprint metadata doesn't exist
      }
    }

    const result = await syncManager.syncStory(changePath, changeName, sprintId);
    if (result.success) {
      const updatedMetadata = await syncManager.getSyncMetadata(changePath);
      if (updatedMetadata?.issueId) {
        issueId = updatedMetadata.issueId;
        console.log(chalk.green(`✓ Synced to Redmine: Issue #${issueId}`));
      }
    }
  } catch (error) {
    console.log(chalk.yellow('\nRedmine sync skipped:', (error as Error).message));
  }

  // Update metadata
  metadata.redmine = {
    ...metadata.redmine,
    issueId,
    syncStatus: issueId ? 'synced' : 'pending',
    lastSync: new Date().toISOString(),
    lastSyncBy: 'story-breakdown',
  };

  await fs.writeFile(metadataPath, yaml.stringify(metadata), 'utf-8');

  console.log('');
}

/**
 * Refine a story with acceptance criteria
 */
async function refineStory(storyName: string, options: { addAcceptanceCriteria?: boolean }) {
  const changePath = path.join(process.cwd(), CHANGES_DIR, storyName);
  const storyPath = path.join(changePath, 'story.md');

  // Check if story exists
  try {
    await fs.access(storyPath);
  } catch {
    console.log(chalk.red(`\nStory '${storyName}' not found.\n`));
    return;
  }

  console.log(chalk.cyan(`\n🔍 Refining story: ${storyName}\n`));

  let storyContent = await fs.readFile(storyPath, 'utf-8');

  // Check if acceptance criteria section exists
  if (storyContent.includes('## Acceptance Criteria')) {
    console.log(chalk.gray('Acceptance Criteria section already exists.\n'));

    if (!options.addAcceptanceCriteria) {
      const { action } = await inquirer.prompt([
        {
          type: 'list',
          name: 'action',
          message: 'What would you like to do?',
          choices: ['Add more criteria', 'View current criteria', 'Edit criteria', 'Cancel'],
        },
      ]);

      if (action === 'Cancel') {
        return;
      }

      if (action === 'View current criteria') {
        const acMatch = storyContent.match(/## Acceptance Criteria[\s\S]*?(?=\n##|\n*$)/);
        if (acMatch) {
          console.log(chalk.cyan('\nCurrent Acceptance Criteria:\n'));
          console.log(acMatch[0].trim());
        }
        return;
      }
    }
  }

  // Collect new acceptance criteria
  const { newCriteria } = await inquirer.prompt([
    {
      type: 'editor',
      name: 'newCriteria',
      message: 'Enter acceptance criteria (one per line):',
      default: '- [ ] ...\n- [ ] ...',
    },
  ]);

  // Update story.md
  if (storyContent.includes('## Acceptance Criteria')) {
    // Replace existing section
    storyContent = storyContent.replace(
      /## Acceptance Criteria[\s\S]*?(?=\n##|\n*$)/,
      `## Acceptance Criteria\n\n${newCriteria.trim()}`
    );
  } else {
    // Insert after Definition of Done section or before Notes
    const dodMatch = storyContent.match(/## Definition of Done[\s\S]*?(?=\n##|\n*$)/);
    if (dodMatch) {
      storyContent = storyContent.replace(
        dodMatch[0],
        dodMatch[0] + '\n\n## Acceptance Criteria\n\n' + newCriteria.trim()
      );
    } else {
      // Add before Notes or at the end
      const notesMatch = storyContent.match(/## Notes/);
      if (notesMatch) {
        storyContent = storyContent.replace(
          notesMatch[0],
          '## Acceptance Criteria\n\n' + newCriteria.trim() + '\n\n' + notesMatch[0]
        );
      } else {
        storyContent += '\n\n## Acceptance Criteria\n\n' + newCriteria.trim();
      }
    }
  }

  await fs.writeFile(storyPath, storyContent, 'utf-8');

  console.log(chalk.green(`✓ Story refined successfully!`));

  // Sync to Redmine
  try {
    const manager = getInstanceManager();
    const wrapper = await manager.createWrapper();
    const mapper = new StatusMapper();
    const syncManager = new OneWaySyncManager(wrapper, mapper, process.cwd());

    const metadata = await syncManager.getSyncMetadata(changePath);
    if (metadata?.issueId) {
      await wrapper.updateIssue(metadata.issueId, {
        description: storyContent.substring(0, 5000),
      });
      console.log(chalk.green(`✓ Updated Redmine issue #${metadata.issueId}`));
    }
  } catch (error) {
    console.log(chalk.yellow('\nRedmine sync skipped:', (error as Error).message));
  }

  console.log('');
}

/**
 * List stories for a change
 */
async function listStories(changeName?: string) {
  const changesPath = path.join(process.cwd(), CHANGES_DIR);

  try {
    const entries = await fs.readdir(changesPath, { withFileTypes: true });
    const changeDirs = entries.filter(e => e.isDirectory());

    const stories: Array<{ name: string; path: string; hasStory: boolean; hasProposal: boolean }> = [];

    for (const dir of changeDirs) {
      const changePath = path.join(changesPath, dir.name);
      const storyPath = path.join(changePath, 'story.md');
      const proposalPath = path.join(changePath, 'proposal.md');

      const hasStory = await fileExists(storyPath);
      const hasProposal = await fileExists(proposalPath);

      if (hasProposal) {
        stories.push({
          name: dir.name,
          path: changePath,
          hasStory,
          hasProposal,
        });
      }
    }

    if (stories.length === 0) {
      console.log(chalk.yellow('\nNo stories found.\n'));
      console.log(chalk.gray('Run `openspec new change <name>` to create a change with a proposal.\n'));
      return;
    }

    // Filter if changeName is specified
    const filtered = changeName
      ? stories.filter(s => s.name === changeName)
      : stories;

    if (filtered.length === 0) {
      console.log(chalk.yellow(`\nNo story found for '${changeName}'.\n`));
      return;
    }

    console.log(chalk.cyan('\n📋 Stories:\n'));

    for (const story of filtered) {
      const hasStoryBadge = story.hasStory ? chalk.green('✓') : chalk.gray('○');
      const name = chalk.bold(story.name);
      const metadataPath = path.join(story.path, '.openspec.yaml');
      let issueId = '';

      try {
        const content = await fs.readFile(metadataPath, 'utf-8');
        const metadata = yaml.parse(content);
        if (metadata.redmine?.issueId) {
          issueId = chalk.gray(` (Issue #${metadata.redmine.issueId})`);
        }
      } catch {
        // No metadata
      }

      console.log(`${hasStoryBadge} ${name}${issueId}`);
      console.log(`   ${story.path}\n`);
    }
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      console.log(chalk.yellow('\nNo changes directory found.\n'));
    } else {
      console.log(chalk.red(`\nError: ${(error as Error).message}\n`));
    }
  }
}

/**
 * Helper function to extract capabilities from proposal
 */
function extractCapabilities(proposal: string): string[] {
  const capabilities: string[] = [];
  let inCapabilities = false;

  const lines = proposal.split('\n');
  for (const line of lines) {
    if (line.includes('Capabilities') || line.includes('功能')) {
      inCapabilities = true;
      continue;
    }

    if (inCapabilities) {
      if (line.startsWith('##') || line.trim() === '') {
        break;
      }

      const match = line.match(/^[-*]\s+(.+)$/);
      if (match) {
        capabilities.push(match[1].trim());
      }
    }
  }

  // If no capabilities found, return the title as a single capability
  if (capabilities.length === 0) {
    const titleMatch = proposal.match(/^#\s+(.+)$/m);
    if (titleMatch) {
      capabilities.push(titleMatch[1].trim());
    }
  }

  return capabilities;
}

/**
 * Helper function to extract summary from proposal
 */
function extractSummary(proposal: string): string {
  // Extract content from Why section or first paragraph
  const whyMatch = proposal.match(/## Why[\s\S]*?(?=\n##|\n*$)/i);
  if (whyMatch) {
    return whyMatch[0].trim();
  }

  // Get first paragraph
  const lines = proposal.split('\n');
  const firstParagraph: string[] = [];
  for (const line of lines) {
    if (line.startsWith('#')) continue;
    if (line.trim() === '') break;
    firstParagraph.push(line);
  }

  return firstParagraph.join('\n').trim() || proposal.substring(0, 500);
}

/**
 * Generate story.md content
 */
function generateStoryContent(name: string, summary: string, capabilities: string[]): string {
  const today = new Date().toISOString().split('T')[0];
  const status = 'propose';

  let content = `# Story: ${name}\n\n`;
  content += `**Status**: ${status}\n`;
  content += `**Priority**: Medium\n`;
  content += `**Story Points**: 5\n\n`;
  content += `## User Story\n\n`;
  content += `As a user,\n`;
  content += `I want ${name},\n`;
  content += `So that ${summary.substring(0, 100)}...\n\n`;
  content += `## Capabilities\n\n`;
  capabilities.forEach(cap => {
    content += `- **${cap}**\n`;
  });
  content += `\n## Acceptance Criteria\n\n`;
  content += `<!-- Define the acceptance criteria for this story -->\n\n`;
  content += `- [ ] **AC1**: ...\n`;
  content += `- [ ] **AC2**: ...\n`;
  content += `- [ ] **AC3**: ...\n\n`;
  content += `## Definition of Done\n\n`;
  content += `- [ ] All acceptance criteria met\n`;
  content += `- [ ] Code reviewed\n`;
  content += `- [ ] Tests pass\n`;
  content += `- [ ] Documentation updated\n\n`;
  content += `## Related Tasks\n\n`;
  content += `<!-- Tasks will be populated by openspec task breakdown command -->\n\n`;
  content += `## Notes\n\n`;
  content += `<!-- Any additional notes about this story -->\n\n`;
  content += `---\n\n`;
  content += `*Last updated: ${today}*\n`;

  return content;
}

/**
 * Helper function to check if file exists
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
 * Register story commands with the CLI
 */
export function registerStoryCommand(program: Command): void {
  const storyCmd = program
    .command('story')
    .description('Story management');

  storyCmd
    .command('breakdown <sprint-name> <change-name>')
    .description('Break down a proposal into a story')
    .option('-i, --interactive', 'Interactive mode')
    .action((sprintName, changeName, options) => breakdownStory(sprintName, changeName, options));

  storyCmd
    .command('refine <story-name>')
    .description('Refine a story with acceptance criteria')
    .option('-a, --add', 'Add acceptance criteria')
    .action((storyName, options) => refineStory(storyName, options));

  storyCmd
    .command('list [change-name]')
    .description('List stories for a change or all stories')
    .action((changeName) => listStories(changeName));
}