from __future__ import annotations
from typing import List, Dict, Any
import os, json, csv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from configs.errors_prompt import ERRORS_PROMPT

from dotenv import load_dotenv
load_dotenv()


class FactErrorGenerator:
    """
    LangChain-based pipeline that:
      - Iterates over transcript fact JSON files in a folder
      - Selects 10 clinically manipulable facts per consult
      - Performs controlled corruption of source_text
      - Produces CSV-ready rows with filenames
    """

    def __init__(self, model: str = "gpt-5-nano"):
        self.llm = ChatOpenAI(model=model)
        self.parser = JsonOutputParser()

        # External system prompt
        self.PROMPT_ERROR_SYSTEM = ERRORS_PROMPT

        # ChatPromptTemplate
        self.error_prompt = ChatPromptTemplate.from_messages([
            ("system", self.PROMPT_ERROR_SYSTEM),
            ("user", "Here are the facts:\n\n{facts_json}")
        ])


    # ---------------- Generate errors for a single consult ----------------
    def generate_fact_errors(
        self,
        consult_name: str,
        facts_dict: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Sends facts to LLM, selects 10 critical facts, returns altered versions.
        """
        json_payload = json.dumps(facts_dict, indent=2)

        out = (self.error_prompt | self.llm | self.parser).invoke(
            {"facts_json": json_payload}
        )

        rows = []
        for idx, item in enumerate(out, start=1):
            filename = f"{consult_name}_{idx}"  # user will create this transcript file

            rows.append({
                "consult_name": consult_name,
                "fact_id": item.get("fact_id"),
                "error_type": item.get("error_type"),
                "original_source_text": item.get("original_source_text"),
                "altered_source_text": item.get("altered_source_text"),
                "filename": filename,
                "section": item.get("fact_section")
            })

        return rows
    

    # ---------------- Iterate over all consults in a folder ----------------
    def generate_fact_errors_for_all_consults(
        self,
        transcript_facts_folder: str
    ) -> List[Dict[str, Any]]:
        """
        Iterates over all JSON files in transcript_facts_folder,
        generates altered facts for each consult, and returns combined rows.
        """
        all_rows = []
        i = 0
        for fname in os.listdir(transcript_facts_folder):
            if i == 0:
                i+= 1
                continue
            if not fname.endswith(".json"):
                continue

            consult_name = fname.replace(".json", "")
            path = os.path.join(transcript_facts_folder, fname)

            with open(path, "r", encoding="utf-8") as f:
                facts_dict = json.load(f)
            print("Processing consult:", consult_name)
            rows = self.generate_fact_errors(consult_name, facts_dict)
            all_rows.extend(rows)
            i += 1
            if i % 20 == 0:
                break

        return all_rows


    # ---------------- Save CSV ----------------
    @staticmethod
    def save_to_csv(
        rows: List[Dict[str, Any]],
        csv_path: str
    ):
        """
        Writes the rows to CSV in the requested format.
        """
        fields = [
            "consult_name",
            "fact_id",
            "error_type",
            "original_source_text",
            "altered_source_text",
            "filename",
            "section"
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

agent = FactErrorGenerator(model="gpt-5")

import os
current_dir = os.path.dirname(os.path.abspath(__file__))
transcript_facts_folder = os.path.join(current_dir, "output", "transcript_facts")

all_rows = agent.generate_fact_errors_for_all_consults(transcript_facts_folder)
agent.save_to_csv(all_rows, os.path.join(current_dir, "all_consults_errors.csv"))
