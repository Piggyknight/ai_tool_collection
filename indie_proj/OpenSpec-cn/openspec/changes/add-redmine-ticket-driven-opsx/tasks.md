## 1. Redmine Link Helpers

- [ ] 1.1 Add a small parser for Redmine issue references (`#12`, `redmine:#12`, `redmine:12`)
- [ ] 1.2 Add helper coverage for reading/writing Redmine linkage in `.openspec.yaml`
- [ ] 1.3 Add tests for issue reference parsing and metadata round-tripping

## 2. Propose Workflow

- [x] 2.1 Update OPSX propose skill and command templates to document Redmine issue arguments
- [x] 2.2 Add propose instructions for fetching issue title/details and deriving the change name from the Redmine subject
- [x] 2.3 Add propose instructions for persisting Redmine linkage in change metadata
- [x] 2.4 Add template parity tests asserting generated propose artifacts include the Redmine flow

## 3. Apply Workflow

- [x] 3.1 Update OPSX apply skill and command templates to read linked Redmine metadata
- [x] 3.2 Add apply instructions for moving the linked Redmine issue to the implementation status
- [x] 3.3 Add tests asserting generated apply artifacts include the Redmine status update behavior

## 4. Archive Workflow

- [x] 4.1 Update OPSX archive skill and command templates to read linked Redmine metadata
- [x] 4.2 Add archive instructions for moving the linked Redmine issue to the next workflow status after successful archive
- [x] 4.3 Add tests asserting generated archive artifacts include the post-archive Redmine status update behavior

## 5. Verification

- [x] 5.1 Run focused template/helper tests
- [x] 5.2 Run `openspec-cn validate add-redmine-ticket-driven-opsx --strict`
