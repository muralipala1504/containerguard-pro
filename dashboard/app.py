import sys
import os
import gradio as gr
import docker
import json
import time
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import log_action, get_audit_logs, export_audit_logs_json, export_audit_logs_csv

def load_hosts():
    """Load hosts from config file"""
    config_file = "/etc/containerguard/hosts.conf"
    default_hosts = [{"name": "default", "host": "unix:///var/run/docker.sock"}]
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('hosts', default_hosts)
        except:
            return default_hosts
    return default_hosts

def get_container_status(host_name, host_url):
    """Get containers from a specific host"""
    try:
        client = docker.DockerClient(base_url=host_url)
        containers = client.containers.list(all=True)
        result = []
        for c in containers:
            result.append({
                "host": host_name,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else "unknown",
                "id": c.id[:12]
            })
        return result
    except Exception as e:
        return [{"host": host_name, "name": "Error", "status": str(e), "image": "", "id": ""}]

def auto_heal_on_host(host_name, host_url):
    """Auto-heal containers on a specific host"""
    actions = []
    try:
        client = docker.DockerClient(base_url=host_url)
        containers = client.containers.list(all=True)
        for c in containers:
            if c.status == "exited":
                c.start()
                log_action("system", "auto-heal", f"{host_name}:{c.name}", "Container auto-restarted", "success")
                actions.append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "host": host_name,
                    "container": c.name,
                    "action": "restarted"
                })
    except Exception as e:
        return [{"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "host": host_name, "container": "error", "action": str(e)}]
    return actions

def refresh():
    hosts = load_hosts()
    all_containers = []
    all_actions = []
    
    for host in hosts:
        # Auto-heal first
        heal_actions = auto_heal_on_host(host['name'], host['host'])
        all_actions.extend(heal_actions)
        
        # Get containers
        containers = get_container_status(host['name'], host['host'])
        all_containers.extend(containers)
    
    # Build node text
    node_text = "## 🖥️ Nodes\n\n"
    for host in hosts:
        node_text += f"✅ {host['name']}: Connected\n"
    
    # Build container text
    pod_text = "## 📦 Containers\n\n"
    for c in all_containers:
        icon = "🟢" if c["status"] == "running" else ("🟡" if c["status"] == "restarted" else "🔴")
        pod_text += f"{icon} **{c['host']}** — {c['name']}: {c['status']} ({c['image']})\n"
    
    # Build history text
    audit_logs = get_audit_logs(10)
    history_text = "## 📜 Recent Actions\n\n"
    if audit_logs:
        for log in audit_logs[-10:]:
            history_text += f"**{log['timestamp']}** — {log['user']} — {log['action']} {log['resource']} — {log['status']}\n"
    else:
        history_text += "No actions recorded yet."
    
    return node_text, pod_text, history_text

def restart_container(name):
    hosts = load_hosts()
    for host in hosts:
        try:
            client = docker.DockerClient(base_url=host['host'])
            container = client.containers.get(name)
            container.restart()
            log_action("user", "restart", f"{host['name']}:{name}", "Container restarted manually", "success")
            return f"✅ Restarted {name} on {host['name']}"
        except:
            continue
    return f"❌ Container {name} not found on any host"

def export_json():
    return export_audit_logs_json()

def export_csv():
    return export_audit_logs_csv()

# Build the UI
with gr.Blocks(theme=gr.themes.Soft(), title="ContainerGuard") as demo:
    gr.Markdown("# 🌐 ContainerGuard Dashboard")
    gr.Markdown("Auto-heal · Monitor · Optimize · Multi-Host")
    
    with gr.Row():
        refresh_btn = gr.Button("🔄 Refresh")
    
    with gr.Row():
        with gr.Column(scale=1):
            nodes_output = gr.Markdown("Loading...")
        with gr.Column(scale=2):
            pods_output = gr.Markdown("Loading...")
    
    with gr.Row():
        history_output = gr.Markdown("Loading...")
    
    with gr.Row():
        container_name = gr.Textbox(label="Container Name", placeholder="e.g., test-nginx")
        restart_btn = gr.Button("🔄 Restart Container")
        restart_result = gr.Textbox(label="Result", interactive=False)
    
    with gr.Row():
        export_json_btn = gr.Button("📥 Export JSON")
        export_csv_btn = gr.Button("📥 Export CSV")
        export_output = gr.Textbox(label="Exported Data", interactive=False, lines=5)
    
    refresh_btn.click(refresh, outputs=[nodes_output, pods_output, history_output])
    restart_btn.click(restart_container, inputs=[container_name], outputs=[restart_result])
    export_json_btn.click(export_json, outputs=[export_output])
    export_csv_btn.click(export_csv, outputs=[export_output])
    demo.load(refresh, outputs=[nodes_output, pods_output, history_output])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
