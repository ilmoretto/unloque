import os
from flask import Flask

def create_app():
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    from .routes import web_bp
    app.register_blueprint(web_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
