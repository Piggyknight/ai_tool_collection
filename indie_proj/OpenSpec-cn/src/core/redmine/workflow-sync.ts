import { promises as fs } from 'fs';
import path from 'path';
import os from 'os';
import yaml from 'yaml';
import { RedmineCliWrapper } from './cli-wrapper.js';
import { getInstanceManager, type RedmineInstance } from './instance-manager.js';
import { StatusMapper, type HermesState } from './status-mapping.js';
import type { TaskProgress } from '../../utils/task-progress.js';

interface RedmineChangeMetadata {
  redmine?: {
    instance?: string;
    issueId?: number | string;
  };
}

export interface RedmineWorkflowSyncResult {
  issueId?: number;
  status?: string;
  notePath?: string;
  updated: boolean;
  noteAdded?: boolean;
  skippedReason?: string;
  error?: string;
}

export interface ArchiveNoteOptions {
  changeName: string;
  changeDir: string;
  archivePath: string;
  schemaName: string;
  issueId: number;
  progress: TaskProgress;
}

function parseIssueId(rawIssueId: number | string | undefined): number | undefined {
  if (typeof rawIssueId === 'number' && Number.isFinite(rawIssueId)) {
    return rawIssueId;
  }
  if (typeof rawIssueId === 'string' && rawIssueId.trim() !== '') {
    const parsed = Number.parseInt(rawIssueId.trim(), 10);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return undefined;
}

async function readRedmineMetadata(changeDir: string): Promise<{ issueId: number; instance?: string } | null> {
  const metadataPath = path.join(changeDir, '.openspec.yaml');
  let content: string;

  try {
    content = await fs.readFile(metadataPath, 'utf-8');
  } catch {
    return null;
  }

  let parsed: RedmineChangeMetadata | null;
  try {
    parsed = yaml.parse(content) as RedmineChangeMetadata | null;
  } catch {
    return null;
  }
  const issueId = parseIssueId(parsed?.redmine?.issueId);
  if (!issueId) {
    return null;
  }

  return {
    issueId,
    instance: parsed?.redmine?.instance,
  };
}

async function createWrapper(projectRoot: string, instanceName?: string): Promise<RedmineCliWrapper> {
  const manager = getInstanceManager();
  await manager.loadConfig();

  let instance: RedmineInstance | undefined;
  if (instanceName) {
    instance = manager.getInstanceByName(instanceName);
    if (!instance) {
      throw new Error(`Redmine instance '${instanceName}' not found`);
    }
  }

  if (!instance) {
    return manager.createWrapper(projectRoot);
  }

  return new RedmineCliWrapper({
    server: instance.server,
    apiKey: instance.apiKey,
    projectId: instance.projectId,
    cliPath: instance.cliPath,
  });
}

export async function getChangeRedmineIssue(changeDir: string): Promise<{ issueId: number; instance?: string } | null> {
  return readRedmineMetadata(changeDir);
}

export async function syncChangeRedmineStatus(
  changeDir: string,
  state: HermesState,
  options: { projectRoot?: string } = {}
): Promise<RedmineWorkflowSyncResult> {
  const metadata = await readRedmineMetadata(changeDir);
  if (!metadata) {
    return {
      updated: false,
      skippedReason: 'No redmine.issueId found in .openspec.yaml',
    };
  }

  const mapper = new StatusMapper();
  const status = mapper.hermesToRedmine(state);

  try {
    const projectRoot = options.projectRoot ?? path.resolve(changeDir, '../../..');
    const wrapper = await createWrapper(projectRoot, metadata.instance);
    await wrapper.updateStatus(metadata.issueId, status);
    return {
      issueId: metadata.issueId,
      status,
      updated: true,
    };
  } catch (error) {
    return {
      issueId: metadata.issueId,
      status,
      updated: false,
      error: (error as Error).message,
    };
  }
}

async function listRelativeFiles(dir: string): Promise<string[]> {
  const results: string[] = [];

  async function walk(current: string): Promise<void> {
    const entries = await fs.readdir(current, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        await walk(fullPath);
      } else {
        results.push(path.relative(dir, fullPath).replace(/\\/g, '/'));
      }
    }
  }

  try {
    await walk(dir);
  } catch {
    return [];
  }

  return results.sort();
}

export async function createArchiveRedmineNote(options: ArchiveNoteOptions): Promise<string> {
  const completed = options.progress.completed;
  const total = options.progress.total;
  const remaining = Math.max(total - completed, 0);
  const files = await listRelativeFiles(options.changeDir);
  const notePath = path.join(
    os.tmpdir(),
    `openspec-redmine-archive-${options.issueId}-${Date.now()}.md`
  );

  const fileList = files.length > 0
    ? files.map((file) => `- ${file}`).join('\n')
    : '- No artifact files found';

  const content = `# OpenSpec Archive: ${options.changeName}

- Change: ${options.changeName}
- Schema: ${options.schemaName}
- Redmine issue: #${options.issueId}
- Archive target: ${options.archivePath.replace(/\\/g, '/')}
- Tasks: ${completed}/${total} complete (${remaining} remaining)

## Archived Artifacts

${fileList}

## QA Notes

- Review the archived proposal, design, tasks, and specs for expected behavior.
- Re-run relevant tests for files touched while implementing this change.
- Pay attention to any tasks left incomplete before archive.
`;

  await fs.writeFile(notePath, content, 'utf-8');
  return notePath;
}

export async function syncArchivedChangeToRedmine(
  archivedChangeDir: string,
  notePath: string,
  options: { projectRoot?: string } = {}
): Promise<RedmineWorkflowSyncResult> {
  const metadata = await readRedmineMetadata(archivedChangeDir);
  if (!metadata) {
    return {
      updated: false,
      notePath,
      skippedReason: 'No redmine.issueId found in .openspec.yaml',
    };
  }

  const mapper = new StatusMapper();
  const status = mapper.hermesToRedmine('code-review');

  try {
    const projectRoot = options.projectRoot ?? path.resolve(archivedChangeDir, '../../../..');
    const wrapper = await createWrapper(projectRoot, metadata.instance);
    await wrapper.addNoteFromFile(metadata.issueId, notePath);
    await wrapper.updateStatus(metadata.issueId, status);
    return {
      issueId: metadata.issueId,
      status,
      notePath,
      updated: true,
      noteAdded: true,
    };
  } catch (error) {
    return {
      issueId: metadata.issueId,
      status,
      notePath,
      updated: false,
      noteAdded: false,
      error: (error as Error).message,
    };
  }
}
