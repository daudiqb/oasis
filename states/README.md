# State code

This directory contains *code*, *raw data*, and *JSON files* for the state part of our
project.


`update(state_code, **changes)` partially updates an existing state. For example,
`update('AL', population=5000000)` changes only its population. Supported fields
are `name`, `population`, `capital`, and `area_sq_miles`; the state code identifies
the record and cannot be changed. Empty updates return the existing record.
Invalid fields or missing states raise `ValueError`, and a database outage returns
`None`. Validation occurs before saving so rejected changes leave the state intact.

`delete(state_code)` removes a state only if no cities reference its code.
It returns `True` when deleted, `False` when missing, and `None` if the state
or city query is unavailable. Invalid codes and states with cities raise
`ValueError` without deleting the state. `DELETE /states/<state_code>` requires
an `X-User-Email` permitted to delete states; it returns 200 on success, 400 for
invalid codes or remaining cities, 404 for missing states, and 503 for outages.

`load_states()` in `states/load.py` reads the bundled `raw_data/states.csv`
using a path relative to the module, so it works from any working directory.
It returns 50 records with `state_code` and `name`, plus default population,
capital, and area values. DC and Puerto Rico are excluded because they are not
states. Missing columns, invalid records, and duplicate codes raise errors.
An optional file path supports other CSV files with the same columns.

State queries persist through `data.db_connect` in MongoDB. `read()`,
`read_one()`, and `exists()` share a lazy, per-process RAM cache. Successful
creates, updates, and deletes clear the cache; the next read reloads MongoDB.
Returned dictionaries are copies, so callers cannot modify cached records.
`@needs_db` still returns `None` when the database is reported down.

Call `states.query.clear_cache()` after writes made outside the query module,
or restart the API after `make load_db`. Each server process has its own cache;
writes from another process do not automatically refresh it.

Run `python -m states.load` to print normalized CSV records, or use
`make load_db` from the repository root to persist the bundled data.

`states/fields.py` describes the public state fields with display names, JSON
value types, required-on-create flags, descriptions, and optional defaults.
`get_flds()` returns a copy; `get_fld_names()` lists the fields and
`get_disp_name(name)` looks up a label (unknown names raise `KeyError`).

`GET /states/fields` returns `{"Fields": {...}}` with this dictionary. It is
public, requires no database connection, and takes precedence over the
`/states/<state_code>` route. Required flags describe creation; updates remain
partial, and `state_code` cannot be changed. MongoDB's `_id` is excluded.
