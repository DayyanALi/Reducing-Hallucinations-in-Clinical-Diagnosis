import json
from random import choice
from typing import Any, Dict, List, Optional
from generator.clients import openai_gpt4
from generator.output_parsers import get_StrOutputParser
from generator.prompt_template import (get_inject_contextual_hallucination_in_diagnoses_prompt, 
                        get_inject_consistency_hallucination_in_diagnoses_prompt,
                        get_inject_consistency_hallucination_in_notes_prompt,
                        get_inject_contextual_hallucination_in_notes_prompt,
                        get_inject_diagnostic_hallucination_in_diagnoses_prompt,
                        get_inject_reasoning_hallucination_in_diagnoses_prompt)
from copy import deepcopy
from random import sample, choice
from utils.data_types import Transcript_Notes_record, Hallucinated_Notes_record

class ContextualHallucinationInjector:
    def __init__(self, model: Any, parser=None, prompt_template: Optional[str] = None):
        self.prompt = get_inject_contextual_hallucination_in_diagnoses_prompt(parser=parser, template=prompt_template)
        self.parser = get_StrOutputParser()
        self.chain = self.prompt | model | self.parser

    def inject(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        diagnoses = record.get("diagnoses") or record.get("diag_and_rationale", [])
        if not diagnoses or len(diagnoses) < 3:
            return None  # Require at least 3 for 2 correct + 1 hallucinated

        choice_pair = choice(diagnoses)
        orig_diag = choice_pair["diagnosis"]
        orig_rat = choice_pair["rationale"]

        # Get transcript
        transcript = record.get("transcript") or record.get("src") or record.get("dialogue") or ""

        # Get hallucinated rationale
        hallucinated = self.chain.invoke({
            "transcript": transcript,
            "original_diagnosis": orig_diag,
            "original_rationale": orig_rat
        }).strip()

        if not hallucinated.endswith("."):
            hallucinated += "."

        # Sample 2 correct diagnoses excluding the chosen one
        other_correct = [d for d in diagnoses if d["diagnosis"] != orig_diag]
        if len(other_correct) < 2:
            return None

        correct_two = sample(other_correct, 2)

        hallucinated_entry = {
            "diagnosis": orig_diag,
            "rationale": hallucinated
        }

        # Final hallucinated diagnoses field
        hallucinated_diagnoses = deepcopy(correct_two) + [hallucinated_entry]

        # Build updated record
        new_rec = dict(record)
        new_rec.update({
            "original_diagnosis": orig_diag,
            "original_rationale": orig_rat,
            "hallucinated_rationale": hallucinated,
            "hallucinated_diagnoses": hallucinated_diagnoses,
            "error_type": "contextual_hallucination"
        })

        return new_rec
    

class ConsistencyHallucinationInjector:
    def __init__(self, model: Any, parser=None, prompt_template: Optional[str] = None):
        self.prompt = get_inject_consistency_hallucination_in_diagnoses_prompt(parser=parser, template=prompt_template)
        self.parser = get_StrOutputParser()
        self.chain = self.prompt | model | self.parser

    def inject(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        diagnoses = record.get("diagnoses") or record.get("diag_and_rationale", [])
        if not diagnoses or len(diagnoses) < 3:
            return None  # Need at least 3 for 2 real + 1 hallucinated

        choice_pair = choice(diagnoses)
        orig_diag = choice_pair["diagnosis"]
        orig_rat = choice_pair["rationale"]

        transcript = record.get("transcript") or record.get("src") or record.get("dialogue") or ""

        hallucinated = self.chain.invoke({
            "transcript": transcript,
            "original_diagnosis": orig_diag,
            "original_rationale": orig_rat,
        }).strip()

        if not hallucinated.endswith("."):
            hallucinated += "."

        # Sample 2 other correct diagnoses
        other_correct = [d for d in diagnoses if d["diagnosis"] != orig_diag]
        if len(other_correct) < 2:
            return None
        correct_two = sample(other_correct, 2)

        hallucinated_entry = {
            "diagnosis": orig_diag,
            "rationale": hallucinated
        }

        hallucinated_diagnoses = deepcopy(correct_two) + [hallucinated_entry]

        new_rec = dict(record)
        new_rec.update({
            "original_diagnosis": orig_diag,
            "original_rationale": orig_rat,
            "hallucinated_rationale": hallucinated,
            "hallucinated_diagnoses": hallucinated_diagnoses,
            "error_type": "consistency_hallucination",
        })

        return new_rec 


class HallucinationInjector:
    def __init__(self, model: Any, hallucination_type: str, parser=None, prompt_template: Optional[str] = None):
        if hallucination_type.lower() == "contextual":
            self.prompt = get_inject_contextual_hallucination_in_notes_prompt(parser=parser, template=prompt_template)
        elif hallucination_type.lower() == "consistency":
            self.prompt = get_inject_consistency_hallucination_in_notes_prompt(parser=parser, template=prompt_template)
        elif hallucination_type.lower() == "reasoning":
            self.prompt = get_inject_reasoning_hallucination_in_diagnoses_prompt(parser=parser, template=prompt_template)
        elif hallucination_type.lower() == "diagnostic":
            self.prompt = get_inject_diagnostic_hallucination_in_diagnoses_prompt(parser=parser, template=prompt_template)
        self.parser = get_StrOutputParser()
        self.chain = self.prompt | model | self.parser
        self.hallucination_type = hallucination_type.lower()  
    
    def inject_in_notes(self, record: Transcript_Notes_record) -> Hallucinated_Notes_record:
        transcript = record.transcript
        note = record.notes
        file = record.file

        hallucinated_note = self.chain.invoke({"transcript":transcript, "note":note})

        return Hallucinated_Notes_record(
            transcript=transcript,
            original_notes=note,
            hallucinated_notes=hallucinated_note,
            hallucination_types=[self.hallucination_type],
            file=file
        )
