# Diwan UI/UX overhaul

Status: implemented, rebased onto upstream master `8e3d05d`, and locally reviewed; configured PDF renderer and physical hardware checks are documented environment limits. See the [completion checklist](docs/UI_UX_COMPLETION.md), [surface coverage](docs/UI_UX_SURFACE_COVERAGE.md), and [chronological evidence](docs/UI_UX_AUDIT.md).
Created: 2026-09-25.

## Goal

Make every Diwan surface coherent, readable, accessible, and efficient for daily correspondence work, in Arabic/RTL and English/LTR. Cover Desk, portal, all DocTypes and embedded tables, reports, workspace, and printed outputs.

Use the existing navy/orange identity as the starting point. Refine it through actual screen review. Preserve native Frappe behavior, configurable masters, permission enforcement, audit logging, reference-number bidi handling, and existing workflow rules.

## Complete source inventory

| Surface | Coverage |
| --- | --- |
| Operational DocTypes | Correspondence, Correspondence Request, Internal Mail Movement, Delivery Sheet, Envelope |
| Configuration and oversight DocTypes | Correspondence Category (including tree), Correspondence Type, Confidentiality Level, Document Access Profile, Correspondence Settings, Access Log Entry |
| Embedded child DocTypes | Correspondence Authorized Viewer, Correspondence Transfer Log, Follow-up Action, Correspondence Category Field, Correspondence Numbering Rule, Confidentiality Level Bypass Role, Delivery Sheet Item, Envelope Document, Document Access Profile Department Field, Document Access Profile Role, Document Access Profile Searchable Field |
| Desk pages | correspondence-request-new, correspondence-track |
| Portal views | /track; /diwan/requests (list/detail and submit/edit tabs); /diwan/queue (queue, tray, delivery_sheets, envelopes, audit_log tabs). Five former routes remain compatibility redirects. |
| Reports | Overdue Correspondence, Correspondence Completion Time, Access Log Report |
| Workspace and metrics | Masar Diwan workspace, five correspondence number cards, two dashboard charts |
| Print formats | Delivery Sheet Print, Envelope Label, Document Label |

Totals: 22 DocTypes (11 top-level, including one singleton; 11 child tables), two custom Desk pages, eight portal views across three canonical routes, three reports, three print formats.

Audit dialogs, detail panels, dynamic category fields, attachment controls, scanning, and workflow actions within their owning surfaces. Check navigation links for additional runtime surfaces during the browser audit.

## Phases and deliverables

### 1. Baseline and user journeys

- Capture current desktop and mobile views; record concrete usability issues per surface rather than assuming source-level concerns are visible defects.
- Map requester, employee, department head, Diwan officer, senior management, and tracking-user journeys against actual role permissions.
- Trace drafting → submission → review → revision/approval → registration → referral → completion/archive; separately trace internal movement and physical delivery.
- Record findings in a coverage matrix with surface, issue, priority, planned change, and verification evidence.
- Establish representative test records and available local browser access without changing production data.

Exit: every inventory item mapped to a review task; highest-impact friction identified.

### 2. Shared design foundations

- Consolidate semantic colors, typography, spacing, surfaces, borders, focus states, and status treatment across existing Desk and portal assets.
- Define consistent page headers, primary/secondary actions, filters, list rows, badges, form sections, dialogs, feedback, and loading/empty/error states.
- Use scoped styles and shared helpers; avoid styling unrelated ERPNext screens.
- Design Arabic-first layouts with logical CSS properties, explicit mixed-direction reference handling, and translated text.
- Establish responsive navigation, keyboard access, visible focus, readable contrast, and useful touch targets.

Exit: shared patterns demonstrated on Correspondence and one portal workflow before wider rollout.

### 3. Core correspondence and request experience

- Improve Correspondence and Correspondence Request forms and lists: clear identity/status, meaningful grouping, relevant columns/filters, ownership, deadlines, attachments, and next actions.
- Improve both custom Desk pages and portal submission, requests, tray, queue, and tracking.
- Make revision reasons, validation, save/submission progress, and completion feedback clear; preserve entered data on recoverable errors.
- Improve category-driven fields and embedded authorized viewers, follow-ups, and transfer history.
- Keep role-dependent actions understandable and aligned with server permissions.

Exit: complete requester-to-officer-to-tracking flow verified with permitted and restricted roles.

### 4. Movement, delivery, and printing

- Improve Internal Mail Movement, Delivery Sheet, Envelope, their lists, portal pages, and embedded document/item tables.
- Clarify selection, handoff, receipt, workflow state, and print actions using the existing business rules.
- Verify delivery sheet and label hierarchy, page breaks, Arabic text, reference numbers, and QR readability in print previews.

Exit: supported movement and delivery journeys verified through their final actions and print output.

### 5. Administration, oversight, and reporting

- Improve every configuration/oversight DocType and its child tables: labels, descriptions, grouping, grid columns, and discoverability.
- Review category tree navigation and dynamic-field configuration.
- Make access-profile and confidentiality configuration understandable without changing enforcement semantics.
- Improve audit-log browsing, report filters/results, workspace navigation, metrics, and chart readability.

Exit: all remaining inventory items implemented or explicitly documented as reviewed with no change needed and a reason.

### 6. Full verification and polish

- Review Arabic/RTL and English/LTR at representative mobile, tablet, and desktop widths (360, 768, and 1440 pixels).
- Verify keyboard navigation, focus after dialogs, labels, non-color status cues, loading/empty/error states, long subjects, large tables, and mixed-script references.
- Verify existing workflow transitions, role visibility, confidentiality masking, attachment access, audit logging, scanning, and print behavior remain correct.
- Run appropriate lint/static checks and existing relevant regression tests; add targeted tests only for meaningful changed behavior.
- Capture before/after evidence and close the coverage matrix. Report any environment-dependent checks that could not be performed.

Exit: every surface accounted for, key journeys pass, and no unresolved critical usability or functional regressions.

## Implementation approach

Deliver small, reviewable batches in phase order. Complete the shared foundation and representative screens before propagating patterns. Use existing Frappe components and APIs where practical. Keep shared assets in public/css and public/js, shell changes in templates/pages/diwan_shell.html, and surface-specific behavior with its owning page or DocType.

Do not equate a CSS refresh with completion: form organization, navigation, action clarity, feedback, and end-to-end task completion are part of the goal. Do not claim browser or role verification from static inspection alone.

## Progress

- [x] Create goal and inventory all 22 DocTypes, two Desk pages, eight portal pages, three reports, workspace, and three print formats.
- [x] Implement shared design foundations, Arabic/RTL and English/LTR layouts, responsive navigation, status treatment, form guides, and action feedback.
- [x] Implement the request/correspondence, movement/delivery, configuration, workspace, report, and print source batches.
- [x] Synchronize local presentation metadata and verify the principal requester, officer, tracking, delivery, audit, report, dynamic-category, and print-preview journeys. Detailed evidence is in `docs/UI_UX_AUDIT.md`.
- [x] Complete the targeted checks and final source/site review in `docs/UI_UX_COMPLETION.md`; record renderer/hardware limits separately.

The user authorized local implementation and asked to defer testing until the source batches were complete. That sequencing was followed. The local site presentation audit has zero source/DB mismatches. No code has been pushed, and pushing is not authorized.

## Upstream integration — 2026-09-26

`bara` now contains upstream master `8e3d05d`; `codex/UI` contains the preserved overhaul and the adaptations described in [the rebase audit](docs/UI_UX_REBASE.md). Local master remains at `acbf4ba`. No push or merge into bara has been performed.

New coverage includes merged portal tabs, separate Approve/Register stages, category-scoped correspondence fields, Employee-first department lookup, draft privacy, envelope search, and the reorganized workspace. Historical approval evidence below the original phases predates the split; current verification is recorded in the rebase audit.
