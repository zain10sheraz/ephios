"""Settings for mutation runs only: on-disk reusable test DB so each mutant skips migrations."""
from tests.settings import *  # noqa: F401,F403

DATABASES["default"]["TEST"] = {"NAME": "data/mutation_test.sqlite3"}  # noqa: F405
