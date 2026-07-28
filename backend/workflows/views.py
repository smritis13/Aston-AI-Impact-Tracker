from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import *
from .serializers import *
from workflows.utils.workflow_engine import WorkflowEngine
from workflows.utils.tools_registery import ToolRegistry
from base.pagination import CustomPagination
# workflows/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from workflows.utils.tools_registery import ToolRegistry, initialize_tools
import logging
import json


class AgentListCreateView(generics.ListCreateAPIView):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer

class AgentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer

class WorkflowDefinitionListCreateView(generics.ListCreateAPIView):
    queryset = WorkflowDefinition.objects.all()
    serializer_class = WorkflowDefinitionSerializer
    pagination_class = CustomPagination

class WorkflowDefinitionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WorkflowDefinition.objects.all()
    serializer_class = WorkflowDefinitionSerializer

class WorkflowExecutionListCreateView(generics.ListCreateAPIView):
    queryset = WorkflowExecution.objects.all()
    serializer_class = WorkflowExecutionSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the execution record
        instance = serializer.save(status='pending')
        
        # Execute the workflow (you could make this async with Celery)
        # try:
        workflow_engine = WorkflowEngine()  # Create an instance first
        result = workflow_engine.execute_workflow(instance)
        print('==================================================')
        print(f'workflow_engine.execute_workflow: {result}')
        print('==================================================')
        # instance.status = 'completed'
        # instance.output_data = result
        # instance.save()
        # except Exception as e:
        #     instance.status = 'failed'
        #     instance.output_data = {'error': str(e)}
        #     instance.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class WorkflowExecutionDetailView(generics.RetrieveAPIView):
    queryset = WorkflowExecution.objects.all()
    serializer_class = WorkflowExecutionSerializer

class AvailableToolsView(APIView):
    def get(self, request):
        tools = ToolRegistry.list_tools()
        serializer = AvailableToolsSerializer({'tools': tools})
        return Response(serializer.data)

class ToolConfigListCreateView(generics.ListCreateAPIView):
    queryset = ToolConfig.objects.all()
    serializer_class = ToolConfigSerializer

class ToolConfigDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ToolConfig.objects.all()
    serializer_class = ToolConfigSerializer




logger = logging.getLogger(__name__)


class SearchQuerySerializer(serializers.Serializer):
    """Serializer for validating the search query input.

    We allow an optional ``max_results`` field so callers can request only the first
    N entries.  The default used by the view is five results.
    """
    query = serializers.CharField(max_length=255, required=True)
    max_results = serializers.IntegerField(min_value=1, required=False)

class TavilySearchTestView(APIView):
    """DRF view to test the tavily_search tool."""
    
    def post(self, request, *args, **kwargs):
        # try:
            # Ensure tools are initialized
        initialize_tools()

        # Validate request data
        serializer = SearchQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        query = serializer.validated_data["query"]

        # Get the tavily_search tool
        try:
            tavily_tool = ToolRegistry.get_tool("serpapi_search", [])
        except ValueError as e:
            logger.error(f"Failed to get serpapi_search tool: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Run the search
        result = tavily_tool._run(query)
        
        # Parse the output; the tavily wrapper may already return native list/dict
        parsed_result = result  # json.loads(result) if string

        # Trim according to optional max_results
        max_results = serializer.validated_data.get("max_results", 10)
        if isinstance(parsed_result, list) and len(parsed_result) > max_results:
            parsed_result = parsed_result[:max_results]

        # Structure the response
        if isinstance(parsed_result, list):
            response_data = {
                "query": query,
                "results": [
                    {
                        "title": res.get("title", ""),
                        "url": res.get("url", ""),
                        "snippet": res.get("snippet", ""),
                        # "score": res.get("score")
                    }
                    for res in parsed_result
                ]
            }
        else:
            # Fallback for unexpected formats
            response_data = {
                "query": query,
                "raw_result": str(parsed_result)
            }
        logger.info(f"Tavily Search Result for '{query}': {response_data}")
        # except Exception as e:
        #     logger.error(f"Tavily search failed: {str(e)}")
        #     response_data = {"error": str(e)}

        return Response({
            "status": "success",
            "data": response_data
        }, status=status.HTTP_200_OK)

        # except Exception as e:
        #     logger.error(f"Tavily search test failed: {str(e)}")
        #     return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)