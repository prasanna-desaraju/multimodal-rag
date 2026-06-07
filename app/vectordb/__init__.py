"""Vector DB adapters and store implementations.

Importing this package will register available vector DB providers.
"""

from .vectordb_interface import VECTORDB_REGISTRY  # noqa: F401

# Import concrete providers so they register themselves
from . import providers  # noqa: F401
