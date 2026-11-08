import socket
import struct

from fastapi import HTTPException

from app.core.config import settings


def scan_upload(data):
    if settings().upload_scanning == "disabled":
        return
    try:
        with socket.create_connection((settings().clamav_host, settings().clamav_port), timeout=15) as client:
            client.settimeout(30)
            client.sendall(b"zINSTREAM\0")
            for offset in range(0, len(data), 65536):
                chunk = data[offset : offset + 65536]
                client.sendall(struct.pack("!I", len(chunk)) + chunk)
            client.sendall(struct.pack("!I", 0))
            response = b""
            while b"\0" not in response and len(response) < 4096:
                chunk = client.recv(1024)
                if not chunk:
                    break
                response += chunk
        status = response.split(b"\0", 1)[0].strip()
        if status.endswith(b" FOUND"):
            raise HTTPException(422, "The upload was blocked by the malware scanner")
        if status != b"stream: OK":
            raise HTTPException(503, "Upload scanning is unavailable; please try again later")
    except (OSError, TimeoutError) as exc:
        raise HTTPException(503, "Upload scanning is unavailable; please try again later") from exc
