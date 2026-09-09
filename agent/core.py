import docker
import logging
import os
import sys
import json
from datetime import datetime
from actions import ContainerActions

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(
    handlers=[logging.FileHandler("/var/log/containerguard.log"), logging.StreamHandler()],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContainerGuardAgent:
    """Main agent class with auto-healing for multiple hosts"""
    
    def __init__(self):
        self.clients = []
        self.hosts = self._load_hosts()
        self._connect_to_hosts()
    
    def _load_hosts(self):
        """Load hosts from config file"""
        config_file = "/etc/containerguard/hosts.conf"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('hosts', [])
            except Exception as e:
                logger.warning(f"⚠️ Failed to load hosts config: {e}")
        
        # Fallback: use DOCKER_HOST env var
        docker_host = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")
        return [{"name": "default", "host": docker_host}]
    
    def _connect_to_hosts(self):
        """Connect to all Docker hosts"""
        for host in self.hosts:
            try:
                client = docker.DockerClient(base_url=host['host'])
                version = client.version()['Version']
                self.clients.append({
                    "name": host['name'],
                    "client": client,
                    "host": host['host']
                })
                logger.info(f"✅ Connected to {host['name']} (Docker {version})")
            except Exception as e:
                logger.error(f"❌ Failed to connect to {host['name']}: {e}")
    
    def get_all_containers(self, host=None):
        """Get containers from all hosts or a specific host"""
        containers = []
        for client_info in self.clients:
            if host and client_info['name'] != host:
                continue
            try:
                containers.extend(client_info['client'].containers.list(all=True))
            except Exception as e:
                logger.error(f"Error listing containers on {client_info['name']}: {e}")
        return containers
    
    def check_and_heal(self):
        """Check health and auto-restart exited containers on all hosts"""
        total_restarted = 0
        status_report = []
        
        for client_info in self.clients:
            name = client_info['name']
            client = client_info['client']
            
            try:
                containers = client.containers.list(all=True)
                logger.info(f"Found {len(containers)} containers on {name}")
                
                for container in containers:
                    status = container.status
                    container_name = container.name
                    
                    if status == 'exited':
                        logger.warning(f"⚠️ {container_name} on {name}: EXITED - Attempting restart...")
                        actions = ContainerActions(client)
                        if actions.restart_container(container.id):
                            total_restarted += 1
                            status = 'restarted'
                        else:
                            status = 'exited_failed'
                    elif status == 'running':
                        logger.info(f"✅ {container_name} on {name}: RUNNING")
                    else:
                        logger.info(f"ℹ️ {container_name} on {name}: {status}")
                    
                    status_report.append({'name': container_name, 'status': status, 'host': name})
            except Exception as e:
                logger.error(f"Error checking containers on {name}: {e}")
        
        if total_restarted > 0:
            logger.info(f"🔄 Auto-restarted {total_restarted} container(s) across all hosts")
        
        return status_report, total_restarted
    
    def run_once(self):
        """Run a single monitoring + healing cycle"""
        logger.info("🔍 Starting monitoring + healing cycle...")
        results, restarted = self.check_and_heal()
        logger.info(f"📊 Monitored containers across {len(self.clients)} hosts, restarted {restarted}")
        return results

if __name__ == "__main__":
    logger.info("🚀 ContainerGuard Agent - Multi-Host Mode")
    agent = ContainerGuardAgent()
    results = agent.run_once()
    
    print("\n📋 Container Status Summary:")
    for r in results:
        status_icon = "🔄" if r['status'] == 'restarted' else ("⚠️" if r['status'] == 'exited_failed' else "✅")
        print(f"  {status_icon} {r['name']} ({r['host']}): {r['status']}")
