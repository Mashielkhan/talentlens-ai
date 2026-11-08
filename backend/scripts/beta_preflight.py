"""Read-only production dependency checks; does not send email or print secrets."""

import json
import smtplib
import socket
import ssl

from redis import Redis
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.ml.embeddings import embed_sections


def main():
    config = settings()
    if config.environment != "production":
        raise SystemExit("Use the production configuration for beta preflight")
    results = {}
    checks = {
        "database": check_database,
        "redis": check_redis,
        "clamav": check_scanner,
        "smtp": check_smtp,
        "embedding_model": lambda: embed_sections({"skills": "Python FastAPI"}),
    }
    for name, check in checks.items():
        try:
            check()
            results[name] = "ok"
        except Exception as exc:
            results[name] = "failed: " + type(exc).__name__
    print(json.dumps(results, indent=2))
    if any(v != "ok" for v in results.values()):
        raise SystemExit(1)


def check_database():
    with engine.connect() as conn:
        if conn.scalar(text("SELECT version_num FROM alembic_version")) != "0002":
            raise ValueError("Migration required")
        conn.execute(text("SELECT '[1,0,0]'::vector"))


def check_redis():
    with Redis.from_url(settings().redis_url, socket_connect_timeout=5, socket_timeout=5) as client:
        client.ping()


def check_scanner():
    with socket.create_connection((settings().clamav_host, settings().clamav_port), timeout=10) as client:
        client.sendall(b"zPING\0")
        if not client.recv(128).startswith(b"PONG"):
            raise ValueError("Scanner unavailable")


def check_smtp():
    config = settings()
    cls = smtplib.SMTP_SSL if config.smtp_security == "ssl" else smtplib.SMTP
    kwargs = {"context": ssl.create_default_context()} if config.smtp_security == "ssl" else {}
    with cls(config.smtp_host, config.smtp_port, timeout=15, **kwargs) as client:
        if config.smtp_security == "starttls":
            client.starttls(context=ssl.create_default_context())
        if config.smtp_username:
            client.login(config.smtp_username, config.smtp_password)
        client.noop()


if __name__ == "__main__":
    main()
