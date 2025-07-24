# module that contains the models for the agent
# os.environ["GOOGLE_API_KEY"] needs to set to the api key for google gen ai, see: https://ai.google.dev/gemini-api/docs/api-key?hl=en
from langchain.chat_models import init_chat_model
from langchain_ollama import ChatOllama

# llm_local_model_1 = ChatOllama(
#     model="gemma3:12b",
#     temperature=0.3,
#     # other params...
# )


_gemini_2_5_flash_model = init_chat_model("gemini-2.5-flash-preview-05-20", model_provider="google_genai")
_gemini_2_0_flash_model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")


main_llm_model = _gemini_2_0_flash_model
llm_summary_model = _gemini_2_5_flash_model
llm_refinement_model = _gemini_2_5_flash_model
llm_explainer_model = _gemini_2_5_flash_model
llm_infer_difficulty_model = _gemini_2_5_flash_model



