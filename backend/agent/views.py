from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Workflow, Node, Edge
from .serializers import WorkflowSerializer, NodeSerializer, EdgeSerializer
from django.shortcuts import get_object_or_404
from rest_framework import generics
from .utils.WorkflowExecutor import WorkflowExecutor

# Endpoint to create a new workflow (or list workflows)
# Workflow Views
class WorkflowListCreateView(generics.ListCreateAPIView):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer

class WorkflowDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer


# Node Views
class NodeListCreateView(generics.ListCreateAPIView):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer

class NodeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer


# Edge Views
class EdgeListCreateView(generics.ListCreateAPIView):
    queryset = Edge.objects.all()
    serializer_class = EdgeSerializer

class EdgeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Edge.objects.all()
    serializer_class = EdgeSerializer

# Endpoint to execute a workflow
class ExecuteWorkflowView(APIView):
    def post(self, request, workflow_id):
        """
        Expecting JSON with {"user_input": "..." }
        """
        workflow = get_object_or_404(Workflow, id=workflow_id)
        user_input = request.data.get("user_input", "")
        
        executor = WorkflowExecutor()
        result = executor.build_and_run_workflow(workflow_id)
        
        return Response({"workflow_result": result}, status=status.HTTP_200_OK)
