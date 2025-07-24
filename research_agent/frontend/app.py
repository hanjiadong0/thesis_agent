# frontend/app.py
import gradio as gr
from langchain_core.runnables import RunnableConfig

from agent.core import Agent, AgentState
from agent.tools import get_all_tools
import agent.utils as utils
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chat_models import init_chat_model
from typing import List, Tuple, Dict, Any, Union
import logging
import colorlog
import json
import re

logger = logging.getLogger(__name__)

# Initialize your LLM and tools
llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
tools = get_all_tools()
agent_instance = Agent(llm, tools)


async def research_agent_chatbot(message: str, history: List[Dict[str, Any]]):
    langgraph_messages = []
    for chat_message in history:
        if chat_message["role"] == "user":
            langgraph_messages.append(HumanMessage(content=chat_message["content"]))
        elif chat_message["role"] == "assistant":
            content = chat_message["content"]
            if f'<img src="data:image/png;base64' in chat_message["content"]: # avoid adding the image to the context of the LLM
                content = ("This a placeholder for an assistant reply with a successfully created concept graph. The message itself has been replaced by this placeholder since"
                           "it contained a very long encoded string (base64) of the actual image.")
            langgraph_messages.append(AIMessage(content=content))

    langgraph_messages.append(HumanMessage(content=message))
    agent_history = []
    thread_id = "research_agent"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        async for chunk in agent_instance.astream({"messages": langgraph_messages}, config=RunnableConfig(**config)):
            # logger.info(f"research_agent_chatbot: chunk: {chunk}")
            if "research_agent" in chunk:
                llm_output_message = chunk["research_agent"]["messages"][-1]

                if llm_output_message.tool_calls:
                    tool_call_info = [
                        {"name": tc["name"], "args": tc["args"]}
                        for tc in llm_output_message.tool_calls
                    ]
                    tool_call_str = "\n".join([f"- **Tool:** {tc['name']}\n  **Args:** {tc['args']}" for tc in tool_call_info])
                    tool_call_msg = dict(
                        role="assistant",
                        content=llm_output_message.content,
                        metadata={"title": f"🛠️ Calling Tool(s): {', '.join([tc['name'] for tc in tool_call_info])}", "status": "pending", "log": tool_call_str}
                    )
                    agent_history.append(tool_call_msg)
                else:
                    # Final LLM message after tool call
                    if agent_history:
                        last_message = agent_history[-1]
                        content = last_message["content"]

                        # --- Attempt to inject image if tool produced concept graph ---
                        try:
                            # base64_match = re.search(r"'image_base64':\s*'([^']+)'", content)
                            is_concept_graph_tool_result = "CONCEPT_GRAPH" in content
                            if is_concept_graph_tool_result:
                                with open(utils.local_resource_dir + "concept_graph_encoding.txt", "r") as f:
                                    base64_str = f.read()
                                # base64_str = base64_match.group(1)
                                img_tag = f'<img src="data:image/png;base64,{base64_str}" style="max-width:100%;">'
                                content += f"\n\n### 📊 Concept Graph Visualization:\n\n{img_tag}"
                        except Exception as e:
                            logger.warning(f"Could not extract base64 image: {e}")
                        # --- Image injection ends ---

                        final_msg = dict(
                            role="assistant",
                            content="### *Final Tool Result:* \n" + content +
                                    "\n\n### *Final LLM Answer*: \n" + llm_output_message.content
                        )
                    else:
                        final_msg = {"role": "assistant", "content": "### *Final LLM Answer*: \n" + llm_output_message.content}
                    agent_history.append(final_msg)

            elif "research_tool_executor" in chunk:
                tool_output_message = chunk["research_tool_executor"]["messages"][-1]
                last_assistant_msg_dict = agent_history[-1]

                if isinstance(last_assistant_msg_dict, dict) and "metadata" in last_assistant_msg_dict:
                    # Attempt to extract image_base64 from the tool_output_message content

                    # base64_match = re.search(r"'image_base64':\s*'([^']+)'", tool_output_message.content) # [cite: 7, 8]
                    is_concept_graph_tool_result = "CONCEPT_GRAPH" in tool_output_message.content
                    # if base64_match:
                    if is_concept_graph_tool_result:
                        # base64_str = base64_match.group(1) # [cite: 8]
                        with open(utils.local_resource_dir + "concept_graph_encoding.txt", "r") as f:
                            base64_str = f.read()
                        img_tag = f'<img src="data:image/png;base64,{base64_str}" style="max-width:100%;">' # [cite: 8]
                        # Replace the tool output content with just the image and a descriptive header
                        last_assistant_msg_dict["content"] += f"\n\n### 📊 Concept Graph Visualization:\n\n{img_tag}" # [cite: 9]
                    else:
                        # If no base64 image, still show the tool result, but you can refine this
                        last_assistant_msg_dict["content"] += f"\n\n Tool_Result: \n{tool_output_message.content}"
                    last_assistant_msg_dict["metadata"]["status"] = "done"

            yield agent_history

    except Exception as e:
        error_message = dict(role="assistant",
                             content=f"An error occurred: {str(e)}")
        logger.error(f"research_agent_chatbot: Error occurred: {str(e)}")
        agent_history.append(error_message)
        yield agent_history


def create_gradio_app():
    demo = gr.ChatInterface(
        fn=research_agent_chatbot,
        title="ReAct Research Agent",
        chatbot=gr.Chatbot(height=500, show_copy_button=True, avatar_images=(None, "../resources/Research_Assistant.jpeg"), type="messages"),
        examples=[
            "Refine the following query for arXiv retrieval: 'Ethics in generative models'. Then select a recent AI paper using the refined query. Finally summarize the paper at a medium difficulty level.",
            "Search for recent AI papers about machine learning and natural language processing.",
            "Generate a visual concept graph for a specific scientific paper"
        ],
        theme="ocean",
        type="messages",
    )
    return demo

    # In the current implementation, two API keys and an additional environment variable are required:
    # os.environ["GOOGLE_API_KEY"] needs to set to the api key for google gen ai, see: https://ai.google.dev/gemini-api/docs/api-key?hl=en
    # os.environ["GOOGLE_SEARCH_API_KEY"] needs to set to the api key for google search, see: https://developers.google.com/custom-search/v1/overview?hl=en
    # os.environ["GOOGLE_CSE_ID"] needs to set to the cse id for google search, see: https://developers.google.com/custom-search/v1/overview?hl=en
    # the first environment variable is used for access to google llm api, the latter two are used for access to google search api

    # Run via "python -m frontend.app" in research_agent directory



if __name__ == "__main__":
    colorlog.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(log_color)s%(levelname)s%(reset)s - %(name)s - %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red,bg_white',
        }
    )

    app = create_gradio_app()
    app.launch()
