
import json, os, zipfile, hashlib, threading, io

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.environ.get('APK_DB_FILE', os.path.join(THIS_DIR, 'signatures.json'))
_db_lock = threading.Lock()

def extract_signature(apk_path: str) -> str | None:

    try:
        with zipfile.ZipFile(apk_path, 'r') as apk:
            cert_files = [f for f in apk.namelist() if f.startswith('META-INF/') and (f.endswith('.RSA') or f.endswith('.DSA'))]
            if cert_files:
                cert_bytes = apk.read(cert_files[0])
                return hashlib.sha256(cert_bytes).hexdigest()
        
        with open(apk_path, 'rb') as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except Exception as e:
        
        return None

def db_read() -> dict:
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def db_write(d: dict) -> None:
    with _db_lock:
        tmp = DB_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        os.replace(tmp, DB_FILE)

def db_put(label: str, signature: str) -> None:
    d = db_read()
    d[label] = signature
    db_write(d)

def db_delete(label: str) -> bool:
    d = db_read()
    if label in d:
        del d[label]
        db_write(d)
        return True
    return False

def check_apk_against_db(apk_path: str) -> dict:
    sig = extract_signature(apk_path)
    if not sig:
        return {'genuine': False, 'reason': 'no_signature', 'match_label': None, 'signature': None}
    d = db_read()
    for label, known_sig in d.items():
        if sig == known_sig:
            return {'genuine': True, 'reason': 'match', 'match_label': label, 'signature': sig}
    return {'genuine': False, 'reason': 'no_match', 'match_label': None, 'signature': sig}
