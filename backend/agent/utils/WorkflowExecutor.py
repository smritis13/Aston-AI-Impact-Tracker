from langgraph.graph import Graph
# from langchain_community.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI

from langchain.prompts import PromptTemplate
from django.core.exceptions import ObjectDoesNotExist
from agent.models import Workflow, Node, Edge  # Adjust import based on your app structure
import json
from django.conf import settings
from langchain.schema import AIMessage, HumanMessage


class WorkflowExecutor:
    """A class to execute workflows defined by Workflow, Node, and Edge models."""

    def __init__(self):
        """Initialize with API key for LLM."""
        
        self.llm = ChatOpenAI(openai_api_key=settings.OPENAI_API_KEY,model_name="gpt-4", temperature=0.3)
        self.node_handlers = {
            "tool": self._execute_tool_node,
            "llm": self._execute_llm_node,
        }

    def _execute_tool_node(self, state: dict, config: dict) -> dict:
        """Handles tool nodes, e.g., web search with Tavily."""
        if config.get("tool_name") == "tavily_search":
            query = config.get("query",'')
            if not query:
                raise ValueError("No query provided for web search")
            

            results = {
                "results": [
                    
                    {"snippet": "tiger is 250kg"},
                    {"snippet": "lions are not that big. their weight is 100kg on average"},
                    {"snippet": "city cats weigh less than 10kg"}
                ]
            }

            node_id = config.get("node_id", "-1")
            unique_key = f"search_results_{node_id}"

            state[unique_key] = [result["snippet"] for result in results["results"]]

        else:
            raise ValueError(f"Unknown tool: {config.get('tool_name')}")
        return state
    
    def custom_serializer(SELF,obj):
        # If the object is an instance of AIMessage or HumanMessage, return its content.
        if isinstance(obj, (AIMessage, HumanMessage)):
            return obj.content
        # Fallback: try string representation
        return str(obj)

    def _execute_llm_node(self, state: dict, config: dict) -> dict:
        """
        Executes an LLM node using a simple prompt provided in the config.
        
        Config Example:
        {
            "prompt": "Generate a comprehensive report on AI trends in a given industry based on the extracted data."
        }
        """

        prompt = config.get("prompt", "")

        json_state = json.dumps(state, default=self.custom_serializer)


        if "{state}" in prompt:
            prompt = prompt.format(state=json_state)
        else:
            # Alternatively, you could append the entire state to the prompt:
            prompt += "\nContext: " + json_state

        print('executing llm node with the prompt: ' + prompt)
        if not prompt:
            raise ValueError("No prompt provided for LLM node")
        
        # Call the LLM with the prompt
        response = self.llm([HumanMessage(content=prompt)])
        
        
        # Store the LLM output in the state (under key 'llm_output')
        node_id = config.get("node_id", "-1")
        unique_key = f"llm_output_{node_id}"

        state[unique_key] = response

        return state
    

    def _make_node_handler(self, handler, config):
        def node_func(state):
            print("Executing node with config:", config)
            return handler(state, config)
        return node_func

    def build_and_run_workflow(self, workflow_id: int) -> dict:
        """Builds and executes a workflow based on its nodes and edges."""
        # Load the workflow
        try:
            workflow = Workflow.objects.get(id=workflow_id)
        except ObjectDoesNotExist:
            return {"error": "Workflow not found"}

        # Initialize the LangGraph graph
        graph = Graph()
        nodes = workflow.nodes.all()
        edges = workflow.edges.all()

        # Map node UUIDs to string identifiers for LangGraph
        node_map = {}
        for node in nodes:
            node_id = str(node.id)
            node_map[node.id] = node_id
            # Capture the node's config and type in default arguments.

            if node.node_type not in self.node_handlers:
                raise ValueError(f"Unsupported node type: {node.node_type}")
            
            print(f"Adding node {node_id}: type={node.node_type}, config={node.config}")

            node_config = dict(node.config)  # make a shallow copy
            node_config["node_id"] = node_id  # inject the node id
            
            graph.add_node(
                node_id,
                self._make_node_handler(self.node_handlers[node.node_type], node_config)
            )

        # Add edges to define the flow
        for edge in edges:
            source_id = node_map[edge.source.id]
            target_id = node_map[edge.target.id]
            graph.add_edge(source_id, target_id)

        # Identify entry and exit points
        all_targets = set(edge.target.id for edge in edges)
        all_sources = set(edge.source.id for edge in edges)
        
        entry_nodes = [node for node in nodes if node.id not in all_targets]
        exit_nodes = [node for node in nodes if node.id not in all_sources]

        if not entry_nodes:
            raise ValueError("No entry node found (no node without incoming edges)")
        if not exit_nodes:
            raise ValueError("No exit node found (no node without outgoing edges)")
        
        # For simplicity, assume one entry and one exit (extend for multiple if needed)
        graph.set_entry_point(node_map[entry_nodes[0].id])
        graph.set_finish_point(node_map[exit_nodes[0].id])

        # Compile and execute the graph
        compiled_graph = graph.compile()
        initial_state = {}
        # try:
        final_state = compiled_graph.invoke(initial_state)
        # except Exception as e:
            # final_state = {"error": f"Execution failed: {str(e)}"}

        # Save the result to the workflow
        report = final_state.get("report", final_state.get("error", "No report generated"))
        workflow.last_result = report
        workflow.save()

        return final_state
