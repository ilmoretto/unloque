import os
import json
import time
import queue
import threading
from flask import Blueprint, render_template, request, jsonify, Response, current_app
from werkzeug.utils import secure_filename
from unloque.core.engine import ZipEngine

web_bp = Blueprint("web", __name__)

class ActiveJobManager:
    def __init__(self):
        self.engine = None
        self.event_queue = queue.Queue()
        self.thread = None
        self.status = "idle"
        self.lock = threading.Lock()

    def start(self, zip_path: str, wordlist_target: str, workers: int = None):
        with self.lock:
            self.stop()
            self.event_queue = queue.Queue()
            self.engine = ZipEngine(zip_path)
            self.status = "running"

            def worker():
                try:
                    for stats in self.engine.crack_generator(wordlist_target, workers=workers, chunk_size=20):
                        payload = {
                            "type": "progress",
                            "tested": stats.tested,
                            "total": stats.total,
                            "rate": round(stats.rate, 1),
                            "percent": round(stats.percent, 1),
                            "elapsed": round(stats.elapsed, 2),
                            "eta": round(stats.eta, 1),
                            "status": stats.status
                        }
                        if stats.found:
                            payload["type"] = "found"
                            payload["password"] = stats.password
                        elif stats.status == "exhausted":
                            payload["type"] = "finished"
                            payload["found"] = False
                        elif stats.status == "stopped":
                            payload["type"] = "stopped"

                        self.event_queue.put(payload)
                        if stats.found or stats.status in ("exhausted", "stopped", "error"):
                            break
                        time.sleep(0.02)
                except Exception as e:
                    self.event_queue.put({"type": "error", "message": str(e)})

            self.thread = threading.Thread(target=worker, daemon=True)
            self.thread.start()

    def pause(self):
        if self.engine:
            self.engine.pause()
            self.status = "paused"

    def resume(self):
        if self.engine:
            self.engine.resume()
            self.status = "running"

    def stop(self):
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
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "/tmp")
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    return jsonify({
        "status": "success",
        "filepath": filepath,
        "filename": filename,
        "size_bytes": os.path.getsize(filepath)
    })

@web_bp.route("/api/crack/start", methods=["POST"])
def crack_start():
    data = request.get_json() or {}
    zip_path = data.get("zip_path")
    wordlist_path = data.get("wordlist_path") or "wordlists"

    if not zip_path or not os.path.exists(zip_path):
        return jsonify({"status": "error", "message": "Arquivo ZIP inválido ou não encontrado."}), 400

    job_manager.start(zip_path, wordlist_path, workers=data.get("workers"))
    return jsonify({"status": "started", "job_id": "job_active"})

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
