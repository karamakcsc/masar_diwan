# Portal interaction checks

`portal.cjs` exercises behavior that static checks cannot cover: failed upload recovery, retry and submission of the same draft, required-field focus, record-preserving language changes, RTL overflow, mobile drawer keyboard behavior, and queue filtering.

Use a **development site** and a browser authenticated as a dedicated test user with Correspondence Employee and Diwan Officer access. This test creates a uniquely named request and a small private text attachment, then submits that request. It retains these records as test evidence; it never changes existing business records or passwords.

Requires Node 20+ and `playwright-core`. Connect to the browser opened by `agent-browser` (`agent-browser get cdp-url` provides its CDP URL):

```sh
DIWAN_UI_URL=http://your-development-site:8001 \
DIWAN_UI_CDP=http://127.0.0.1:9222 \
node tests/ui/portal.cjs
```

If Playwright is installed outside the repository, set `DIWAN_PLAYWRIGHT` to its absolute module directory. Screenshots are written to `/tmp/diwan-*.png`. The script checks English messages, then Arabic layout; start the authenticated browser in English.

`edit-draft.cjs` uses the same environment variables and verifies save → reload → edit → save against one dedicated draft, preserving its identity and text line breaks. It retains that draft as evidence.

`revision.cjs` verifies submission, officer review, required revision note, full-form editing, and resubmission on the same audit request. Use the dedicated combined requester/officer test account. It retains its clearly named request.

`desk-categories.cjs` exercises delayed category responses and value retention on the real Desk page. `dynamic-fields.cjs` exercises all seven shared control types and keyboard Link selection. Both use mocked metadata/search responses, save no documents, and use the same environment variables. They do not establish server-side dynamic-field generation or Link search permissions.

`tracking.cjs` verifies exact-reference keyboard lookup and real missing-reference feedback, then uses controlled responses for restricted and envelope states. It checks the mobile document overflow boundary and saves a screenshot. It does not establish restricted-record permissions from mocked responses.

`bulk.cjs` needs two pending requests whose names begin `UI audit`. It intercepts both endpoint-style and portal `cmd` POSTs, aborts other POSTs during the action, and verifies a controlled partial failure. It tests client recovery, not actual approval persistence.

`rejection.cjs` requires `DIWAN_REJECTION_TARGET` pointing to a JSON file with a `name` key for a dedicated pending UI audit request with a previous decision note. It confirms the previous note is context only, the fresh note is required, and the requester sees the rejection. This test changes that audit request to Rejected.

`desk-request.cjs` uses the same browser environment variables. It verifies the custom Desk page keeps a rejected attachment staged, retries upload, and submits the same draft. It retains the submitted audit request and private text attachment as evidence.
