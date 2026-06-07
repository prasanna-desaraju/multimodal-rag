"""Chunking utilities and registered chunker implementations.

This package exposes chunker implementations that are auto-registered
via the `register_chunker` decorator in `chunker_interface`.
"""

from .chunker_interface import CHUNKER_REGISTRY  # noqa: F401

# Import concrete chunkers so they register themselves
from . import text_chunker  # noqa: F401
from . import table_chunker  # noqa: F401
from . import image_chunker  # noqa: F401
