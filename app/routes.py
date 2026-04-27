from flask import Blueprint, jsonify

main = Blueprint("main", __name__)

@main.route("/")
def index():
    return jsonify({"status": "ok", "message": "Data-Forge is running"})

@main.route("/health")
def health():
    return jsonify({"status": "healthy"})
