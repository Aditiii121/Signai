"""
SignAI v3 — Flask Backend Server
Serves the frontend and provides API endpoints for AI interpretation and Zoom integration.
"""

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import time
import hashlib
import hmac
import json
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ─── Serve Frontend ───────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ─── AI Interpretation Endpoint ───────────────────────────────────────────────
@app.route('/interpret', methods=['POST'])
def interpret():
    data = request.get_json()
    text = data.get('text', '').strip().upper()
    mode = data.get('mode', 'alphabet')

    # Local interpretation (no external API needed)
    interpretation = local_interpret(text, mode)
    return jsonify({'interpretation': interpretation})


def local_interpret(text, mode):
    """Smart local interpretation of sign language sequences."""
    
    # Known word mappings
    word_map = {
        'HELLO': 'A warm ASL greeting — open palm waving from the temple.',
        'I LOVE YOU': 'The iconic ILY handshape: thumb, index, and pinky extended simultaneously.',
        'ILY': 'I Love You — combined I, L, Y handshape. A universal sign of affection.',
        'YES': 'An affirmation gesture — closed fist nodding up and down.',
        'NO': 'Negation gesture — index and middle fingers snap down to thumb.',
        'THANK YOU': 'Gratitude: flat hand from chin moving outward toward the person.',
        'OK': 'Approval sign: index and thumb forming a circle, other fingers up.',
        'CALL ME': 'Request a call: thumb and pinky extended (shaka) held to ear.',
        'WAIT': 'Request to pause: both hands open, fingers spread, waving gently.',
        'GOOD': 'Positive: flat hand touches chin, moves forward and down.',
        'SORRY': 'Apology: closed fist circles over chest in a slow motion.',
        'PLEASE': 'Polite request: flat hand circles on chest.',
        'HELP ME': 'Assistance needed: fist on open palm, both lift upward.',
        'OPEN': 'Open hand gesture — all five fingers spread wide.',
    }

    if text in word_map:
        return f'Detected: <strong>"{text}"</strong>. {word_map[text]}'

    # Try to interpret as a spelled word
    words = text.split()
    if len(words) > 1:
        # Multi-word phrase
        return (f'Signed phrase: <strong>"{text}"</strong>. '
                f'A {len(words)}-word sequence detected through sign language. '
                f'This appears to be a conversational phrase.')

    if len(text) <= 3:
        spelled = ' – '.join(list(text))
        return (f'Spelled: <strong>{spelled}</strong>. '
                f'Short ASL fingerspelling sequence detected.')

    # Common English words that might be spelled out
    common_words = {
        'HI': 'Greeting', 'BYE': 'Farewell', 'STOP': 'Command to stop',
        'GO': 'Command to proceed', 'COME': 'Request to approach',
        'FOOD': 'Referring to food/eating', 'WATER': 'Requesting water',
        'HOME': 'Referring to home', 'WORK': 'Referring to work/office',
        'MEET': 'Meeting/gathering', 'ZOOM': 'Video conference',
        'NAME': 'Asking about name', 'TIME': 'Asking about time',
    }

    if text in common_words:
        return (f'Detected: <strong>"{text}"</strong> — {common_words[text]}. '
                f'This is a commonly used sign in daily conversation.')

    return (f'Detected: <strong>"{text}"</strong>. '
            f'This appears to be an ASL fingerspelling sequence of {len(text)} characters. '
            f'The letters were signed individually to spell out this word.')


# ─── Zoom Meeting Support ─────────────────────────────────────────────────────
@app.route('/api/zoom/config', methods=['GET'])
def zoom_config():
    """Return Zoom configuration (demo mode if no real credentials)."""
    sdk_key = os.environ.get('ZOOM_SDK_KEY', '')
    has_credentials = bool(sdk_key)
    return jsonify({
        'configured': has_credentials,
        'demoMode': not has_credentials,
        'message': 'Zoom SDK configured' if has_credentials else 'Running in demo mode — set ZOOM_SDK_KEY and ZOOM_SDK_SECRET env vars for real meetings'
    })


@app.route('/api/zoom/signature', methods=['POST'])
def zoom_signature():
    """Generate Zoom meeting signature (requires real SDK credentials)."""
    sdk_key = os.environ.get('ZOOM_SDK_KEY', '')
    sdk_secret = os.environ.get('ZOOM_SDK_SECRET', '')
    
    if not sdk_key or not sdk_secret:
        return jsonify({
            'error': 'Zoom SDK not configured',
            'demoMode': True,
            'signature': 'demo-signature-' + str(int(time.time()))
        })

    data = request.get_json()
    meeting_number = data.get('meetingNumber', '')
    role = data.get('role', 0)

    try:
        import jwt
        iat = int(time.time()) - 30
        exp = iat + 60 * 60 * 2
        payload = {
            'sdkKey': sdk_key,
            'mn': meeting_number,
            'role': role,
            'iat': iat,
            'exp': exp,
            'tokenExp': exp
        }
        signature = jwt.encode(payload, sdk_secret, algorithm='HS256')
        return jsonify({'signature': signature})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.route('/health')
def health():
    return jsonify({'status': 'running', 'version': 'SignAI v3.0', 'timestamp': int(time.time())})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('RENDER') is None
    print("\n" + "="*60)
    print("  ✋ SignAI v3.0 — Sign Language Communicator")
    print("="*60)
    print(f"  🌐 Open in browser: http://localhost:{port}")
    print(f"  📱 For Zoom: Set ZOOM_SDK_KEY & ZOOM_SDK_SECRET env vars")
    print(f"  🛑 Press Ctrl+C to stop")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=port, debug=debug)
