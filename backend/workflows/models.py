from django.db import models

from base.models import BaseModel

import uuid
import json

class Agent(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    agent_type = models.CharField(max_length=50)  # e.g., 'llm', 'tool', 'human'
    config = models.JSONField(default=dict)
    
    def __str__(self):
        return self.name

class WorkflowDefinition(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    graph_definition = models.JSONField()  # Stores the LangGraph definition
    
    def __str__(self):
        return self.name

class WorkflowExecution(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pending')  # pending, running, completed, failed
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict, blank=True, null=True)
    execution_trace = models.JSONField(default=list, blank=True, null=True)  # Store execution steps
    
    def __str__(self):
        return f"{self.workflow.name} - {self.id}"


class ToolConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    tool_id = models.CharField(max_length=50)  # Corresponds to the tool ID in ToolRegistry
    description = models.TextField(blank=True)
    config = models.JSONField(default=dict)  # For tool-specific configuration
    api_key_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


