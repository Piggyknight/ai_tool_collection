/**
 * Redmine CLI Wrapper
 *
 * Wraps redmine-cli functionality for programmatic access via subprocess calls.
 * All interactions with Redmine go through the redmine-cli executable.
 */

import { execa } from 'execa';
import path from 'path';
import * as os from 'os';
import { promises as fs } from 'fs';
import ora from 'ora';

export interface RedmineConfig {
  server: string;
  apiKey: string;
  projectId: number;
  cliPath?: string; // Path to red-cli.exe, defaults to 'red-cli.exe' in PATH
}

export interface RedmineIssue {
  id: number;
  project: { id: number; name: string };
  tracker: { id: number; name: string };
  status: { id: number; name: string };
  priority: { id: number; name: string };
  author: { id: number; name: string };
  assigned_to?: { id: number; name: string };
  subject: string;
  description: string;
  start_date?: string;
  due_date?: string;
  done_ratio: number;
  estimated_hours?: number;
  spent_hours?: number;
  created_on: string;
  updated_on: string;
  fixed_version?: { id: number; name: string };
  parent?: { id: number };
  custom_fields?: Array<{ id: number; name: string; value: string }>;
}

export interface RedmineVersion {
  id: number;
  project: { id: number; name: string };
  name: string;
  description: string;
  status: string;
  sharing: string;
  created_on: string;
  updated_on: string;
  due_date?: string;
}

export interface IssueCreateOptions {
  projectId: number;
  trackerId?: number;
  statusId?: number;
  priorityId?: number;
  subject: string;
  description?: string;
  categoryId?: number;
  fixedVersionId?: number;
  assignedToId?: number;
  parentId?: number;
  estimatedHours?: number;
  customFields?: Array<{ id: number; value: string }>;
}

export interface IssueUpdateOptions {
  statusId?: number;
  priorityId?: number;
  assignedToId?: number;
  doneRatio?: number;
  estimatedHours?: number;
  subject?: string;
  description?: string;
  notes?: string;
}

export interface IssueFilters {
  projectId?: number;
  trackerId?: number;
  statusId?: number;
  assignedToId?: number;
  fixedVersionId?: number;
  parentId?: number;
  query?: string;
}

export class RedmineCliWrapper {
  private cliPath: string;

  constructor(private config: RedmineConfig) {
    this.cliPath = config.cliPath || 'red-cli.exe';
  }

  /**
   * Execute a redmine-cli command and return parsed JSON output
   */
  async execute(args: string[], options?: { json?: boolean; silent?: boolean }): Promise<any> {
    const defaultOptions = { json: true, silent: true };
    const opts = { ...defaultOptions, ...options };
    const finalArgs = opts.json ? [...args, '--json'] : args;

    try {
      const { stdout } = await execa(this.cliPath, finalArgs, {
        windowsHide: true,
        shell: true,
      });

      if (opts.json && stdout) {
        return JSON.parse(stdout);
      }
      return stdout;
    } catch (error) {
      const err = error as Error & { stdout?: string; stderr?: string; exitCode?: number };
      throw new RedmineCliError(
        `Failed to execute redmine-cli: ${err.message}`,
        args,
        err.exitCode,
        err.stdout,
        err.stderr
      );
    }
  }

  /**
   * Create a new Redmine version (Sprint)
   */
  async createVersion(
    name: string,
    dueDate?: string,
    description?: string
  ): Promise<RedmineVersion> {
    // Note: redmine-cli may not have a direct version create command
    // We'll need to use the API or alternative method
    // For now, this is a placeholder for the implementation
    throw new Error('Version creation not yet implemented - requires Redmine API');
  }

  /**
   * Get all versions for the configured project
   */
  async getVersions(): Promise<RedmineVersion[]> {
    // This may require implementing a custom command in redmine-cli
    // or using the API directly
    throw new Error('Version listing not yet implemented - requires Redmine API');
  }

  /**
   * Create a new issue
   */
  async createIssue(options: IssueCreateOptions): Promise<number> {
    const args: string[] = [
      'issue',
      'create',
      '--project', options.projectId.toString(),
      '--subject', options.subject,
    ];

    if (options.trackerId) {
      args.push('--tracker', options.trackerId.toString());
    }
    if (options.statusId) {
      args.push('--status', options.statusId.toString());
    }
    if (options.priorityId) {
      args.push('--priority', options.priorityId.toString());
    }
    if (options.description) {
      // Create a temp file for description (redmine-cli expects file or editor)
      const descFile = path.join(os.tmpdir(), `openspec-desc-${Date.now()}.md`);
      await fs.writeFile(descFile, options.description, 'utf-8');
      args.push('--description', descFile);
      // TODO: Clean up temp file
    }
    if (options.fixedVersionId) {
      args.push('--target-version', options.fixedVersionId.toString());
    }
    if (options.assignedToId) {
      args.push('--assign', options.assignedToId.toString());
    }
    if (options.parentId) {
      args.push('--parent', options.parentId.toString());
    }
    if (options.estimatedHours) {
      args.push('--estimated', options.estimatedHours.toString());
    }

    // Execute non-interactively (this might need custom flags in redmine-cli)
    // For now, we'll use the API directly for reliability
    throw new Error('Interactive issue creation not yet implemented - use API approach');
  }

  /**
   * Update an existing issue
   */
  async updateIssue(id: number, options: IssueUpdateOptions): Promise<void> {
    const args: string[] = ['issue', 'edit', id.toString()];

    if (options.statusId) {
      args.push('--status', options.statusId.toString());
    }
    if (options.priorityId) {
      args.push('--priority', options.priorityId.toString());
    }
    if (options.assignedToId) {
      args.push('--assign', options.assignedToId.toString());
    }
    if (options.doneRatio !== undefined) {
      args.push('--done', options.doneRatio.toString());
    }
    if (options.subject) {
      args.push('--subject', options.subject);
    }
    if (options.notes) {
      args.push('--note', options.notes);
    }

    await this.execute(args);
  }

  /**
   * Get a single issue by ID
   */
  async getIssue(id: number): Promise<RedmineIssue> {
    const result = await this.execute(['issue', 'view', id.toString()]);
    return result.issue as RedmineIssue;
  }

  /**
   * List issues with optional filters
   */
  async listIssues(filters?: IssueFilters): Promise<RedmineIssue[]> {
    const args: string[] = ['issue', 'list'];

    if (filters?.projectId) {
      args.push('--project', filters.projectId.toString());
    }
    if (filters?.trackerId) {
      // redmine-cli uses tracker name, not ID
      // We'll need to handle this conversion
    }
    if (filters?.statusId) {
      // redmine-cli uses status name
    }
    if (filters?.assignedToId) {
      args.push('--me'); // If assigned to current user
    }
    if (filters?.fixedVersionId) {
      // Need to handle version name
    }
    if (filters?.parentId) {
      args.push('--parent', filters.parentId.toString());
    }
    if (filters?.query) {
      args.push('--query', filters.query);
    }

    const result = await this.execute(args);
    return result.issues || [];
  }

  /**
   * Add a note to an issue
   */
  async addNote(id: number, note: string, isPrivate: boolean = false): Promise<void> {
    const args: string[] = ['issue', 'note', id.toString(), '-m', note];
    if (isPrivate) {
      args.push('--private');
    }
    await this.execute(args);
  }

  /**
   * Add a note to an issue from a file.
   */
  async addNoteFromFile(id: number, noteFile: string, isPrivate: boolean = false): Promise<void> {
    const args: string[] = ['issue', 'note', id.toString(), '--message-file', noteFile];
    if (isPrivate) {
      args.push('--private');
    }
    await this.execute(args);
  }

  /**
   * Add a note to an issue (alias for consistency)
   */
  async addIssueNote(id: number, note: string): Promise<void> {
    await this.addNote(id, note);
  }

  /**
   * Update issue status
   */
  async updateStatus(id: number, statusName: string): Promise<void> {
    await this.execute(['issue', 'edit', id.toString(), '--status', statusName]);
  }

  /**
   * Test connection to Redmine
   */
  async testConnection(): Promise<boolean> {
    try {
      await this.execute(['project', 'list']);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get available trackers
   */
  async getTrackers(): Promise<Array<{ id: number; name: string }>> {
    // This might require a custom command or API call
    return [];
  }

  /**
   * Get available statuses
   */
  async getStatuses(): Promise<Array<{ id: number; name: string }>> {
    // This might require a custom command or API call
    return [];
  }
}

export class RedmineCliError extends Error {
  constructor(
    message: string,
    public args: string[],
    public exitCode?: number,
    public stdout?: string,
    public stderr?: string
  ) {
    super(message);
    this.name = 'RedmineCliError';
  }
}
