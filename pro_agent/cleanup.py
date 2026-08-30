"""
ContainerGuard Pro - Auto-Cleanup
Removes unused Docker images, volumes, and build cache
"""

import docker
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AutoCleanup:
    def __init__(self, client):
        self.client = client
        self.cleaned = {
            "images": 0,
            "volumes": 0,
            "build_cache": 0,
            "space_freed": 0
        }
    
    def cleanup_unused_images(self):
        """Remove unused Docker images"""
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
        """Remove dangling volumes"""
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
    
    def cleanup_build_cache(self):
        """Remove Docker build cache"""
        try:
            result = self.client.api.prune_builds()
            self.cleaned["build_cache"] = result.get('SpaceReclaimed', 0)
            logger.info(f"🗑️ Freed {self.cleaned['build_cache']} bytes of build cache")
            return self.cleaned["build_cache"]
        except Exception as e:
            logger.error(f"❌ Build cache cleanup failed: {e}")
            return 0
    
    def run_cleanup(self):
        """Run all cleanup operations"""
        logger.info("🧹 Starting auto-cleanup...")
        
        images = self.cleanup_unused_images()
        volumes = self.cleanup_dangling_volumes()
        build_cache = self.cleanup_build_cache()
        
        self.cleaned["space_freed"] = build_cache
        
        logger.info(f"✅ Cleanup complete: {images} images, {volumes} volumes, {build_cache} bytes freed")
        return self.cleaned
