import { describe, it, expect } from 'vitest';
import { transformToClaudeCodeInstructions, transformToHyphenCommands } from '../../src/utils/command-references.js';

describe('transformToHyphenCommands', () => {
  describe('basic transformations', () => {
    it('should transform single command reference', () => {
      expect(transformToHyphenCommands('/opsx:new')).toBe('/opsx-new');
    });

    it('should transform multiple command references', () => {
      const input = '/opsx:new and /opsx:apply';
      const expected = '/opsx-new and /opsx-apply';
      expect(transformToHyphenCommands(input)).toBe(expected);
    });

    it('should transform command reference in context', () => {
      const input = 'Use /opsx:apply to implement tasks';
      const expected = 'Use /opsx-apply to implement tasks';
      expect(transformToHyphenCommands(input)).toBe(expected);
    });

    it('should handle backtick-quoted commands', () => {
      const input = 'Run `/opsx:continue` to proceed';
      const expected = 'Run `/opsx-continue` to proceed';
      expect(transformToHyphenCommands(input)).toBe(expected);
    });
  });

  describe('edge cases', () => {
    it('should return unchanged text with no command references', () => {
      const input = 'This is plain text without commands';
      expect(transformToHyphenCommands(input)).toBe(input);
    });

    it('should return empty string unchanged', () => {
      expect(transformToHyphenCommands('')).toBe('');
    });

    it('should not transform similar but non-matching patterns', () => {
      const input = '/ops:new opsx: /other:command';
      expect(transformToHyphenCommands(input)).toBe(input);
    });

    it('should handle multiple occurrences on same line', () => {
      const input = '/opsx:new /opsx:continue /opsx:apply';
      const expected = '/opsx-new /opsx-continue /opsx-apply';
      expect(transformToHyphenCommands(input)).toBe(expected);
    });
  });

  describe('multiline content', () => {
    it('should transform references across multiple lines', () => {
      const input = `Use /opsx:new to start
Then /opsx:continue to proceed
Finally /opsx:apply to implement`;
      const expected = `Use /opsx-new to start
Then /opsx-continue to proceed
Finally /opsx-apply to implement`;
      expect(transformToHyphenCommands(input)).toBe(expected);
    });
  });

  describe('all known commands', () => {
    const commands = [
      'new',
      'continue',
      'apply',
      'ff',
      'sync',
      'archive',
      'bulk-archive',
      'verify',
      'explore',
      'onboard',
    ];

    for (const cmd of commands) {
      it(`should transform /opsx:${cmd}`, () => {
        expect(transformToHyphenCommands(`/opsx:${cmd}`)).toBe(`/opsx-${cmd}`);
      });
    }
  });
});

describe('transformToClaudeCodeInstructions', () => {
  it('should replace non-Claude user question tool references', () => {
    const input = `使用 **AskUserQuestion tool**（开放式，无预设选项）询问：
使用 **AskUserQuestion tool** 让用户选择
使用 **AskUserQuestion tool** 确认
使用 **AskUserQuestion tool** 进行澄清`;

    const output = transformToClaudeCodeInstructions(input);

    expect(output).toContain('直接向用户提出开放式问题：');
    expect(output).toContain('直接列出候选项并请用户选择');
    expect(output).toContain('直接向用户确认');
    expect(output).toContain('直接向用户提出澄清问题');
    expect(output).not.toContain('AskUserQuestion');
  });

  it('should replace TodoWrite wording with Claude Code wording', () => {
    const output = transformToClaudeCodeInstructions('使用 **TodoWrite tool** 跟踪进度');
    expect(output).toBe('使用 Claude Code 的待办能力 跟踪进度');
  });
});
