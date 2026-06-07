"""Embedding adapters and implementations.

Importing this package will register available embedders.
"""

from .embedding_interface import EMBEDDER_REGISTRY  # noqa: F401

# Import concrete embedders so they register themselves
from . import sentence_transformer_embedding  # noqa: F401
