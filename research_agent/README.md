# Research_Agent
## Setup Instructions

To run this application, you need to configure the following environment variables:

* **`GOOGLE_API_KEY`**: This key is required for accessing the Google Generative AI API. You can obtain it by following the instructions [here](https://ai.google.dev/gemini-api/docs/api-key?hl=en).
* **`GOOGLE_SEARCH_API_KEY`**: This key is necessary for utilizing the Google Search API. Details on how to get this key can be found [here](https://developers.google.com/custom-search/v1/overview?hl=en).
* **`GOOGLE_CSE_ID`**: This is your Custom Search Engine ID for the Google Search API. Refer to the documentation [here](https://developers.google.com/custom-search/docs/tutorial/creatingcse?hl=en) for guidance on setting this up.

The `GOOGLE_API_KEY` is used for accessing the Google Large Language Model (LLM) API, while `GOOGLE_SEARCH_API_KEY` and `GOOGLE_CSE_ID` are used for accessing the Google Search API.

## How to Run

Navigate to the `research_agent` directory and execute the application using the following command:

```bash
python -m frontend.app