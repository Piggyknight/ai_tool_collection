/**
 * Claude Code Command Adapter
 *
 * Formats commands for Claude Code following its frontmatter specification.
 */

import path from 'path';
import { transformToClaudeCodeInstructions } from '../../../utils/command-references.js';
import type { CommandContent, ToolCommandAdapter } from '../types.js';

/**
 * Escapes a string value for safe YAML output.
 * Quotes the string if it contains special YAML characters.
 */
function escapeYamlValue(value: string): string {
  // Check if value needs quoting (contains special YAML characters or starts/ends with whitespace)
  const needsQuoting = /[:\n\r#{}[\],&*!|>'"%@`]|^\s|\s$/.test(value);
  if (needsQuoting) {
    // Use double quotes and escape internal double quotes and backslashes
    const escaped = value.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
    return `"${escaped}"`;
  }
  return value;
}

/**
 * Claude Code adapter for command generation.
 * File path: .claude/commands/opsx/<id>.md
 * Frontmatter: description, argument-hint
 */
export const claudeAdapter: ToolCommandAdapter = {
  toolId: 'claude',

  getFilePath(commandId: string): string {
    return path.join('.claude', 'commands', 'opsx', `${commandId}.md`);
  },

  formatFile(content: CommandContent): string {
    const body = transformToClaudeCodeInstructions(content.body);

    return `---
description: ${escapeYamlValue(content.description)}
argument-hint: ${escapeYamlValue('[command arguments]')}
---

用户提供的参数：$ARGUMENTS

${body}
`;
  },
};
