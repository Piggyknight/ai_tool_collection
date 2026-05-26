import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { promises as fs } from 'fs';
import path from 'path';
import os from 'os';

const updateStatus = vi.fn();
const addNoteFromFile = vi.fn();

vi.mock('../../../src/core/redmine/instance-manager.js', () => ({
  getInstanceManager: () => ({
    loadConfig: vi.fn().mockResolvedValue(undefined),
    getInstanceByName: vi.fn(),
    createWrapper: vi.fn().mockResolvedValue({
      updateStatus,
      addNoteFromFile,
    }),
  }),
}));

describe('Redmine workflow sync', () => {
  let tempDir: string;
  let changeDir: string;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'openspec-redmine-sync-'));
    changeDir = path.join(tempDir, 'openspec', 'changes', 'redmine-change');
    await fs.mkdir(changeDir, { recursive: true });
    updateStatus.mockReset();
    addNoteFromFile.mockReset();
  });

  afterEach(async () => {
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('updates associated issue status for apply', async () => {
    const { syncChangeRedmineStatus } = await import('../../../src/core/redmine/workflow-sync.js');
    await fs.writeFile(
      path.join(changeDir, '.openspec.yaml'),
      'schema: spec-driven\nredmine:\n  issueId: 123\n',
      'utf-8'
    );

    const result = await syncChangeRedmineStatus(changeDir, 'applying', { projectRoot: tempDir });

    expect(result).toEqual({
      issueId: 123,
      status: 'Applying',
      updated: true,
    });
    expect(updateStatus).toHaveBeenCalledWith(123, 'Applying');
  });

  it('adds archive note and moves the issue to code review', async () => {
    const { syncArchivedChangeToRedmine } = await import('../../../src/core/redmine/workflow-sync.js');
    const notePath = path.join(tempDir, 'note.md');
    await fs.writeFile(notePath, '# Archive note\n', 'utf-8');
    await fs.writeFile(
      path.join(changeDir, '.openspec.yaml'),
      'schema: spec-driven\nredmine:\n  issueId: "456"\n',
      'utf-8'
    );

    const result = await syncArchivedChangeToRedmine(changeDir, notePath, { projectRoot: tempDir });

    expect(result).toEqual({
      issueId: 456,
      status: 'Code Review',
      notePath,
      updated: true,
      noteAdded: true,
    });
    expect(addNoteFromFile).toHaveBeenCalledWith(456, notePath);
    expect(updateStatus).toHaveBeenCalledWith(456, 'Code Review');
  });

  it('skips cleanly when change has no associated issue', async () => {
    const { syncChangeRedmineStatus } = await import('../../../src/core/redmine/workflow-sync.js');

    const result = await syncChangeRedmineStatus(changeDir, 'applying', { projectRoot: tempDir });

    expect(result.updated).toBe(false);
    expect(result.skippedReason).toContain('No redmine.issueId');
    expect(updateStatus).not.toHaveBeenCalled();
  });
});
