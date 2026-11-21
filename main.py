"""Copy the front-page image into the competition output folder.

This script is the entrypoint for the make.fun news-image-20261121
submission. All it does is take the already-rendered front page
(entry.png, sitting next to this file), sanity-check that it really
is a valid 1024x1024 PNG under the size cap, and place an exact copy
in the output directory the harness points at. The image covers
Saturday 21 November 2026: 44 verified stories, 11 of them leads.

Standard library only. No network access, no randomness, no
timestamps anywhere in the path. Deterministic by construction:
the bytes written out are exactly the bytes read in, so two runs
always produce the same file.
"""

from __future__ import annotations

import os
import struct
import sys

# The PNG magic bytes every PNG file starts with.
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

EXPECTED_SIDE = 1024
MAX_FILE_BYTES = 1_048_576


def fail(message: str) -> "SystemExit":
    """Print an error to stderr and stop with a non-zero status."""
    print(f"entry check failed: {message}", file=sys.stderr)
    return SystemExit(1)


def check_png(payload: bytes) -> tuple[int, int]:
    """Validate the image bytes and return (width, height)."""
    if len(payload) < len(PNG_MAGIC):
        raise ValueError("file is too short to be a PNG image")

    if payload[: len(PNG_MAGIC)] != PNG_MAGIC:
        raise ValueError("missing PNG signature in the first 8 bytes")

    if len(payload) > MAX_FILE_BYTES:
        raise ValueError(
            f"file is {len(payload)} bytes, over the 1048576 byte limit"
        )

    # Walk to the first chunk header; IHDR must come first.
    offset = len(PNG_MAGIC)
    if len(payload) < offset + 8:
        raise ValueError("file ends before the first chunk header")

    chunk_len = struct.unpack(">I", payload[offset : offset + 4])[0]
    chunk_kind = payload[offset + 4 : offset + 8]
    if chunk_kind != b"IHDR":
        raise ValueError("first chunk is not IHDR; not a well-formed PNG")

    if chunk_len != 13 or len(payload) < offset + 8 + 13:
        raise ValueError("IHDR chunk is truncated")

    width, height = struct.unpack(
        ">II", payload[offset + 8 : offset + 16]
    )
    if (width, height) != (EXPECTED_SIDE, EXPECTED_SIDE):
        raise ValueError(
            f"image is {width}x{height}, expected 1024x1024"
        )
    return width, height


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")

    try:
        with open(source, "rb") as handle:
            payload = handle.read()
    except OSError as exc:
        print(f"entry check failed: cannot read entry.png: {exc}",
              file=sys.stderr)
        return 1

    try:
        check_png(payload)
    except ValueError as exc:
        print(f"entry check failed: {exc}", file=sys.stderr)
        return 1

    target_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    try:
        os.makedirs(target_dir, exist_ok=True)
        destination = os.path.join(target_dir, "entry.png")
        with open(destination, "wb") as handle:
            handle.write(payload)
    except OSError as exc:
        print(f"entry check failed: cannot write output: {exc}",
              file=sys.stderr)
        return 1

    print(f"wrote {len(payload)} bytes to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
