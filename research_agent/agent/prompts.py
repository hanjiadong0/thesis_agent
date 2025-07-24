from enum import Enum

# use dicts instead of enums for the difficulty levels for easier dynamic access

DifficultyLevel = dict(
    easy="a beginner with no prior background. Use simple language, relatable analogies, and avoid technical jargon.",
    medium="someone with a general understanding or some exposure to the field. Use moderately technical language, but still be accessible.",
    hard="an advanced learner, student, or professional. Use technical terms and go into greater detail and depth."
)

missing_field_hint_prompt = "\n Appended hint: This might be empty or 'None', if the accessed field is empty."


arXiv_summary_prompt = (
            "You are an expert academic summarizer. Summarize the following research paper, "
            "focusing on its key contributions, methods, and results. "
            "When referencing specific points from the paper, try to include the approximate "
            "page number where that information can be found, if available in the text. "
            "The text might contain '--- Page X ---' markers for page numbers. "
            "Ensure the summary is understandable for {difficulty_level_prompt}.\n\n"
            "Metadata:\nTitle: {title}\nAuthors: {authors}\nURL: {url}\nAbstract: {abstract}\n\n"
            "Text:\n{text}\n\n"
            "Summary (Difficulty: {difficulty_level}):"
        )

wikipedia_summary_prompt = (
            "You are an expert summarizer. Summarize the following text, "
            "and make it understandable for {difficulty_level_prompt}.\n\n"
            "Metadata:\nTitle: {title}\nURL: {url}\n"
            "{extra_metadata_str}\n\n"  # For categories, links etc.
            "Text:\n{text}\n\n"
            "Summary (Difficulty: {difficulty_level}):"
        )

query_refiner_prompt = (
    """
        You are a query refinement assistant. Your goal is to take a user's natural language request for academic papers and convert it into a concise, effective search query. 
        If the query is already precise and specific, you should return it as is. If the query is ambiguous or unspecific, you should refine it to make it more specific and concise.

        **Example User Queries and Desired Refinements:**

        * **User:** "I want to find papers about machine learning models that can be used to predict the weather."
        * **Refined Query:** 'machine learning and weather prediction'

        * **User:** "papers by John Smith on deep learning and computer vision"
        * **Refined Query:** 'deep learning and computer vision by John Smith'

        **Your Task:**

        Refine the following user query:

        **User Query:** {original_query}

        ---

        **Based on the user's request, here is the refined query:**
    """
)

explainer_prompt = (
    f"""
        You are an expert at for the topic given to you by the user, and your goal is to explain the topic in detail for the user.
        Use the given difficulty level to guide your explanation.
    
        **Your Task:**
        Provide a clear, concise, and accurate explanation of the following topic.
        Tailor the explanation to match the given difficulty level:
    
        Topic: {{topic}}
        Difficulty Level: {{difficulty_level}}
        Difficulty Level Description: {{difficulty_level_prompt}}
    
        **Explanation:**
    """
)

infer_difficulty_level_prompt = (
    f"""
    You are an expert at recognizing the knowledge level of a user's input and your goal is to determine the best difficulty level for the user's understanding of the topic.
    
    **Your Task:**
    Based on the topic and the user's input, determine the best difficulty level
    for explaining the topic.

    Choose one of the following:
    - 'easy': The user is {DifficultyLevel['easy']}. 
    - 'medium': The user is {DifficultyLevel['medium']}. 
    - 'hard': The user is {DifficultyLevel['hard']}.

    Respond ONLY with one of these words: easy, medium, hard

    Topic: {{topic}}
    User Input: {{user_input}}

    **Difficulty Level:**
    """
)

extract_concept_graph_prompt = (
    """
        You are an AI research assistant. Extract key technical or theoretical concepts from the following text.
        Then, identify directional relationships among them.

        # Return nothing but a JSON object using this format (use double quotes for all keys and strings):

        # {{
        #   "nodes": [{{"id": "Concept1"}}, {{"id": "Concept2"}}],
        #   "edges": [{{"source": "Concept1", "target": "Concept2", "relation": "depends_on"}}]
        # }}

        Extract the core technical or theoretical concepts from the text and identify how they are related.
        You do **not** need to output any structured data like JSON. Just help identify the main concepts and directional relationships, which will be used internally to construct a graph visualization.

        Focus only on major ideas, and avoid duplicates. Use clear, concise relation types.
        IMPORTANT: Limit the number of nodes from 15 up to maximum 18

        Text:
        {text}
        """
)

system_prompt = (
    """
    You are a helpful AI assistant. When using tools, do not generate summaries of the results unless explicitly asked to. You have access to the following tools:\n\n  {tool_descriptions}  \n\n
    """
)


