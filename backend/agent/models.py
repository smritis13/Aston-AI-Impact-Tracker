from django.db import models
import uuid

class Workflow(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    # When the workflow is executed, you might store the result
    last_result = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Node(models.Model):
    NODE_TYPES = [
        ('prompt', 'Prompt'),
        ('llm', 'LLM'),
        ('tool', 'Tool'),
        ('map', 'Map'),
        # add more types as needed
    ]
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='nodes')
    node_type = models.CharField(max_length=20, choices=NODE_TYPES)
    name = models.CharField(max_length=100)
    config = models.JSONField(default=dict)  # store LLM config, prompt template, etc.
    position = models.JSONField(default=dict)  # store {x: number, y: number} for front-end visualization

    def __str__(self):
        return f"{self.name} ({self.node_type})"

class Edge(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='edges')
    source = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='edge_sources')
    target = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='edge_targets')
    label = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.source.name} -> {self.target.name}"
