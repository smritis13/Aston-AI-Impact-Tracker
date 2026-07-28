import pusher
from dotenv import load_dotenv

class PusherService:
    def __init__(self):
        import os

        load_dotenv()

        self.pusher_client = None
        app_id = os.getenv('PUSHER_APP_ID')
        key = os.getenv('PUSHER_KEY')
        secret = os.getenv('PUSHER_SECRET')
        cluster = os.getenv('PUSHER_CLUSTER')

        if not all([app_id, key, secret, cluster]):
            print("Pusher is not configured; realtime streaming is disabled.")
            return

        self.pusher_client = pusher.Pusher(
            app_id=app_id,
            key=key,
            secret=secret,
            cluster=cluster,
            ssl=True
        )

    def stream_thought(self, conversation_id: str, thought: str):
        """Stream a thought to the frontend via Pusher."""
        if not self.pusher_client:
            return

        try:
            self.pusher_client.trigger(
                f'conversation-{conversation_id}',
                'stream_thought',
                {'thought': thought}
            )
        except Exception as exc:
            print(f"Pusher stream_thought failed: {exc}")

    def stream_by_key(self, key: str, thought: str, progress: float = None):
        """Stream a thought to the frontend via Pusher using a custom key."""
        if not self.pusher_client:
            return

        # print(f'Streaming to {key} with thought: {thought}')
        # safe_thought = thought.encode("ascii", "backslashreplace").decode()
        try:
            self.pusher_client.trigger(f"stream-{key}", "stream_thought", {"thought": thought, "progress": progress})
        except Exception as exc:
            print(f"Pusher stream_by_key failed: {exc}")
        # self.pusher_client.trigger(
        #     f'stream-{key}',
        #     'stream_thought',
        #     {'thought': thought}
        # ) 
