# agent/tools.py
from langchain_core.tools import tool
import arxiv
import time
import os
from pypdf import PdfReader
import wikipedia
from googleapiclient.discovery import build
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import requests
import logging
from . import prompts
from . import models
from io import BytesIO
import json
import base64
import textwrap
import networkx as nx
import matplotlib.pyplot as plt
import agent.utils as utils

logger = logging.getLogger(__name__)


class ApiRateLimiter:
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.interval = 60.0 / requests_per_minute
        self.last_request_time = 0

    def wait_for_slot(self):
        current_time = time.time()
        elapsed_time = current_time - self.last_request_time
        if elapsed_time < self.interval:
            sleep_time = self.interval - elapsed_time
            # print(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)
        self.last_request_time = time.time()


# Initialize a rate limiter for arXiv (e.g., 20 requests per minute, well within limits)
# ArXiv generally recommends 3 seconds between requests if making many, so 20/min is very safe.
arxiv_rate_limiter = ApiRateLimiter(requests_per_minute=20)
wikipedia_rate_limiter = ApiRateLimiter(requests_per_minute=20)  # safe rate for anonymous access
llm_rate_limiter = ApiRateLimiter(requests_per_minute=10)

@tool
def select_arXiv_papers(query: str, max_results: int = 3) -> str:
    """
    Selects papers from arXiv based on a query and returns their titles, abstracts, and links.

    Args:
        query (str): The search query (e.g., "machine learning").
        max_results (int): The maximum number of papers to retrieve. Defaults to 3.

    Returns:
        str: A formatted string containing the selected papers' titles, summaries, and URLs.
    """
    arxiv_rate_limiter.wait_for_slot()  # Apply rate limit before the API call

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order=arxiv.SortOrder.Descending
    )

    papers_info = []
    # No rate limit needed here as client.results internally fetches results in batches with delays.
    for result in client.results(search):
        papers_info.append({
            'title': result.title,
            'abstract': result.summary,
            'url': result.entry_id  # This is the main arXiv abstract page URL
        })
    markdown_string = ""
    logger.info(f"select_arXiv_papers: number of papers found: {len(papers_info)}")
    for item in papers_info:
        markdown_string += f"### [{item['title']}]({item['url']})\n"  # Title as a hyperlink heading
        markdown_string += f"{item['abstract']}\n"
        markdown_string += f"\n---\n"  # Separator for better readability

    return markdown_string


def _extract_text_from_pdf(filepath: str, marker="---PAGE_BREAK---", is_paper=True) -> tuple[str, dict]:
    """
    Extracts text from a PDF file, adding a marker at the beginning of each new page.
    Not used as a tool but rather as an internal helper function.

    Args:
        pdf_path (str): The path to the PDF file.
        marker (str): The string to use as a page break marker.

    Returns:
        str: The extracted text with page markers.
    """
    logger.debug(f"Current working directory: {os.getcwd()}")
    try:
        reader = PdfReader(filepath)
        full_text = []

        for i, page in enumerate(reader.pages):
            # Add a page marker before extracting text for each page (except the first)
            if i > 0:
                full_text.append(f"\n{marker} Page {i + 1} {marker}\n")
            else:
                # indicate the beginning of the text with a special marker
                full_text.append(f"---BEGIN_PDF_TEXT---\nPage {i + 1}\n")

            # Extract text from the current page
            extracted_page_text = page.extract_text()
            full_text.append(extracted_page_text)

        metadata = {
            'title': str(reader.metadata.title) + prompts.missing_field_hint_prompt,
            'authors': str(reader.metadata.author) + prompts.missing_field_hint_prompt,
            'url': filepath
        }
        if is_paper:
            metadata['abstract'] = str(
                reader.metadata.subject) + prompts.missing_field_hint_prompt
        return "".join(full_text), metadata
    except Exception as e:
        logger.error(f"_extract_text_from_pdf: Error extracting text from PDF {filepath}: {e}")
        return "", {}


def retrieve_arXiv_full_text(paper_url: str, download_dir: str = utils.local_paper_dir) -> tuple[str, dict]:
    """
    Retrieves the full text of a paper (by downloading and parsing its PDF)
    and returns it along with its metadata.
    Not used as a tool but rather as an internal helper function.

    Args:
        paper_url (str): The URL of the arXiv paper (e.g., from the select_papers output).
        download_dir (str): A temporary directory to store downloaded PDFs before parsing.

    Returns:
        tuple[str, dict]: A tuple containing the full text of the paper and its metadata.
    """
    arxiv_rate_limiter.wait_for_slot()  # Apply rate limit before the API call

    # Extract the arXiv ID from the URL
    try:
        arxiv_id = paper_url.split('/')[-1]
    except IndexError:
        logger.error(f"retrieve_arXiv_full_text: Invalid arXiv URL: {paper_url}")
        return "", {}

    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])

    temp_filepath = None  # Initialize to None
    full_text = ""
    metadata = {}

    try:
        paper = next(client.results(search))

        # Create temporary download directory if it doesn't exist
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        filename = f"{arxiv_id}.pdf"
        temp_filepath = os.path.join(download_dir, filename)

        # Download the PDF
        logger.info(f"retrieve_arXiv_full_text: Downloading PDF for '{paper.title}' to {temp_filepath}...")
        logger.debug(f"retrieve_arXiv_full_text: PDF URL: {paper.pdf_url}")
        # paper.download_pdf(dirpath=download_dir, filename=filename)
        # download_pdf is not working, so we use the following code instead
        # Mimic a browser's User-Agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        }

        # Make the request and stream the content to save memory for large files
        response = requests.get(paper.pdf_url, stream=True, headers=headers, timeout=30)

        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # Save the content to a file
        with open(temp_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"retrieve_arXiv_full_text: Successfully downloaded PDF to: {temp_filepath}. Extracting text...")

        # Extract text from PDF
        full_text, _ = _extract_text_from_pdf(temp_filepath)
        metadata = {
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'url': paper.entry_id,
            'abstract': paper.summary
        }

    except StopIteration:
        logger.warning(f"retrieve_arXiv_full_text: Paper with ID '{arxiv_id}' not found.")
    except Exception as e:
        logger.error(f"retrieve_arXiv_full_text: Error downloading or parsing paper {arxiv_id}: {e}")
    finally:
        # Clean up the downloaded PDF file
        if temp_filepath and os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
                logger.debug(f"retrieve_arXiv_full_text: Deleted temporary PDF file {temp_filepath}.")
            except Exception as e:
                logger.error(f"retrieve_arXiv_full_text: Error cleaning up temporary file {temp_filepath}: {e}")
    return full_text, metadata



@tool
def select_wikipedia_articles(query: str, max_results: int = 3) -> str:
    """
    Selects Wikipedia articles based on a search query and returns their titles,
    summaries (snippets), and URLs.

    Args:
        query (str): The search query.
        max_results (int): The maximum number of articles to retrieve. Defaults to 3.

    Returns:
        str: A formatted string containing the selected articles' titles, summaries, and URLs.
    """
    wikipedia_rate_limiter.wait_for_slot()  # Apply rate limit before the search call
    markdown_string = ""
    try:
        # wikipedia.search() returns a list of titles
        titles = wikipedia.search(query, results=max_results)

        articles_info = []
        for title in titles:
            wikipedia_rate_limiter.wait_for_slot()  # Apply rate limit before each summary call
            try:
                # wikipedia.summary() returns a concise summary for a given title
                # auto_suggest=False to prevent additional API calls for suggestions
                summary = wikipedia.summary(title, sentences=5, auto_suggest=False, redirect=True)
                # fetch the page object
                page = wikipedia.page(title, auto_suggest=False, redirect=True)
                url = page.url

                articles_info.append({
                    'title': title,
                    'summary': summary,
                    'url': url
                })
            except wikipedia.exceptions.PageError:
                # This can happen if a search result title doesn't map to a direct page
                logger.warning(f"select_wikipedia_articles: Wikipedia page '{title}' not found or could not be summarized.")
            except wikipedia.exceptions.DisambiguationError as e:
                # Handle disambiguation pages by just noting them or picking the first option
                logger.warning(f"select_wikipedia_articles: Disambiguation page '{title}'. Options: {e.options}. Skipping for now.")
            except Exception as e:
                logger.error(f"select_wikipedia_articles: An unexpected error occurred for retrieved page '{title}': {e}")

        for item in articles_info:
            markdown_string += f"### [{item['title']}]({item['url']})\n"  # Title as a hyperlink heading
            markdown_string += f"{item['summary']}\n"
            markdown_string += f"\n---\n"  # Separator for better readability

    except Exception as e:
        logger.error(f"select_wikipedia_articles: An error occurred during Wikipedia search: {e}")

    return markdown_string


def retrieve_wikipedia_full_text(article_title_or_url: str) -> tuple[str, dict]:
    """
    Retrieves the full text content of a Wikipedia article given its title or URL.
    Not used as a tool but rather as an internal helper function.

    Args:
        article_title_or_url (str): The title of the Wikipedia article
                                     (e.g., "Artificial intelligence") or its full URL.

    Returns:
        list[str]: A list containing one formatted string with the full text of the article.
                   Returns an empty list if retrieval fails.
    """
    wikipedia_rate_limiter.wait_for_slot()  # Apply rate limit before the API call
    page_content, metadata = "", {}
    try:
        if "wikipedia.org/wiki/" in article_title_or_url:
            # Simple extraction from URL
            title = article_title_or_url.split('/')[-1].replace('_', ' ')
        else:
            title = article_title_or_url

        page = wikipedia.page(title, auto_suggest=False, redirect=True)  # Get the Page object

        metadata = {
            'title': page.title,
            'url': page.url,
            'summary_snippet': page.summary,  # A shorter summary from the Wikipedia object itself
            'categories': [c for c in page.categories],
            'links': [l for l in page.links]  # Be cautious, links can be very numerous
        }

        page_content = page.content

    except wikipedia.exceptions.PageError:
        logger.warning(f"retrieve_wikipedia_full_text: Wikipedia page '{article_title_or_url}' not found.")
    except wikipedia.exceptions.DisambiguationError as e:
        logger.warning(f"retrieve_wikipedia_full_text: Disambiguation page '{article_title_or_url}'. Options: {e.options}. Please be more specific.")
    except Exception as e:
        logger.error(f"retrieve_wikipedia_full_text: An unexpected error occurred during Wikipedia retrieval for '{article_title_or_url}': {e}")
    return page_content, metadata


@tool
def web_search(query: str, num_results: int = 3) -> str:
    """
    Performs a web search and summarizes the top results.
    Useful for finding general information, news, definitions, or answering factual questions.

    Args:
        query (str): The search query. Be precise and concise.
        num_results (int): The maximum number of top search results to return.
                            Defaults to 3.

    Returns:
        str: A formatted string containing the summarized search results, or a message
             indicating no results were found.
    """
    try:
        service = build("customsearch", "v1", developerKey=os.environ["GOOGLE_SEARCH_API_KEY"])
        search_results = service.cse().list(q=query, cx=os.environ["GOOGLE_SEARCH_ENGINE_ID"],
                                            num=num_results).execute()

        if "items" not in search_results:
            return "No relevant search results found for your query."

        formatted_results = []
        for i, result in enumerate(search_results["items"]):
            # Customize how each result is presented to the LLM
            formatted_results.append(
                f"Result {i + 1}:\n"
                f"Title: {result.get('title', 'N/A')}\n"
                f"Snippet: {result.get('snippet', 'N/A')}\n"
                f"Link: {result.get('link', 'N/A')}"
            )

        return "\n\n".join(formatted_results)

    except Exception as e:
        return f"An error occurred during Google Search: {e}"


from datetime import datetime


@tool
def get_current_date() -> str:
    """
    Returns the current date based on the system time.

    Returns:
        str: The current date in ISO format (YYYY-MM-DD).

    Example:
        >>> get_current_date()
        '2025-06-09'
    """
    return datetime.now().date().isoformat()


def summarize_with_preprompt(text: str, metadata: dict, difficulty_level: str = "medium") -> str:
    """
    Summarizes a text using direct LLM prompting, incorporating metadata and
    adjusting difficulty. Intended for texts that fit within a single LLM context window.
    Not used as a tool but rather as an internal helper function.

    Args:
        text (str): The full text content.
        metadata (dict): Dictionary with paper/article metadata (e.g., title, authors, url, abstract).
        difficulty_level (str): 'easy', 'medium', 'hard'. Default is 'medium'.

    Returns:
        str: The summarized text.
    """
    llm_rate_limiter.wait_for_slot()

    if "abstract" in metadata:  # Likely a paper
        prompt_template = prompts.arXiv_summary_prompt
        # Ensure authors list is string
        metadata['authors'] = ', '.join(metadata.get('authors', [])) if isinstance(metadata.get('authors'), list) else metadata.get('authors','N/A')
    else:
        prompt_template = prompts.wikipedia_summary_prompt
        extra_metadata_str = ""
        if metadata.get('categories'):
            extra_metadata_str += f"Categories: {', '.join(metadata['categories'])}\n"


    # Create the prompt
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["title", "url", "text", "difficulty_level", "difficulty_level_prompt"] + (
            ["authors", "abstract"] if "abstract" in metadata else ["extra_metadata_str"])
    )

    llm_chain = prompt | models.llm_summary_model | utils.parser

    # Prepare input for the chain
    input_data = {
        "title": metadata.get('title', 'N/A'),
        "url": metadata.get('url', 'N/A'),
        "text": text,
        "difficulty_level": difficulty_level,
        "difficulty_level_prompt": prompts.DifficultyLevel[difficulty_level]
    }
    if "abstract" in metadata:
        input_data["authors"] = metadata['authors']
        input_data["abstract"] = metadata['abstract']
    else:
        input_data["extra_metadata_str"] = extra_metadata_str

    try:
        # Check if text length is within typical context window limits
        # (e.g., 100k tokens for GPT-4o, but for safety, aim lower like 50-70k characters)
        # This is a rough character count approximation of token count.
        if len(text) > utils.max_characters_for_summary_input:  # Adjust based on your LLM's context window and typical token size
            logger.warning(f"summarize_with_preprompt: Text might be too long for direct summarization ({len(text)} characters). Truncating to {utils.max_characters_for_summary_input} characters for direct summarization.")
            # Forcing a cut-off if it's too long to be safe
            text = text[:utils.max_characters_for_summary_input]
        response = llm_chain.invoke(input_data)
        return response
    except Exception as e:
        logger.error(f"summarize_with_preprompt: Error during direct LLM summarization: {e}")
        return "Summarization failed."


@tool
def summarize_document(source_type: str, identifier: str,
                       difficulty_level: str = "medium") -> str:
    """
    Method to retrieve a document and summarize it based on a specified difficulty.

    Args:
        source_type (str): 'arxiv' or 'wikipedia' or 'local' (for local repository).
        identifier (str): URL for arXiv, title/URL for Wikipedia, or title of the document in the local repository.
        difficulty_level (str): 'easy', 'medium', 'hard'. Default is 'medium'.

    Returns:
        str: The summarized text.
    """

    # Step 1: Retrieve the full text and metadata using the appropriate subroutine
    if source_type.lower() == 'arxiv':
        logger.info(f"summarize_document: Retrieving full text from arXiv for: {identifier}")
        full_text, metadata = retrieve_arXiv_full_text(identifier)
    elif source_type.lower() == 'wikipedia':
        logger.info(f"summarize_document: Retrieving full text from Wikipedia for: {identifier}")
        full_text, metadata = retrieve_wikipedia_full_text(identifier)
    elif source_type.lower() == 'local':
        logger.info(f"summarize_document: Retrieving full text from local file for: {identifier}")
        full_text, metadata = _extract_text_from_pdf(utils.local_paper_dir + identifier + ".pdf")
    else:
        return "Invalid source type. Please choose 'arxiv' or 'wikipedia' or 'file'."

    if not full_text:
        return f"Could not retrieve full text for {identifier} from {source_type}."

    summary = summarize_with_preprompt(full_text, metadata, difficulty_level)

    return summary


@tool
def refine_query_arXiv(query: str) -> str:
    """
    Method to rephrase, clarify, or expand upon ambiguous or unspecific user queries.
    Input should be the original user's query.

    Args:
        query (str): The original user's query.

    Returns:
        str: The refined query.
    """
    llm_rate_limiter.wait_for_slot()
    prompt_template = prompts.query_refiner_prompt
    refinement_prompt_template = PromptTemplate(template=prompt_template, input_variables=["original_query"])
    refinement_chain = refinement_prompt_template | models.llm_refinement_model | utils.parser
    refined_query = refinement_chain.invoke({"original_query": query})
    return refined_query


# Tool to provide a standalone explanation of a topic using the LLM only (no external research).
# Acts as a benchmark for comparing with tools that use retrieval-augmented generation (RAG).
@tool
def explain_topic(topic: str, difficulty_level: str = "medium") -> str:
    """
    Generates a standalone explanation of a given topic using an LLM,
    without access to external context or research. This serves as a
    baseline or comparison method.

    Args:
        topic (str): The subject to explain.
        difficulty_level (str): The target audience level: 'easy', 'medium', or 'hard'. Defaults to 'medium'.

    Returns:
        str: An LLM-generated explanation of the topic tailored to the specified difficulty level.
    """
    llm_rate_limiter.wait_for_slot()
    prompt_template = prompts.explainer_prompt
    prompt_template = PromptTemplate(
        template=prompt_template,
        input_variables=["topic", "difficulty_level", "difficulty_level_prompt"]
    )

    llm_chain = prompt_template | models.llm_explainer_model | utils.parser

    result = llm_chain.invoke({
        "topic": topic,
        "difficulty_level": difficulty_level,
        "difficulty_level_prompt": prompts.DifficultyLevel[difficulty_level]
    })

    return result


# Tool to infer difficulty level based on user input and topic
@tool
def infer_difficulty_level(topic: str, user_input: str) -> str:
    """
    Uses an LLM to infer the appropriate difficulty level ('easy', 'medium', or 'hard')
    based on the user's input and topic. This helps the agent choose the correct
    explanation style automatically.

    Args:
        topic (str): The subject the user is asking about.
        user_input (str): The user's request or question related to the topic.

    Returns:
        str: One of 'easy', 'medium', or 'hard'.
    """
    llm_rate_limiter.wait_for_slot()
    prompt_template = prompts.infer_difficulty_level_prompt

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["topic", "user_input"]
    )

    llm_chain = prompt | models.llm_infer_difficulty_model | utils.parser
    response = llm_chain.invoke({"topic": topic, "user_input": user_input})
    return response.strip().lower()


@tool
def extract_concept_graph(source_type: str, identifier: str) -> str:
    """
    Extracts and visualizes a concept graph from a document source, saving it as a PNG,
    and returns its Base64 encoded string for display.

    Args:
        source_type (str): One of 'arxiv', 'wikipedia', or 'local'.
        identifier (str): URL for arXiv, title/URL for Wikipedia, or local PDF filename (without .pdf extension).

    Returns:
        str: The string representation of a Python dictionary with 'nodes', 'edges' representing the concept graph.

    This tool is automatically triggered when the user mentions 'concept graph'. It not only extracts
    the graph but also visualizes it and provides the image data for direct display.
    """
    if source_type.lower() == 'arxiv':
        full_text, metadata = retrieve_arXiv_full_text(identifier)
    elif source_type.lower() == 'wikipedia':
        full_text, metadata = retrieve_wikipedia_full_text(identifier)
    elif source_type.lower() == 'local':
        full_text, metadata = _extract_text_from_pdf(utils.local_paper_dir + identifier + ".pdf")
    else:
        raise ValueError(f"Unsupported source_type: {source_type}")

    if not full_text:
        raise ValueError(f"Failed to retrieve content for: {identifier} from source: {source_type}")

    metadata_text = f"Title: {metadata.get('title', '')}\nAbstract: {metadata.get('abstract', '')}\n"
    combined_text = metadata_text + "\n\n" + full_text[:utils.max_characters_for_summary_input]

    prompt_template = prompt_template = PromptTemplate(
    template=prompts.extract_concept_graph_prompt,
    input_variables=["text"]
)


    chain = prompt_template | models.llm_summary_model | utils.parser

    try:
        raw_response = chain.invoke({"text": combined_text})

        if raw_response.startswith("```json") and raw_response.endswith("```"):
            json_string = raw_response[len("```json"):].strip()
            if json_string.endswith("```"):
                json_string = json_string[:-len("```")].strip()
        else:
            json_string = raw_response.strip()

        concept_graph = json.loads(json_string)
        logger.debug(f"extract_concept_graph: Extracted concept graph from {source_type} for {identifier}: {concept_graph}")
        # --- Graph Visualization and Saving ---
        G = nx.DiGraph()

        # Add nodes and edges
        for node in concept_graph.get('nodes', []):
            G.add_node(node['id'])

        for edge in concept_graph.get('edges', []):
            G.add_edge(edge['source'], edge['target'], relation=edge.get('relation', ''))

        # Spring layout TODO: fix layout 
        pos = nx.spring_layout(G, k=1.8, iterations=200, seed=42) 

        plt.figure(figsize=(30, 20)) 
        ax = plt.gca()
        ax.set_aspect('equal')

        
        base_node_size = 3500 # Minimum node size, adjusted upwards
        font_size = 10       # Font size for node labels
        max_label_width = 15 # Max characters per line for wrapping
        label_font_weight = 'bold'
        label_color = 'black'

        node_sizes = {}
        node_labels_wrapped = {}

        for node_id in G.nodes():
            original_label = node_id
            # Wrap text based on max_label_width
            wrapped_label = "\n".join(textwrap.wrap(original_label, width=max_label_width))
            node_labels_wrapped[node_id] = wrapped_label

            # Estimate required size based on wrapped text dimensions
            num_lines = wrapped_label.count('\n') + 1
            max_line_length = max(len(line) for line in wrapped_label.split('\n'))

            width_factor = font_size * 20 #
            height_factor = font_size * 30 

            estimated_node_width = max_line_length * width_factor
            estimated_node_height = num_lines * height_factor

        
            estimated_node_size = max(base_node_size, (estimated_node_width * estimated_node_height) / 1500)

            node_sizes[node_id] = estimated_node_size

        # Draw nodes with dynamically calculated sizes
        node_size_list = [node_sizes[node] for node in G.nodes()]
        nx.draw_networkx_nodes(G, pos, node_color='skyblue', node_size=node_size_list, alpha=0.9, linewidths=1, edgecolors='black')

        # Draw edges with arrows
        nx.draw_networkx_edges(
            G, pos,
            arrowstyle='-|>',
            arrowsize=25,
            width=1.8,
            edge_color='gray',
            connectionstyle='arc3,rad=0.1' # Slightly curved edges
        )

        # Draw labels using plt.text for multi-line support
        for node, (x, y) in pos.items():
            plt.text(x, y, node_labels_wrapped[node],
                     horizontalalignment='center',
                     verticalalignment='center',
                     fontsize=font_size,
                     color=label_color,
                     fontweight=label_font_weight,
                     bbox=dict(facecolor='white', alpha=0.0, edgecolor='none', pad=0.5)) # Transparent background for text

        # Draw edge labels
        edge_labels = nx.get_edge_attributes(G, 'relation')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='darkgreen', font_size=10)

        plt.title(f"Concept Graph for {identifier}", size=18)
        plt.axis('off') # Hide axes
        plt.tight_layout() # Adjust layout to prevent labels from overlapping the edge of the figure


        # Create a BytesIO object to save the plot to memory
        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        plt.close() # Close the plot to free memory

        # Get the Base64 encoded string from the buffer's content
        encoded_string = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Instead of returning the string encoding the image, locally store it in the resources folder
        filename = f"concept_graph_encoding.txt"
        filepath = os.path.join(utils.local_resource_dir, filename)
        with open(filepath, "w") as f:
            f.write(encoded_string)


        return "CONCEPT_GRAPH: \n" + str(concept_graph)

    except Exception as e:
        # Re-raising specific errors or logging them could be useful here
        raise ValueError(f"Failed to extract concept graph: {e}")


def get_all_tools():
    return [select_arXiv_papers, select_wikipedia_articles, summarize_document, web_search, get_current_date,
            refine_query_arXiv, infer_difficulty_level, extract_concept_graph]
    # return[explain_topic] # Different tool for standalone explanations without retrieval
