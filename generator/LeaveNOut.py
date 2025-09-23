# Basic structure of your LangGraph system
from typing import TypedDict, List, Annotated
from langchain_community.chat_models import ChatOllama  # or any Hugging Face model
from langgraph.graph import StateGraph, END
import json
import random
from uqlm import BlackBoxUQ, WhiteBoxUQ, LLMPanel, UQEnsemble
import pandas as pd
import asyncio

# Define your state
class AgentState(TypedDict):
    original_transcript: str
    original_summary: str
    atomic_facts: List[dict]
    selected_facts: List[dict]
    edited_transcript: str
    generated_soap_note: str
    n_value: int
    hallucination_scores: dict

# Initialize your models
fact_model = ChatOllama(model="llama3.1")
soap_model = ChatOllama(model="llama3.1")

# Initialize UQLM components
blackbox_uq = BlackBoxUQ(llm=fact_model, scorers=["semantic_negentropy"], use_best=True)
whitebox_uq = WhiteBoxUQ(llm=soap_model, scorers=["min_probability"])

# Create the graph
builder = StateGraph(AgentState)

# Add nodes (same as before)
builder.add_node("extract_facts", extract_atomic_facts)
builder.add_node("select_facts", select_facts_to_remove)
builder.add_node("edit_transcript", edit_transcript)
builder.add_node("generate_soap", generate_soap_note)

# Add UQLM evaluation node
builder.add_node("evaluate_hallucinations", evaluate_with_blackbox_uq)

# Define the flow
builder.set_entry_point("extract_facts")
builder.add_edge("extract_facts", "select_facts")
builder.add_edge("select_facts", "edit_transcript")
builder.add_edge("edit_transcript", "generate_soap")
builder.add_edge("generate_soap", "evaluate_hallucinations")
builder.add_edge("evaluate_hallucinations", END)

# Compile the graph
graph = builder.compile()


# UQLM Evaluation Function

async def evaluate_with_blackbox_uq(state: AgentState):
    """Evaluate hallucinations using BlackBoxUQ.score with existing responses"""
    
    primary_response = state['generated_soap_note']
    
    alternative_responses = await generate_alternative_soap_notes(
        state['edited_transcript'], 
        num_alternatives=5
    )
    
    # Use BlackBoxUQ.score to evaluate consistency
    blackbox_uq = BlackBoxUQ(
        llm=fact_model, 
        scorers=["semantic_negentropy", "exact_match", "bert_score"]
    )
    
    # Score the primary response against the alternatives
    results = await blackbox_uq.score(
        responses=[primary_response],  # Your main SOAP note
        sampled_responses=[alternative_responses],  # List of alternative versions
        show_progress_bars=False
    )
    
    # Extract confidence scores
    scores_df = results.to_df()
    
    # Check for presence of removed facts
    fact_presence = check_fact_presence(
        state['generated_soap_note'], 
        state['selected_facts']
    )
    
    return {
        "hallucination_scores": {
            "semantic_negentropy": scores_df.iloc[0]['semantic_negentropy'],
            "exact_match_consistency": scores_df.iloc[0]['exact_match'],
            "bert_score_consistency": scores_df.iloc[0]['bert_score'],
            "fact_presence_check": fact_presence,
            "hallucination_indication": scores_df.iloc[0]['semantic_negentropy'] < 0.7  # Threshold
        }
    }

async def generate_alternative_soap_notes(transcript: str, num_alternatives: int = 5):
    """Generate alternative SOAP notes for consistency comparison"""
    prompt = f"""
    Based on the following doctor-patient conversation, create a comprehensive SOAP note:
    
    CONVERSATION:
    {transcript}
    
    SOAP NOTE:
    """
    
    alternative_notes = []
    for i in range(num_alternatives):
        # Add some variation by modifying temperature or adding slight variations
        response = await soap_model.ainvoke(prompt)
        alternative_notes.append(response.content)
    
    return alternative_notes

def check_fact_presence(soap_note: str, removed_facts: list):
    """Check if any of the removed facts appear in the SOAP note"""
    presence_results = {}
    soap_note_lower = soap_note.lower()
    
    for fact in removed_facts:
        fact_text = fact['fact'].lower()
        # Simple substring check (you can make this more sophisticated)
        is_present = fact_text in soap_note_lower
        presence_results[fact['fact']] = {
            'present': is_present,
            'category': fact['category'],
            'severity': 'high' if fact['category'] != 'Age & Sex' else 'low'
        }
    
    return presence_results

async def evaluate_with_uqlm(state: AgentState):
    """Evaluate hallucinations using UQLM techniques"""
    # Prepare the facts that should NOT be in the generated SOAP note
    removed_facts = [f['fact'] for f in state['selected_facts']]
    
    # Method 1: Black-Box UQ with semantic negentropy
    bb_results = await blackbox_uq.generate_and_score(
        prompts=[state['edited_transcript']], 
        num_responses=5
    )
    
    # Method 2: White-Box UQ with minimum probability
    wb_results = await whitebox_uq.generate_and_score(
        prompts=[state['edited_transcript']]
    )
    
    # Method 3: Create a panel of judges (using the same model for simplicity)
    panel = LLMPanel(llm=fact_model, judges=[fact_model, soap_model])
    panel_results = await panel.generate_and_score(
        prompts=[state['edited_transcript']]
    )
    
    # # Method 4: Ensemble approach (more advanced)
    # scorers = ["exact_match", "noncontradiction", "min_probability"]
    # ensemble = UQEnsemble(llm=fact_model, scorers=scorers)
    
    # If you have ground truth data, you can tune the ensemble
    # ensemble = await ensemble.tune(
    #     prompts=tuning_prompts, 
    #     ground_truth_answers=ground_truth_answers
    # )
    
    # ensemble_results = await ensemble.generate_and_score(
    #     prompts=[state['original_summary']], 
    #     num_responses=5
    # )
    
    fact_presence = {}
    for fact in removed_facts:
        fact_presence[fact] = fact.lower() in state['generated_soap_note'].lower()
    
    # Compile all resulKts
    hallucination_scores = {
        "blackbox_semantic_negentropy": bb_results.to_df().iloc[0]['semantic_negentropy'],
        "whitebox_min_probability": wb_results.to_df().iloc[0]['min_probability'],
        "llm_judge_score": panel_results.to_df().iloc[0]['judge_score'],
        "ensemble_score": ensemble_results.to_df().iloc[0]['ensemble_score'],
        "fact_presence_check": fact_presence,
        "hallucination_rate": sum(fact_presence.values()) / len(fact_presence) if fact_presence else 0
    }
    
    return {"hallucination_scores": hallucination_scores}

def extract_atomic_facts(state: AgentState):
    """Enhanced fact extraction with proper medical categories"""
    prompt = f"""
    You are a medical fact extraction expert. Extract all atomic facts from the following medical summary.
    Break down complex statements into simple, independent facts.
    
    Categories to use (select exactly one for each fact):
    - Age & Sex: Demographic information only
    - Exam Findings: Physical examination observations
    - Treatment Plan: Medications, procedures, therapies
    - Symptoms: Patient-reported complaints
    - Labs & Imaging: Test results and imaging findings
    - Medical History: Past medical conditions
    - Diagnosis: Current medical diagnoses
    
    For each fact, provide a JSON array of objects with 'fact' and 'category' fields.
    
    Medical Summary:
    {state['original_transcript']}
    
    Return only valid JSON, no other text.
    """
    response = fact_model.invoke(prompt)
    try:
        json_str = response.content.strip()
        if json_str.startswith('```json'):
            json_str = json_str[7:-3]  
        elif json_str.startswith('```'):
            json_str = json_str[3:-3]
        
        facts = json.loads(json_str)
        return {"atomic_facts": facts}
    except json.JSONDecodeError:
        # Fallback parsing if JSON fails
        print(f"Failed to parse JSON from: {response.content}")
        return {"atomic_facts": []}

def select_facts_to_remove(state: AgentState):
    """Select N orthogonal facts to remove, considering categories"""
    n = state['n_value']
    facts = state['atomic_facts']
    
    facts_by_category = {}
    for fact in facts:
        category = fact.get('category', 'Unknown')
        if category not in facts_by_category:
            facts_by_category[category] = []
        facts_by_category[category].append(fact)
    

    selected = []
    categories_covered = set()
    

    for category, category_facts in facts_by_category.items():
        if len(selected) >= n:
            break
        if category not in categories_covered and category != 'Age & Sex':
            if category_facts:
                selected.append(random.choice(category_facts))
                categories_covered.add(category)
    
    # If we need more facts, select randomly from remaining categories
    remaining_categories = [cat for cat in facts_by_category.keys() 
                           if cat not in categories_covered and cat != 'Age & Sex']
    while len(selected) < n and remaining_categories:
        category = random.choice(remaining_categories)
        if facts_by_category[category]:
            selected.append(random.choice(facts_by_category[category]))
            remaining_categories.remove(category)
    
    # If we still need more facts, select from any category (except Age & Sex)
    all_facts = [f for f in facts if f.get('category', 'Unknown') != 'Age & Sex']
    while len(selected) < n and all_facts:
        fact = random.choice(all_facts)
        if fact not in selected:
            selected.append(fact)
        all_facts.remove(fact)
    
    return {"selected_facts": selected}

def edit_transcript(state: AgentState):
    """Edit the transcript to remove selected facts"""
    facts_to_remove = state['selected_facts']
    fact_descriptions = "\n".join([f"- {f['fact']} ({f['category']})" for f in facts_to_remove])
    
    prompt = f"""
    You are a medical transcript editor. Your task is to rewrite the following doctor-patient conversation transcript
    to remove all occurrences of the specified facts while maintaining the natural flow and meaning of the conversation.
    
    Facts to remove:
    {fact_descriptions}
    
    Original transcript:
    {state['original_transcript']}
    
    Rewritten transcript (maintain the same format and length as much as possible):
    """
    
    response = fact_model.invoke(prompt)
    return {"edited_transcript": response.content}

def generate_soap_note(state: AgentState):
    """Generate a SOAP note from the edited transcript"""
    prompt = f"""
    You are a medical scribe. Based on the following doctor-patient conversation,
    create a comprehensive SOAP note (Subjective, Objective, Assessment, Plan).
    
    Conversation:
    {state['edited_transcript']}
    
    SOAP Note:
    """
    
    response = soap_model.invoke(prompt)
    return {"generated_soap_note": response.content}

