# core/report_generation/base_graph_report_generator.py

import json
import os
import re
from typing import TypedDict, List, Dict, Literal
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from langgraph.graph import StateGraph, END
from django.utils.timezone import now
from content.models import Report
from core.llm.utils.ThoughtLoggerCallback import ThoughtLoggerCallback
from dotenv import load_dotenv
import asyncio
import threading
from queue import Queue
# from core.llm.utils.CrawlAIScraper import CrawlAiScraper
from content.models import ScrapedURL
from core.llm.utils.SimpleHtmlScraper import SimpleHtmlScraper

load_dotenv()
api_key = os.getenv("TAVILY_API_KEY")

# Control whether scraping is enabled
SCRAPING_ENABLED = False

class GraphState(TypedDict):
    query: str
    sub_questions: List[str]
    findings: Dict[str, str]
    sources: Dict[str, List[str]]  # Separate sources for each query
    final_report: str
    scraped_pages: Dict[str, List[Dict[str, str]]]  # Added for scraping
    research_summary: str

class ScrapeTask:
    def __init__(self, url: str, report_id, scraper):
        self.url = url
        self.report_id = report_id
        self.scraper = scraper

    async def scrape(self) -> tuple[str, str, str, str]:
        try:
            result = await self.scraper.scrape_only(self.url)
            if result and "text" in result:
                title = result.get("title", "")[:255]
                content = self.clean_content(result["text"])
                return self.url, title, content, ""
            return self.url, "", "", "No content available"
        except Exception as e:
            return self.url, "", "", f"Error: {str(e)[:100]}"

    @staticmethod
    def clean_content(content: str) -> str:
        cleaned = content.encode("utf-8", errors="ignore").decode("utf-8")
        return cleaned[:5000]

class BaseGraphReportGenerator:
    def __init__(
        self,
        report_length: Literal["short", "medium", "detailed"] = "medium",
        max_links_to_scrape: int = 100,
    ):
        self.report_length = report_length
        self.max_links_to_scrape = max_links_to_scrape
        self.callback = ThoughtLoggerCallback()
        self.scraper = SimpleHtmlScraper()  # Initialize the scraper

        self.llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-5.4",
            temperature=0.3,
            callbacks=[self.callback]
        )

        self.search_tool = TavilySearchResults(tavily_api_key=api_key, max_results=10,search_depth="advanced",include_answer="advanced") #time_range="week",


        # Define LangGraph workflow
        workflow = StateGraph(GraphState)
        workflow.add_node("plan", self.plan_query)
        workflow.add_node("search", self.search_each_question)
        
        # Add scraping node if enabled
        if SCRAPING_ENABLED:
            workflow.add_node("scrape", self.scrape_node)
            workflow.add_edge("search", "scrape")
            workflow.add_edge("scrape", "synthesize")
        else:
            workflow.add_edge("search", "synthesize")
            
        workflow.add_node("synthesize", self.synthesize_report)

        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "search")
        workflow.add_edge("synthesize", END)

        self.graph = workflow.compile()

    def plan_query(self, state: GraphState) -> GraphState:
        query = state["query"]
        messages = [
            SystemMessage(content="You are an AI analyst tasked with breaking a consulting question into research sub-questions."),
            HumanMessage(content=f"Break this question into 10-15 research sub-questions: {query}. return the sub-questions in a json array of strings.")
        ]
        response = self.llm(messages)

        content = response.content.strip()
        content = re.sub(r'^```json\s*|^```|```$', '', content).strip()

        json_response = json.loads(content)
        

        return {"query": query, "sub_questions": json_response, "findings": {}, "sources": {}, "final_report": "", "scraped_pages": {}, "research_summary": ""}

    def search_each_question(self, state: GraphState) -> GraphState:
        findings = {}
        sources = {}


        for q in state["sub_questions"]:
            

            
            docs = self.search_tool.run(q)

            snippets = [d.get("snippet") or d.get("content", "") for d in docs]
            snippets_text = "\n\n".join(snippets)
            urls = [d.get("url") for d in docs if d.get("url")]
            
            # Store sources separately
            sources[q] = urls

            messages = [
                SystemMessage(content="You are a summarization AI. Write a concise paragraph summarizing the key points below."),
                HumanMessage(content=f"Question: {q}\n\nResults:\n{snippets_text}")
            ]
            
            summary = self.llm(messages).content
            findings[q] = summary


        return {**state, "findings": findings, "sources": sources}

    def scrape_node(self, state: GraphState) -> GraphState:
        thoughts = state.get("thoughts", []) + ["Starting scraping phase."]
        report_id = state.get("report_id")
        scraped = {}
        url_queue = Queue()
        results_dict = {}

        # Extract URLs from sources
        for q, urls in state["sources"].items():
            scraped[q] = []
            
            # Limit the number of URLs to scrape
            max_items = min(self.max_links_to_scrape, len(urls))
            for url in urls[:max_items]:
                url_queue.put(ScrapeTask(url, report_id, self.scraper))

        def worker():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            while True:
                try:
                    task = url_queue.get_nowait()
                except:
                    break
                url, title, content, error = loop.run_until_complete(task.scrape())
                if content and not error:
                    if report_id:
                        try:
                            ScrapedURL.objects.update_or_create(
                                report_id=report_id,
                                url=url,
                                defaults={"title": title, "content": content}
                            )
                        except Exception as e:
                            print(f"DB error: {str(e)}")
                    results_dict[url] = {"url": url, "title": title, "scraped_text": content}
                    thoughts.append(f"Scraped <{url}> with title '{title}'")
                else:
                    thoughts.append(f"Failed to scrape <{url}>: {error or 'No content'}")
                url_queue.task_done()
            loop.close()

        # Use multiple threads for scraping
        num_threads = min(5, url_queue.qsize())
        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Organize scraped content by query
        for q, urls in state["sources"].items():
            max_items = min(self.max_links_to_scrape, len(urls))
            for url in urls[:max_items]:
                if url in results_dict:
                    scraped[q].append(results_dict[url])

        return {**state, "scraped_pages": scraped, "thoughts": thoughts}

    def synthesize_report(self, state: GraphState) -> GraphState:
        format_hint = {
            "short": "a 2-paragraph summary",
            "medium": "a 4-6 paragraph structured report",
            "detailed": "a detailed, multi-section report with headings and recommendations"
        }[self.report_length]

        # Create research summary with findings and sources
        research_summary = "\n\n".join(
            f"### {q}\n\n{state['findings'][q]}\n\n**Sources:**\n" + "\n".join(f"- {source}" for source in state['sources'][q])
            for q in state["sub_questions"]
        )

        

        # Include scraped content if available
        if SCRAPING_ENABLED and state.get("scraped_pages"):
            scraped_content = "\n\n".join(
                f"### Scraped content for: {q}\n" + "\n\n".join(
                    f"From {page['url']}:\n{page['scraped_text'][:1000]}..." 
                    for page in pages
                )
                for q, pages in state["scraped_pages"].items() if pages
            )
            # if scraped_content:
                # research_summary += "\n\n## Additional Scraped Content\n\n" + scraped_content

        messages = [
            SystemMessage(content="You are a strategy consultant generating a structured report."),
            HumanMessage(content=(
                f"Write {format_hint} answering this question:\n\n{state['query']}\n\n"
                f"Base it only on the following research:\n\n{research_summary}"
            ))
        ]

        final_report = self.llm(messages).content

        final_report = re.sub(r'^```json\s*|^```|```$', '', final_report).strip()

        state["research_summary"] = research_summary

        return {**state, "final_report": final_report}

    def run(self, query: str) -> str:
        initial_state = {
            "query": query,
            "sub_questions": [],
            "findings": {},
            "sources": {},
            "final_report": "",
            "research_summary": "",
            "scraped_pages": {},
            "thoughts": []
        }
        final_state = self.graph.invoke(initial_state)
        
        # Get the report ID after creation
        # Create a new report
        report_obj = Report.objects.create(
            topic=final_state["query"],
            query=final_state["query"],
            generated_report=final_state["final_report"],
            thoughts=self.callback.get_thoughts(),
            updated_at=now(),
            metadata={
                "length": self.report_length,
                "sub_questions": final_state["sub_questions"],
                "research_summary": final_state["research_summary"],
                "findings": final_state["findings"],
                "sources": final_state["sources"],
                "scraped_pages_count": sum(len(pages) for pages in final_state.get("scraped_pages", {}).values())
            }
        )
        report_id = report_obj.id if report_obj else None
        
        return final_state["final_report"], self.callback.get_thoughts(), report_id