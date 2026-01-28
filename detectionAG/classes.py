import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from configs.fact_extract_prompt import (
    FACT_EXTRACT_SYSTEM, FACT_EXTRACT_USER,
    PHASE1_SYSTEM, PHASE1_USER,
    PHASE2_SYSTEM, PHASE2_USER
)
from promptTemplate import NOTE_PROMPT, USER_PROMPT_NOTES

class SoapGenerator:
    def __init__(self, model_name):
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", NOTE_PROMPT), 
            ("human", USER_PROMPT_NOTES)
        ])

    def generate(self, transcript):
        chain = self.prompt | self.llm | StrOutputParser()
        return chain.invoke({"transcript": transcript})

class FactExtractor:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-5.1", temperature=0) 
    
    def to_qnote(self, note_text):
        if isinstance(note_text, str):
            try:
                clean_text = note_text.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_text)
            except json.JSONDecodeError:
                pass 

        messages = [
            {"role": "system", "content": FACT_EXTRACT_SYSTEM},
            {"role": "user", "content": FACT_EXTRACT_USER.format(note_text=note_text)}
        ]
        response = self.llm.invoke(messages)
        try:
            content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except json.JSONDecodeError:
            print(f"❌ Extraction Failed. Raw: {response.content[:100]}...")
            return {}

class SoapEvaluator:
    def __init__(self):
        self.eval_llm = ChatOpenAI(model="gpt-5.1", temperature=0)

    def run_pipeline(self, transcript, gold_facts, gen_facts):
        # --- PREP: Build a Content Map (ID -> Text) ---
        # We need this because Phase 1 drops the text, but Phase 2 needs it.
        fact_content_map = {}
        if isinstance(gen_facts, dict):
            for section, facts in gen_facts.items():
                if isinstance(facts, list):
                    for f in facts:
                        if isinstance(f, dict) and 'fact_id' in f:
                            fact_content_map[f['fact_id']] = f.get('content', '')

        # --- PHASE 1: Alignment ---
        p1_input_text = PHASE1_USER.format(
            gold_facts=json.dumps(gold_facts), 
            gen_facts=json.dumps(gen_facts)
        )
        
        p1_res = self.eval_llm.invoke([
            {"role": "system", "content": PHASE1_SYSTEM},
            {"role": "user", "content": p1_input_text}
        ])
        
        try:
            alignment_data = json.loads(p1_res.content.replace("```json", "").replace("```", "").strip())
        except json.JSONDecodeError:
            print(f"❌ Phase 1 JSON Error: {p1_res.content[:100]}...")
            return {}

        # --- PHASE 2: Verification ---
        def normalize_id(f_id):
            """Strips leading zeros to match keys (e.g., 'Plan-005' -> 'Plan-5')"""
            if not f_id or '-' not in f_id: return f_id
            parts = f_id.rsplit('-', 1)
            if parts[1].isdigit():
                return f"{parts[0]}-{int(parts[1])}"
            return f_id
        gen_assessment = alignment_data.get('gen_assessment', [])
        
        # 1. Prepare facts for Phase 2 by RE-ATTACHING content
        normalized_content_map = {normalize_id(k): v for k, v in fact_content_map.items()}
        facts_to_verify = []
        
        for f in gen_assessment:
            if f.get('status') == 'NOT_IN_GOLD':
                raw_id = f.get('fact_id')
                norm_id = normalize_id(raw_id)
                
                if norm_id not in normalized_content_map:
                    continue 

                content = normalized_content_map[norm_id]

                # --- SAFETY CHECK 2: Empty Content Detection ---
                # If the content is essentially empty, it's a structural error (Ghost Fact).
                # We skip sending this to the LLM to save tokens and avoid confusion.
                if not content or len(content.strip()) < 2:
                    continue

                # Re-attach the content safely
                verification_payload = {
                    "fact_id": raw_id, # Keep original ID for reporting
                    "content": content, 
                    "status": "NOT_IN_GOLD"
                }
                facts_to_verify.append(verification_payload)
        if facts_to_verify:
            # Debug: Check if content is attached
            # print(f"DEBUG: Sending {len(facts_to_verify)} facts to Phase 2. Sample: {facts_to_verify[0]}")

            p2_input_text = PHASE2_USER.format(
                transcript=transcript, 
                facts_json=json.dumps(facts_to_verify)
            )
            
            p2_res = self.eval_llm.invoke([
                {"role": "system", "content": PHASE2_SYSTEM},
                {"role": "user", "content": p2_input_text}
            ])
            
            try:
                p2_json = json.loads(p2_res.content.replace("```json", "").replace("```", "").strip())
                print(p2_json)
                verification_results = p2_json.get('verdict', [])
                verification_map = {v['fact_id']: v for v in verification_results}

                # Update main data
                for fact in gen_assessment:
                    if fact.get('status') == 'NOT_IN_GOLD':
                        verdict = verification_map.get(fact.get('fact_id'))
                        if verdict:
                            # Handle capitalization mismatch (Status vs status)
                            print(verdict)
                            status = verdict.get('classification') or verdict.get('status')
                            reasoning = verdict.get('reasoning') or verdict.get('Reasoning')
                            
                            fact['final_status'] = status if status else "UNVERIFIED_SCHEMA_MISMATCH"
                            fact['verification_reasoning'] = reasoning if reasoning else "No reasoning provided"
                        else:
                            fact['final_status'] = 'UNVERIFIED_ID_MISMATCH'
                            
            except json.JSONDecodeError:
                print(f"❌ Phase 2 JSON Error: {p2_res.content[:100]}...")

        return alignment_data