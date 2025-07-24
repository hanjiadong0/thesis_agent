# agent/core.py
from typing import List, TypedDict, Union, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, AnyMessage, SystemMessage
from langchain_core.tools import Tool
from langchain_core.runnables import RunnableConfig
import logging
from . import prompts

logger = logging.getLogger(__name__)
# Example AgentState - adjust based on your actual state
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

class Agent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        tool_descriptions = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        tool_names = ", ".join([tool.name for tool in self.tools])

        system_prompt = SystemMessage(
            content=prompts.system_prompt.format(tool_descriptions=tool_descriptions))

        llm_with_tools = self.llm.bind_tools(self.tools)
        # Node 1: Agent Node (LLM decides Thought/Action/Answer)
        def assistant(state: AgentState):
            return {
                "messages": [llm_with_tools.invoke([system_prompt] + state["messages"])]
            }

        # Node 2: Tool Node (Execute the chosen tool)
        def execute_tool(state: AgentState):
            messages = state["messages"]
            last_message = messages[-1]

            # Ensure the last message contains tool calls
            if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
                logger.error("execute_tool: Expected last message to be an AIMessage with tool_calls.")
                raise ValueError("Expected last message to be an AIMessage with tool_calls.")

            tool_calls = last_message.tool_calls
            observations = []

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Find and execute the tool
                found_tool = next((t for t in self.tools if t.name == tool_name), None)
                if not found_tool:
                    logger.error(f"execute_tool: Tool '{tool_name}' not found.")
                    raise ValueError(f"Tool '{tool_name}' not found.")

                try:
                    # Invoke the tool with its arguments
                    tool_output = found_tool.invoke(tool_args)
                    observations.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
                except Exception as e:
                    observations.append(
                        ToolMessage(content=f"Error executing tool {tool_name}: {e}", tool_call_id=tool_call["id"]))
                    logger.error(f"execute_tool: Error executing tool {tool_name}: {e}")

            return {
                "messages": observations,
            }

        # Node 3 (Conditional Edge Logic): Decide next step
        def should_continue(state: AgentState) -> str:
            messages = state["messages"]
            last_message = messages[-1]

            # If the last message is a ToolMessage, it means the tool has executed,
            # so the agent should think again.
            if isinstance(last_message, ToolMessage):
                return "continue"

            # If the last message is an AIMessage, check if it's a final answer
            if isinstance(last_message, AIMessage) and not last_message.tool_calls:
                # Check if the LLM generated a "Final Answer:" pattern or just a direct response
                # This is a bit heuristic; for robust ReAct, the prompt guides it.
                # LangChain's bind_tools will prevent direct "Final Answer" output if tools are callable.
                # Instead, the agent simply provides content without tool_calls.
                return "end"

            # Default to continue if an action was decided (tool_calls present)
            return "continue"

        # Add the nodes
        workflow.add_node("research_agent", assistant)
        # workflow.add_node("tools", ToolNode(tools=tools))
        workflow.add_node("research_tool_executor", execute_tool)

        # Set the entry point
        workflow.add_edge(START, "research_agent")
        # alternatively: workflow.set_entry_point("agent")

        # Define the conditional edge from the agent
        workflow.add_conditional_edges(
            "research_agent",  # Source node
            # tools_condition,
            should_continue,  # Function to determine next node
            {
                "continue": "research_tool_executor",  # If agent needs to call a tool, go to 'tool' node
                "end": END  # If agent has a final answer, end the graph
            }
        )

        # Define the edge from the tool back to the agent (loop)
        workflow.add_edge("research_tool_executor", "research_agent")

        return workflow.compile()

    def invoke(self, input_data):
        return self.graph.invoke(input_data)

    async def astream(self, input_data: AgentState, config: RunnableConfig = None):
        async for chunk in self.graph.astream(input_data, config=config):
            yield chunk
