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

The query module initializes its state records from this loader, preserving
previously available details for Alabama, Alaska, and Arizona. Run
`python -m states.load` to print the normalized records, or append a CSV path.
The current query storage is in memory; loading does not persist to MongoDB.
