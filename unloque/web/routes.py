import os
import json
import time
import queue
import threading
from typing import List
from flask import Blueprint, render_template, request, jsonify, Response, current_app
from werkzeug.utils import secure_filename
from unloque.core.engine import ZipEngine
from unloque.core.analyzer import analyze_zip
from unloque.core.profiler import generate_profile_words
from unloque.core.mutator import mutate_words

web_bp = Blueprint("web", __name__)

class ActiveJobManager:
    def __init__(self):
        self.engine = None
        self.event_queue = queue.Queue()
        self.thread = None
        self.status = "idle"
        self.lock = threading.RLock()
        self.current_job_id = None

    def start(self, zip_path: str, wordlist_target, workers: int = None, use_mutations: bool = False):
        with self.lock:
            self.stop()
            self.event_queue = queue.Queue()
            self.engine = ZipEngine(zip_path)
            self.status = "running"
            self.current_job_id = f"job_{int(time.time())}"

            words_source = wordlist_target
            if use_mutations:
                try:
                    loaded = self.engine._load_wordlist(wordlist_target)
                    base_for_mut = loaded[:1000] if len(loaded) > 1000 else loaded
                    words_source = mutate_words(base_for_mut, ["leetspeak", "years", "suffixes", "casing"])
                except Exception:
                    words_source = wordlist_target

            def worker():
                try:
                    for stats in self.engine.crack_generator(words_source, workers=workers, chunk_size=20):
                        payload = {
                            "type": "progress",
                            "tested": stats.tested,
                            "total": stats.total,
                            "rate": round(stats.rate, 1),
                            "percent": round(stats.percent, 1),
                            "elapsed_sec": round(stats.elapsed, 2),
                            "eta_sec": round(stats.eta, 1),
                            "current_password": stats.current_password,
                            "status": stats.status
                        }
                        if stats.found:
                            payload["type"] = "found"
                            payload["password"] = stats.password
                            self.status = "found"
                        elif stats.status == "exhausted":
                            payload["type"] = "finished"
                            payload["found"] = False
                            payload["total_tested"] = stats.tested
                            payload["elapsed_sec"] = round(stats.elapsed, 2)
                            self.status = "finished"
                        elif stats.status == "stopped":
                            payload["type"] = "stopped"
                            payload["total_tested"] = stats.tested
                            payload["elapsed_sec"] = round(stats.elapsed, 2)
                            self.status = "stopped"

                        self.event_queue.put(payload)
                        if stats.found or stats.status in ("exhausted", "stopped", "error"):
                            break
                        time.sleep(0.015)
                except Exception as e:
                    self.status = "error"
                    self.event_queue.put({"type": "error", "message": str(e)})

            self.thread = threading.Thread(target=worker, daemon=True)
            self.thread.start()
            return self.current_job_id

    def pause(self):
        with self.lock:
            if self.engine:
                self.engine.pause()
                self.status = "paused"
                self.event_queue.put({"type": "status_change", "status": "paused"})

    def resume(self):
        with self.lock:
            if self.engine:
                self.engine.resume()
                self.status = "running"
                self.event_queue.put({"type": "status_change", "status": "running"})

    def stop(self):
        with self.lock:
            if self.engine:
                self.engine.stop()
                self.status = "stopped"

job_manager = ActiveJobManager()

@web_bp.route("/")
def index():
    return render_template("index.html")

@web_bp.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "Nenhum arquivo enviado."}), 400
    
    file = request.files["file"]
    if not file.filename:
        return jsonify({"status": "error", "message": "Nome de arquivo vazio."}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".zip", ".txt"]:
        return jsonify({"status": "error", "message": "Extensão de arquivo não permitida. Apenas .zip e .txt são suportados."}), 400

    upload_folder = current_app.config.get("UPLOAD_FOLDER", os.path.join(os.getcwd(), "uploads"))
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    return jsonify({
        "status": "success",
        "filepath": filepath,
        "filename": filename,
        "size_bytes": os.path.getsize(filepath)
    })

@web_bp.route("/api/audit", methods=["POST"])
def audit_zip():
    data = request.get_json() or {}
    filepath = data.get("filepath")
    if not filepath or not os.path.exists(filepath):
        return jsonify({"status": "error", "message": "Caminho do arquivo inválido ou não encontrado."}), 400

    try:
        result = analyze_zip(filepath)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@web_bp.route("/api/crack/start", methods=["POST"])
def crack_start():
    data = request.get_json() or {}
    zip_path = data.get("zip_path")
    wordlist_path = data.get("wordlist_path")
    custom_words = data.get("custom_words")
    use_mutations = bool(data.get("use_mutations", False))
    workers = data.get("workers")

    if not zip_path or not os.path.exists(zip_path):
        return jsonify({"status": "error", "message": "Arquivo ZIP inválido ou não encontrado."}), 400

    target_words = None
    if custom_words and isinstance(custom_words, list) and len(custom_words) > 0:
        target_words = custom_words
    elif wordlist_path and os.path.exists(wordlist_path):
        target_words = wordlist_path
    else:
        repo_wordlists = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "wordlists")
        if os.path.exists(repo_wordlists):
            target_words = repo_wordlists
        elif wordlist_path and os.path.exists(wordlist_path):
            target_words = wordlist_path
        else:
            target_words = "wordlists"

    job_id = job_manager.start(
        zip_path=zip_path,
        wordlist_target=target_words,
        workers=workers,
        use_mutations=use_mutations
    )
    return jsonify({"status": "started", "job_id": job_id})

@web_bp.route("/api/crack/pause", methods=["POST"])
def crack_pause():
    job_manager.pause()
    return jsonify({"status": "paused"})

@web_bp.route("/api/crack/resume", methods=["POST"])
def crack_resume():
    job_manager.resume()
    return jsonify({"status": "resumed"})

@web_bp.route("/api/crack/stop", methods=["POST"])
def crack_stop():
    job_manager.stop()
    return jsonify({"status": "stopped"})

@web_bp.route("/api/crack/events")
def crack_events():
    def event_stream():
        while True:
            try:
                event_data = job_manager.event_queue.get(timeout=1.0)
                yield f"data: {json.dumps(event_data)}\n\n"
                if event_data.get("type") in ("found", "finished", "stopped", "error"):
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")

@web_bp.route("/api/profile/generate", methods=["POST"])
def profile_generate():
    data = request.get_json() or {}
    name = data.get("name", "")
    surname = data.get("surname", "")
    birth_year = str(data.get("birth_year", ""))
    keywords = data.get("keywords", [])

    words = generate_profile_words(name=name, surname=surname, birth_year=birth_year, keywords=keywords)
    return jsonify({
        "status": "success",
        "total_generated": len(words),
        "words": words
    })

@web_bp.route("/api/mutate/generate", methods=["POST"])
def mutate_generate():
    data = request.get_json() or {}
    base_words = data.get("base_words", [])
    rules = data.get("rules", ["leetspeak", "years", "suffixes"])

    if isinstance(base_words, str):
        base_words = [w.strip() for w in base_words.split("\n") if w.strip()]

    words = mutate_words(base_words=base_words, rules=rules)
    return jsonify({
        "status": "success",
        "total_generated": len(words),
        "words": words
    })

@web_bp.route("/api/wordlists", methods=["GET"])
def list_wordlists():
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    wordlists_dir = os.path.join(repo_root, "wordlists")
    result = []

    if os.path.exists(wordlists_dir):
        for item in sorted(os.listdir(wordlists_dir)):
            if item.endswith(".txt"):
                fpath = os.path.join(wordlists_dir, item)
                size_bytes = os.path.getsize(fpath)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        lines_count = sum(1 for line in f if line.strip())
                except Exception:
                    lines_count = 0

                result.append({
                    "filename": item,
                    "filepath": fpath,
                    "size_bytes": size_bytes,
                    "lines_count": lines_count
                })

    return jsonify({"status": "success", "wordlists": result})

@web_bp.route("/api/examples", methods=["GET"])
def list_examples():
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    examples_dir = os.path.join(repo_root, "examples")
    result = []

    if os.path.exists(examples_dir):
        for item in sorted(os.listdir(examples_dir)):
            if item.endswith(".zip"):
                fpath = os.path.join(examples_dir, item)
                result.append({
                    "filename": item,
                    "filepath": fpath,
                    "size_bytes": os.path.getsize(fpath)
                })

    return jsonify({"status": "success", "examples": result})

@web_bp.route("/api/save-custom-wordlist", methods=["POST"])
def save_custom_wordlist():
    data = request.get_json() or {}
    words: List[str] = data.get("words", [])
    filename = secure_filename(data.get("filename", "wordlist_customizada.txt"))
    if not filename.endswith(".txt"):
        filename += ".txt"

    upload_folder = current_app.config.get("UPLOAD_FOLDER", os.path.join(os.getcwd(), "uploads"))
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        for w in words:
            f.write(f"{w}\n")

    return jsonify({
        "status": "success",
        "filepath": filepath,
        "filename": filename,
        "total_words": len(words),
        "size_bytes": os.path.getsize(filepath)
    })
