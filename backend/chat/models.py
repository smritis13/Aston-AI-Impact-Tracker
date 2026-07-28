from django.db import models
import uuid

# Create your models here.

class Conversation(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    conversation_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.conversation_id)

class Message(models.Model):
    SENDER_CHOICES = (
        ('user', 'User'),
        ('system', 'System'),
    )

    conversation = models.ForeignKey(Conversation, related_name="messages", on_delete=models.CASCADE)
    text = models.TextField()
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.text[:50]}"

class Reference(models.Model):
    # Link each reference to the message that generated it.
    message = models.ForeignKey(Message, related_name="references", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    url = models.URLField(max_length=500, blank=True, null=True)
    file_type = models.CharField(max_length=10, blank=True, null=True)
    server_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.title} ({self.url or 'No URL'})"

