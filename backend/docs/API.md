# Hate Speech Detection REST API - v1

Base path: `/api/v1`
Default host: `http://127.0.0.1:5000`

`GET /api/v1` returns a machine-readable index of every endpoint, generated
from the live URL map. `GET /api/v1/health` reports whether the model loaded.

---

## Conventions

**Resources are nouns, actions are HTTP methods.** Classifying a text creates a
prediction, so it is `POST /predictions`, not `POST /predict`.

**Status codes**

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created — with a `Location` header pointing at the new resource |
| 202 | Accepted — long-running work queued (training) |
| 204 | No Content — successful `DELETE` |
| 400 | Malformed request |
| 401 | Missing or invalid key |
| 404 | No such resource |
| 405 | Wrong method — `details.allowed_methods` lists what is allowed |
| 406 | Cannot produce the requested representation |
| 409 | Conflict — e.g. a training job is already running |
| 413 | Upload exceeds `HSD_MAX_UPLOAD_MB` |
| 415 | `Content-Type` is not `application/json` |
| 422 | Body failed validation |
| 503 | Model or corpus unavailable |

**Errors are always JSON**, never an HTML page:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request body failed validation.",
    "details": { "text": ["Length must be between 1 and 500 characters."] }
  },
  "status": 422
}
```

**Collections** return a consistent envelope:

```json
{
  "data": [ ... ],
  "pagination": {
    "page": 1, "per_page": 20, "total": 137, "pages": 7,
    "has_prev": false, "has_next": true
  },
  "links": { "self": "...", "next": "...", "last": "..." },
  "total": 137, "page": 1, "pages": 7
}
```

Query parameters: `page` (≥1), `per_page` (≤ `HSD_MAX_PAGE_SIZE`, alias
`limit`).

**Numbers are numbers.** `confidence` is a float in `[0,1]`; `latency_ms` is an
integer. Formatting them for display is the client's job.

**Authentication**

| Header | Used by |
|--------|---------|
| `X-API-KEY` | public prediction endpoint (optional by default) |
| `X-ADMIN-KEY` | every `/admin/*` route and admin-only reads |

`Authorization: Bearer <key>` is accepted in place of either. Set
`HSD_REQUIRE_API_KEY=1` to make the API key mandatory on
`POST /predictions`.

---

## Predictions

### `POST /api/v1/predictions`

Classify a text and store the result.

```json
{ "text": "you are stupid" }
```

`201 Created`, `Location: /api/v1/predictions/42`

```json
{
  "id": 42,
  "text": "you are stupid",
  "label": 1,
  "label_name": "Offensive",
  "confidence": 0.8731,
  "probabilities": { "Normal": 0.0712, "Offensive": 0.8731, "Hate": 0.0557 },
  "language": "en",
  "model": "BiLSTM",
  "latency_ms": 118
}
```

Errors: `415` wrong content type · `422` empty / missing / over-long text ·
`503` model not loaded.

### `GET /api/v1/predictions`

Paginated history, newest first.

| Parameter | Description |
|-----------|-------------|
| `page`, `per_page` | pagination |
| `label` | `0`, `1` or `2` |
| `lang` | `en`, `hi` or `hi-en` |
| `q` | substring match on the text |

### `GET /api/v1/predictions/{id}`

One prediction. `404` if it does not exist.

### `DELETE /api/v1/predictions/{id}` — admin

`204` on success.

### `GET /api/v1/predictions/export`

CSV of the full (optionally filtered) history; accepts the same filters as the
list endpoint. Honours `?format=csv` and `Accept: text/csv`; any other format
is a `406`. Encoded UTF-8 with BOM so Excel renders Devanagari correctly.

---

## Annotations (human feedback)

### `POST /api/v1/annotations`

Record the label a human says is correct.

```json
{ "text": "...", "label": 2, "language": "en" }
```

`correct_label` is accepted as an alias for `label`. `201 Created`.

### `GET /api/v1/annotations` — admin

Paginated feedback log.

### `GET /api/v1/annotations/{id}` — admin

---

## Flagged terms

### `POST /api/v1/flagged-terms`

Flag words as the reason a text was rated Offensive or Hate.

```json
{ "words": ["stupid", "useless"], "label": "Offensive" }
```

`label` accepts `"Offensive"`/`"Hate"` or `1`/`2`. `201 Created`:

```json
{
  "created": ["stupid"], "updated": ["useless"], "skipped": ["a"],
  "counts": { "created": 1, "updated": 1, "skipped": 1 }
}
```

Words shorter than two characters after normalisation are skipped and reported
rather than silently dropped.

### `GET /api/v1/flagged-terms`

`?min_frequency=` (default `2`) filters out unconfirmed one-off reports.
Returns full rows in `data` plus a flat `words` array for text highlighting.

### `DELETE /api/v1/flagged-terms/{word}` — admin

---

## Analytics

| Endpoint | Returns |
|----------|---------|
| `GET /api/v1/analytics` | everything below, composed; `?days=` for the trend window |
| `GET /api/v1/analytics/summary` | totals, class counts, mean confidence/latency |
| `GET /api/v1/analytics/trend` | daily prediction volume, `?days=1..365` |
| `GET /api/v1/analytics/languages` | language distribution and language × class matrix |
| `GET /api/v1/analytics/models` | metrics from the last training run |
| `GET /api/v1/analytics/dataset` | training corpus composition |
| `GET /api/v1/analytics/errors` | confusion matrix and mismatched samples, `?limit=` |

`/analytics/models` reports availability honestly:

```json
{ "available": false, "models": {}, "source": null,
  "message": "No training report found. ..." }
```

When a report exists, each model carries `accuracy`, `macro_f1`, `precision`,
`recall` and `support` parsed from `backend/reports/training_report_all.json`.

The confusion matrix is keyed `{actual_label_name: {predicted_label_name: count}}`.

---

## Survey

### `GET /api/v1/survey/items/next`

One unresolved text to label.

```json
{ "text": "...", "original_label": 0, "vote_count": 2, "is_resolved": false }
```

Returns `404` with `code: "survey_exhausted"` once everything is resolved.

### `POST /api/v1/survey/votes`

```json
{ "text": "...", "label": 1 }
```

`user_label` is accepted as an alias. `201 Created`:

```json
{
  "item": { "id": 3, "vote_count": 3, "is_resolved": true, "resolved_label": 1, ... },
  "vote": { "label": 1, "label_name": "Offensive" },
  "consensus": { "reached": true, "threshold": 3, "corpus_updated": true }
}
```

Once `HSD_SURVEY_CONSENSUS` identical votes are cast, the label is written
back into `clean_data.csv`.

### `GET /api/v1/survey/stats` — admin

Participation counters plus the human label distribution.

---

## Admin

### `POST /api/v1/admin/sessions`

Exchange the admin password for the admin key.

```json
{ "password": "..." }
```

`201` -> `{ "token": "...", "token_type": "admin_key" }`. `401` if the password is wrong.

Send the token as `X-ADMIN-KEY` on subsequent admin requests.

### `DELETE /api/v1/admin/sessions/current`

`204`. Stateless — the client discards its token.

### `POST /api/v1/admin/datasets`

`multipart/form-data` with a `file` field containing a CSV.

Required columns: a text column (`text`, `comment`, `tweet` or `sentence`) and
a label column (`truelabel`, `label`, `class` or `target`). Labels outside
`0/1/2` and rows with fewer than three characters of text are dropped and
reported. `lang` is carried through when present, derived otherwise.

`201 Created`:

```json
{
  "rows_received": 120, "rows_accepted": 118,
  "rows_dropped_empty_text": 1, "rows_dropped_invalid_label": 1,
  "mapped_columns": { "text": "text", "truelabel": "label", "lang": "derived" },
  "rows_added": 115, "duplicates_merged": 3,
  "total_rows": 68255, "path": "backend\\data\\clean_data.csv"
}
```

### `GET /api/v1/admin/datasets`

Current corpus composition.

### `POST /api/v1/admin/training-jobs`

Queue a retrain. Returns **`202 Accepted`** immediately with a `Location`
header — training runs on a background thread.

```json
{ "id": 7, "status": "queued", "created_at": "...", "started_at": null, ... }
```

Returns `409` with the in-flight job if one is already running; concurrent runs
would corrupt the shared tokenizer.

### `GET /api/v1/admin/training-jobs/{id}`

Poll for `queued` -> `running` -> `succeeded` | `failed` | `interrupted`.
(`interrupted` means the server restarted mid-job.) The model is reloaded
automatically after a successful run.

### `GET /api/v1/admin/training-jobs`

Recent jobs.

### `GET /api/v1/admin/trends`

Change in label mix between the older and newer half of the recent window.
Always `200`; check `sufficient_data`:

```json
{
  "sufficient_data": true,
  "window_size": 20,
  "trends": {
    "Normal":    { "previous_count": 6, "current_count": 4, "change_percent": -33.3 },
    "Offensive": { "previous_count": 3, "current_count": 5, "change_percent":  66.7 },
    "Hate":      { "previous_count": 1, "current_count": 1, "change_percent":   0.0 }
  }
}
```

---

## Deprecated routes

The pre-v1 URLs still work and still return their original response shapes, so
nothing already integrated breaks. Each response carries `Deprecation: true`
and `Link: <successor>; rel="successor-version"`.

| Deprecated | Replacement |
|------------|-------------|
| `POST /predict` | `POST /api/v1/predictions` |
| `POST /api/classify` | `POST /api/v1/predictions` |
| `GET /history` | `GET /api/v1/predictions` |
| `GET /history/export` | `GET /api/v1/predictions/export` |
| `POST /feedback` | `POST /api/v1/annotations` |
| `POST /feedback/flag-words` | `POST /api/v1/flagged-terms` |
| `GET /flagged-terms` | `GET /api/v1/flagged-terms` |
| `GET /analytics` | `GET /api/v1/analytics` |
| `GET /survey/next` | `GET /api/v1/survey/items/next` |
| `POST /survey/submit` | `POST /api/v1/survey/votes` |
| `GET /admin/survey-overview` | `GET /api/v1/survey/stats` |
| `GET /admin/survey-labels` | `GET /api/v1/survey/stats` |
| `GET /admin/flagged-terms` | `GET /api/v1/flagged-terms?min_frequency=1` |
| `POST /admin/upload` | `POST /api/v1/admin/datasets` |
| `POST /admin/retrain` | `POST /api/v1/admin/training-jobs` |
| `GET /admin/trends` | `GET /api/v1/admin/trends` |

One deliberate behaviour change: `POST /admin/retrain` now returns `202`
immediately instead of blocking the connection — and the whole dev server —
for the duration of training.

Set `HSD_ENABLE_LEGACY_ROUTES=0` to remove them entirely.

---

## Configuration

See `.env.example`. Notable values:

| Variable | Default | Purpose |
|----------|---------|---------|
| `HSD_API_KEY` | `dev-api-key-change-me` | value for `X-API-KEY` |
| `HSD_ADMIN_KEY` | `dev-admin-key-change-me` | value for `X-ADMIN-KEY` |
| `HSD_ADMIN_PASSWORD` | `admin123` | verified by `POST /admin/sessions` |
| `HSD_REQUIRE_API_KEY` | `0` | require a key on `POST /predictions` |
| `HSD_CORS_ORIGINS` | `localhost:3000,127.0.0.1:3000` | allowed browser origins |
| `HSD_ENABLE_LEGACY_ROUTES` | `1` | serve the pre-v1 URLs |
| `HSD_SURVEY_CONSENSUS` | `3` | votes needed to settle a label |

The server prints a warning at startup for as long as the shipped default
secrets are still in use.
