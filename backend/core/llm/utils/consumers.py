# core/llm/utils/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.report_id = self.scope['url_route']['kwargs'].get('report_id')
        self.stream_id = self.scope['url_route']['kwargs']['stream_id']
        self.channel_type = self.scope['url_route']['kwargs']['channel_type']
        
        # Get channel prefix from query parameters
        self.channel_prefix = self.scope['query_string'].decode().split('=')[1] if 'channel_prefix=' in self.scope['query_string'].decode() else None
        
        self.group_name = (
            f"{self.channel_prefix}_{self.channel_type}_{self.stream_id}"
            if self.channel_prefix
            else f"report_{self.report_id}_{self.channel_type}_{self.stream_id}"
            if self.report_id
            else f"stream_{self.channel_type}_{self.stream_id}"
        )
        print(f"Connecting to {self.group_name}")  # Debug
        try:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        except Exception as e:
            print(f"Connection failed: {e}")
            await self.close()

    async def disconnect(self, close_code):
        print(f"Disconnected from {self.group_name}")
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def stream_message(self, event):
        print(f"Sending: {event['message']}")
        await self.send(text_data=event['message'])