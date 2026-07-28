import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from core.llm.langchain.tools.use_case_tool import UseCaseTool
from core.llm.langchain.use_case_prompts import USE_CASE_RESEARCHER_PROMPT, AGENT_INPUT_PROMPT
from django.conf import settings
from typing import Dict, List
import uuid
from dotenv import load_dotenv
import os
from langchain.agents import AgentExecutor
from content.models import UseCaseTheme, UseCase

from core.llm.utils.pusher_service import PusherService
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult,HumanMessage, AIMessage

from langchain_core.chat_history import BaseChatMessageHistory
from langchain.memory import ConversationBufferMemory

from chat.models import Conversation, Message

# Load environment variables from .env file
load_dotenv()

class CustomOutputParser(StrOutputParser):
    def parse(self, text: str) -> str:
        """
        Custom parser that handles HTML tables and strips Markdown markers.
        """
        # Clean the response first
        cleaned_text = re.sub(r'^```[a-zA-Z]*\n|\n```$', '', text, flags=re.MULTILINE)
        cleaned_text = cleaned_text.strip()
        
        # If the output is an HTML table, return it directly
        if cleaned_text.startswith('<div class="table-responsive">'):
            return cleaned_text
        
        # If the output contains HTML table but is wrapped in other content
        html_table_match = re.search(r'<div class="table-responsive">.*?</div>', cleaned_text, re.DOTALL)
        if html_table_match:
            return html_table_match.group(0)
        
        # Otherwise, attempt to parse as a string
        return super().parse(cleaned_text)
    
class DjangoMessageHistory(BaseChatMessageHistory):
    """
    Loads past messages from Message model; does NOT write back since messages are saved at the view level.
    """
    def __init__(self, conversation_id: str):
        # Ensure Conversation exists
        self.conversation = Conversation.objects.get(conversation_id=conversation_id)

    def add_message(self, message: str) -> None:
        # No-op: messages are saved at the view level
        return

    def clear(self) -> None:
        # No-op: messages are managed at the view level
        return

    @property
    def messages(self):
        # Fetch and return all prior turns as LangChain messages
        msgs = []
        for m in self.conversation.messages.order_by('timestamp'):
            if m.sender == 'user':
                msgs.append(HumanMessage(content=m.text))
            else:
                msgs.append(AIMessage(content=m.text))
        return msgs

class ThoughtStreamingCallback(BaseCallbackHandler):
    def __init__(self, stream_func):
        self.stream_func = stream_func

    def on_llm_start(self, serialized: dict, prompts: list, **kwargs):
        self.stream_func("Starting LLM processing...")

    def on_llm_end(self, response: LLMResult, **kwargs):
        self.stream_func("LLM processing completed")

    def on_llm_error(self, error: Exception, **kwargs):
        self.stream_func(f"LLM Error: {str(error)}")

    def on_chain_start(self, serialized: dict, inputs: dict, **kwargs):
        self.stream_func("Starting chain processing...")

    def on_chain_end(self, outputs: dict, **kwargs):
        self.stream_func("Chain processing completed")

    def on_chain_error(self, error: Exception, **kwargs):
        self.stream_func(f"Chain Error: {str(error)}")

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs):
        tool_name = serialized.get('name', 'Unknown')
        self.stream_func(f"Using tool: {tool_name}\nTool input: {input_str}\nTool kwargs: {kwargs}")

    def on_tool_end(self, output: str, **kwargs):
        if isinstance(output, dict):
            self.stream_func(f"Tool output: {str(output)}")
        else:
            self.stream_func(f"Tool output: {output}")

    def on_tool_error(self, error: Exception, **kwargs):
        self.stream_func(f"Tool Error: {str(error)}")

    def on_text(self, text: str, **kwargs):
        self.stream_func(f"{text}")

    def on_agent_action(self, action: AgentAction, **kwargs):
        if hasattr(action, 'log') and 'Thought:' in action.log:
            thought_match = re.search(r'Thought:\s*(.*)', action.log)
            if thought_match:
                self.stream_func(f"💭 Thought: {thought_match.group(1)}")
       
        self.stream_func(f"⚙️ Action: {action.tool}\n📝 Input: {action.tool_input}")

    def on_agent_finish(self, finish: AgentFinish, **kwargs):
        self.stream_func("Agent finished processing")

class UseCaseResearcher:
    def _truncate_chat_history(self, history: str, max_length: int = 40000) -> str:
        """Truncate chat history to specified max length."""
        if len(history) <= max_length:
            return history
        return history[-max_length:]

    def _format_chat_history(self, messages, max_length: int = 40000) -> str:
        """Format chat history in a clear, readable way."""
        formatted_history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_history.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                formatted_history.append(f"Assistant: {msg.content}")
        formatted_history = self._truncate_chat_history("\n".join(formatted_history), max_length)
        return "\n".join(formatted_history)

    def clean_llm_response(self, response: str) -> str:
        """
        Clean and format LLM response by removing markdown code blocks and extra whitespace.
        
        Args:
            response (str): The raw response from the LLM
            
        Returns:
            str: Cleaned response with markdown code blocks removed and whitespace normalized
        """
        # Remove markdown code blocks (```language and ```)
        cleaned = re.sub(r"^```[a-zA-Z]*|```$", "", response.strip(), flags=re.MULTILINE)

        # Remove any remaining extra whitespace
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        return cleaned.strip()

    def __init__(self, conversation_id: str = None, theme_id: int = None):
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.theme_id = theme_id
        self.company = None  
        
        # Initialize LangChain LLM
        self.llm_model = ChatOpenAI(
            model="gpt-5.4",
            api_key=os.getenv('OPENAI_API_KEY'),
            temperature=0
        )

        # Initialize tools
        self.use_case_tool = UseCaseTool(theme_id=self.theme_id, company=self.company).get_langchain_tool()
        self.web_search_tool = TavilySearchResults(
            max_results=5,
            api_key=os.getenv('TAVILY_API_KEY')
        )
        self.tools = [self.use_case_tool, self.web_search_tool]

        self.usecase_themes = UseCaseTheme.objects.filter(id=self.theme_id) if self.theme_id else UseCaseTheme.objects.all()
        
        # Initialize Pusher service for streaming
        self.pusher_service = PusherService()

        chat_memory = DjangoMessageHistory(self.conversation_id)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            chat_memory=chat_memory,
            input_key="input",
            output_key="output",
            return_messages=True
        )

       
        
        # Define the agent prompt with required variables
        self.agent_prompt = ChatPromptTemplate.from_messages([
            ("system", USE_CASE_RESEARCHER_PROMPT + "\n\nAvailable tools:\n{tools}\n\nTool names: {tool_names}\n\nThemes:\n{usecase_themes}\n\nConversation ID: {conversation_id}\n\nIf the user asks for use cases for a specific company, always pass the company name as the 'company' parameter to the UseCaseSearch tool.\n"),
            ("human", "{input}"),
            ("ai", "{agent_scratchpad}")
        ])

        # Create the ReAct agent
        agent = create_react_agent(
            llm=self.llm_model,
            tools=self.tools,
            prompt=self.agent_prompt,
        )
    
        # Custom parsing error handler
        def custom_parsing_error_handler(error):
            error_msg = f"Parsing error: {str(error)}"
            # self._stream(error_msg)
            # Try to extract and clean HTML table if present
            output = getattr(error, 'output', None)
            if isinstance(output, str):
                html_table_match = re.search(r'<div class="table-responsive">.*?</div>', output, re.DOTALL)
                if html_table_match:
                    table_html = html_table_match.group(0).strip()
                    return f"""
**Thought**: The output could not be parsed as a standard response, but a valid HTML table was detected. Returning the cleaned table as the final answer.
Final Answer: {table_html}
"""
            # Fallback to default error message
            return """
**Thought**: An error occurred while parsing the response. I will attempt to provide a final answer based on available information.
**Action**: [Final Answer][## Result\n\nAn error occurred while processing the query. Please rephrase or provide more details to get a better response.]
"""

        # Create the agent executor with callback handler
        self.agent = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=custom_parsing_error_handler,
            max_iterations=5,
            output_parser=CustomOutputParser(),
            return_intermediate_steps=True,
            callbacks=[ThoughtStreamingCallback(self._stream)],
            memory=self.memory
        )

    def _stream(self, message: str):
        """Stream a message to the frontend via Pusher."""

        if len(message) > 1000:
            message = message[:1000] + "..."
        if self.conversation_id:
            self.pusher_service.stream_thought(self.conversation_id, message)

    def _detect_company_mention(self, query: str) -> str:
        """
        Detect if the user query mentions a specific company and extract the company name.
        Uses the LLM to analyze the query and match against known companies in the database.
        
        Args:
            query (str): The user's query text
            
        Returns:
            str: The detected company name if found, None otherwise
        """
        # Get list of unique companies from the database
        companies = UseCase.objects.exclude(company__isnull=True).exclude(company='').values_list('company', flat=True).distinct()
        companies_list = list(companies)
        
        if not companies_list:
            return None
            
        # Create a prompt for the LLM to detect company mentions
        company_detection_prompt = f"""Given the following user query and a list of known companies, determine if the query mentions any specific company.
If a company is mentioned, return ONLY the company name from the list that best matches the mention.
If no company is mentioned or the mention is ambiguous, return 'None'.

Known companies:
{', '.join(companies_list)}

User query: {query}

Return ONLY the company name or 'None'."""

        try:
            # Use the LLM to detect company mentions
            response = self.llm_model.invoke(company_detection_prompt)
            detected_company = response.content if hasattr(response, 'content') else str(response).strip()

            
            # Validate that the detected company exists in our list
            if detected_company and detected_company != 'None':
                return detected_company
            return None
            
        except Exception as e:
            print(f"Error detecting company mention: {str(e)}")
            return None

    def _update_tools_with_company(self, company: str):
        """
        Update the UseCaseTool with a new company value and refresh the tools list.
        """
        self.use_case_tool = UseCaseTool(theme_id=self.theme_id, company=company).get_langchain_tool()
        self.tools = [self.use_case_tool, self.web_search_tool]
        # Update the agent's tools
        self.agent.tools = self.tools

    def chat(self, prompt: str) -> Dict[str, any]:
        """
        Process a user query using the agent and return a dictionary with the answer and references.
        Optionally filter use cases by company.
        """
        # First detect if the query mentions a company
        detected_company = self._detect_company_mention(prompt)
        if detected_company:
            self.company = detected_company
            self._update_tools_with_company(detected_company)

        agent_input = AGENT_INPUT_PROMPT.format(prompt=prompt)

        # try:
        self._stream("Processing query")
        formatted_themes = "\n".join([f"- {theme.title}" for theme in self.usecase_themes])
        
        self._stream("Initializing search...")
        # Add company to the agent input if provided
        agent_vars = {
            "input": agent_input,
            "usecase_themes": formatted_themes,
            "tools": "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools]),
            "tool_names": ", ".join([tool.name for tool in self.tools]),
            "chat_history": self._format_chat_history(self.memory.chat_memory.messages),
            "conversation_id": self.conversation_id
        }
        if self.company:
            agent_vars["company"] = self.company

        agent_response = self.agent.invoke(agent_vars)

        self._stream("Processing search results...")
        
        answer = self.clean_llm_response(agent_response.get("output", ""))
        
        references = []
        if "intermediate_steps" in agent_response:
            for action in agent_response["intermediate_steps"]:
                tool_output = action[1]
                if isinstance(tool_output, dict) and "references" in tool_output:
                    references.extend(tool_output["references"])
                elif isinstance(tool_output, list):
                    for result in tool_output:
                        if isinstance(result, dict) and "title" in result and "url" in result:
                            references.append({
                                "title": result["title"],
                                "url": result["url"],
                                "type": "web"
                            })

        if references and "References" not in answer:
            answer += "\n\n\n\n## References\n"
            for i, ref in enumerate(references, 1):
                answer += f"- [{ref['title']}]({ref['url']}) \n"

        if not answer or "Agent stopped" in answer:
            self._stream("No results found. Requesting user to rephrase query.")
            answer = """## Result

I apologize, but I was unable to properly process your query using the available tools. Can you try rephrasing your query or asking about a specific aspect of the topic?"""

        self._stream("Search completed successfully.")
        return {
            "answer": answer,
            "references": references,
            "conversation_id": self.conversation_id
        }
        
        # except Exception as e:
        #     error_msg = f"Error in chat: {str(e)}"
        #     self._stream(error_msg)
        #     return {
        #         "answer": f"## Result\nError processing query: {str(e)}\n\n## Explanation\nAn error occurred while processing the query with the agent.",
        #         "references": [],
        #         "conversation_id": self.conversation_id
        #     }