
import os, tempfile, logging, shutil
from flask import Flask, request, jsonify, send_from_directory, current_app
from flask_cors import CORS
import check as checker

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "apk_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder=THIS_DIR, static_url_path='')
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

@app.route('/')
def root_index():
    return send_from_directory(THIS_DIR, 'index.html')

@app.post('/api/add')
def api_add():
    if 'file' not in request.files:
        logging.debug("missing 'file' in request.files")
        return jsonify(error="missing file"), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify(error="empty filename"), 400
    label = request.form.get('label') or f.filename
    temp_path = os.path.join(UPLOAD_DIR, f.filename)
    try:
        f.save(temp_path)
    except Exception as e:
        logging.exception("failed to save uploaded file")
        return jsonify(error="failed to save file", detail=str(e)), 500
    logging.debug(f"Saved temp file: {temp_path}")
    try:
        sig = checker.extract_signature(temp_path)
        logging.debug(f"Extracted signature: {sig}")
        if not sig:
            return jsonify(error="could not extract signature (no cert and fallback failed)"), 400
        checker.db_put(label, sig)
        logging.debug(f"DB updated with: {label} -> {sig}")
        return jsonify(message="added", label=label, signature=sig)
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass

@app.post('/api/check')
def api_check():
    if 'file' not in request.files:
        return jsonify(error="missing file"), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify(error="empty filename"), 400
    temp_path = os.path.join(UPLOAD_DIR, f.filename)
    try:
        f.save(temp_path)
    except Exception as e:
        logging.exception("failed to save uploaded file for check")
        return jsonify(error="failed to save file", detail=str(e)), 500
    try:
        result = checker.check_apk_against_db(temp_path)
        logging.debug(f"Check result: {result}")
        return jsonify(result)
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass

@app.get('/api/list')
def api_list():
    return jsonify(entries=checker.db_read())

@app.delete('/api/delete/<label>')
def api_delete(label):
    ok = checker.db_delete(label)
    return jsonify(deleted=bool(ok), label=label)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    logging.info(f"Starting server on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
