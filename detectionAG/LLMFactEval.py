import re
import json
from tqdm import tqdm
from langchain_openai import ChatOpenAI

class LLMFactEvaluator:
    
    EVAL_PROMPT = """
    You are an expert in evaluating medical facts.

    Reference Facts:
    {reference_facts}

    Predicted Fact to Evaluate:
    {pred_fact}

    Task: Is this predicted fact supported by any reference fact(s)? Return in this format:
    {{
        "supported": "YES/NO",
        "supporting_claim": "exact supporting reference fact if YES, NA if NO",
        "explanation": "brief explanation"
    }}
    """

    def __init__(self, api_key):
        self.llm = ChatOpenAI(
            api_key=api_key,
            model_name="gpt-4o",
            temperature=0.7
        )

    def parse_llm_response(self, response):
        supported_match = re.search(r'"supported":\s*"(YES|NO)"', response)
        claim_match = re.search(r'"supporting_claim":\s*"([^"]*)"', response)
        explanation_match = re.search(r'"explanation":\s*"([^"]*)"', response)
        
        return {
            'supported': supported_match.group(1) if supported_match else 'NO',
            'supporting_claim': claim_match.group(1) if claim_match else 'NA',
            'explanation': explanation_match.group(1) if explanation_match else ''
        }

    def evaluate_single_pair(self, pred_row, ref_row):
        pred_facts = json.loads(pred_row['facts_content'])
        ref_facts = json.loads(ref_row['facts_content'])
        
        results = []
        supported_count = 0
        
        pred_facts_count = len(pred_facts)
        ref_facts_count = len(ref_facts)
        
        all_ref_facts = "\n".join([f"- {fact['content']}" for fact in ref_facts])
        
        print(f"Processing {pred_facts_count} facts...")
        
        for fact in tqdm(pred_facts):  
            prompt = self.EVAL_PROMPT.format(
                reference_facts=all_ref_facts,
                pred_fact=fact['content'] 
            )
            
            response = self.llm.invoke(prompt).content
            result = self.parse_llm_response(response)
            
            if result['supported'] == 'YES':
                supported_count += 1
                
            results.append({
                'fact_id': fact['fact_id'],
                'content': fact['content'],
                'supported': result['supported'],
                'supporting_claim': result['supporting_claim'],
                'explanation': result['explanation']
            })
        
        link_score = min(1.0, supported_count / ref_facts_count)
        correct_score = supported_count / pred_facts_count
        
        return {
            'file_name': pred_row['file_name'],
            'link_score': link_score,
            'correct_score': correct_score,
            'facts_details': json.dumps(results)
        }