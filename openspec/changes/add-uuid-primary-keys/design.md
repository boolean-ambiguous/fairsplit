# Design: add-uuid-primary-keys

## Context

Every id today is an autoincrement `int`, which quietly does double duty as "creation order" wherever the app lists things (`Member`/`Expense` ordering) or breaks ties (expense remainder allocation). Switching to random UUIDs severs that accidental coupling — every place that relied on "ascending id" for something other than identity needs an explicit decision about what it should do instead.

## Decisions

### UUID fields are non-Optional

`id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)`, no `| None`. Unlike autoincrement ids (which are `None` until the DB assigns one on flush), `default_factory` populates the field at Python object construction time — a UUID id is genuinely never `None` at any point in the object's life, so `| None` would be a vestige of the old convention, not a real possibility. Verified empirically: SQLAlchemy 2.x's `Uuid` type stores as `CHAR(32)` on SQLite (no native UUID type there) and round-trips as real `uuid.UUID` Python objects, not strings.

One free simplification this buys: `record_expense`'s `session.add(expense); session.flush()` was needed so autoincrement `expense.id` existed before inserting `ExpenseShare` rows. With UUIDs the id exists before `add()` is even called, so the `flush()` is no longer load-bearing. Left in place anyway — smaller diff, and it's harmless.

### Member listing and expense listing order switch from id to created_at

`group_members()` ordered `.order_by(Member.id)` and `group_expenses()` ordered `.order_by(Expense.id.desc())` — both only "worked" because autoincrement ids happen to equal creation order. `Member` gets a `created_at` field (missing until now); both queries switch to ordering by their respective `created_at`.

### Expense remainder allocation: order-dependent by design, resolved by the caller

`split_evenly` used to be order-*independent* (`sorted(participant_ids)` internally) — deliberately, since "ascending id" was a meaningful, stable tie-break under autoincrement ids. Under UUIDs, "ascending id" is still deterministic (UUIDs are totally ordered) but the specific winner is arbitrary and non-meaningful.

Rather than accept an arbitrary tie-break, `split_evenly`'s contract changes: it now assigns the remainder to the first N entries of whatever list it's given, full stop — no internal sorting. The caller (`record_expense`) becomes responsible for supplying a meaningfully-ordered list, which it does by querying the group's members ordered by `created_at` and re-indexing the submitted `participant_ids` against that order. This also removes a latent trust issue: the old code implicitly assumed the HTTP form submitted `participant_ids` in a useful order (an accident of checkbox DOM order), never guaranteed by anything.

**Rejected alternative**: keep `split_evenly` sorting internally, just sort UUIDs directly. Simpler diff, but the resulting behavior (remainder goes to whichever participant happens to have the lexicographically smallest UUID) is arbitrary and would ship as an undocumented accident — exactly the kind of implicit coupling this whole change exists to remove.

### Settlement tie-break: left alone, on purpose

`suggest_settlements`'s heap-based tie-break compares `(balance, member_id)` tuples directly — this remains fully deterministic under UUIDs (still a total order), it just no longer means "earliest joined." Considered mirroring the expense-remainder fix (thread join order through as a secondary sort key) and rejected: `suggest_settlements` is a pure function with zero DB access today, exercised directly with synthetic keys in its own tests; coupling it to `Member.created_at` would mean the caller resolving and passing a secondary order through for a cosmetic property only visible when two members' balances are *exactly* equal. Not worth it. Recorded here explicitly so the non-decision isn't an accident.

### Unguessable identifiers: verified, not assumed

FastAPI validates `uuid.UUID`-typed path/form params natively (Pydantic under the hood). Verified directly against this repo's installed versions: a malformed UUID in a path segment 422s before the route body runs at all (no DB hit); a well-formed-but-unknown UUID reaches the handler and 404s exactly like today. Both failure modes reveal nothing more than "not accessible" — no timing or response-shape difference to exploit.

## Risks / Trade-offs

- No migration path for existing data — accepted; `fairsplit.db` is gitignored, disposable local state, consistent with the project's "no migrations, `init_db()` just calls `create_all`" posture from day one.
