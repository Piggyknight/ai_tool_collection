## ADDED Requirements

### Requirement: Redmine Ticket Propose Input

OPSX propose workflows SHALL recognize Redmine issue references as first-class proposal input.

#### Scenario: Propose from Redmine issue reference

- **WHEN** the user invokes `/opsx:propose #12`
- **AND** Redmine integration is configured for the current project
- **THEN** the workflow SHALL fetch Redmine issue `12`
- **AND** derive the OpenSpec change name from the Redmine issue subject
- **AND** the derived change name SHALL include the Redmine issue ID
- **AND** use the Redmine issue subject and details as source context for generated planning artifacts
- **AND** persist the Redmine issue linkage in the change metadata

#### Scenario: Propose from explicit Redmine prefix

- **WHEN** the user invokes `/opsx:propose redmine:#12`
- **THEN** the workflow SHALL treat the argument as Redmine issue `12`
- **AND** follow the same Redmine-backed propose behavior as `#12`

#### Scenario: Redmine unavailable during propose

- **WHEN** the user invokes `/opsx:propose #12`
- **AND** Redmine is not configured or the issue cannot be fetched
- **THEN** the workflow SHALL report the Redmine failure clearly
- **AND** SHALL NOT silently create a proposal without Redmine context
- **AND** SHALL ask whether to continue with manual input or stop

### Requirement: Redmine Link Metadata

OPSX workflows SHALL persist enough Redmine metadata on the OpenSpec change to support later lifecycle synchronization.

#### Scenario: Store Redmine linkage

- **WHEN** an OpenSpec change is created from Redmine issue `12`
- **THEN** `.openspec.yaml` in the change directory SHALL include the linked Redmine issue ID
- **AND** the change directory name SHOULD include the Redmine issue ID for human traceability
- **AND** SHOULD include the generated change name, issue subject, status at propose time, and resolved Redmine instance when available

#### Scenario: Preserve linkage during archive

- **WHEN** a Redmine-linked change is archived
- **THEN** the Redmine linkage metadata SHALL move with the change into the archive directory

### Requirement: Apply Updates Linked Redmine Issue

OPSX apply workflows SHALL update the linked Redmine issue when implementation begins.

#### Scenario: Apply linked change

- **WHEN** the user invokes `/opsx:apply <change>`
- **AND** the selected change metadata links to Redmine issue `12`
- **THEN** the workflow SHALL update Redmine issue `12` to the configured implementation status
- **AND** the default implementation status SHALL be the Redmine status mapped from Hermes state `applying`
- **AND** the workflow SHALL report whether the Redmine update succeeded

#### Scenario: Apply unlinked change

- **WHEN** the user invokes `/opsx:apply <change>`
- **AND** the selected change has no Redmine linkage
- **THEN** the workflow SHALL continue with the normal OPSX apply behavior without requiring Redmine

### Requirement: Archive Advances Linked Redmine Issue

OPSX archive workflows SHALL advance the linked Redmine issue after successful local archive.

#### Scenario: Archive posts QA handoff note

- **WHEN** the user invokes `/opsx:archive <change>`
- **AND** the local archive operation succeeds
- **AND** the selected change metadata links to Redmine issue `12`
- **THEN** the workflow SHALL add a Redmine note to issue `12`
- **AND** the note SHALL summarize the overall implementation change
- **AND** the note SHALL include relevant OpenSpec planning documents or document paths
- **AND** the note SHALL include changed-file summary when available
- **AND** the note SHALL include QA-focused checks or suggested tests for follow-up validation

#### Scenario: Archive linked change

- **WHEN** the user invokes `/opsx:archive <change>`
- **AND** the local archive operation succeeds
- **AND** the selected change metadata links to Redmine issue `12`
- **THEN** the workflow SHALL update Redmine issue `12` to the configured post-archive next-step status
- **AND** the default post-archive next-step status SHALL be the Redmine status mapped from Hermes state `code-review`
- **AND** the workflow SHALL report whether the Redmine update succeeded

#### Scenario: Archive fails before Redmine update

- **WHEN** the user invokes `/opsx:archive <change>`
- **AND** the local archive operation fails
- **THEN** the workflow SHALL NOT advance the linked Redmine issue status

#### Scenario: Archive unlinked change

- **WHEN** the user invokes `/opsx:archive <change>`
- **AND** the selected change has no Redmine linkage
- **THEN** the workflow SHALL continue with the normal OPSX archive behavior without requiring Redmine
