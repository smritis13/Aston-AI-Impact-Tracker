from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from core.llm.langchain.use_case_researcher import UseCaseResearcher
from core.llm.langchain.langgraph.DeepResearch import DeepResearch
from core.llm.langchain.AIAgent import AIAgent
from core.llm.llm import LLM
from rest_framework import status
from .models import *
from .serializers import *
from uuid import UUID
from core.llm.utils.ConversationTitleGenerator import ConversationTitleGenerator
from core.llm.utils.AdvancedAugmentedResponse import AdvancedAugmentedResponse
from core.llm.utils.Streamer import Streamer
import asyncio
import time
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
import threading
# Create your views here.



class ConversationListAPIView(generics.ListAPIView):
    queryset = Conversation.objects.all().order_by('-created_at')
    serializer_class = ConversationSerializer


class ConversationDetailAPIView(generics.RetrieveAPIView):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    lookup_field = "conversation_id"


CHAT_ENGINE_CACHE = {}

class ChatIndexView(APIView):
    def post(self, request, *args, **kwargs):
        prompt = request.data.get("prompt", "")
        use_web_search = request.data.get("use_web_search", False)
        use_deep_research = request.data.get("use_deep_research", False)
        index_name = request.data.get("index_name", "combined_context")
        theme_id = request.data.get("theme_id", None)
        conversation_id = request.data.get("conversation_id", None)
        conversation = None

        if conversation_id:
            try:
                conversation = Conversation.objects.get(conversation_id=UUID(conversation_id))
            except (Conversation.DoesNotExist, ValueError):
                conversation = Conversation.objects.create()
        else:
            conversation = Conversation.objects.create()

        Message.objects.create(conversation=conversation, text=prompt, sender="user")

        llm = LLM(index_name="combined_context", conversation_id=conversation.conversation_id, recreate=False)
        
        # pipeline = AdvancedAugmentedResponse(index_name=index_name)
        # result = llm.retrieve_and_chat(prompt)
        # result = pipeline.answer_question(prompt)
        
        if use_web_search:
            result = llm.retrieve_and_chat_with_WebSearch(prompt)
        elif use_deep_research:
            deep_research = DeepResearch(conversation_id=conversation.conversation_id) #,llm_model="gpt-4o-mini"
            result = deep_research.research_sync(prompt)
        else:
            usecase_researcher = UseCaseResearcher(conversation_id=conversation.conversation_id, theme_id=theme_id)
            result = usecase_researcher.chat(prompt)

        response_text = result["answer"]
        references = result["references"]

        # save the result to the database
        Message.objects.create(conversation=conversation, text=response_text, sender="system")

        user_messages_count = Message.objects.filter(conversation=conversation, sender="user").count()

        if not conversation.title and user_messages_count >0:
            title_gen = ConversationTitleGenerator()
            conversation_title = title_gen.generate_title(conversation)
            conversation.title = conversation_title
            conversation.save()

        return Response({
            "response": response_text,
            "references": references,
            "conversation_id": conversation.conversation_id
        }, status=status.HTTP_200_OK)



class AdvancedAugmentedResponseView(APIView):
    def post(self, request, *args, **kwargs):
        """
        Expects a POST request with a JSON body containing:
          - question: The question to answer.
          - (optional) index_name: The index name to use.
          - (optional) recreate: Whether to recreate the index.
          
        Returns a JSON response with the generated answer, key points, and references.
        """
        question = request.data.get("question", "").strip()
        if not question:
            return Response({"error": "No question provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        index_name = request.data.get("index_name", "combined_context")
        recreate = request.data.get("recreate", False)
        
        # Initialize the AdvancedAugmentedResponse pipeline.
        pipeline = AdvancedAugmentedResponse(index_name=index_name, recreate=recreate)
        result = pipeline.answer_question(question)
        
        return Response(result, status=status.HTTP_200_OK)

class AIAgentQueryView(APIView):
    """
    API endpoint for querying the LangChain AI agent.
    """

    def post(self, request, *args, **kwargs):
        query = request.data.get("query")
        force_refresh = request.data.get("force_refresh", False)

        if not query:
            return Response({"error": "Query is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            agent = AIAgent()
            response = agent.handle_query(query, force_refresh)
            return Response({"response": response}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TestStreamingView(APIView):
    """
    API endpoint for testing the streaming functionality.
    Sends a message every second for a specified duration.
    """
    
    def post(self, request, *args, **kwargs):
        duration = request.data.get("duration", 5)  # Default 5 seconds
        message = request.data.get("message", "Test message")  # Default test message
        
        # Create a Streamer instance
        streamer = Streamer()
        
        # Start a background thread to send messages
        def send_messages():
            for i in range(duration):
                streamer.stream_thought(f"{message} {i+1}/{duration}")
                time.sleep(1)
            # Send completion status
            streamer.stream_status("completed", {"message": "Streaming test completed"})
        
        # Start the background thread
        thread = threading.Thread(target=send_messages)
        thread.start()
        
        return Response({
            "status": "started",
            "stream_id": streamer.stream_id,
            "message": f"Streaming test started. Will send {duration} messages."
        }, status=status.HTTP_200_OK)
