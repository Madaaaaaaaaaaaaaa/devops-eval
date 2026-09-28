import os
import time

import psycopg
from flask import Flask, Response, jsonify, request
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Gauge,
                               Histogram, generate_latest)

app = Flask(__name__)

REQUESTS = Counter("http_requests_total", "Requêtes reçues",
                   ["endpoint", "code"])
LATENCY = Histogram("http_request_duration_seconds", "Latence des requêtes",
                    ["endpoint"])
VERSION = Gauge("app_version_info", "Version/SHA déployé", ["version"])
VERSION.labels(os.getenv("APP_VERSION", "dev")).set(1)


def get_conn():
    url = os.getenv("DATABASE_URL",
                    "postgresql://app:app@localhost:5432/app")
    return psycopg.connect(url)


@app.before_request
def start_timer():
    request.start_time = time.time()


@app.after_request
def record_metrics(resp):
    endpoint = request.url_rule.rule if request.url_rule else "unknown"
    REQUESTS.labels(endpoint, resp.status_code).inc()
    LATENCY.labels(endpoint).observe(time.time() - request.start_time)
    return resp


@app.get("/health")
def health():
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1")
        return jsonify(status="ok"), 200
    except Exception:
        return jsonify(status="db_down"), 503


@app.post("/visit")
def visit():
    with get_conn() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS visits "
                     "(id SERIAL PRIMARY KEY, ts TIMESTAMP DEFAULT now())")
        conn.execute("INSERT INTO visits DEFAULT VALUES")
        count = conn.execute("SELECT count(*) FROM visits").fetchone()[0]
    return jsonify(visits=count), 201


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
