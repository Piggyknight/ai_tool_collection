/**
 * Command Reference Utilities
 *
 * Utilities for transforming command references to tool-specific formats.
 */

/**
 * Transforms colon-based command references to hyphen-based format.
 * Converts `/opsx:` patterns to `/opsx-` for tools that use hyphen syntax.
 *
 * @param text - The text containing command references
 * @returns Text with command references transformed to hyphen format
 *
 * @example
 * transformToHyphenCommands('/opsx:new') // returns '/opsx-new'
 * transformToHyphenCommands('Use /opsx:apply to implement') // returns 'Use /opsx-apply to implement'
 */
export function transformToHyphenCommands(text: string): string {
  return text.replace(/\/opsx:/g, '/opsx-');
}

/**
 * Adjusts generic workflow instructions for Claude Code's native interaction model.
 * Claude Code can ask the user directly; it does not expose an AskUserQuestion tool.
 */
export function transformToClaudeCodeInstructions(text: string): string {
  return text
    .replace(/使用 \*\*AskUserQuestion tool\*\*（开放式，无预设选项）询问：/g, '直接向用户提出开放式问题：')
    .replace(/使用 \*\*AskUserQuestion Tool\*\*（开放式，无预设选项）询问：/g, '直接向用户提出开放式问题：')
    .replace(/使用 \*\*AskUserQuestion tool\*\* 让用户选择/g, '直接列出候选项并请用户选择')
    .replace(/使用 \*\*AskUserQuestion tool\*\* 确认/g, '直接向用户确认')
    .replace(/使用 \*\*AskUserQuestion tool\*\* 进行澄清/g, '直接向用户提出澄清问题')
    .replace(/使用 \*\*AskUserQuestion 工具\*\*/g, '直接向用户询问')
    .replace(/使用 \*\*TodoWrite tool\*\*/g, '使用 Claude Code 的待办能力');
}
