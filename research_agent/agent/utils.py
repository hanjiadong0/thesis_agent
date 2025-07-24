from langchain_core.output_parsers import StrOutputParser


parser = StrOutputParser()

max_characters_for_summary_input = 70000

local_paper_dir = "texts/"

local_resource_dir = "resources/"