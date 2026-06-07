"""Retrieval adapters and pipelines.

Importing this package will register available rewriters, retrievers,
and refiners.
"""

from .rewriter_interface import REWRITER_REGISTRY  # noqa: F401
from .retriever_interface import RETRIEVER_REGISTRY  # noqa: F401
from .refiner_interface import REFINER_REGISTRY  # noqa: F401

# Import default implementations so they register
from . import rewrite_simple  # noqa: F401
from . import retriever_vector  # noqa: F401
from . import refine_simple  # noqa: F401
from . import rerank_crossencoder  # noqa: F401
from . import context_builder  # noqa: F401
