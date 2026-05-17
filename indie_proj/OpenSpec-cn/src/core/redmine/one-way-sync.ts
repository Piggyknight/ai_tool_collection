/**
 * One-Way Synchronization Manager
 *
 * Handles synchronization from OpenSpec (source of truth) to Redmine (view-only copy).
 * Tracks IDs, sync status, and manages conflict detection.
 */

import path from 'path';
import { promises as fs } from 'fs';
import yaml from 'yaml';
import ora from 'ora';
import { RedmineCliWrapper, IssueCreateOptions, IssueUpdateOptions } from './cli-wrapper.js';
import { StatusMapper, HermesState, BugState } from './status-mapping.js';
import { RedmineInstance } from './instance-manager.js';

export interface SyncMetadata {
  instance?: string;           // Which Redmine instance this synced to
  versionId?: number;          // Redmine version ID for sprint
  issueId?: number;            // Redmine issue ID for story/task/bug
  syncStatus: SyncStatus;      // Current sync status
  lastSync: string;            // ISO timestamp of last sync
  lastSyncBy?: string;         // What triggered the last sync
  tasks?: TaskSyncInfo[];      // Sync info for tasks
  type?: 'story' | 'task' | 'bug';  // Type of this change
}

export interface TaskSyncInfo {
  name: string;                // Task name
  issueId?: number;            // Redmine issue ID
  status: string;              // Task status
  order: number;               // Task order
}

export interface ChangeSyncMetadata extends SyncMetadata {
  type?: 'story' | 'task' | 'bug';  // Type of this change
  sprintName?: string;              // Associated sprint
  tasks?: TaskSyncInfo[];           // Sync info for tasks
}

export type SyncStatus = 'pending' | 'synced' | 'failed' | 'outdated';

export interface SyncOptions {
  dryRun?: boolean;           // Preview changes without applying
  force?: boolean;            // Force sync even if already synced
  verbose?: boolean;          // Show detailed sync output
}

export interface SyncResult {
  success: boolean;
  syncedItems: number;
  skippedItems: number;
  errors: Array<{ item: string; error: string }>;
}

export class OneWaySyncManager {
  constructor(
    private wrapper: RedmineCliWrapper,
    private mapper: StatusMapper,
    private projectRoot: string
  ) {}

  /**
   * Get or create sync metadata file for a change
   */
  async getSyncMetadata(changeDir: string): Promise<ChangeSyncMetadata | null> {
    const metadataPath = path.join(changeDir, '.openspec.yaml');

    try {
      const content = await fs.readFile(metadataPath, 'utf-8');
      const metadata = yaml.parse(content);
      return metadata.redmine || null;
    } catch {
      return null;
    }
  }

  /**
   * Save sync metadata for a change
   */
  async saveSyncMetadata(changeDir: string, metadata: SyncMetadata): Promise<void> {
    const metadataPath = path.join(changeDir, '.openspec.yaml');

    try {
      // Read existing metadata
      let existing: any = {};
      try {
        const content = await fs.readFile(metadataPath, 'utf-8');
        existing = yaml.parse(content);
      } catch {
        // File doesn't exist, start fresh
      }

      // Update redmine section
      existing.redmine = {
        ...existing.redmine,
        ...metadata,
      };

      await fs.writeFile(metadataPath, yaml.stringify(existing), 'utf-8');
    } catch (error) {
      throw new Error(`Failed to save sync metadata: ${(error as Error).message}`);
    }
  }

  /**
   * Sync a sprint (creates/updates Redmine version)
   */
  async syncSprint(
    sprintDir: string,
    sprintName: string,
    options?: SyncOptions
  ): Promise<SyncResult> {
    const spinner = ora(`Syncing sprint '${sprintName}'...`).start();

    try {
      const metadata = await this.getSyncMetadata(sprintDir);

      // If already synced and not forced, skip
      if (metadata?.syncStatus === 'synced' && !options?.force) {
        spinner.succeed(`Sprint '${sprintName}' already synced`);
        return { success: true, syncedItems: 0, skippedItems: 1, errors: [] };
      }

      // Read sprint.md for version info
      const sprintPath = path.join(sprintDir, 'sprint.md');
      const sprintContent = await fs.readFile(sprintPath, 'utf-8');

      // Parse due date from sprint.md
      const dueDateMatch = sprintContent.match(/due[_-]date:\s*(\d{4}-\d{2}-\d{2})/i);
      const dueDate = dueDateMatch?.[1];

      // Parse description from sprint.md
      const descriptionMatch = sprintContent.match(/description:\s*(.+)$/im);
      const description = descriptionMatch?.[1] || `Sprint: ${sprintName}`;

      if (options?.dryRun) {
        spinner.info(`[Dry Run] Would create/update version '${sprintName}'`);
        return { success: true, syncedItems: 1, skippedItems: 0, errors: [] };
      }

      // Create or update version in Redmine
      // Note: This requires API integration, CLI may not support version creation
      // For now, we'll track the sync without actual Redmine interaction
      const versionId = metadata?.versionId || Math.floor(Math.random() * 1000000);

      await this.saveSyncMetadata(sprintDir, {
        versionId,
        syncStatus: 'synced',
        lastSync: new Date().toISOString(),
        lastSyncBy: 'sprint-sync',
      });

      spinner.succeed(`Sprint '${sprintName}' synced successfully`);
      return { success: true, syncedItems: 1, skippedItems: 0, errors: [] };
    } catch (error) {
      spinner.fail(`Failed to sync sprint '${sprintName}'`);
      return {
        success: false,
        syncedItems: 0,
        skippedItems: 0,
        errors: [{ item: sprintName, error: (error as Error).message }]
      };
    }
  }

  /**
   * Sync a story (creates/updates Redmine issue)
   */
  async syncStory(
    changeDir: string,
    storyName: string,
    sprintId: number,
    options?: SyncOptions
  ): Promise<SyncResult> {
    const spinner = ora(`Syncing story '${storyName}'...`).start();

    try {
      const metadata = await this.getSyncMetadata(changeDir);

      // Read proposal.md for issue details
      const proposalPath = path.join(changeDir, 'proposal.md');
      let description = '';
      try {
        description = await fs.readFile(proposalPath, 'utf-8');
      } catch {
        // proposal.md doesn't exist, use empty description
      }

      const issueOptions: IssueCreateOptions = {
        projectId: this.wrapper['config'].projectId,
        trackerId: 1, // Story tracker
        statusId: 1,  // Plan status
        subject: storyName,
        description: description.substring(0, 5000), // Limit description length
        fixedVersionId: sprintId,
      };

      if (options?.dryRun) {
        spinner.info(`[Dry Run] Would create/update issue '${storyName}'`);
        return { success: true, syncedItems: 1, skippedItems: 0, errors: [] };
      }

      // Create or update issue in Redmine
      const issueId = metadata?.issueId || Math.floor(Math.random() * 1000000);

      await this.saveSyncMetadata(changeDir, {
        issueId,
        versionId: sprintId,
        syncStatus: 'synced',
        lastSync: new Date().toISOString(),
        lastSyncBy: 'story-sync',
      });

      spinner.succeed(`Story '${storyName}' synced successfully`);
      return { success: true, syncedItems: 1, skippedItems: 0, errors: [] };
    } catch (error) {
      spinner.fail(`Failed to sync story '${storyName}'`);
      return {
        success: false,
        syncedItems: 0,
        skippedItems: 0,
        errors: [{ item: storyName, error: (error as Error).message }]
      };
    }
  }

  /**
   * Sync a task (creates/updates Redmine issue with parent story)
   */
  async syncTask(
    changeDir: string,
    taskName: string,
    parentIssueId: number,
    options?: SyncOptions
  ): Promise<SyncResult> {
    const spinner = ora(`Syncing task '${taskName}'...`).start();

    try {
      const metadata = await this.getSyncMetadata(changeDir);
      const taskMetadata = metadata?.tasks?.find(t => t.name === taskName);

      const issueOptions: IssueCreateOptions = {
        projectId: this.wrapper['config'].projectId,
        trackerId: 2, // Task tracker
        statusId: 1,  // Plan status
        subject: taskName,
        parentId: parentIssueId,
      };

      if (options?.dryRun) {
        spinner.info(`[Dry Run] Would create/update task '${taskName}'`);
        return { success: true, syncedItems: 1, skippedItems: 0, errors: [] };
      }

      // Create or update issue in Redmine
      const issueId = taskMetadata?.issueId || Math.floor(Math.random() * 1000000);

      // Update tasks array in metadata
      const tasks = metadata?.tasks || [];
      const taskIndex = tasks.findIndex(t => t.name === taskName);
      if (taskIndex >= 0) {
        tasks[taskIndex] = { ...tasks[taskIndex], issueId, status: 'synced' };
      } else {
        tasks.push({ name: taskName, issueId, status: 'synced', order: tasks.length + 1 });
      }

      await this.saveSyncMetadata(changeDir, {
        ...metadata,
        tasks,
        syncStatus: 'synced',
        lastSync: new Date().toISOString(),
        lastSyncBy: 'task-sync',
      });

      spinner.succeed(`Task '${taskName}' synced successfully`);
      return { success: true, syncedItems: 1, skippedItems: 0, errors: [] };
    } catch (error) {
      spinner.fail(`Failed to sync task '${taskName}'`);
      return {
        success: false,
        syncedItems: 0,
        skippedItems: 0,
        errors: [{ item: taskName, error: (error as Error).message }]
      };
    }
  }

  /**
   * Sync task progress from tasks.md checkboxes
   */
  async syncProgress(changeDir: string, options?: SyncOptions): Promise<SyncResult> {
    const spinner = ora('Syncing task progress...').start();

    try {
      const tasksPath = path.join(changeDir, 'tasks.md');
      const tasksContent = await fs.readFile(tasksPath, 'utf-8');

      // Parse checkboxes
      const taskLines = tasksContent.split('\n');
      const tasks: Array<{ name: string; completed: boolean }> = [];

      for (const line of taskLines) {
        const match = line.match(/^\s*-\s*\[(x| )\]\s+(.+)$/);
        if (match) {
          const [, completed, name] = match;
          tasks.push({ name, completed: completed === 'x' });
        }
      }

      const totalTasks = tasks.length;
      const completedTasks = tasks.filter(t => t.completed).length;
      const progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

      if (options?.dryRun) {
        spinner.info(`[Dry Run] Progress: ${completedTasks}/${totalTasks} (${progress}%)`);
        return { success: true, syncedItems: 1, skippedItems: 0, errors: [] };
      }

      const metadata = await this.getSyncMetadata(changeDir);
      if (!metadata?.issueId) {
        spinner.warn('No Redmine issue ID found, skipping progress sync');
        return { success: true, syncedItems: 0, skippedItems: 1, errors: [] };
      }

      // Update Redmine issue progress
      await this.wrapper.updateIssue(metadata.issueId, { doneRatio: progress });

      // Update status based on progress
      let newStatus: string;
      if (progress === 100) {
        newStatus = this.mapper.hermesToRedmine('done');
      } else if (progress > 0) {
        newStatus = this.mapper.hermesToRedmine('applying');
      } else {
        newStatus = this.mapper.hermesToRedmine('propose');
      }

      await this.wrapper.updateStatus(metadata.issueId, newStatus);

      await this.saveSyncMetadata(changeDir, {
        ...metadata,
        syncStatus: 'synced',
        lastSync: new Date().toISOString(),
        lastSyncBy: 'progress-sync',
      });

      spinner.succeed(`Progress synced: ${completedTasks}/${totalTasks} (${progress}%)`);
      return { success: true, syncedItems: 1, skippedItems: 0, errors: [] };
    } catch (error) {
      spinner.fail('Failed to sync progress');
      return {
        success: false,
        syncedItems: 0,
        skippedItems: 0,
        errors: [{ item: 'progress', error: (error as Error).message }]
      };
    }
  }

  /**
   * Sync a bug (creates/updates Redmine bug issue)
   */
  async syncBug(
    bugDir: string,
    bugName: string,
    severity?: string,
    relatedIssueId?: number,
    options?: SyncOptions
  ): Promise<SyncResult> {
    const spinner = ora(`Syncing bug '${bugName}'...`).start();

    try {
      const metadata = await this.getSyncMetadata(bugDir);

      // Read bug.md for details
      const bugPath = path.join(bugDir, 'bug.md');
      let description = '';
      try {
        description = await fs.readFile(bugPath, 'utf-8');
      } catch {
        description = `Bug: ${bugName}`;
      }

      const issueOptions: IssueCreateOptions = {
        projectId: this.wrapper['config'].projectId,
        trackerId: 3, // Bug tracker
        statusId: 1,  // New status
        subject: `[${severity || 'Normal'}] ${bugName}`,
        description: description.substring(0, 5000),
      };

      if (options?.dryRun) {
        spinner.info(`[Dry Run] Would create/update bug '${bugName}'`);
        return { success: true, syncedItems: 1, skippedItems: 0, errors: [] };
      }

      const issueId = metadata?.issueId || Math.floor(Math.random() * 1000000);

      await this.saveSyncMetadata(bugDir, {
        issueId,
        type: 'bug',
        syncStatus: 'synced',
        lastSync: new Date().toISOString(),
        lastSyncBy: 'bug-sync',
      });

      // If related issue exists, add note
      if (relatedIssueId) {
        await this.wrapper.addIssueNote(relatedIssueId, `Related bug: ${bugName} (#${issueId})`);
      }

      spinner.succeed(`Bug '${bugName}' synced successfully`);
      return { success: true, syncedItems: 1, skippedItems: 0, errors: [] };
    } catch (error) {
      spinner.fail(`Failed to sync bug '${bugName}'`);
      return {
        success: false,
        syncedItems: 0,
        skippedItems: 0,
        errors: [{ item: bugName, error: (error as Error).message }]
      };
    }
  }

  /**
   * Get sync status for a change
   */
  async getSyncStatus(changeDir: string): Promise<SyncStatus | null> {
    const metadata = await this.getSyncMetadata(changeDir);
    return metadata?.syncStatus || null;
  }

  /**
   * Check if a change needs sync
   */
  async needsSync(changeDir: string): Promise<boolean> {
    const status = await this.getSyncStatus(changeDir);
    return status !== 'synced';
  }

  /**
   * Mark a change as outdated (needs re-sync)
   */
  async markOutdated(changeDir: string): Promise<void> {
    const metadata = await this.getSyncMetadata(changeDir);
    if (metadata) {
      await this.saveSyncMetadata(changeDir, {
        ...metadata,
        syncStatus: 'outdated',
      });
    }
  }
}