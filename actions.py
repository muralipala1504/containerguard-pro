import docker
import logging
import json
import os
import sys
from datetime import datetime, timedelta

# Add Pro repo to path if available
PRO_PATH = "/home/ruser/containerguard-pro"
if PRO_PATH not in sys.path and os.path.exists(PRO_PATH):
    sys.path.insert(0, PRO_PATH)

# Import license check (with fallback)
try:
    from license import check_license
    LICENSE_AVAILABLE = True
except ImportError:
    LICENSE_AVAILABLE = False

# Import Pro features (with fallback)
try:
    from pro_agent.slack import SlackAlert
    from pro_agent.cleanup import AutoCleanup
    PRO_AVAILABLE = True
except ImportError:
    PRO_AVAILABLE = False

logger = logging.getLogger(__name__)

class ContainerActions:
    def __init__(self, client):
        self.client = client
        self.history_file = "/tmp/containerguard_history.json"
        self.action_history = self._load_history()
        self.is_pro = False
        
        # Check license if available
        if LICENSE_AVAILABLE:
            self.is_pro = check_license()
        
        # Initialize Pro features
        self.slack = None
        self.cleanup = None
        
        if self.is_pro and PRO_AVAILABLE:
            try:
                self.slack = SlackAlert()
                self.cleanup = AutoCleanup(client)
                logger.info("✅ Pro features enabled: Slack alerts, Auto-cleanup")
            except Exception as e:
                logger.warning(f"⚠️ Pro features initialization failed: {e}")
        else:
            logger.info("ℹ️ Free tier: 7-day history limit, no Pro features")

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _trim_history(self, history):
        if self.is_pro:
            return history
        cutoff = datetime.now() - timedelta(days=7)
        trimmed = []
        for entry in history:
            try:
                entry_time = datetime.fromisoformat(entry['timestamp'])
                if entry_time > cutoff:
                    trimmed.append(entry)
            except (KeyError, ValueError):
                trimmed.append(entry)
        return trimmed

    def _save_history(self):
        try:
            self.action_history = self._trim_history(self.action_history)
            with open(self.history_file, 'w') as f:
                json.dump(self.action_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def restart_container(self, container_id):
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info(f"✅ Restarted container: {container.name}")
            self.action_history.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'restart',
                'container': container.name,
                'status': 'success'
            })
            self._save_history()
            if self.is_pro and self.slack:
                self.slack.send_alert(container.name, "restarted", "success")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to restart {container_id}: {e}")
            self.action_history.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'restart',
                'container': str(container_id),
                'status': 'failed',
                'error': str(e)
            })
            self._save_history()
            return False

    def get_history(self):
        return self.action_history

    def run_cleanup(self):
        """Run auto-cleanup (Pro only)"""
        if self.is_pro and self.cleanup:
            return self.cleanup.run_cleanup()
        elif self.is_pro:
            logger.warning("⚠️ Cleanup module not available. Check Pro repo.")
            return None
        else:
            logger.info("ℹ️ Cleanup requires Pro license")
            return None

    def cleanup_exited_containers(self):
        try:
            exited = self.client.containers.list(all=True, filters={'status': 'exited'})
            removed = []
            for container in exited:
                container.remove()
                removed.append(container.name)
                logger.info(f"🗑️ Removed exited container: {container.name}")
            if removed:
                self.action_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'cleanup',
                    'containers': removed,
                    'status': 'success'
                })
                self._save_history()
            return removed
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return []
