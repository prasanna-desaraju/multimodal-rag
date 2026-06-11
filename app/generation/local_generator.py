from __future__ import annotations

from typing import List, Dict, Any, Optional
import logging

from .generator_interface import Generator, register_generator
from ..models.document import Document

logger = logging.getLogger(__name__)


@register_generator("local")
class LocalGenerator(Generator):
    """Local transformer-backed generator for offline testing.

    This uses Hugging Face `transformers` text-generation pipeline. It is
    intended for local testing and development. Quality will depend on the
    chosen model and may be far from ChatGPT quality unless a capable model
    is provided and hardware is available.
    """

    def __init__(self, model_name: str = "gpt2", max_length: int = 256):
        try:
            from transformers import pipeline
        except Exception as exc:
            raise NotImplementedError(
                "Install 'transformers' to use LocalGenerator: pip install transformers[torch]"
            ) from exc

        self.model_name = model_name
        self.max_length = max_length
        # Create pipeline (downloads model on first run)
        try:
            self._pipe = pipeline("text-generation", model=self.model_name, tokenizer=self.model_name)
        except Exception as e:
            logger.exception("Failed to initialize text-generation pipeline for model %s", self.model_name)
            raise

    def generate(self, query: str, inserted_context: List[Document], timeout: Optional[float] = None, retries: int = 1, **kwargs) -> Dict[str, Any]:
        context_texts = [d.content for d in inserted_context if getattr(d, "content", None)]
        context_block = "\n\n".join(context_texts)
        prompt = f"Context:\n{context_block}\n\nQuery:\n{query}\n\nAnswer:"

        # Run the local generation pipeline
        out = self._pipe(prompt, max_length=self.max_length, do_sample=True, top_k=50, num_return_sequences=1)
        # `generated_text` contains the prompt+continuation; attempt to strip the prompt prefix
        generated = out[0].get("generated_text", "")
        if generated.startswith(prompt):
            text = generated[len(prompt):].strip()
        else:
            # fallback: return full generated text
            text = generated

        return {"text": text, "raw": out}
