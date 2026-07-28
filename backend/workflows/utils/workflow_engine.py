import json
import logging
import time
from typing import Dict, Any, List, TypedDict, Optional, Callable

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI  # Updated import
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langgraph.graph import StateGraph, END

from workflows.models import Agent
from workflows.utils.workflow_monitor import WorkflowMonitor
from workflows.utils.tools_registery import ToolRegistry

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict, total=False):
    input: Dict[str, Any]
    intermediate_steps: List[Dict[str, Any]]

class WorkflowEngine:
    def __init__(self):
        self.api_keys = []
        self.agent_factory = AgentFactory(self.api_keys)
    
    def execute_workflow(self, execution_instance):
        workflow_def = execution_instance.workflow
        input_data = execution_instance.input_data
        workflow_id = str(execution_instance.id)
        
        graph_definition = workflow_def.graph_definition  # Already a dict
        start_time = time.time()
        WorkflowMonitor.log_workflow_start(workflow_id, input_data)
        
        try:
            workflow_builder = WorkflowBuilder(graph_definition, self.api_keys)
            workflow = workflow_builder.build()
            initial_state = {"input": input_data, "intermediate_steps": []}
            result = workflow.invoke(initial_state)
            
            end_node = next(node for node in graph_definition["nodes"] if node["type"] == "end")
            end_mapping = end_node["data"].get("output_mapping", {})
            
            # print('==================================================')
            # print(f'result: {result}')
            # print('==================================================')


            
            final_output = {}
            for out_key, expr in end_mapping.items():
                parts = expr.split(".")
                node_id = parts[0]
                value = result.get(node_id, {}).get("output", {})
                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                        for attr in parts[1:]:
                            value = value.get(attr)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse output from {node_id}: {value}")
                        value = None
                final_output[out_key] = value
            
            execution_instance.output_data = result #final_output
            execution_instance.status = "completed"
            execution_instance.save()
            
            execution_time = time.time() - start_time
            WorkflowMonitor.log_workflow_end(workflow_id, "completed", final_output, execution_time)
            return final_output
        
        except Exception as e:
            logger.error(f"Workflow execution error: {str(e)}", exc_info=True)
            WorkflowMonitor.log_error(workflow_id, "unknown", str(e))
            execution_instance.status = "failed"
            execution_instance.output_data = {"error": str(e)}
            execution_instance.save()
            execution_time = time.time() - start_time
            WorkflowMonitor.log_workflow_end(workflow_id, "failed", {"error": str(e)}, execution_time)
            raise

class WorkflowBuilder:
    def __init__(self, graph_definition, api_keys=None):
        if isinstance(graph_definition, str):
            self.graph_definition = json.loads(graph_definition)
        else:
            self.graph_definition = graph_definition
        self.nodes = self.graph_definition.get("nodes", [])
        self.edges = self.graph_definition.get("edges", [])
        self.api_keys = api_keys or {}
        self.agent_factory = AgentFactory(self.api_keys)
        self.workflow = StateGraph(state_schema=WorkflowState)
        
        self.start_node = next((node for node in self.nodes if node.get("type") == "start"), None)
        self.end_node = next((node for node in self.nodes if node.get("type") == "end"), None)
        if not self.start_node or not self.end_node:
            raise ValueError("Workflow must have both start and end nodes")
    
    def build(self):
        self.workflow.add_node(self.start_node["id"], self._create_start_node_func())
        predecessor_map = {edge["target"]: edge["source"] for edge in self.edges}
        
        for node in self.nodes:
            if node.get("type") == "process":
                self._add_process_node(node, predecessor_map)
        self.workflow.add_node(self.end_node["id"], self._create_end_node_func())
        
        for edge in self.edges:
            self.workflow.add_edge(edge["source"], edge["target"])
        
        self.workflow.set_entry_point(self.start_node["id"])
        return self.workflow.compile()
    
    def _create_start_node_func(self):
        def start_node_func(state: WorkflowState) -> WorkflowState:
            state["intermediate_steps"] = []
            return state
        return start_node_func
    
    def _create_end_node_func(self):
        def end_node_func(state: WorkflowState) -> WorkflowState:
            return state
        return end_node_func
    
    def _add_process_node(self, node, predecessor_map):
        node_id = node.get("id")
        node_data = node.get("data", {})
        agent_id = node_data.get("agent_id")
        input_mapping = node_data.get("input_mapping", {})
        
        def process_node(state: WorkflowState) -> WorkflowState:
            input_mapper = InputMapper()
            mapped_inputs = input_mapper.map_inputs(state, input_mapping)

            print('==================================================')
            print(f'mapped_inputs: {mapped_inputs}')
            print(f'input_mapping: {input_mapping}')
            print('==================================================')
            
            if not mapped_inputs:  # No explicit mapping provided
                predecessor_id = predecessor_map.get(node_id)
                if predecessor_id and predecessor_id in state:
                    mapped_inputs = state[predecessor_id].get("output", {})
                    if isinstance(mapped_inputs, str):
                        try:
                            mapped_inputs = json.loads(mapped_inputs)
                        except json.JSONDecodeError:
                            logger.warning(f"Node {node_id} failed to parse predecessor output as JSON: {mapped_inputs}")
                            mapped_inputs = {}
                else:
                    phase_outputs = {}
                    for step in state["intermediate_steps"]:
                        output = step["output"]
                        if isinstance(output, str):
                            try:
                                output = json.loads(output)
                                phase_outputs.update(output)
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse output from {step['node_id']}: {output}")
                    mapped_inputs = phase_outputs or state["input"]
            
            logger.debug(f"Mapped inputs for node {node_id}: {mapped_inputs}")
            
            try:
                agent = self.agent_factory.get_agent(agent_id)
                if isinstance(agent, AgentExecutor):
                    result = agent({"input": json.dumps(mapped_inputs) if isinstance(mapped_inputs, dict) else str(mapped_inputs)})
                    
                    # print('==================================================')
                    # print(f'mapped_inputs: {mapped_inputs}')
                    # print(f'result of node_id: {node_id}')
                    # print(f'result: {result}')
                    # print('==================================================')

                    result = result.get("output", result)

                else:
                    result = agent({"input": json.dumps(mapped_inputs) if isinstance(mapped_inputs, dict) else str(mapped_inputs)})                
                
               
                state[node_id] = {"output": result}
                state["intermediate_steps"].append({
                    "node_id": node_id,
                    "input": mapped_inputs,
                    "output": result
                })
            except Exception as e:
                error_msg = f"Error in node {node_id}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                state[node_id] = {"output": {"error": error_msg}}
                state["intermediate_steps"].append({
                    "node_id": node_id,
                    "input": mapped_inputs,
                    "output": {"error": error_msg},
                    "error": str(e)
                })
            return state
        
        self.workflow.add_node(node_id, process_node)

class InputMapper:
    def map_inputs(self, state: WorkflowState, input_mapping: Dict[str, Any]) -> Dict[str, Any]:
        mapped_inputs = {}

        # 👉 Handle case where input_mapping is just a string like "search"
        if isinstance(input_mapping, str):
            node_id = input_mapping
            for step in reversed(state["intermediate_steps"]):
                if step["node_id"] == node_id:
                    return step["output"] if isinstance(step["output"], dict) else {"output": step["output"]}
            return {}  # fallback if node not found

        # 👉 Normal case (dictionary mapping)
        for param, expr in input_mapping.items():
            if isinstance(expr, str) and expr.startswith("$"):
                parts = expr[1:].split(".")
                node_id = parts[0]
                node_output = None
                for step in reversed(state["intermediate_steps"]):
                    if step["node_id"] == node_id:
                        node_output = step["output"]
                        break
                if node_output and len(parts) > 1:
                    for attr in parts[1:]:
                        if isinstance(node_output, dict):
                            node_output = node_output.get(attr)
                        else:
                            node_output = None
                            break
                mapped_inputs[param] = node_output
            elif isinstance(expr, str) and expr.startswith("input."):
                key = expr.split(".", 1)[1]
                mapped_inputs[param] = state["input"].get(key)
            else:
                mapped_inputs[param] = expr

        return mapped_inputs


class AgentFactory:
    def __init__(self, api_keys=None):
        self.api_keys = api_keys or {}
    
    def get_agent(self, agent_id) -> Callable:
        try:
            agent = Agent.objects.get(id=agent_id)
            if agent.agent_type == "llm":
                return self._build_llm_agent(agent.config)
            elif agent.agent_type == "tool":
                return self._build_tool_agent(agent.config)
            else:
                raise ValueError(f"Unknown agent type: {agent.agent_type}")
        except Agent.DoesNotExist:
            raise ValueError(f"Agent with id {agent_id} does not exist")
    
    def _build_llm_agent(self, config):
        model_name = config.get("model", "gpt-5.4-mini")
        temperature = config.get("temperature", 0)
        system_prompt = config.get("system_prompt", "")

        openai_api_key = self.api_keys.get("openai")
        if not openai_api_key:
            raise ValueError("OpenAI API key not found in api_keys for ChatOpenAI")
        
        llm = ChatOpenAI(model=model_name, temperature=temperature, api_key=openai_api_key)
        
        tools = config.get("tools", [])

        if tools:
            tools = [ToolRegistry.get_tool(tool_id, self.api_keys) for tool_id in tools]
            
            # ✅ Prompt with agent_scratchpad required for function-calling agent
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "{input}"),
                ("assistant", "{agent_scratchpad}")
            ])

            agent = create_openai_functions_agent(llm, tools, prompt)
            return AgentExecutor(agent=agent, tools=tools)
        
        else:
            # ✅ Prompt without agent_scratchpad for simple LLM chain
            prompt = ChatPromptTemplate.from_template(system_prompt + "\n\nUser: {input}")
            

            chain = prompt | llm | StrOutputParser()

            def wrapped_invoke(inputs):
                # Ensure inputs are formatted properly
                if isinstance(inputs, dict) and "input" not in inputs:
                    inputs = {"input": json.dumps(inputs) if isinstance(inputs, dict) else str(inputs)}
                
                # 🖨️ Print the rendered prompt before sending it to the model
                try:
                    rendered = prompt.format(**inputs)
                    print("============ PROMPT TO LLM ============")
                    print(rendered)  # `to_string()` prints readable message sequence
                    print("=======================================")
                except Exception as e:
                    logger.warning(f"Could not render prompt for debugging: {e}")
                
                return chain.invoke(inputs)
            
            return wrapped_invoke


    def _build_tool_agent(self, config):
        tool_type = config.get("tool_type")
        return SimpleToolAgent(tool_type).process

class LLMAgent:
    def __init__(self, chain):
        self.chain = chain
    
    def process(self, inputs: Dict[str, Any]) -> str:
        try:
            input_str = self._format_input(inputs)
            return self.chain.invoke({"input": input_str})
        except Exception as e:
            logger.error(f"Error in LLM agent: {str(e)}", exc_info=True)
            return f"Error processing input: {str(e)}"
    
    def _format_input(self, inputs):
        if isinstance(inputs, dict):
            if len(inputs) > 1:
                return json.dumps(inputs)
            elif len(inputs) == 1 and isinstance(next(iter(inputs.values())), str):
                return next(iter(inputs.values()))
            else:
                return json.dumps(inputs)
        return str(inputs)

class SimpleToolAgent:
    def __init__(self, tool_type):
        self.tool_type = tool_type
    
    def process(self, inputs: Dict[str, Any]) -> str:
        try:
            input_str = self._format_input(inputs)
            if self.tool_type == "calculator":
                return str(eval(input_str))
            return f"Processed with {self.tool_type}: {input_str}"
        except Exception as e:
            logger.error(f"Error in tool agent: {str(e)}", exc_info=True)
            return f"Error processing input: {str(e)}"
    
    def _format_input(self, inputs):
        if isinstance(inputs, dict):
            if len(inputs) > 1:
                return json.dumps(inputs)
            elif len(inputs) == 1 and isinstance(next(iter(inputs.values())), str):
                return next(iter(inputs.values()))
            else:
                return json.dumps(inputs)
        return str(inputs)