# workflows/serializers.py
from rest_framework import serializers
from .models import *

class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = '__all__'

class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDefinition
        fields = '__all__'

class WorkflowExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowExecution
        fields = '__all__'
        read_only_fields = ('status', 'output_data', 'execution_trace')

# workflows/serializers.py
# Add these serializers to your existing serializers.py

class ToolConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolConfig
        fields = '__all__'


class AvailableToolsSerializer(serializers.Serializer):
    tools = serializers.DictField(read_only=True)