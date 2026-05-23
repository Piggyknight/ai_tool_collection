## Why

OPSX currently treats `/opsx:propose` arguments as a change name or free-form description. Teams that use Redmine still have to manually copy the issue title, description, comments, and status context into the OpenSpec proposal, then manually move the Redmine issue through workflow states as implementation starts and finishes.

This creates duplicated work and weak traceability between an OpenSpec change and the source Redmine ticket. A shorthand such as `/opsx:propose #12` should make Redmine the source of truth for the initial change context, while later OPSX lifecycle actions should keep the linked Redmine issue state aligned.

## What Changes

- Teach OPSX propose instructions to recognize a Redmine issue reference argument such as `#12` or `redmine:#12`.
- When a Redmine issue reference is provided, fetch the issue title and details from the configured Redmine instance, derive the OpenSpec change name from the issue subject, prefix the change name with the Redmine issue ID for traceability, and use the issue content as proposal context.
- Persist the Redmine issue linkage in change metadata so later OPSX actions can resolve the same issue without needing the number repeated.
- Teach OPSX apply instructions to update the linked Redmine issue to the configured implementation state when work begins.
- Teach OPSX archive instructions to update the linked Redmine issue to the next configured workflow state after archive succeeds.
- Teach OPSX archive instructions to add a Redmine note containing the overall implementation summary, relevant OpenSpec documents, changed-file summary, and QA-focused test guidance before moving the issue to the next workflow state.
- Keep Redmine integration optional: non-Redmine OPSX usage remains unchanged, and missing Redmine configuration produces a clear, recoverable message.

## Capabilities

### New Capabilities

- `opsx-redmine-ticket-workflow`: Redmine ticket references in OPSX propose/apply/archive workflows and linked Redmine status transitions.

### Modified Capabilities

- None.

## Impact

- **User-facing behavior**:
  - `/opsx:propose #12` creates a change from Redmine issue 12 with a name such as `redmine-12-<subject-kebab>`.
  - `/opsx:apply <change>` updates the linked Redmine issue to the implementation state.
  - `/opsx:archive <change>` posts an implementation-and-QA note to the linked Redmine issue, then updates it to the next workflow state after archival.
- **Implementation areas**:
  - `src/core/templates/workflows/propose.ts`
  - `src/core/templates/workflows/apply-change.ts`
  - `src/core/templates/workflows/archive-change.ts`
  - `src/core/redmine/*`
  - change metadata helpers if Redmine linkage needs first-class read/write support
- **Testing**:
  - Template tests for Redmine issue-reference guidance in generated OPSX skills/commands.
  - Redmine helper tests for issue reference parsing, metadata persistence, and status target resolution.
