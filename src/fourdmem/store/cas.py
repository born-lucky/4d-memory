"""Git-family loose objects: `{type} {size}\\0` + payload, SHA-256, zlib."""

from __future__ import annotations

import hashlib
import zlib
from pathlib import Path


def payload(kind: str, data: bytes) -> bytes:
    return f"{kind} {len(data)}\0".encode("utf-8") + data


def oid_of(kind: str, data: bytes) -> bytes:
    return hashlib.sha256(payload(kind, data)).digest()


def oid_hex(digest: bytes) -> str:
    return digest.hex()


class CAS:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.objects = self.root / "objects"
        self.objects.mkdir(parents=True, exist_ok=True)

    def _path(self, digest: bytes) -> Path:
        h = oid_hex(digest)
        d = self.objects / h[:2]
        d.mkdir(parents=True, exist_ok=True)
        return d / h[2:]

    def put(self, kind: str, data: bytes) -> bytes:
        digest = oid_of(kind, data)
        path = self._path(digest)
        if not path.exists():
            path.write_bytes(zlib.compress(payload(kind, data), 6))
        return digest

    def get(self, digest: bytes) -> tuple[str, bytes]:
        raw = zlib.decompress(self._path(digest).read_bytes())
        header, body = raw.split(b"\0", 1)
        kind, size_s = header.decode("utf-8").split(" ", 1)
        size = int(size_s)
        if len(body) != size:
            raise ValueError(f"CAS size mismatch for {oid_hex(digest)}")
        return kind, body

    def has(self, digest: bytes) -> bool:
        return self._path(digest).exists()
