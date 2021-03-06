"""Astrocats: Scripts for creating and analyzing catalogs of astronomical data.
"""

import os

__version__ = '0.2.16'
__author__ = 'James Guillochon'
__license__ = 'MIT'

# Set the path for the user's configuration file
_CONFIG_PATH = os.path.join(os.path.expanduser('~'),
                            '.config', 'astrocats', 'astrocatsrc')
