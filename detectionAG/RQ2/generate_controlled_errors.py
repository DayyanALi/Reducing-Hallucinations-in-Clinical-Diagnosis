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
        ])


    # ---------------- Generate errors for a single consult ----------------
    def generate_fact_errors(
        self,
        consult_name: str,
        clinical_note: str,
        transcript: str
    ) -> List[Dict[str, Any]]:

        out = (self.error_prompt | self.llm | self.parser).invoke({
            "clinical_note": clinical_note,
            "transcript": transcript
        })

        rows = []
        for idx, item in enumerate(out, start=1):
            filename = f"{consult_name}_{idx}"

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
        notes_folder: str,
        transcripts_folder: str
    ) -> List[Dict[str, Any]]:

        all_rows = []
        i = 0
        for fname in os.listdir(notes_folder):
            i += 1
            if i % 3 == 0:
                break

            if not fname.endswith(".txt"):
                continue

            consult_name = fname.replace(".txt", "")
            note_path = os.path.join(notes_folder, fname)
            transcript_path = os.path.join(transcripts_folder, f"{consult_name}.txt")

            if not os.path.exists(transcript_path):
                print(f"Skipping {consult_name}, transcript not found.")
                continue

            with open(note_path, "r", encoding="utf-8") as f:
                clinical_note = f.read()

            with open(transcript_path, "r", encoding="utf-8") as f:
                transcript = f.read()

            print("Processing consult:", consult_name)

            rows = self.generate_fact_errors(
                consult_name,
                clinical_note,
                transcript
            )

            all_rows.extend(rows)

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
notes_folder = "detectionAG/output/notes_text/gpt-5-nano"
transcripts_folder = "data/babylon_data_cleaned/babylonhealth primock57 main transcripts combined"

all_rows = agent.generate_fact_errors_for_all_consults(
    notes_folder,
    transcripts_folder
)

agent.save_to_csv(all_rows, os.path.join(current_dir, "updated_all_consults_errors.csv"))
