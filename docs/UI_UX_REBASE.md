# UI overhaul on the updated master baseline

Completed locally on 2026-09-26. No push, production change, or merge of the UI branch into bara.

## Branch preservation

- Original base: `acbf4ba`.
- Original complete UI checkpoint: `83c8a95`, retained by `backup/ui-before-master-20260926` (80 files, including previously untracked source, tests and documentation).
- Base backups: `backup/bara-before-master-20260926` and `backup/master-before-20260926`.
- Fetched master and local bara: `8e3d05d`. Bara retains its upstream/bara tracking configuration.
- Rebased UI checkpoint: `8d3865f`, with conflict adaptations; subsequent integration fixes are committed on codex/UI.
- Local master remains `acbf4ba`; remote master was only read/fetched.

Of the 80 checkpoint files, 22 overlapped upstream changes. Immediately after rebase, 56 non-overlapping files were byte-identical to the checkpoint; the other two were intentionally adapted (request-list Approved indicator and tab-aware pagination). Later changes add integration verification, documentation, translation loading and related help text.

## Upstream changes accounted for

| Commits | Change and integration |
| --- | --- |
| `e79e213` | Desk envelope search retained; added independent loading/error states, stale-response protection, keyboard search, accessible result region and mobile scrolling |
| `904b6bc`, `6cde1d0` | Upstream field types/order and QR presentation retained alongside the UI tabs and descriptions |
| `00b3aee` | Reviewer access no longer exposes other owners' drafts; retained without weakening permissions |
| `dc12525` | Active Employee department precedes User Permission fallback; updated administrative help in EN/AR |
| `7fd7a0a`, `ad9cd84`, `8e3d05d` | Retained task-oriented workspace, five number cards and three canonical portal shortcuts |
| `834e224`, `5c82f30` | Category-scoped dynamic fields, editable direct correspondence category and locked request-derived category retained; obsolete category selector removed |
| `4f1a512` | Separate Approve/Register actions reflected in portal decisions, bulk sequences, Desk guidance, list indicators and requester timelines |
| `53494b9` | Migrated the redesigned pages into requests/queue tabs; old routes redirect while preserving supported query parameters |

The source workflow's modification timestamp had not advanced with its transition changes. Frappe skipped it during the first site migration, leaving the old combined action installed. Updating that timestamp made the normal importer install Approve/Register; the existing upstream cache invalidation was retained.

Portal JavaScript had no app message dictionary in website boot data, leaving some labels English on Arabic pages. All canonical portal controllers now supply a Diwan-scoped dictionary to the shared shell using safe JSON serialization, preserving site translation overrides.

## Verification

- Eight focused Python regressions pass: pagination bounds and tab/filter/language retention; legacy redirects; Employee precedence/fallback; draft privacy; denied envelope search; scoped translation overrides.
- Seven merged tab views rendered in EN/AR at 360/768/1440 (42 combinations), with no horizontal document overflow or page JavaScript errors and with tab-preserving language links.
- Real browser workflow: save draft → legacy edit redirect → same-request submit → Start Review → Approve without a type → required-type feedback → Register → persisted resulting correspondence `CR-2026-0004`. Requester detail shows five stages.
- Existing browser suites pass: upload failure/retry and same-draft submission; full draft reload/edit/save; required revision note and resubmission; seven dynamic field controls and keyboard Link selection; Desk category response ordering/value retention.
- Bulk test passes validation, partial success, recovery links and processed-row lockout; all workflow writes were intercepted. Successful mock sequence is Start Review → Approve → Register.
- Actual Envelope `ENV-2026-0025` was found and opened through Desk search. Accessible table headers/scroll region, detail and 360px overflow checks passed. The temporary envelope and its attached files were removed afterward.
- An isolated category verified real Custom Fields on both document types, category conditions, required-field enforcement, source-request category locking, and cached Data→Link updates. Category and Custom Field records were removed; Frappe retains unused SQL columns by design.
- Final source/site comparison found zero field-property mismatches across 21 changed DocTypes. All three canonical portal routes loaded Arabic JavaScript messages, and a real audit next-page navigation preserved the tab and language.
- Installed workspace has five number cards and exactly three portal shortcuts. Correspondence and access-profile metadata were resynchronized after final help-text edits.
- Arabic mobile audit screenshot was inspected after fixing JavaScript translations; the row-filter label and row counts are translated. Desk envelope mobile screenshot was inspected.
- Final Python/JSON/Jinja/JavaScript parsing and Git whitespace checks pass. Backup refs and branch ancestry verified before completion.

Browser test requests use clearly marked `UI audit` subjects and are retained as test evidence, as documented by the suites. No existing business record was used for workflow transitions. Tests generated normal access logs.

## Environment and limits

Development site: `bara.diwan`. Database backup was taken before migration at `sites/bara.diwan/private/backups/20260926_212331-bara_diwan-database.sql.gz` (outside this repository).

The site initially had no web server or configured Redis services running. Only the web server and those Redis instances were started; no worker or scheduler was started. Chrome's missing shared libraries were unpacked under `/tmp/diwan-browser-libs`, without a privileged/system installation. Temporary browser authentication was removed and the services started for this check were stopped afterward.

Configured wkhtmltopdf output and physical camera/printer checks retain their previously documented environment limits. Earlier print evidence remains historical; printing code was preserved and was not changed by this integration. Department/draft privacy regression tests use controlled mocks; the earlier live role matrix is documented in UI_UX_AUDIT.md.
