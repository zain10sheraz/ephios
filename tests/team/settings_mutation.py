"""Settings for mutation runs only: on-disk reusable test DB so each mutant skips migrations."""

from tests.settings import *

DATABASES["default"]["TEST"] = {"NAME": "data/mutation_test.sqlite3"}
