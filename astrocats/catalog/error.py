"""Class for representing spectra.
"""
from astrocats.catalog.catdict import CatDict
from astrocats.catalog.key import KEY_TYPES, Key, KeyCollection


class ERROR(KeyCollection):
    # Any
    VALUE = Key('value')
    # Numeric
    ERROR = Key('error', KEY_TYPES.NUMERIC)
    # Booleans
    UPPER_LIMIT = Key('upperlimit', KEY_TYPES.BOOL)
    # Strings
    UNIT = Key('unit', KEY_TYPES.STRING)
    KIND = Key('kind', KEY_TYPES.STRING)
    SOURCE_KIND = Key('sourcekind', KEY_TYPES.STRING)


class Error(CatDict):
    """
    """

    _KEYS = ERROR

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.REQ_KEY_TYPES = [
            [ERROR.VALUE]
        ]
