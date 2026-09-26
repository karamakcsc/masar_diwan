# UI/UX completion checklist

This is the current checklist. [Surface coverage](UI_UX_SURFACE_COVERAGE.md) accounts for every inventory item; `UI_UX_AUDIT.md` preserves chronological evidence, including older coverage snapshots. Source implementation spans the full inventory; the goal is not complete until the open checks below are resolved or a concrete environment limitation is documented.

## Evidence already established

- Shared Desk/portal identity, scoped styles, navigation, form hierarchy and translated feedback are implemented.
- Eight portal routes rendered in EN/AR at 360/768/1440 without horizontal document overflow or JavaScript errors. Ten editable/configuration Desk forms rendered their guides. Ten native list routes and the category tree initialized without page errors. All 11 child controls initialized; representative category and delivery row editors opened on unsaved forms.
- Upload failure/retry, same-document save/submission, full draft editing, revision note/edit/resubmission, and mobile drawer keyboard behavior passed browser checks. The custom Desk request page also passed its own failed-upload/retry/submission flow on one saved draft.
- Requester-only controller checks reject staff pages and another owner's draft editor.
- Bulk approval succeeded for two guarded audit requests with database-confirmed links. Controlled partial-failure recovery, type validation and processed-row lockout passed separately. A real officer rejection required a fresh note after an earlier revision note and appeared on requester detail.
- Approval/registration, correspondence completion, internal movement, envelope linkage, delivery proof requirement and receipt linkage passed server integration checks.
- Populated overdue/completion date filters and 51-record pagination passed server checks.
- Seven dynamic control types and keyboard Link selection passed browser component checks. Delayed category responses and value retention passed on the real custom Desk page with controlled metadata responses.
- Tracking missing-reference lookup passed against the real API. Restricted/envelope display cases passed with controlled responses.
- A real audit category group/leaf generated Custom Fields on both document types. The portal enforced required subgroup/field selection and restored saved values. The fixture and generated fields were removed.
- A restricted employee was denied audit-correspondence tracking detail, list/report visibility, and private attachment download; the authorized owner could see the document. The temporary user and document edits were removed.
- All three Desk reports loaded their filters; Access Log Report displayed 32 live rows and its summary. Populated Overdue and Completion reports retained owner/type selections and displayed expected audit rows/summaries; their temporary date/log fixtures were restored or removed. The real audit portal's three-filter combination and Clear action passed. Populated delivery and envelope portal rows, Desk/print links, and envelope tracking passed at mobile/desktop widths; their fixtures were removed.
- Individual portal approval produced CR-2026-0003 from a named UI-audit request, with a verified request/correspondence link. Populated native request and correspondence lists rendered their rows, actions, and status indicators. Camera-start denial left manual tracking visible and usable.
- Department access matrix passed on actual tracking/list/overdue data: a matching-department employee could see Normal and Confidential correspondence; a different-department employee could not; neither could see Highly Confidential without an owner/bypass grant. Actual mobile tracking pages showed full detail for the matching employee and a masked result for the other. The correspondence and both temporary users were restored/removed.
- A real category field kept its initial value through Request Revision, accepted a new value on Resubmit, and copied only the revised value into registered Correspondence on Approve & Register. Exact audit workflow/category/type/numbering fixtures were removed.
- Populated Correspondence Type, Confidentiality Level, and Document Access Profile native lists showed their actual rows and actions. The currently empty category list showed a create action; its parent quick-filter label now fits. An unsaved category form displayed 50 of 51 child rows on page one and row 51 on page two, with no document saved.
- Populated Envelope, Delivery Sheet, and Internal Mail Movement native lists showed isolated rows and lifecycle indicators. A second pass confirmed the widened quick-filter labels and stored-order Arabic Delivery Sheet reference. All exact fixture records were removed and the correspondence links restored.
- In an unsaved Category Field row editor, Tab advanced from the Label input to the visible Field Type select; no page JavaScript error occurred.
- English and actual Arabic Desk workspace screenshots were inspected; all five status cards and translated labels fit at mobile/desktop widths.
- Six EN/AR print examples rendered; Chromium label PDFs measured 90×50mm, delivery PDFs repeated table headers. Frappe's parser extracts label dimensions/margins. An eight-document envelope now prints all references across three repeated, QR-bearing 90×50mm labels in Chromium.
- All 25 modified presentation documents match the local site after fixing a help-text placeholder and clarifying future-search configuration. Arabic translation CSV has no duplicate keys. The sole unchanged child DocType already has a required field and detailed help text.

## Verification boundaries

1. **Native grids.** All ten native routes, populated core/configuration/operational lists, all 11 child controls, two row editors, the category tree/empty state, and officer read-only Access Log Entry detail passed targeted checks. The full “Approved & Numbered” badge, 51-row Category Field pager, and Label-to-Field-Type keyboard transition were captured. Every key action in every child table was not sampled; those controls use native Frappe grid behavior.
2. **Print/scanning hardware.** Eight-document envelopes printed all references across three Chromium label pages; actual Correspondence label HTML and private QR inlining passed. Controlled camera failure left manual entry available. Frappe passes 90×50mm dimensions alongside the site A4 value; wkhtmltopdf's own converter source gives explicit width/height precedence. The configured wkhtmltopdf binary and physical camera/printer are unavailable locally, so actual configured-renderer pagination and hardware output remain unverified.
3. **Final integration review.** The final source/site audit found zero mismatches across 25 modified presentation documents. All app Python, Jinja, JSON and JavaScript files parsed; `git diff --check` passed. The changed source inventory is confined to Diwan presentation, navigation, reporting/filtering, and related helper files. No code was pushed.

## Test-data handling

Use dedicated audit accounts/records. The existing access logger commits transactions, so rollback does not reliably remove workflow fixtures. Confirm authoritative state after each fixture run and clean only exact, known test records. Do not reset existing credentials. Some clearly named browser audit requests and audit events are deliberately retained as evidence.
