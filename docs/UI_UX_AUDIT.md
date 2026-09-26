# Diwan UI/UX coverage and evidence

Updated: 2026-09-25. This is an implementation ledger, not a claim that the full overhaul is complete.

## Environment

- Working branch: `codex/UI`. No code pushed.
- Actual local site: `bara.diwan`, development web server on port 8001. Earlier accounts/sites mentioned in CLAUDE.md are not present here.
- Dedicated `ui.audit@diwan.local` account created for browser verification; no existing credentials changed. Test requests have subjects beginning `UI audit - attachment recovery` and small private `ui-audit.txt` attachments.
- Browser: Chrome driven by agent-browser; Playwright connected to that browser for assertions. System browser dependencies were unavailable, so local extracted libraries under `/tmp/diwan-browser-libs` were used without modifying system packages.
- Modified DocType presentation metadata synchronized locally; pre-sync metadata backed up at `/tmp/diwan-ui-doctype-backup.json`.

## Findings addressed in the first implementation batch

| Finding | Change | Evidence |
| --- | --- | --- |
| Disabled search looked interactive | Replaced with a working tracking link | Rendered desktop/mobile portal views |
| Repeated rail/navigation links and unbounded hidden drawer | Single visible navigation; hidden/inert dialog when closed | Browser snapshots and keyboard checks |
| Drawer lacked Escape, focus trapping, and focus return | Modal keyboard behavior, background inertness, scroll lock, responsive close | 360px Arabic interaction test |
| Radio choices used display:none | Visually hidden native radios with visible keyboard focus | Browser accessibility tree and axe checks |
| Form labels lacked associations | Explicit input/select/textarea labels; radio-group names; selection labels | axe A/AA checks on checked portal screens |
| Tables could widen the page | Local scroll regions, readable headers, real record links | All eight routes at three widths and two languages |
| Queues had no local filter | Explicitly labeled loaded-row filtering, counts, recoverable no-match state | Browser interaction test; batch-selection table deliberately excluded |
| Language links dropped record parameters | Preserve query parameters and fragment | Open-record EN→AR browser test |
| Upload HTTP failures were counted as success | Check responses, retain failed files, prevent submission until upload succeeds | Forced HTTP 500, successful retry, real submission |
| Save buttons allowed overlapping saves | Shared busy state covering save, uploads, and workflow action | Browser interaction test and code review |
| Many existing portal phrases lacked Arabic translations | Added headings, actions, guidance, and empty/error messages | Arabic screenshots inspected |
| Forms had unclear/unlabeled sections | Shared task guidance plus named correspondence/request/delivery sections | Ten Desk forms rendered; representative screenshot inspected |
| Identity palette duplicated between surfaces | Shared token asset; route-scoped Desk styling | Runtime rendering, JS lint, diff review |

## Batch-1 surface coverage (historical snapshot)

For current evidence and remaining work, see [UI_UX_COMPLETION.md](UI_UX_COMPLETION.md). Later sections below supersede this snapshot.

“Foundation applied” means shared styling/behavior exists. It does not mean the surface's entire workflow or all states have been verified.

| Surface | Current state | Remaining verification/work |
| --- | --- | --- |
| Correspondence | Foundation, guidance, labeled sections; new form rendered | Saved record, lifecycle actions, attachments, confidentiality, follow-up grid, mobile/Arabic Desk |
| Correspondence Request | Foundation, guidance, labeled sections; new form rendered | Revision/rejection/approval, dynamic-field scenarios, role-specific Desk behavior |
| Internal Mail Movement | Foundation and guidance; new form rendered | Send/receive handoff, lists, role actions |
| Delivery Sheet | Foundation, guidance, destination/items/confirmation grouping; form rendered | Item editing, proof of receipt, dispatch/delivery workflow |
| Envelope | Foundation, guidance, enclosed-document grouping; form rendered | Document grid, QR tab, linked delivery workflow |
| Correspondence Category | Foundation, guidance, clarified dynamic-field help; form rendered | Tree, leaf/group behavior, dynamic field grid |
| Correspondence Type | Foundation, guidance, prefix help; form rendered | List/filter usability and bilingual form review |
| Confidentiality Level | Foundation and guidance; form rendered | Role table, configuration clarity; original precise field descriptions retained |
| Document Access Profile | Foundation and guidance; form rendered | All configuration sections and embedded tables |
| Correspondence Settings | Foundation and guidance; form rendered | Numbering grid, scanner-policy choices |
| Access Log Entry | Foundation, guidance, labeled context section | Read-only form and list review |
| Correspondence Authorized Viewer | Inherits shared grid treatment | Selection UX and permission regression checks |
| Correspondence Transfer Log | Inherits shared grid treatment | Long histories, read-only presentation, Arabic values |
| Follow-up Action | Inherits shared grid treatment | Row editor, dates, action visibility |
| Correspondence Category Field | Inherits shared grid treatment | All supported dynamic field types and row editor |
| Correspondence Numbering Rule | Inherits shared grid treatment | Grid columns and counter guidance |
| Confidentiality Level Bypass Role | Inherits shared grid treatment | Role selection and explanatory context |
| Delivery Sheet Item | Grid treatment and field guidance | Correspondence picker and large batches |
| Envelope Document | Inherits shared grid treatment | Party fetch, selection, and grid layout |
| Document Access Profile Department Field | Inherits shared grid treatment | Field entry/editor help |
| Document Access Profile Role | Inherits shared grid treatment | Role selection/editor help |
| Document Access Profile Searchable Field | Inherits shared grid treatment | Field entry/editor help |
| Desk correspondence-request-new | Route-scoped foundation | Dedicated screen audit and behavior improvements |
| Desk correspondence-track | Route-scoped foundation | Dedicated screen audit, scan and restricted states |
| /diwan/submit | Shared shell, two-column responsive form, labels, footer actions, robust saves/uploads | Dynamic field matrix, limited-role checks, interrupted/network-ambiguous responses |
| /diwan/requests | Shared shell/tables/links/detail layout; submitted detail and language switch tested | Edit/resubmit, history and all decision states |
| /diwan/queue | Shared shell/tables/filtering/links/detail layout | Full officer decision flow and permission variants |
| /diwan/tray | Shared shell/table and selection names | Batch result feedback and partial failure behavior |
| /diwan/delivery_sheets | Shared shell/table; empty view rendered at all target widths/languages | Populated list, creation navigation, print actions |
| /diwan/envelopes | Shared shell/table; empty view rendered at all target widths/languages | Populated list, tracking and print actions |
| /diwan/audit_log | Shared shell/table/filtering; filter labels fixed | Filter combinations, restricted role review |
| /track | Shared shell, named reference input, responsive result tables | Authorized/restricted/not-found results, QR/camera, attachment download |
| Three reports | Route-scoped foundation only | Filters, result readability, summaries, permission-aware results |
| Workspace / five number cards / two charts | Foundation only | Task-based organization, missing in-progress card placement, chart review |
| Three print formats | Not changed yet | Document/Envelope labels and delivery-sheet print layout, QR, Arabic, pagination |

## Verification completed

- 48 rendered portal views: eight routes × EN/AR × 360/768/1440 pixels. HTTP 200, page heading present, no document-level horizontal overflow, no page JavaScript errors. Several delivery/empty states are still only empty-state coverage.
- Ten editable/configuration Desk forms rendered with one visible shared guide per active form and no JavaScript errors in the form-navigation run. This is not workflow verification.
- Representative screenshots visually inspected: English request desktop, Arabic request mobile, English queue desktop, Correspondence Desk form.
- Automated WCAG 2 A/AA and 2.1 AA rules run with axe on submission, queue, tray, requests, audit, and tracking. Audit dropdown names were fixed and affected screens rechecked. Automated checks do not establish full accessibility conformance.
- Request upload failure/retry/submission, subject validation focus, record-preserving language switch, mobile drawer focus/Escape, and queue filtering have a reusable browser test at `tests/ui/portal.cjs`.
- Shared JS passed ESLint 8 with the repository configuration. Node syntax checks and `git diff --check` passed.
- One startup null-route error introduced during development was caught and fixed before verification. A transient Frappe sidebar initialization error was also observed initially; later original-JS and current-JS checks did not reproduce it.

Screenshots retained outside the repository under:
`/home/bara/.codex/visualizations/2026/09/25/01a0d627-e1aa-7311-b2b4-b51ddecf0cc5/ui-ux/`.

## Next implementation batch

1. Review the two custom Desk pages and saved Correspondence/request detail states, then complete submission/review/revision/registration/tracking using limited-role test users.
2. Improve movement/delivery forms and embedded grids; verify populated portal pages and print outputs.
3. Complete configuration, reports, and workspace organization; finish the role, accessibility, and bilingual verification matrix.

## Implementation batch 2 — testing deferred at the user's request

The user explicitly requested that no more tokens be spent testing until implementation is done. No new tests or browser verification have been run for the changes listed here. The earlier verification section applies only to batch 1.

Implemented in source:

- **Custom Desk request page:** EN/AR labels and direction; labeled inputs, pressed-state choice buttons, keyboard attachment selection, required-field feedback, upload-response handling with retry retention, and guarded saves. The previously hardcoded Arabic screen now follows the session language.
- **Custom Desk tracking:** explanatory header, keyboard search, loading/empty/failure states, stale-response protection, and contained results table.
- **Correspondence:** details/routing/history tabs, section guidance, default document-label print format, tracking action, native list lifecycle indicators and common filters.
- **Requests:** lifecycle list indicators and guided-entry shortcut; draft submission from the requests detail page; guarded revision submission; officer action pending states and persistence of approval notes.
- **Delivery and movement:** lifecycle lists/filters, recipient/item/receipt guidance, meaningful grid widths, delivery and envelope portal links to Desk with creation actions gated by user type and create permission, tracking link for envelope references.
- **Configuration and child tables:** access-profile tabs, settings sections, parent guidance, four-column follow-up/history/dynamic-field/numbering grids, and document/item grids. Single-column viewer/role/field-name tables retain native controls and inherit the shared styling; their existing precise access descriptions remain intact.
- **Shared dynamic fields:** associated labels, unique IDs, explicit empty Select choices, native required checks, retained values during rerender, keyboard Link-picker navigation and selection, result status feedback, and stale-result protection.
- **Bulk approval:** selected-count feedback, progress, disabled controls during processing, per-row outcomes, and individual-review links for partial failures. Processed items cannot be resubmitted from the same batch view.
- **Tracking portal:** visible manual Track action, trimmed input, camera start/stop and failure states, and correct manual versus QR audit channel arguments.
- **Reports:** two correspondence reports now accept department/owner/type/date filters with parameterized SQL while retaining permission clauses. Existing audit-report filters remain; shared styling covers all three reports.
- **Workspace:** shortcuts grouped by daily work, delivery/movement, reports/oversight, configuration, and portals; all five number cards included (the in-progress card was previously absent); both charts retained in reporting context.
- **Print formats:** consistent typography, reference isolation, QR placement, table-based PDF layout, repeated delivery table headers, signature/time sections, and complete envelope content lists. The print changes still require real PDF/label review.
- **Arabic:** added translations for the new controls, messages, sections, report filters, workspace headings, and print labels.

Metadata and workspace/print-format changes from this batch are still source changes; batch 1 alone was synchronized into the running site. Final synchronization must preserve site customization and avoid the documented destructive Workspace reload behavior.

Remaining implementation review: saved-request editing coverage (including categories and dynamic values), portal list pagination beyond current server limits, category tree ergonomics, and final integration of the shared components. Then perform one consolidated verification pass covering the entire inventory, user roles, workflow transitions, Arabic/mobile layouts, reports, scanning, and printing. No push is authorized.


## Implementation batch 3 — integration, unverified

- Six portal lists now use permission-aware pagination with stable ordering and retained language/audit filters. Bulk selection explicitly refers to the current page.
- Draft and revision actions reopen the complete request form, including categories, dynamic values, attachments, decision notes, and original request context, with read/write and ownership checks. Untouched rich text is preserved; edited text uses escaped line breaks.
- Saved drafts retain their document URL. Revision requests use the existing Resubmit workflow action. Category loading guards saves and ignores stale responses.
- Category tree navigation includes hierarchy guidance and a shortcut to the native list.

These changes close the implementation gaps named after batch 2. The original coverage table and verification results describe batch 1; later batches supersede its implementation column but do not extend its verification evidence. All inventory surfaces now have source changes or explicitly retained native controls with shared treatment. Final site synchronization, integrated review, role/workflow verification, bilingual responsive checks, and print rendering remain outstanding. No further tests were run after the user's deferral, and nothing was pushed.

## Consolidated verification — started after source implementation

Local integration completed for 17 changed DocTypes, three print formats, and Workspace presentation fields. A private snapshot of pre-integration records is at `/tmp/diwan-ui-integration-backup.json`. Workspace synchronization used ordinary save with migration mode and developer exports disabled; only content and number-card placement were changed, preserving roles and other settings.

Current evidence:

- Changed Python (12) and JSON (21) files parse successfully; shared/page/list/tree JavaScript passes ESLint; diff whitespace check passed.
- `tests/ui/portal.cjs` passed against the integrated site: attachment rejection/retry, same-draft submission, record-preserving language switch, RTL mobile navigation/focus, filtering, and no JavaScript errors.
- `tests/ui/edit-draft.cjs` captures the successful full-form draft save/reload/edit check. Document identity and multiline draft text were preserved.
- All 48 portal views passed HTTP/heading/overflow/page-error checks again. The Arabic 360px submission screenshot was visually inspected.
- Two correspondence reports executed with no filters, date range, and owner filter without query errors. All returned zero rows, so this does not establish populated-result correctness.

Remaining: finish Desk rendering checks, full role and workflow matrix, populated pagination/report/delivery scenarios, dynamic-field variants, workspace and print visual review, and real scanning/print constraints. The goal remains active; no push.

Desk follow-up: all ten editable/configuration forms rendered their visible shared guide. The first check timed out by selecting a hidden guide from the preceding SPA route; inspecting current browser state showed the requested form was present. Scoping the assertion to visible guides resolved that harness issue. This remains rendering coverage, not workflow verification.


## Workspace and print integration review

- Visually inspected the integrated English workspace. All five lifecycle cards and grouped tasks/charts are present. Fixed truncated task/card names by allowing the native title span to wrap; confirmed the resulting screenshot.
- Found label dimensions existed only in `@page`, while Frappe's PDF option parser extracts `.print-format` styles. Added explicit 90mm/50mm dimensions and 3mm margins to both labels and aligned metadata margins. The actual Frappe parser now extracts these values correctly; changes synchronized locally.
- Rendered all three Jinja print templates in EN/AR using disposable in-memory examples, including a 25-row delivery sheet. Fixed inherited table font sizing and missing Arabic courier/signature translations; visually inspected updated Arabic delivery and envelope renders. QR images loaded in all six samples.
- Browser-generated PDFs have one 90×50mm page for each sample label and two A4 pages for the delivery samples. Text extraction confirms repeated delivery headers and signatures on the final page. This checks Chromium output, not the configured wkhtmltopdf renderer: wkhtmltopdf is absent from this environment. Real printer/QR scanning and large-envelope pagination remain pending.
- Evidence retained with the earlier screenshots under the task visualization directory (`workspace-integrated.png` and print PNG/PDF files).

The source and local site include these fixes. No push. Role/workflow, populated reports/pagination, dynamic variants, and remaining integration review are still open.


## Request revision and portal permission boundary

- Browser workflow passed: create/Submit → Start Review → require a nonempty revision note → Request Revision → reopen full form with note and original draft → edit/Resubmit → same request in Pending Review with revised text. No page JavaScript errors. Reusable check: `tests/ui/revision.cjs`. This used the dedicated combined-role account; it is workflow coverage, not proof of role separation.
- Separately tested controller access with a temporary requester-only account: denied queue, tray, audit log, delivery sheets, and envelopes; denied editing a different owner's draft; allowed opening new-request form. Temporary account and draft were rolled back, with no password changes or welcome email.
- Full confidentiality/department matrix, approval/registration, movement/delivery states, dynamic-field variants, and populated reports/pagination remain outstanding. No push.

## Populated workflow, report, and pagination checks

Server integration checks passed with isolated audit fixtures:

- Request Submit/Start Review/Approve & Register produced a linked, numbered Correspondence with QR inside the test transaction.
- Overdue report included the exact follow-up-date boundary and reported three overdue days; a later start date excluded it.
- Correspondence Submit for Review/Refer/Mark Completed produced a completion-report row and removed it from overdue results.
- A 51-record request fixture paginated as 50/1, with no duplicate records across pages and retained language/previous/next links.
- Movement Send/Confirm Receipt populated sender/recipient timestamps and received-by information.
- Envelope populated its reference/QR and linked the correspondence. Delivery populated item details, rejected receipt confirmation without proof, then recorded proof time and correspondence linkage after confirmation. The test used the audit QR file as a disposable attachment to exercise presence validation; it does not establish that proof contents are validated.

These are controller/database checks; they do not establish browser ergonomics or every role variant. The pagination fixture and movement/delivery fixtures rolled back. Important correction: `access_log.log_event()` commits, so the initial approval fixture partially survived rollback (audit type and an approved request without its subsequently rolled-back correspondence). Those two exact test records were removed after verifying no business correspondence, requests, or numbering rules depended on the type. Audit events remain. The prior requester-only account and permission draft were confirmed absent; pagination requests were also absent.

Remaining verification: dynamic-field variants, department/confidentiality behavior through changed surfaces, custom Desk-page interaction, populated browser list/grid/report states, mobile/Arabic workspace, and configured PDF/hardware limits. No push.


## Dynamic controls and custom Desk category integration

Found and fixed a real custom Desk-page gap: category callbacks lacked ordering guards, saved prefill could overwrite current edits, and saving was possible before field metadata arrived. The Desk page now guards category/subcategory requests, retains edits, blocks saves during loading, and validates required subcategory selection. The portal also merges values typed during an outstanding request immediately before rerendering.

Browser checks passed with mocked metadata/search responses on the real pages: latest category response wins; switching away/back retains edited field values; all seven dynamic field types render with associated labels and required validation; value collection preserves checkbox/numeric values; keyboard Link navigation selects the intended result and closes the menu. Reusable tests are `tests/ui/desk-categories.cjs` and `tests/ui/dynamic-fields.cjs`. These are client component checks, not server metadata/permission verification. Changed Desk JS passed ESLint. No push.


## Custom Desk tracking interaction review

Added explicit Track action and Enter-key lookup for the exact-reference field, real URLs for search results (preserving open-in-new-tab behavior), current `/desk` document links, and a named keyboard-focusable scroll region around envelope document tables. ESLint passed.

Browser check passed against the real missing-reference API. Controlled restricted/envelope responses verified message rendering, keyboard lookup, document link, and mobile table containment; these mocks do not prove authorization. Inspected the 390px mobile screenshot with native sidebar closed: no document overflow, envelope table scroll remains local. Reusable test: `tests/ui/tracking.cjs`. Evidence: `tracking-envelope-mobile.png` in the task visualization directory. No push.


## Arabic workspace review

Verified the actual Desk boot language, not only document direction. A query-string Arabic override produced RTL layout while boot translations remained English for the English audit account. Temporarily setting only the dedicated audit user's language to Arabic exposed missing workspace translations. Added 18 shortcut/card/chart/configuration labels. After cache clearing, visually inspected Arabic workspace at 390px and 1440px: all five cards present, full translated labels visible, no horizontal document overflow or page JavaScript errors. The audit user's original language was restored. Screenshots retained as `workspace-ar-390.png` and `workspace-ar-1440.png` in the task visualization directory. No push.

## Native list and tree route check

All ten non-singleton top-level DocType List routes loaded their expected `cur_list` and scoped Diwan styling with no page JavaScript errors. Category Tree rendered its hierarchy guide. This verifies route initialization and shared integration; it does not yet establish populated row actions, every filter, or embedded row-editor behavior. The current completion checklist is `docs/UI_UX_COMPLETION.md`; the earlier surface table is explicitly labeled as a historical batch-1 snapshot.

## Bulk approval browser verification

The corrected controlled-response check passed: missing type prompts selection; a two-row batch reports one success and one failure; failed row links to individual review; both attempted rows are disabled afterward and cannot be accidentally retried in the same batch. `tests/ui/bulk.cjs` intercepts portal `cmd` POSTs as well as endpoint URLs and aborts unmatched POSTs during the action.

The initial harness matched only endpoint URLs, while this portal uses `cmd` POSTs. It therefore actually approved two selected, explicitly guarded `UI audit` requests. The UI showed both approvals; database verification confirms CR-2026-0001 and CR-2026-0002 link back to those approved audit requests. These are retained test evidence, not business records. The development site also displayed its existing missing outgoing-email-account message during real approval. No external email was sent. Do not claim the initial run was mocked or mutation-free. The corrected partial-failure run intercepted all workflow writes.


## Access Log Entry role-aware detail review

The initial combined-role audit account could save because System Manager intentionally has write permission in existing metadata. Temporarily removed that role from the dedicated account, then verified the officer view: `can_write` false, no visible Save action, named context section, no JavaScript errors. Screenshot visually inspected. Restored the exact original audit-account roles afterward. Changed the shared guide from “Read-only history…” to “History…” to avoid making a false claim for administrators; enforcement is unchanged.

## Real category, permission, and report integration

Created an isolated group/leaf Correspondence Category with one required Data field. Frappe generated matching Custom Fields on Correspondence Request and Correspondence. The real portal form required the subgroup and field; a saved audit draft reopened with group, leaf, and value intact. Deleted the exact audit draft/category pair, reran dynamic-field synchronization, and confirmed both generated Custom Fields were removed.

Used existing, clearly named audit correspondence CR-2026-0001 for a temporary Highly Confidential access check. A temporary employee user received a restricted tracking result, saw no Correspondence list or overdue-report row, and could not download the attached private file. The authorized owner could view tracking detail and list row. Restored the correspondence's original confidentiality/follow-up values and deleted the temporary user. Audit events were retained as expected.

All three Desk report routes loaded their declared filters with no page errors. Access Log Report displayed 32 live rows and its summary. The Reference Document Type filter placeholder clipped at desktop width; widened that exact report control to 240px. Report route checks do not replace per-filter browser interaction or populated completion-report rendering.


## Final-source presentation audit and child controls

Compared all 21 modified DocType, Workspace, and Print Format source documents against their local-site presentation data. One mismatch exposed an angle-bracket placeholder that Frappe treated as HTML in the Category Field slug description; changed it to plain text and resynchronized. Recheck: zero presentation mismatches. Arabic translation CSV has no duplicate keys; `git diff --check` passes.

All 11 child controls initialized in their owning Desk forms: ten Tables plus the Authorized Viewers Table MultiSelect. The category-field and delivery-item row editors opened on unsaved forms, with their expected labels and guidance; screenshots were inspected. This establishes control/row-editor rendering, while high-volume rows and all field-type editor variants remain outside that browser sample.

The Access Log Report screenshot shows 32 actual rows and summary cards. Its reference-type filter was clipped and has been widened to 240px. All three query-report routes expose their declared filter fields. Screenshots retained in the task visualization directory.


## Officer rejection and previous-note correction

Browser verification exposed a real bug: the queue decision textarea was prefilled with `detail.decision_note`, so an old revision note met the Reject requirement without a fresh explanation. The queue now displays the previous note separately and starts a blank decision textarea. Tested on a dedicated pending audit request containing an earlier note: the previous text stayed visible, empty Reject showed required-note feedback, and a fresh rejection persisted and appeared on the requester detail page. The earlier accidentally rejected audit request's visible reason was corrected to describe that test outcome. Reusable check: `tests/ui/rejection.cjs` with an explicit audit target. No business requests were used.

## Actual label preview and renderer limitation

Rendered `Document Label` for existing UI audit correspondence CR-2026-0001 through Frappe's real `get_print` path. Its HTML contains the reference and QR image; Frappe's private-image inliner resolves the QR to a data URI. The PDF option parser extracts 90mm by 50mm and 3mm margins. However, `prepare_options` also passes the site's default `page-size=A4` alongside the explicit width/height. The configured `wkhtmltopdf` binary is absent locally, so page-size precedence and final label output under that renderer remain unverified. Earlier Chromium PDFs are valid browser evidence only. This is an open print risk, not a proven successful configured PDF export.

## Large-envelope label pagination

Envelope labels now group documents in sets of three, printing one complete 90×50mm label per group. Every label repeats the envelope reference, total count, page number, and QR. The full set of references remains printed rather than being truncated. An eight-document fixture rendered all eight references and three loaded QR images; Chromium produced exactly three label-sized PDF pages with references 1–3, 4–6, and 7–8 in order. Screenshot and PDF saved in the task visualization directory. Source and local Print Format were synchronized. The configured wkhtmltopdf renderer remains unavailable locally, so its page-break handling still requires verification elsewhere.


## Custom Desk request full journey

Against the real custom Desk page, forced an attachment upload HTTP 500, confirmed the file stayed staged and the draft remained available, retried the upload successfully, and submitted the same request. The saved record is Pending Review with one private attachment. A first test run selected Frappe's hidden responsive dropdown instead of the visible Submit action and left a dedicated Draft with one attachment; that extra draft was deleted after the second run passed. The corrected reusable test uses the visible Submit for Review button by accessible name: `tests/ui/desk-request.cjs`. No business requests were touched.


## Populated delivery and envelope portals

The former `/app` Desk URLs were confirmed to redirect to `/desk`; portal Manage, New, and record links now use canonical `/desk` paths. Created isolated Envelope and Delivery Sheet records containing an existing UI audit correspondence. At 390px and 1440px, both populated pages rendered one record, retained Desk and print actions, and had no document-level overflow. Envelope tracking displayed its linked correspondence. The mobile screenshots were inspected. Both fixtures were deleted and the audit correspondence's original envelope/delivery links restored; access events remain in the audit log. Screenshot evidence is in the task visualization directory.

## Populated report and audit filters

The real audit-log portal combined Event Type = Download, Result = Denied, and Channel = Desk on retained access events; every displayed row matched all three selections, and Clear reset the controls. The populated Overdue Correspondence Desk report displayed audit correspondence CR-2026-0001, an overdue count of one, and its expected two-day value after an isolated follow-up-date change. Current Owner and Correspondence Type report controls retained their selected values and the row remained visible. The audit correspondence's original follow-up date was restored and verified afterward. The report screenshot was inspected; the owner filter text clips, so it needs a small width adjustment. These checks establish live rows and filter interaction, but the completion report still needs a populated browser sample.

The owner report filter is now given the same 240px minimum as the audit reference-type filter. A temporary transfer-log row on CR-2026-0003 then yielded a populated Correspondence Completion Time report: one completed item, average zero days, the correct audit reference, and retained owner/type selections. The screenshot was inspected; the exact temporary log row was deleted afterward.

## Officer approval, native rows, and camera fallback

The existing UI-audit Desk request went from Pending Review through Start Review and individual Approve & Register in the portal. The page showed Approved & Numbered, its new CR-2026-0003 reference, and the entered decision note; database checks confirmed the request/correspondence back-link. No page JavaScript errors appeared. The audit records are retained as workflow evidence.

Populated native Correspondence Request and Correspondence lists showed the audit rows, list actions, lifecycle indicators, and no page errors. The request list's longest status badge clipped, so its status column now has a scoped 190px minimum in source. Screenshot inspection also showed the native Correspondence list attempting one more narrow date column at 1440px; this is an ordinary Frappe responsive list constraint, and the row's subject, status, type, and reference remain legible. A source-only CSS change still needs a fresh browser capture because this long-lived Chrome context retained the older stylesheet while a cache-disabled reload stalled.

On the public tracking page, a controlled camera-start rejection showed the camera access/manual-entry message, restored the Scan button, kept Stop hidden, and left the reference input visible. Physical camera, QR scanning, and printer output remain environment-dependent.

## PDF dimension precedence resolved from renderer source

Frappe's local `prepare_options` includes site `page-size=A4` alongside the label's parsed `page-width=90mm` and `page-height=50mm`. The [wkhtmltopdf converter source](https://github.com/wkhtmltopdf/wkhtmltopdf/blob/master/src/lib/pdfconverter.cc) selects explicit width and height ahead of `pageSize` in its printer setup, so the A4 value is not itself a reason to expect A4 label output. The [paper-size parser](https://github.com/wkhtmltopdf/wkhtmltopdf/blob/master/src/lib/pdfsettings.cc) does not recognize a named `Custom` size; a brief source-only experiment adding that value was removed. The local site Print Formats remained on their original valid 90×50mm CSS. This resolves the option-precedence question by source inspection, while actual wkhtmltopdf pagination and printer output remain unverified because the binary is absent.

## Final request-list badge check

The audit browser had accumulated 20 tabs; closing those dedicated audit tabs restored reliable navigation. A fresh 1440px request-list capture proved the status cell grew to 190px, but Frappe's `.indicator-pill` still capped the text at 150px. The scoped list CSS now removes that cap and the latest capture shows the complete “Approved & Numbered” value, with the pill text's client and scroll widths equal. The requester email remains subject to Frappe's native list column ellipsis at this width.

## Additional real category types and employee Link search

An isolated category group/leaf defined Link (to Correspondence Type), Select, Currency, and Check fields. Each generated the expected Custom Field type on both Correspondence Request and Correspondence, and the live category metadata endpoint returned the four definitions. A temporary Website User with only Correspondence Employee role used Frappe's real `search_link` endpoint to find the allowed Circular correspondence type. This validates server-side generation and restricted-role search; the shared browser Link control's keyboard selection had already passed with controlled responses. The exact category pair, generated fields, and temporary user were removed and verified absent. Category values flowing through a full revision/approval remain to check.

## Department access and category workflow completion

With isolated User Permission records, a matching-department employee saw the audit correspondence at Normal and Confidential levels in tracking, the native list query, and the overdue report; an employee in another department saw none. At Highly Confidential, both employees were restricted despite one matching the department, matching that tier's `department_members_can_read=0` configuration. Original correspondence fields and all temporary users/permissions were restored or removed. Separate real 390px browser logins for the matching and other employees showed full tracking detail with subject/QR/attachment versus the restricted message with no subject. The screenshots were inspected. The browser users, passwords file, and permission records were removed; a fresh database session confirmed cleanup after an overly strict in-process restoration assertion failed despite the committed state being correct.

A separate real category group/leaf with a required Data field followed Submit → Start Review → Request Revision → edit → Resubmit → Start Review → Approve & Register. The field held `A-001` through the revision request, then saved `B-002`; the generated Correspondence contained only `B-002`. The exact test request, registered correspondence, QR file, category, type, numbering rule, and generated Custom Fields were deleted afterward. This verifies category values across the complete revision/approval path, beyond the earlier save/reload check.

## Populated configuration lists and large child grid

Native Correspondence Type, Confidentiality Level, and Document Access Profile lists displayed 4, 3, and 2 real rows respectively, with their key identifiers and values readable at 1440px; screenshots were inspected. Correspondence Category currently has zero records, and its native empty state shows a create action. Its “Parent Correspondence Category” quick-filter placeholder clipped; a 280px scoped width now shows the full text in a fresh capture. An unsaved Category form accepted 51 in-memory Dynamic Field child rows: the first page rendered rows 1–50, and clicking Last showed row 51 alone on page 2. No category document was saved. This verifies the grid's high-volume pagination, but not every keyboard action in every child table.

## Administrative configuration language and site state

The Document Access Profile screen previously described `searchable_fields` as a live unified search setting. The current correspondence search does not read it; it searches reference number and subject. Renamed that section “Future Search” and clarified the parent and child-field descriptions in English/Arabic, without changing search or access behavior. Added plain-language help to the three one-column Role/User child tables for confidentiality bypass, authorized viewers, and department exemptions. The fourth one-column child table, Document Access Profile Department Field, already has a required field and detailed explanation, so its source stayed unchanged. This accounts for all 11 child DocTypes. All 25 modified presentation documents now match local site metadata.

A later attempt to inspect populated native Envelope, Delivery Sheet, and Internal Mail Movement lists timed out under high host load, so it supplies no browser evidence. The three exact audit fixtures were deleted, the correspondence links restored, and a fresh database session confirmed their absence. The dedicated audit browser was closed; `/login` returned HTTP 200 in 0.26 seconds afterward. No development-server restart or configuration change was performed.

## Populated operational lists and reference polish

A fresh isolated pass rendered real rows in the native Envelope, Delivery Sheet, and Internal Mail Movement lists. Their identifiers, lifecycle indicators, and key columns were readable. Screenshot review caught clipped quick-filter labels for linked delivery sheet, delivery sheet number, and recipient party, plus reversed visual order in the mixed Arabic/numeric Delivery Sheet reference. Scoped Desk CSS gives those filters 225px and applies the existing bidi-override treatment to the Delivery Sheet subject and ID cells. A second fresh-browser pass confirmed filter widths and computed bidi styles; the screenshot shows `كشف-2026-020` in stored order in both cells. All three exact audit records were deleted, the correspondence links were restored, and the dedicated browser was closed. No server restart, configuration change, or push.

## Final local verification and boundaries

An unsaved Category Field row editor advanced keyboard focus from its Label input to the visible Field Type select with Tab; no JavaScript error occurred. This samples native grid keyboard behavior alongside the earlier 51-row pagination check, without claiming an exhaustive key-by-key audit of all 11 child tables. The browser was closed without saving the form.

The final source/site comparison found zero mismatches across 25 modified presentation documents. Static parsing passed for 101 Python, 9 Jinja, 47 JSON and 25 JavaScript app files; `git diff --check` passed. Source scope review found only Diwan UI, navigation, report-filter, pagination, and supporting documentation/test changes. Configured wkhtmltopdf and physical camera/printer output could not be exercised on this host; Chromium previews and camera-denial/manual-entry checks remain the available local evidence. No server restart, configuration change, or push.
