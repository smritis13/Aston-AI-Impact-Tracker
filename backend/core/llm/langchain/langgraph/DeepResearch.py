import os
import re
import json
import asyncio
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from langgraph.graph import StateGraph, END, START
from core.llm.utils.ThoughtLoggerCallback import ThoughtLoggerCallback
from core.llm.langchain.langgraph.prompts import (
    DEEPRESEARCH_PLAN_PROMPT,
    DEEPRESEARCH_SUMMARIZE_PROMPT,
    DEEPRESEARCH_SYNTHESIZE_PROMPT,
    DEEPRESEARCH_REFINE_CHECK_PROMPT,
    DEEPRESEARCH_REFINE_PLAN_PROMPT
)
from core.llm.utils.pusher_service import PusherService

load_dotenv()
api_key = os.getenv("TAVILY_API_KEY")

class ResearchState(TypedDict):
    query: str
    iteration: int
    plans: List[List[str]]
    findings: Dict[str, str]
    sources: Dict[str, List[Dict[str, str]]]
    final_answer: str

class DeepResearch:
    """
    A sophisticated deep-research engine: breaks query into multi-level sub-questions,
    searches concurrently, refines iteratively, and synthesizes a comprehensive answer.
    Streams internal thoughts via PusherService.
    """
    def __init__(
        self,
        conversation_id: str = None,
        llm_model: str = "gpt-5.4-mini",
        temperature: float = 0.2,
        max_iterations: int = 10,
    ):
        self.conversation_id = conversation_id
        self.callback = ThoughtLoggerCallback()
        self.pusher = PusherService()
        self.llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model=llm_model,
            temperature=temperature,
            callbacks=[self.callback]
        )
        self.search_tool = TavilySearchResults(
            tavily_api_key=api_key,
            max_results=10,
            search_depth="advanced",
            include_answer=True
        )
        self.max_iterations = max_iterations

        # Define the research workflow graph
        graph = StateGraph(ResearchState)
        graph.add_node("plan", self._plan)
        graph.add_node("search", self._search_concurrent)
        graph.add_node("refine_check", self._check_refinement)
        graph.add_node("refine_plan", self._plan_refinement)
        graph.add_node("synthesize", self._synthesize)

        graph.set_entry_point("plan")
        graph.add_edge("plan", "search")
        graph.add_edge("search", "refine_check")
        graph.add_conditional_edges(
            "refine_check",
            lambda s: "refine_plan" if s["iteration"] < self.max_iterations else "synthesize",
            {
                "refine_plan": "refine_plan",
                "synthesize": "synthesize"
            }
        )
        graph.add_edge("refine_plan", "search")
        graph.add_edge("synthesize", END)

        self.graph = graph.compile()

    def _stream(self, message: str):
        if self.conversation_id:
            self.pusher.stream_thought(self.conversation_id, message)

    def _plan(self, state: ResearchState) -> ResearchState:
        self._stream("Planning multi-level research structure...")
        prompt = f"{DEEPRESEARCH_PLAN_PROMPT}\n<user_query> {state['query']} </user_query>"
        response = self.llm([
            SystemMessage(content=prompt)
        ])
        # Expect JSON of first-level sub-questions array

        raw = response.content.strip()
        cleaned = re.sub(r'^```json\\s*|```$', '', raw).strip()
        subqs = json.loads(cleaned)

        state['plans'] = [subqs]
        state['iteration'] = 1
        return state

    async def _fetch_and_summarize(self, question: str) -> Any:
        self._stream(f"Searching for: {question}")
        docs = self.search_tool.run(question)
        snippets = [d.get("snippet") or d.get("content", "") for d in docs]
        self._stream(f"Found {len(docs)} docs for: {question}")
        summary = self.llm([
            SystemMessage(content=DEEPRESEARCH_SUMMARIZE_PROMPT),
            HumanMessage(content="\n\n".join(snippets))
        ]).content

        if len(summary) > 50:
            self._stream(f"Summary (truncated): {summary[:50]}...")
        else:
            self._stream(f"Summary: {summary}")
            
        sources = [ {"title": d.get("title",""), "url": d.get("url","")} for d in docs if d.get("url") ]
        return question, summary, sources

    async def _search_concurrent(self, state: ResearchState) -> ResearchState:
        self._stream(f"Initiating concurrent searches (iteration {state['iteration']})...")
        questions = state['plans'][-1]
        tasks = [self._fetch_and_summarize(q) for q in questions ]

        results = await asyncio.gather(*tasks)

        # store findings
        for q, summary, sources in results:
            state['findings'][q] = summary
            state['sources'][q] = sources
        self._stream("Search and summarization complete for this batch.")
        return state

    def _check_refinement(self, state: ResearchState) -> ResearchState:
        self._stream("Assessing need for deeper refinement...")
        context = json.dumps(state['findings'], indent=2)
        prompt = f"{DEEPRESEARCH_REFINE_CHECK_PROMPT}\n\n <current_findings> {context} </current_findings> \n<user_query> {state['query']} </user_query>"
        decision = self.llm([
            SystemMessage(content=prompt)
        ]).content.strip().lower()
        if "yes" in decision:
            state['iteration'] += 1
            self._stream(f"Refinement needed: iteration {state['iteration']}")
            return state
        self._stream("Refinement not required, proceeding to synthesis.")
        state['iteration'] = self.max_iterations
        return state

    def _plan_refinement(self, state: ResearchState) -> ResearchState:
        self._stream("Generating refinement sub-questions...")
        prev = state['plans'][-1]
        prompt = f"{DEEPRESEARCH_REFINE_PLAN_PROMPT}\n<existing_findings> {json.dumps(state['findings'])} </existing_findings> \n<previous_sub_questions> {json.dumps(prev)} </previous_sub_questions> \n<user_query> {state['query']} </user_query>"
        response = self.llm([
            SystemMessage(content=prompt)
        ])

        raw = response.content.strip()
        cleaned = re.sub(r'^```json\\s*|```$', '', raw).strip()
    
        new_subqs = json.loads(cleaned)
        state['plans'].append(new_subqs)
        return state

    def _synthesize(self, state: ResearchState) -> ResearchState:
        self._stream("Synthesizing comprehensive answer...")
        blocks = []
        for lvl, questions in enumerate(state['plans'], 1):
            for q in questions:
                blocks.append(f"### {q}\n{state['findings'][q]}\n")
        prompt = f"{DEEPRESEARCH_SYNTHESIZE_PROMPT}\n\n{''.join(blocks)}"
        final = self.llm([
            SystemMessage(content=prompt),
            HumanMessage(content=f"User query: {state['query']}")
        ]).content
        state['final_answer'] = self._fix_tables(final)
        self._stream("Deep research complete.")
        return state

    def _fix_tables(self, text: str) -> str:
        regex = re.compile(r"((?:\|.*\n)+)", re.MULTILINE)
        def repl(m):
            lines = m.group(1).strip().split("\n")
            out = []
            for line in lines:
                parts = [c.strip() for c in line.strip("|").split("|")]
                out.append("| " + " | ".join(parts) + " |")
            return "\n".join(out)
        return regex.sub(repl, text)

    async def research(self, query: str) -> Dict[str, Any]:
        self._stream("Starting deep research process...")
        init: ResearchState = {
            "query": query,
            "iteration": 0,
            "plans": [],
            "findings": {},
            "sources": {},
            "final_answer": ""
        }
        result = await self.graph.ainvoke(init)
        # flatten sources
        all_src = []
        for srcs in result['sources'].values():
            all_src.extend(srcs)

        return {
            "answer": result['final_answer'],
            "sources": all_src,
            "references": all_src,  # ← Add this line
            "thoughts": self.callback.get_thoughts(),
            "conversation_id": self.conversation_id
        }

    def research_sync(self, query: str) -> Dict[str, Any]:
        """Synchronous wrapper for research method."""
        return asyncio.run(self.research(query))
