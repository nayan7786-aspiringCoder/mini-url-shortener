#!/usr/bin/env python3
"""
Mini URL Shortener - Flask Web Application
Track B: 2nd Year (Flask Web App) & Deployment Ready

Run locally:
    python app.py
Accessible at:
    http://localhost:5000
"""

import os
from flask import Flask, render_template, request, redirect, jsonify, url_for
from storage import Storage
from shortener import URLShortenerService

app = Flask(__name__)

# Initialize persistence and service
DB_PATH = os.environ.get("DB_PATH", "urls.db")
storage = Storage(db_path=DB_PATH)
service = URLShortenerService(storage)


@app.route("/", methods=["GET"])
def index():
    urls = service.list_urls(sort_by="created_at", descending=True)
    return render_template("index.html", urls=urls)


@app.route("/shorten", methods=["POST"])
def shorten():
    original_url = request.form.get("url", "").strip()
    alias = request.form.get("alias", "").strip() or None

    success, code, message = service.shorten(original_url, custom_alias=alias)
    urls = service.list_urls(sort_by="created_at", descending=True)

    short_url = None
    if success:
        # Build absolute short URL
        base_url = request.host_url.rstrip("/")
        short_url = f"{base_url}/{code}"

    return render_template(
        "index.html",
        urls=urls,
        success=success,
        message=message,
        short_url=short_url,
        code=code,
    )


@app.route("/<short_code>", methods=["GET"])
def resolve_and_redirect(short_code):
    success, original_url, _ = service.resolve(short_code, increment_clicks=True)
    if success and original_url:
        return redirect(original_url, code=302)
    return render_template("index.html", urls=service.list_urls(), success=False, message=f"Short code '{short_code}' not found."), 404


@app.route("/api/shorten", methods=["POST"])
def api_shorten():
    data = request.get_json(force=True, silent=True) or {}
    original_url = data.get("url", "").strip()
    alias = data.get("alias", "").strip() or None

    success, code, message = service.shorten(original_url, custom_alias=alias)
    if success:
        base_url = request.host_url.rstrip("/")
        return jsonify({
            "success": True,
            "code": code,
            "short_url": f"{base_url}/{code}",
            "original_url": original_url,
        }), 201
    return jsonify({"success": False, "error": message}), 400


@app.route("/api/stats/<short_code>", methods=["GET"])
def api_stats(short_code):
    success, stats, message = service.get_stats(short_code)
    if success and stats:
        return jsonify({"success": True, "stats": stats})
    return jsonify({"success": False, "error": message}), 404


@app.route("/api/urls", methods=["GET"])
def api_urls():
    urls = service.list_urls()
    return jsonify({"success": True, "count": len(urls), "urls": urls})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
