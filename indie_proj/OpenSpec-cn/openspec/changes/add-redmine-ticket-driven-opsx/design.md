## Overview

The existing OPSX workflow is mostly prompt-driven: generated skills and command files instruct the coding assistant to run OpenSpec CLI commands and edit change artifacts. Redmine integration code already exists under `src/core/redmine`, including instance detection, issue fetching, issue status updates, and OpenSpec-to-Hermes status mapping.

This change should connect those two layers without changing the base OPSX lifecycle for users who do not pass a Redmine ticket reference.

## Design

### Issue Reference Parsing

OPSX propose instructions should treat the first argument as a Redmine ticket reference when it matches one of these forms:

- `#12`
- `redmine:#12`
- `redmine:12`

The parsed value is the numeric Redmine issue ID. Other input continues to behave as a change name or description.

### Redmine Issue Fetch

When the propose input is a Redmine issue reference, the generated instructions should tell the assistant to:

1. Resolve the configured Redmine instance for the current project/worktree.
2. Fetch the issue with `red-cli issue view <id> --json` or the existing `RedmineCliWrapper.getIssue` equivalent.
3. Use the issue subject to derive a kebab-case OpenSpec change name fragment.
4. Prefix Redmine-driven change names with the issue ID using `redmine-<issue-id>-<subject-kebab>` so the directory name, status output, and archive path remain easy to match back to Redmine.
5. Use the issue subject, description, tracker, priority, assignee, status, and relevant custom fields as source context for `proposal.md`, `design.md`, `specs`, and `tasks`.

If Redmine configuration or fetch fails, the assistant should report the failure and ask whether to continue with manual input instead of silently creating a weak proposal.

### Link Persistence

The generated propose workflow should persist Redmine linkage in `openspec/changes/<name>/.openspec.yaml`:

```yaml
redmine:
  issueId: 12
  changeName: "redmine-12-<subject-kebab>"
  subject: "<issue subject>"
  status: "<status at propose time>"
  instance: "<resolved instance name, when available>"
```

The metadata must remain with the change when it is archived.

### Apply Status Transition

When `/opsx:apply` selects a change, it should read `.openspec.yaml`. If a Redmine issue is linked, the workflow should update the issue to the configured implementation state before or when the first task begins.

Default target: `Applying`, via the existing Hermes `applying` mapping.

The transition should be best-effort but visible:

- On success, show a short note that Redmine was updated.
- On failure, show the error and continue only after making the failed sync explicit.

### Archive Status Transition

Before `/opsx:archive` moves the change directory, it should prepare a Markdown Redmine note for linked issues. The note should summarize the implementation and give QA enough context to inspect the change and generate tests. It should include:

- change name, schema, Redmine issue ID, and archive path
- a summary derived from `proposal.md`, `design.md`, `tasks.md`, and `specs/**/spec.md`
- completed tasks and any remaining risks or unfinished items
- changed-file summary from `git diff --stat` and `git diff --name-status` when available
- relevant OpenSpec document paths and their QA-useful points
- QA-focused checks and suggested regression/boundary tests

The workflow should write the note to a file and post it with `red-cli issue note <id> --message-file <note-file>` to avoid fragile shell quoting for long multi-line content.

When `/opsx:archive` completes the local archive move successfully, it should post the Redmine note and then update the linked Redmine issue to the next configured workflow state.

Default target: `Code Review`, via the Hermes state after `done` in the existing workflow. If the current or configured mapping says another next step is appropriate, the mapper/config should take precedence.

The Redmine note and status update should happen after the local archive succeeds so Redmine does not advance when archival fails. If Redmine sync fails, the workflow should report the error and keep the generated note file path visible for retry.

### Configuration

Initial implementation can reuse the existing default mappings in `StatusMapper`:

- apply: `applying` -> `Applying`
- archive next step: `code-review` -> `Code Review`

Future configuration can expose explicit `opsx.applyStatus` and `opsx.archiveNextStatus` values under Redmine config if teams need different workflows.

## Open Questions

- Should archive move Redmine directly to `Code Review`, or should it use `getNextHermesState(done)` so teams can model `testing` first?
- Should propose also transition the Redmine issue from `Plan` to `Propose`, or only read data and persist linkage?
