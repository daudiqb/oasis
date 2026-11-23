# Requirements for Security System

## Features Needed

- Different users have different permissions
- Do we need group permissions? (Maybe later.)
- We should be fine-grained about access... someone might be able, e.g., to update a record but not delete it.
- We must be able to easily add different types of security checks as required, e.g.,
    - login
    - auth key
    - dual factor
    - biometrics
    - IP address
- If there is no security record for some feature, it is open to all.

## Design

- Security data should be in our DB.
- First cut: let's use CRUD.
- Having a dictionary of bools to specify checks needed will permit easily adding more later.

## Login check and auth codes

- Users live in the `users` collection (see `users/query.py`). Each has an
  email and an auth code; only a hash of the code is stored.
- A record that requires `login` is only satisfied when the caller passes
  `auth_code=...` and it matches that user's stored hash. Passing `login=True`
  no longer works.
- Other checks (e.g. `dual_factor`) still need their flag passed as `True`.
- Records are read from the `security` collection (one document per feature,
  with a `feature` field). If it is empty or the DB is down, the built-in
  `temp_recs` are used.
