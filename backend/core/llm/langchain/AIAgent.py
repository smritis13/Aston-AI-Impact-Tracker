from django.conf import settings
from langchain.agents import AgentType, initialize_agent
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from .tools.AITrendsTool import AITrendsTool
# SoftwareDevToolsTool removed; not needed for research-impact focus
class AIAgent:
    """
    LangChain agent that can dynamically decide which tool to use.
    """

    def __init__(self, model="gpt-5.4", temperature=0.3):
        self.llm = ChatOpenAI(openai_api_key=settings.OPENAI_API_KEY,model_name=model, temperature=temperature)
        self.memory = ConversationBufferMemory(memory_key="ai_agent_memory")

        # Register available tools
        self.tools = {
            "AI Trends": AITrendsTool(self.llm).langchain_tool(),
            # specialized software development tool removed
            
            # Future tools can be added here
        }

        # Define the agent
        self.agent = initialize_agent(
            tools=list(self.tools.values()),  # Load all tools dynamically
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            # Safety: limit reasoning/action loops to avoid runaway outputs
            max_iterations=3,
        )

    def handle_query(self, query, force_refresh=False):
        """
        Processes a query, determines the relevant tool, and executes it.
        """
        # Determine which tool to use based on query content
        if "ai" in query.lower() and "trends" in query.lower():
            return self.tools["AI Trends"].func(query)  # Pass only `query`
        elif "software" in query.lower() and "development" in query.lower():
            return self.tools["Software Development Tools"].func(query)  # Pass only `query`

        # Default: Let LangChain handle general questions. Limit output length.
        try:
            result = self.agent.run(query)
        except Exception as e:
            return f"Agent error: {str(e)}"

        # Truncate very long outputs to avoid streaming/console flood
        if isinstance(result, str) and len(result) > 20000:
            return result[:20000] + "\n\n[output truncated]"

        return result
