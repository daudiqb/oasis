"""Public data dictionary for state records."""
from copy import deepcopy

STATE_CODE = 'state_code'
NAME = 'name'
POPULATION = 'population'
CAPITAL = 'capital'
AREA_SQ_MILES = 'area_sq_miles'

DISP_NAME = 'disp_name'
TYPE = 'type'
REQUIRED = 'required'
DEFAULT = 'default'

FIELDS = {
    STATE_CODE: {
        DISP_NAME: 'State Code', TYPE: 'string', REQUIRED: True,
        'description': 'Two-character state identifier; cannot be updated.',
    },
    NAME: {
        DISP_NAME: 'Name', TYPE: 'string', REQUIRED: True,
        'description': 'Non-empty state name.',
    },
    POPULATION: {
        DISP_NAME: 'Population', TYPE: 'integer', REQUIRED: False, DEFAULT: 0,
        'description': 'Non-negative population.',
    },
    CAPITAL: {
        DISP_NAME: 'Capital', TYPE: 'string', REQUIRED: False, DEFAULT: '',
        'description': 'State capital.',
    },
    AREA_SQ_MILES: {
        DISP_NAME: 'Area (sq miles)', TYPE: 'number', REQUIRED: False,
        DEFAULT: 0.0, 'description': 'State area in square miles.',
    },
}


def get_flds() -> dict:
    """Return metadata without exposing the shared dictionary to mutation."""
    return deepcopy(FIELDS)


def get_fld_names() -> list:
    """Return the public state field names in display order."""
    return list(FIELDS)


def get_disp_name(fld_nm: str) -> str:
    """Return a field label; unknown field names raise KeyError."""
    return FIELDS[fld_nm][DISP_NAME]
