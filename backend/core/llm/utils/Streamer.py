import json
import uuid
import asyncio
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from typing import Dict, List, Optional, Any

class Streamer:
    """
    A class for streaming thoughts and other data to the frontend via WebSockets.
    """
    
    def __init__(self, report_id: Optional[int] = None, channel_prefix: Optional[str] = None):
        """
        Initialize the Streamer with a report ID and optional channel prefix.
        
        Args:
            report_id: The ID of the report to stream thoughts for
            channel_prefix: Optional prefix for custom channel names
        """
        self.report_id = report_id
        self.channel_prefix = channel_prefix
        self.channel_layer = get_channel_layer()
        self.stream_id = str(uuid.uuid4())
        
    def get_channel_name(self, channel_type: str = "thoughts") -> str:
        """
        Generate a channel name based on the report ID and stream ID.
        
        Args:
            channel_type: The type of channel (e.g., "thoughts", "report", "status")
            
        Returns:
            A channel name string
        """
        if self.channel_prefix:
            return f"{self.channel_prefix}_{channel_type}_{self.stream_id}"
        elif self.report_id:
            return f"report_{self.report_id}_{channel_type}_{self.stream_id}"
        else:
            return f"stream_{channel_type}_{self.stream_id}"
    
    def stream_thought(self, thought: str) -> None:
        """
        Stream a thought to the frontend.
        
        Args:
            thought: The thought to stream
        """
        channel_name = self.get_channel_name("thoughts")
        message = {
            "type": "stream_thought",
            "thought": thought,
            "stream_id": self.stream_id
        }

        # print(f"Streaming thought: {message}")
        
        async_to_sync(self.channel_layer.group_send)(
            channel_name,
            {
                "type": "stream_message",
                "message": json.dumps(message)
            }
        )
    
    async def stream_thought_async(self, thought: str) -> None:
        """
        Asynchronously stream a thought to the frontend.
        
        Args:
            thought: The thought to stream
        """
        channel_name = self.get_channel_name("thoughts")
        message = {
            "type": "stream_thought",
            "thought": thought,
            "stream_id": self.stream_id
        }
        
        await self.channel_layer.group_send(
            channel_name,
            {
                "type": "stream_message",
                "message": json.dumps(message)
            }
        )
    
    def stream_report(self, report_content: str) -> None:
        """
        Stream report content to the frontend.
        
        Args:
            report_content: The report content to stream
        """
        channel_name = self.get_channel_name("report")
        message = {
            "type": "stream_report",
            "content": report_content,
            "stream_id": self.stream_id
        }
        
        async_to_sync(self.channel_layer.group_send)(
            channel_name,
            {
                "type": "stream_message",
                "message": json.dumps(message)
            }
        )
    
    async def stream_report_async(self, report_content: str) -> None:
        """
        Asynchronously stream report content to the frontend.
        
        Args:
            report_content: The report content to stream
        """
        channel_name = self.get_channel_name("report")
        message = {
            "type": "stream_report",
            "content": report_content,
            "stream_id": self.stream_id
        }
        
        await self.channel_layer.group_send(
            channel_name,
            {
                "type": "stream_message",
                "message": json.dumps(message)
            }
        )
    
    def stream_status(self, status: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Stream a status update to the frontend.
        
        Args:
            status: The status to stream (e.g., "started", "completed", "error")
            data: Optional additional data to include
        """
        channel_name = self.get_channel_name("status")
        message = {
            "type": "stream_status",
            "status": status,
            "stream_id": self.stream_id
        }
        
        if data:
            message["data"] = data
        
        async_to_sync(self.channel_layer.group_send)(
            channel_name,
            {
                "type": "stream_message",
                "message": json.dumps(message)
            }
        )
    
    async def stream_status_async(self, status: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Asynchronously stream a status update to the frontend.
        
        Args:
            status: The status to stream (e.g., "started", "completed", "error")
            data: Optional additional data to include
        """
        channel_name = self.get_channel_name("status")
        message = {
            "type": "stream_status",
            "status": status,
            "stream_id": self.stream_id
        }
        
        if data:
            message["data"] = data
        
        await self.channel_layer.group_send(
            channel_name,
            {
                "type": "stream_message",
                "message": json.dumps(message)
            }
        )
    
    def stream_batch(self, thoughts: List[str]) -> None:
        """
        Stream a batch of thoughts to the frontend.
        
        Args:
            thoughts: A list of thoughts to stream
        """
        channel_name = self.get_channel_name("thoughts")
        message = {
            "type": "stream_batch",
            "thoughts": thoughts,
            "stream_id": self.stream_id
        }
        
        async_to_sync(self.channel_layer.group_send)(
            channel_name,
            {
                "type": "stream_message",
                "message": json.dumps(message)
            }
        )
    
    async def stream_batch_async(self, thoughts: List[str]) -> None:
        """
        Asynchronously stream a batch of thoughts to the frontend.
        
        Args:
            thoughts: A list of thoughts to stream
        """
        channel_name = self.get_channel_name("thoughts")
        message = {
            "type": "stream_batch",
            "thoughts": thoughts,
            "stream_id": self.stream_id
        }
        
        await self.channel_layer.group_send(
            channel_name,
            {
                "type": "stream_message",
                "message": json.dumps(message)
            }
        ) 