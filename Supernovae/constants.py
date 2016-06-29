"""Constant variables used by OSC import methods.
"""
from astropy import constants as const
from astropy import units as un

OSC_BIBCODE = '2016arXiv160501054G'
OSC_NAME = 'The Open Supernova Catalog'
OSC_URL = 'https://sne.space'

ACKN_CFA = ("This research has made use of the CfA Supernova Archive, "
            "which is funded in part by the National Science Foundation "
            "through grant AST 0907903.")

ADS_BIB_URL = ("http://adsabs.harvard.edu/cgi-bin/nph-abs_connect?"
               "db_key=ALL&version=1&bibcode=")

CLIGHT = const.c.cgs.value
KM = (1.0 * un.km).cgs.value
TRAVIS_QUERY_LIMIT = 10

REPR_BETTER_QUANTITY = {
    'redshift',
    'ebv',
    'velocity',
    'lumdist',
    'discoverdate',
    'maxdate'
}

COMPRESS_ABOVE_FILESIZE = 90000000   # FIX: units?

MAX_BANDS = [
    ['B', 'b', 'g'],  # B-like bands first
    ['V', 'G'],       # if not, V-like bands
    ['R', 'r']        # if not, R-like bands
]
