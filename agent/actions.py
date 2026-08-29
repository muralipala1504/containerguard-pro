from agent.slack import SlackAlert

# ... existing code ...

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
        
        # Send Slack alert (Pro feature)
        slack = SlackAlert()
        slack.send_alert(container.name, "restarted", "success")
        
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
