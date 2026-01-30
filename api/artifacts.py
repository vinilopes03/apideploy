"""
Utility functions to download artifacts from Celery.
"""
import os
import httpx

from typing import Dict, List
import os
import httpx


def download_artifacts(manifest: dict, workdir: str) -> Dict[str, List[str]]:
    """
    Downloads all artifacts to workdir/<type>/filename and returns local paths per type.
    :param manifest: Artifact manifest.
    :param workdir: Working directory.
    :return: Dictionary of local paths per type.
    """
    out: Dict[str, List[str]] = {}
    with httpx.Client(timeout=300.0, follow_redirects=True) as client:
        for art_type, items in (manifest or {}).items():
            type_dir = os.path.join(workdir, art_type)
            os.makedirs(type_dir, exist_ok=True)
            out.setdefault(art_type, [])
            for a in items:
                filename = a["filename"]
                url = a["download_url"]
                dst = os.path.join(type_dir, filename)
                with client.stream("GET", url) as r:
                    r.raise_for_status()
                    with open(dst, "wb") as f:
                        for chunk in r.iter_bytes():
                            f.write(chunk)
                out[art_type].append(dst)
    return out
