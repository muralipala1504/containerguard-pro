"""
ContainerGuard Pro - Auto-Cleanup
"""

import docker
import logging

logger = logging.getLogger(__name__)

class AutoCleanup:
    def __init__(self, client):
        self.client = client
        self.cleaned = {"images": 0, "volumes": 0, "build_cache": 0}
    
    def cleanup_unused_images(self):
        try:
            images = self.client.images.list(filters={"dangling": True})
            for image in images:
                image.remove()
                self.cleaned["images"] += 1
            logger.info(f"🗑️ Removed {self.cleaned['images']} unused images")
            return self.cleaned["images"]
        except Exception as e:
            logger.error(f"❌ Image cleanup failed: {e}")
            return 0
    
    def cleanup_dangling_volumes(self):
        try:
            volumes = self.client.volumes.list(filters={"dangling": True})
            for volume in volumes:
                volume.remove()
                self.cleaned["volumes"] += 1
            logger.info(f"🗑️ Removed {self.cleaned['volumes']} dangling volumes")
            return self.cleaned["volumes"]
        except Exception as e:
            logger.error(f"❌ Volume cleanup failed: {e}")
            return 0
    
    def run_cleanup(self):
        logger.info("🧹 Starting auto-cleanup...")
        images = self.cleanup_unused_images()
        volumes = self.cleanup_dangling_volumes()
        logger.info(f"✅ Cleanup complete: {images} images, {volumes} volumes")
        return self.cleaned
