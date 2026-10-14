"""IntelliOps AI: local-first incident triage demo. Python 3.11+, zero dependencies."""
from __future__ import annotations
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
DB = Path(os.environ.get("INTELLIOPS_DB", str(BASE / "data" / "incidents.sqlite3")))
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
MAX_BYTES = 16_384
SIGNALS = {
    "critical": ("data breach", "ransomware", "production down", "all users", "payment outage"),
    "high": ("timeout", "unavailable", "500 error", "failed deployment", "database down"),
    "medium": ("slow", "latency", "error", "retry", "failed", "degraded"),
}

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, description TEXT NOT NULL,
        service TEXT NOT NULL, severity TEXT NOT NULL,
        explanation TEXT NOT NULL, recommendation TEXT NOT NULL,
        created_at TEXT NOT NULL)""")
    con.commit()
    return con

def analyze(title, description):
    text = (title + " " + description).casefold()
    severity = "low"
    matches = []
    for level, terms in SIGNALS.items():
        found = [word for word in terms if word in text]
        if found:
            severity, matches = level, found
            break
    explanation = ("Matched signals: " + ", ".join(matches) if matches
                   else "No defined high-risk signals found; manual triage is still required.")
    advice = {
        "critical": "Page the on-call lead, activate the incident process, and validate customer impact.",
        "high": "Escalate to on-call engineering, inspect recent changes and service logs.",
        "medium": "Inspect metrics, logs and recent releases; assign an owner and monitor.",
        "low": "Document the report, reproduce the issue, and schedule follow-up triage.",
    }[severity]
    return severity, explanation, advice

def validate(data):
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    out = {}
    for field, limit in (("title", 120), ("description", 2000), ("service", 80)):
        value = data.get(field, "")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required")
        value = value.strip()
        if len(value) > limit:
            raise ValueError(f"{field} must be at most {limit} characters")
        out[field] = value
    return out

def create_incident(data):
    item = validate(data)
    level, explanation, advice = analyze(item["title"], item["description"])
    stamp = datetime.now(timezone.utc).isoformat()
    with connect() as con:
        cur = con.execute("""INSERT INTO incidents
            (title,description,service,severity,explanation,recommendation,created_at)
            VALUES (?,?,?,?,?,?,?)""",
            (item["title"],item["description"],item["service"],level,explanation,advice,stamp))
        ident = cur.lastrowid
        row = con.execute("SELECT * FROM incidents WHERE id=?", (ident,)).fetchone()
    return dict(row)

def list_incidents(severity=None):
    if severity and severity not in (*SIGNALS.keys(), "low"):
        raise ValueError("Invalid severity filter")
    with connect() as con:
        rows = con.execute("SELECT * FROM incidents WHERE severity=? ORDER BY id DESC LIMIT 100", (severity,)).fetchall() if severity else con.execute("SELECT * FROM incidents ORDER BY id DESC LIMIT 100").fetchall()
    return [dict(r) for r in rows]

class Handler(BaseHTTPRequestHandler):
    def respond(self, code, payload):
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return self.respond(200, {"status":"ok", "database":"sqlite"})
        if path == "/api/incidents":
            try:
                from urllib.parse import parse_qs
                level = parse_qs(urlparse(self.path).query).get("severity", [None])[0]
                return self.respond(200, {"items": list_incidents(level)})
            except ValueError as exc:
                return self.respond(400, {"error":str(exc)})
        if path in ("/", "/index.html", "/style.css", "/main.js"):
            name = "index.html" if path == "/" else path.lstrip("/")
            file = BASE / "web" / name
            if not file.is_file():
                return self.respond(404, {"error":"Not found"})
            raw = file.read_bytes()
            mime = {".html":"text/html", ".css":"text/css", ".js":"application/javascript"}[file.suffix]
            self.send_response(200)
            self.send_header("Content-Type", mime + "; charset=utf-8")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        self.respond(404, {"error":"Not found"})

    def do_POST(self):
        if urlparse(self.path).path != "/api/incidents":
            return self.respond(404, {"error":"Not found"})
        try:
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                return self.respond(415, {"error":"Use application/json"})
            count = int(self.headers.get("Content-Length", "0"))
            if count < 1 or count > MAX_BYTES:
                return self.respond(413, {"error":"Invalid or oversized request"})
            data = json.loads(self.rfile.read(count))
            return self.respond(201, create_incident(data))
        except (ValueError, json.JSONDecodeError) as exc:
            self.respond(400, {"error":str(exc)})

if __name__ == "__main__":
    connect().close()
    print(f"IntelliOps AI at http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
