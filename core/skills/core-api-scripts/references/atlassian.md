# Jira and Confluence through scripts

> **Contents:** 1. Cloud or Data Center · 2. Jira patterns · 3. Confluence patterns · 4. Writes · 5. Replacing MCP tools · 6. Errors

## 1. Cloud or Data Center
| | Jira Cloud | Jira Data Center | Confluence Cloud | Confluence Data Center |
|---|---|---|---|---|
| base | `https://<site>.atlassian.net` | your host | `https://<site>.atlassian.net/wiki` | your host (often `/confluence`) |
| auth | email + API token (Basic) | personal access token (Bearer) | the same Atlassian token | personal access token |
| API | `/rest/api/3` (ADF texts), Agile `/rest/agile/1.0` | `/rest/api/2` (plain text / wiki markup) | v2 `/api/v2/…`, search v1 `/rest/api/search` | v1 `/rest/api/content…` |
| search | `POST /rest/api/3/search/jql`, `nextPageToken` | `GET /rest/api/2/search`, `startAt` | CQL, `_links.next` cursor | CQL, `start`/`limit` |

The client detects Cloud by the `*.atlassian.net` host; `JIRA_CLOUD=1|0` and `CONFLUENCE_CLOUD=1|0` override it (a
custom domain in front of Cloud). In Cloud the old `GET /rest/api/3/search` is being retired — the client uses
`/search/jql`.

## 2. Jira patterns
```python
import sys; sys.path.insert(0, ".claude/skills/core-api-scripts/scripts")
from api_client import jira, pick, text
j = jira()
# custom fields: find the id by name once, then ask for it by id
ids = {f["name"]: f["id"] for f in j.get("/rest/api/3/field")}
sp = ids.get("Story Points") or ids.get("Story point estimate")
total = sum(pick(i, f"fields.{sp}", 0) or 0 for i in j.search("sprint in openSprints() AND project = EBO", fields=[sp]))
print("story points in the open sprint:", total)
# issues without acceptance criteria in the description
for i in j.search("project = EBO AND status = 'To Do'", fields=["summary", "description"], limit=200):
    if "acceptance" not in text(pick(i, "fields.description", "")).lower():
        print(i["key"], pick(i, "fields.summary"))
```
- JQL: `project = X AND statusCategory != Done`, `assignee = currentUser()`, `updated >= -7d`, `sprint in openSprints()`,
  `parent = EPIC-1` (children of an epic in new projects), `labels in (a, b)`, `ORDER BY updated DESC`.
  Validate an unsure query: `j.post("/rest/api/3/jql/parse", json={"queries": [q]})` (a read).
- How many before fetching: `j.count(jql)` — decide whether you need all of them.
- Fields: `summary,status,assignee,priority,labels,parent,updated` cover most reports; `description` and `comment` are
  the heavy ones — only when the task reads them.
- `expand="changelog"` or `/issue/{key}/changelog` for "who changed the status and when".

## 3. Confluence patterns
```python
import sys; sys.path.insert(0, ".claude/skills/core-api-scripts/scripts")
from api_client import confluence, pick, text
c = confluence()
for r in c.search('space = DEV AND type = page AND text ~ "payment" ORDER BY lastmodified DESC', limit=20):
    print(pick(r, "content.id"), pick(r, "content.title"), pick(r, "lastModified"))
page = c.page("123456")                      # the body in storage format (XHTML)
print(text(page)[:3000])                     # plain text for reading; the full body only when you edit it
```
- CQL: `space = KEY`, `type = page`, `title ~ "word"`, `text ~ "phrase"`, `ancestor = <id>` (the whole subtree),
  `label = x`, `lastmodified >= now("-30d")`, `creator = currentUser()`.
- The v2 API needs the space **id**, not the key: `c.get("/api/v2/spaces", keys="DEV")` → `results[0].id`.
- A page tree: `c.pages(f"/api/v2/pages/{id}/children")` recursively, or CQL `ancestor = <id>` in one search.

## 4. Writes
- Run the script without `TF_API_WRITE=1` first: every write prints `[dry-run] METHOD /path {body}` to stderr and
  returns `{"dry_run": True}`; the script must not depend on what a write returns during the dry run (e.g. a new id).
- Jira Cloud texts (description, comment) are ADF: `adf("plain text")`; Data Center takes plain text.
- Editing a Confluence page: read the current version (`page["version"]["number"]`), send `number + 1` with the full
  body; a conflict (409) means someone edited it meanwhile — read again, do not overwrite.
- Bulk: `POST /rest/api/3/issue/bulk` (≤50 creates), `POST /rest/agile/1.0/sprint/{id}/issue` (≤50 moves); larger sets
  in chunks, with a printed count after each chunk.
- Attachments (multipart with the `X-Atlassian-Token: no-check` header) are outside the client; the human uploads them or
  a dedicated script is written and reviewed.

## 5. Replacing MCP tools
| what an Atlassian MCP tool does | here |
|---|---|
| search issues with JQL | `jira().search(jql, fields=[…])` |
| get an issue | `jira().issue(key, fields=[…])` |
| create / edit an issue | `post /rest/api/3/issue` · `put /rest/api/3/issue/{key}` (dry run first) |
| transition an issue | `jira().transition(key, "Done")` |
| add a comment | `jira().comment(key, "text")` |
| search Confluence with CQL | `confluence().search(cql)` |
| get / create / update a page | `confluence().page(id)` · `post /api/v2/pages` · `put /api/v2/pages/{id}` |
| list spaces, projects, users | `api.py search jira users` → the operation → `get` or a script |
The difference is not only fewer tool definitions: a script returns 20 lines of summary where MCP returns 20 full issues.

## 6. Errors
- 401 — wrong or expired token; 403 — the account has no permission (do not look for another account); 404 — no such
  object or no access; 429 — rate limit: wait (the `Retry-After` header) and repeat once, do not loop.
- 400 with `errorMessages` — usually a bad JQL or a field name: check with `jql/parse` or `/rest/api/3/field`.
