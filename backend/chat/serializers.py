# conversation/views.py (continued)
from rest_framework import generics
from .models import *
from rest_framework import serializers


class ReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reference
        fields = ['id', 'title', 'url', 'file_type', 'server_url']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'text', 'sender', 'timestamp']

class MessageListSerializer(serializers.ModelSerializer):
    # This will include a list of associated references for each message.
    references = ReferenceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'text', 'sender', 'timestamp', 'references']

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageListSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['conversation_id','title', 'created_at', 'messages']
