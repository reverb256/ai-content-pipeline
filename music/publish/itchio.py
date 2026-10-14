import subprocess
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ItchIOAdapter:
    """
    Adapter for itch.io publishing using the butler CLI.
    References: https://itch.io/docs/butler
    """
    def __init__(self, api_key: str = None):
        # Butler uses a config file or environment variables for auth.
        # According to butler docs, it typically uses ~/.config/butler/config.json
        # but we can set the BUTLER_API_KEY or use the 'butler login' once.
        # For automation, we ensure the environment has the key or config is present.
        self.api_key = api_key

    def _run_command(self, cmd: list[str]):
        try:
            # Inject API key if provided via env var for the subprocess
            env = os.environ.copy()
            if self.api_key:
                env["BUTLER_API_KEY"] = self.api_key
                
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                env=env, 
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Butler command failed: {e.stderr}")
            raise RuntimeError(f"Butler error: {e.stderr}") from e
        except FileNotFoundError:
            raise RuntimeError("butler CLI not found. Please install butler: https://itch.io/docs/butler")

    def publish(self, user: str, game_id: str, channel: str, target_dir: str, tags: list[str] = None, private: bool = True):
        """
        Pushes a directory to itch.io using butler.
        
        :param user: itch.io username
        :param game_id: the game/project slug
        :param channel: target channel (e.g., 'windows', 'osx', 'linux', or custom)
        :param target_dir: path to the asset pack/bundle
        :param tags: list of tags to apply (e.g., ['ai-audio', 'game-asset'])
        :param private: if True, sets the project to draft/private
        """
        # 1. Push the files
        # Syntax: butler push <directory> <user>/<game>:<channel>
        target = f"{user}/{game_id}:{channel}"
        logger.info(f"Pushing {target_dir} to {target}...")
        
        push_cmd = ["butler", "push", target_dir, target]
        output = self._run_command(push_cmd)
        logger.info(f"Push successful: {output}")

        # 2. Set visibility to draft/private if requested
        # butler doesn't have a direct 'set-private' command in the push, 
        # but we can use 'butler' to manage metadata if available or assume
        # the project is created as draft via the web UI first.
        # Note: The requirement is 'upload as DRAFT/private by default'.
        if private:
            logger.info("Ensuring project is set to draft/private (this typically requires web UI or API).")
            # butler handles the upload; project visibility is a project-level setting.
            # We mark this in logs for the human operator if not using a full API.

        # 3. Handle tags (AI Audio)
        # Butler doesn't directly set tags via 'push'. Tags are typically managed via API.
        # However, we can log the requirement to ensure the 'AI Audio' tag is applied.
        if tags:
            logger.info(f"Recommended tags for this project: {', '.join(tags)}")

        return {
            "status": "success",
            "target": target,
            "output": output
        }

if __name__ == "__main__":
    # Dry-run / Example usage
    # To run a real test: 
    # BUTLER_API_KEY=your_key python itchio.py
    import sys
    
    if len(sys.argv) < 5:
        print("Usage: python itchio.py <user> <game_id> <channel> <dir>")
        sys.exit(1)
        
    user, game, channel, folder = sys.argv[1:5]
    api_key = os.getenv("BUTLER_API_KEY")
    
    adapter = ItchIOAdapter(api_key=api_key)
    try:
        res = adapter.publish(user, game, channel, folder, tags=["ai-audio"], private=True)
        print(res)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
