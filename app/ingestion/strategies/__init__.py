"""Strategy registry for file parsers.

Importing this package will register available strategies.
"""
from .base import ParserStrategy, STRATEGY_REGISTRY  # noqa: F401

# Import concrete strategies so they register themselves
from . import pdf_strategy  # noqa: F401
from . import docx_strategy  # noqa: F401
from . import image_strategy  # noqa: F401
from . import markdown_strategy  # noqa: F401
from . import table_strategy  # noqa: F401
from . import chart_strategy  # noqa: F401

__all__ = [
    "ParserStrategy",
    "STRATEGY_REGISTRY",
    "pdf_strategy",
    "docx_strategy",
    "image_strategy",
    "markdown_strategy",
    "table_strategy",
    "chart_strategy",
]
