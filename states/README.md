# State code

This directory contains *code*, *raw data*, and *JSON files* for the state part of our
project.


`update(state_code, **changes)` partially updates an existing state. For example,
`update('AL', population=5000000)` changes only its population. Supported fields
are `name`, `population`, `capital`, and `area_sq_miles`; the state code identifies
the record and cannot be changed. Empty updates return the existing record.
Invalid fields or missing states raise `ValueError`, and a database outage returns
`None`. Validation occurs before saving so rejected changes leave the state intact.
