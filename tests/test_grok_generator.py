import json
from unittest.mock import patch, Mock

from app.generation.generator import GrokGenerator
from app.models.document import Document


def test_grok_generator_success():
    gen = GrokGenerator(api_key="fake", endpoint="https://example.test/generate")

    fake_resp = Mock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {"text": "This is an answer."}

    with patch("requests.post", return_value=fake_resp) as mock_post:
        out = gen.generate("What is X?", [Document(id="d1", content="info", metadata={})], timeout=5, retries=2)
        assert out["text"] == "This is an answer."
        mock_post.assert_called_once()
