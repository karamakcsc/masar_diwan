# Diwan UI/UX surface coverage

Current source and verification ledger for the [UI/UX goal](../UI_UX_PLAN.md). “Rendered” means an actual browser route/control check; “flow” means a workflow or data check. The [chronological audit](UI_UX_AUDIT.md) records detailed fixtures and evidence. Source coverage alone does not imply that every state was exercised.

## Top-level DocTypes

| Surface | UI work | Verified behavior |
| --- | --- | --- |
| Correspondence | Grouped form, list indicators/filters, tracking action, guidance, print defaults | Form and populated list rendered; tracking, confidentiality, approval/registration, completion, QR and attachment access checked |
| Correspondence Request | Grouped form, list indicators, guided action, dynamic fields | Form and populated list rendered; draft, submission, revision, rejection and approval flows checked |
| Internal Mail Movement | Form guidance, status/list indicator | Form and populated native list rendered; Send/Confirm Receipt flow checked on an isolated record |
| Delivery Sheet | Form/list hierarchy, child items, portal and print links | Form, child row editor, populated native and portal rows, proof requirement and print preview checked; Arabic reference order and quick-filter labels rechecked |
| Envelope | Form/list hierarchy, document table, portal/tracking/label links | Form, populated native and portal rows, tracking and multi-label print preview checked; linked-sheet quick-filter label rechecked |
| Correspondence Category | Clear configuration form, tree guide, list filter, category field controls | Form/tree/list rendered; empty state, generated fields, category save/reload, revision/approval and 51-row child grid checked |
| Correspondence Type | Configuration form and list hierarchy | Form and four populated native rows rendered; type selection used in approval |
| Confidentiality Level | Configuration form and role explanation | Form and three populated native rows rendered; all configured tiers exercised in department access matrix |
| Document Access Profile | Guided access/numbering layout and truthful future-search wording | Form and two populated native rows rendered; department and confidentiality access behavior checked |
| Correspondence Settings | Organized singleton settings form | Form rendered with guidance; existing settings behavior preserved |
| Access Log Entry | Contextual history form and scoped list presentation | Officer read-only detail and live Access Log Report rows checked |

## Child DocTypes

All 11 child controls initialized in their owning Desk forms. Native Link/Data controls are retained for the simple one-column tables.

| Surface | UI treatment and evidence |
| --- | --- |
| Correspondence Authorized Viewer | User Link help explains access at the configured tier; control rendered |
| Correspondence Transfer Log | History columns/labels and control rendered; completion report uses real transfer history |
| Follow-up Action | Row labels/widths and control rendered |
| Correspondence Category Field | Field setup help, row editor, four real generated types and 51-row pagination checked |
| Correspondence Numbering Rule | Configuration labels/guidance and control rendered |
| Confidentiality Level Bypass Role | Role Link help explains cross-department access; control rendered |
| Delivery Sheet Item | Grid fields and row editor rendered; populated delivery/receipt flow checked |
| Envelope Document | Grid fields rendered; populated envelope and label references checked |
| Document Access Profile Department Field | Already has a required Link-field name and detailed department-matching help; native control rendered, source unchanged |
| Document Access Profile Role | Role Link help distinguishes department exemption from confidentiality bypass; control rendered |
| Document Access Profile Searchable Field | Help states that this is reserved for future cross-document search; control rendered |

## Pages, reports and output

| Surface | Verified behavior |
| --- | --- |
| Desk: New Correspondence Request | Failed upload/retry and same-record Submit for Review passed; category race/value-retention checks passed |
| Desk: Correspondence Tracking | Real missing-reference lookup plus controlled restricted/envelope/mobile interactions passed |
| Portal: `/track` | Real allowed/restricted department users, envelope detail, mobile layout and camera-denial/manual-entry feedback passed |
| Portal: `/diwan/submit` | Required category fields, draft/revision editing, save/reload and upload recovery passed |
| Portal: `/diwan/requests` | Request detail and rejection/revision outcome rendered; 51-record pagination passed server check |
| Portal: `/diwan/tray` | Role/controller boundary and bulk approval/recovery passed |
| Portal: `/diwan/queue` | Individual start review, reject with a fresh note, revision and approval passed |
| Portal: `/diwan/delivery_sheets` | Populated rows and Desk/print links checked at mobile/desktop widths |
| Portal: `/diwan/envelopes` | Populated rows, Desk/print links and linked tracking checked at mobile/desktop widths |
| Portal: `/diwan/audit_log` | Live event rows, combined filters and Clear action passed |
| Overdue Correspondence report | Filters and populated row/summary checked in Desk; department/confidentiality matrix checked server-side |
| Correspondence Completion Time report | Filters and populated row/summary checked in Desk |
| Access Log Report | 32 live rows, summary and reference filter presentation checked |
| Workspace, five cards and two charts | EN/AR mobile/desktop screenshots inspected; labels and navigation fit |
| Delivery Sheet Print | EN/AR Chromium A4 preview and repeated headers/signatures checked |
| Document Label | EN/AR Chromium 90×50mm preview, real HTML and private QR inlining checked |
| Envelope Label | Eight references across three QR-bearing Chromium 90×50mm labels checked |

## Open verification boundaries

- The native Category Field row editor moves keyboard focus from Label to the visible Field Type control with Tab. Other child tables use Frappe's native grid controls; exhaustive key-by-key sampling of every table is outside this focused review.
- The configured wkhtmltopdf binary and physical camera/printer are unavailable locally. Chromium previews, PDF-option parsing, renderer-source precedence, and camera-denial behavior do not prove hardware output.
- The final source/site presentation audit compares all 25 modified metadata documents with zero mismatches. Never push code for this goal.
