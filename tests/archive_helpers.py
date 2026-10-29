"""Small compressed archives exercising shared tar safety rejections."""

import gzip
import io
import tarfile


def tar_safety_archive(kind: str) -> bytes:
    if kind in ("stream", "metadata"):
        size = 4096 if kind == "stream" else 65537
        prefix = f"{size} comment=".encode()
        payload = prefix + b"x" * (size - len(prefix) - 1) + b"\n"
        info = tarfile.TarInfo("metadata")
        info.type = tarfile.XHDTYPE
        info.size = size
        plain = info.tobuf() + payload + b"\0" * (-size % tarfile.BLOCKSIZE)
        plain += tarfile.TarInfo("file.txt").tobuf()
    elif kind == "gnu-sparse":
        info = tarfile.TarInfo("file.txt")
        info.type = tarfile.GNUTYPE_SPARSE
        header = bytearray(info.tobuf(format=tarfile.GNU_FORMAT))
        header[482] = 1  # The old GNU format stores map extensions after this header.
        header[483:495] = tarfile.itn(2, 12)
        header[148:156] = b" " * 8
        header[148:156] = f"{sum(header):06o}\0 ".encode()
        blocks = []
        for index in range(160):
            block = bytearray(tarfile.BLOCKSIZE)
            for entry in range(21):
                offset = entry * 24
                block[offset:offset + 24] = tarfile.itn(1, 12) * 2
            block[504] = int(index < 159)
            blocks.append(bytes(block))
        plain = bytes(header) + b"".join(blocks)
    elif kind == "pax-sparse-1.0":
        sparse_map = (b"20000\n" + b"1\n1\n" * 20000)
        payload = sparse_map.ljust(
            (len(sparse_map) + 511) // 512 * 512, b"\0"
        )
        info = tarfile.TarInfo("file.txt")
        info.size = len(payload)
        info.pax_headers = {
            "GNU.sparse.major": "1",
            "GNU.sparse.minor": "0",
            "GNU.sparse.realsize": "2",
        }
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
            archive.addfile(info, io.BytesIO(payload))
        plain = buffer.getvalue()
    else:
        raise ValueError(f"Unknown test archive kind: {kind}")
    return gzip.compress(plain + b"\0" * tarfile.BLOCKSIZE)
