# core/llm/utils/LangGraphChatEngine.py

import os
import re
import json
from typing import TypedDict, List, Dict
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from langgraph.graph import StateGraph, END
from core.llm.utils.ThoughtLoggerCallback import ThoughtLoggerCallback
from core.llm.langchain.langgraph.prompts import CHAT_ENGINE_PLAN_QUERY_PROMPT, CHAT_ENGINE_SUMMARIZE_PROMPT, CHAT_ENGINE_SYNTHESIZE_PROMPT, CHAT_ENGINE_CLASSIFY_QUERY_PROMPT
from core.llm.utils.pusher_service import PusherService

load_dotenv()
api_key = os.getenv("TAVILY_API_KEY")



class ChatGraphState(TypedDict):
    query: str
    sub_questions: List[str]
    findings: Dict[str, str]
    sources: Dict[str, List[str]]
    final_answer: str
    done: bool

class LangGraphChatEngine:
    def __init__(self, conversation_id: str = None):
        self.conversation_id = conversation_id
        self.callback = ThoughtLoggerCallback()
        self.pusher_service = PusherService()

        self.llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-5.4",
            temperature=0.3,
            callbacks=[self.callback]
        )

        self.search_tool = TavilySearchResults(
            tavily_api_key=api_key,
            max_results=10,
            search_depth="advanced",
            include_answer=True
        )

        # Define LangGraph
        workflow = StateGraph(ChatGraphState)
        workflow.add_node("plan", self.plan_query)
        workflow.add_node("search", self.search_each_question)
        workflow.add_node("synthesize", self.synthesize_answer)

        workflow.set_entry_point("plan")
        workflow.add_conditional_edges("plan",lambda state: "END" if state.get("done") else "search")
        workflow.add_edge("search", "synthesize")
        workflow.add_edge("synthesize", END)

        self.graph = workflow.compile()

    def stream_thought(self, thought: str):
        """Stream a thought to the frontend via Pusher."""
        if self.conversation_id:
            self.pusher_service.stream_thought(self.conversation_id, thought)

    def plan_query(self, state: ChatGraphState) -> ChatGraphState:
        query = state["query"]
        self.stream_thought("Planning search strategy...")

        print(f"Query: {query}")

        messages = [
            SystemMessage(content=CHAT_ENGINE_PLAN_QUERY_PROMPT.format(query=query))
        ]
        response = self.llm(messages)
        content = re.sub(r'^```json\s*|^```|```$', '', response.content.strip()).strip()

        # print(f"LLM Response Content: {content}")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            self.stream_thought("Could not parse plan response. Returning default answer.")
            return {**state, "final_answer": "Sorry, I couldn't understand your request.", "done": True}

        if parsed["type"] == "simple":
            self.stream_thought("Simple query detected. No research needed.")
            return {**state, "final_answer": parsed["response"], "done": True}

        self.stream_thought(f"Generated {len(parsed['sub_questions'])} sub-questions to research")
        return {**state, "sub_questions": parsed["sub_questions"], "done": False}

    def search_each_question(self, state: ChatGraphState) -> ChatGraphState:
        findings = {}
        sources = {}
        total_questions = len(state["sub_questions"])

        for i, q in enumerate(state["sub_questions"], 1):
            self.stream_thought(f"Searching for information ({i}/{total_questions}): {q}")
            docs = self.search_tool.run(q)
            snippets = [d.get("snippet") or d.get("content", "") for d in docs]


            self.stream_thought(f"Found {len(docs)} results for {q}")
            
            # Extract both URLs and titles from search results
            source_objects = []
            for d in docs:
                if d.get("url"):
                    source_objects.append({
                        "title": d.get("title", "Untitled"),
                        "url": d.get("url")
                    })

            self.stream_thought(f"Summarizing findings for: {q}")
            summary = self.llm([
                SystemMessage(content=CHAT_ENGINE_SUMMARIZE_PROMPT),
                HumanMessage(content="Context:\n\n" + "\n\n".join(snippets))
            ]).content

            findings[q] = summary
            sources[q] = source_objects

        self.stream_thought("Completed gathering information from all sources")
        return {**state, "findings": findings, "sources": sources}

    def fix_markdown_tables(self, text: str) -> str:
        # Matches Markdown-style tables by looking for at least two lines that look like a table
        table_regex = re.compile(
            r"((?:\|.*\n)+)", re.MULTILINE
        )

        def fix_table_block(match):
            lines = match.group(1).strip().split("\n")
            fixed_lines = []

            for line in lines:
                # Remove leading/trailing pipes and trim spaces
                parts = [col.strip() for col in line.strip("|").split("|")]
                # Reconstruct row with proper spacing
                fixed_line = "| " + " | ".join(parts) + " |"
                fixed_lines.append(fixed_line)

            return "\n".join(fixed_lines)

        return table_regex.sub(fix_table_block, text)
    
    def synthesize_answer(self, state: ChatGraphState) -> ChatGraphState:
        self.stream_thought("Synthesizing information into a comprehensive answer...")
        summary_blocks = "\n\n".join(
            f"### {q}\n{state['findings'][q]}\n" 
            for q in state["sub_questions"]
        )

        # + "\n".join(f"- {url}" for url in state['sources'][q])

        final_response = self.llm([
            SystemMessage(content=CHAT_ENGINE_SYNTHESIZE_PROMPT),
            HumanMessage(content=f"User question: {state['query']}\n\nResearch:\n{summary_blocks}")
        ]).content

        cleaned_response = self.fix_markdown_tables(final_response)
        self.stream_thought("Answer generation complete")

        return {**state, "final_answer": cleaned_response}
    
    def is_complex_query(self, query: str) -> bool:
        self.stream_thought("Classifying the query type...")
        prompt = CHAT_ENGINE_CLASSIFY_QUERY_PROMPT.format(query=query)
        messages = [
            SystemMessage(content=prompt)
        ]
        response = self.llm(messages).content.strip().lower()
        return response == "complex"


    def answer(self, query: str) -> dict:
        self.stream_thought("Starting web search process...")
        initial_state = {
            "query": query,
            "sub_questions": [],
            "findings": {},
            "sources": {},
            "final_answer": "",
            "done": False
        }
        result = self.graph.invoke(initial_state)
        
        # Flatten all sources into a single array of objects with title and url
        all_sources = []
        for sub_question_sources in result["sources"].values():
            all_sources.extend(sub_question_sources)
            
        return {
            "answer": result["final_answer"],
            "references": all_sources,
            "thoughts": self.callback.get_thoughts(),
            "conversation_id": self.conversation_id
        }
