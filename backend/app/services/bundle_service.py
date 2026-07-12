"""Bundle service — creates and serves ZIP bundles of generated files."""
import logging
import os
import zipfile
from typing import AsyncGenerator, Optional

logger = logging.getLogger(__name__)

BUNDLES_DIR = "data/bundles"


class BundleService:
    """Creates and manages ZIP bundles of generated project files."""

    def __init__(self, bundles_dir: str = BUNDLES_DIR) -> None:
        self.bundles_dir = bundles_dir
        os.makedirs(self.bundles_dir, exist_ok=True)

    async def create_bundle(self, job_id: str, generated_files: dict) -> str:
        """Create a ZIP bundle from generated files and return the file path."""
        zip_path = os.path.join(self.bundles_dir, f"{job_id}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, content in generated_files.items():
                zf.writestr(path, content)
        logger.info("Created bundle: %s (%d files)", zip_path, len(generated_files))
        return zip_path

    def get_bundle_path(self, job_id: str) -> Optional[str]:
        """Return the bundle path if it exists."""
        zip_path = os.path.join(self.bundles_dir, f"{job_id}.zip")
        if os.path.exists(zip_path):
            return zip_path
        return None

    async def stream_bundle(self, job_id: str) -> AsyncGenerator[bytes, None]:
        """Stream bundle bytes in chunks."""
        zip_path = self.get_bundle_path(job_id)
        if zip_path is None:
            return
        chunk_size = 64 * 1024
        with open(zip_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
