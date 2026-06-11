from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/v1/generate', methods=['POST'])
def generate():
    payload = request.get_json(silent=True) or {}
    prompt = payload.get('prompt', '')
    # Return a deterministic mock response including a short excerpt of the prompt
    excerpt = (prompt[:300] + '...') if len(prompt) > 300 else prompt
    return jsonify({
        "text": "MOCK GENERATED ANSWER: This response is from the local mock Grok server.",
        "prompt_excerpt": excerpt,
        "raw": payload
    })

if __name__ == '__main__':
    # Listen only on localhost and port 8000 so it's clearly a local test server.
    app.run(host='127.0.0.1', port=8000)
