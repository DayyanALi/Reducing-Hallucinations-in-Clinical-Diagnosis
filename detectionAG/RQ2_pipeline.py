import os
import glob
import json
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Import Prompts (Ensure these exist in your configs/promptTemplate files)
from configs.fact_extract_prompt import * 
from promptTemplate import (
    NOTE_PROMPT, 
    USER_PROMPT_NOTES, 
)

# Import Classes
from classes import SoapGenerator, FactExtractor

# ---------------- CONFIGURATION ---------------- #
load_dotenv()

# Directories
SKIP_GENERATION = False
CLEAN_TRANSCRIPT_DIR = "data/babylon_data/babylonhealth primock57 main transcripts combined"
# Folder containing transcripts with injected errors (omissions/homophones)
NOISY_TRANSCRIPT_DIR = "data/babylon_data/noisy_transcripts" 
BASE_OUTPUT_DIR = "detectionAG/results/rq2_stability"

# Models
MODELS_TO_RUN = ["gpt-5-nano"] 


class StabilityAnalyst:
    """
    Dedicated class for RQ2: Compares two sets of extracted facts (Reference vs Candidate).
    """
    def __init__(self, model_name="gpt-4o"):
        api_key = os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(model=model_name, api_key=api_key, temperature=0)

    def run_differential_analysis(self, clean_facts, noisy_facts):
        """Compares Clean Baseline vs Noisy Candidate."""
        prompt_content = RQ2_DIFF_USER.format(
            clean_facts=json.dumps(clean_facts),
            noisy_facts=json.dumps(noisy_facts)
        )
        
        response = self.llm.invoke([
            {"role": "system", "content": RQ2_DIFF_SYSTEM},
            {"role": "user", "content": prompt_content}
        ])
        
        content = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)


def main():
    # Setup Dirs
    for model in MODELS_TO_RUN:
        for sub in ["clean_notes", "noisy_notes", "reports"]:
            os.makedirs(os.path.join(BASE_OUTPUT_DIR, model, sub), exist_ok=True)

    # Get Input Files (Pairing Clean with Noisy)
    clean_files = sorted(glob.glob(os.path.join(CLEAN_TRANSCRIPT_DIR, "*.txt")))
    print(f"Found {len(clean_files)} clean transcripts.")

    for model_name in MODELS_TO_RUN:
        print(f"\n>>> PROCESSING MODEL: {model_name}")
        
        generator = SoapGenerator(model_name)
        extractor = FactExtractor()
        analyst = StabilityAnalyst() # Using GPT-4o by default for analysis

        for clean_path in clean_files:
            base_name = os.path.splitext(os.path.basename(clean_path))[0]
            
            # Find matching noisy file (Assuming exact filename match in noisy folder)
            noisy_path = os.path.join(NOISY_TRANSCRIPT_DIR, f"{base_name}.txt")
            if not os.path.exists(noisy_path):
                print(f"⚠️  Skipping {base_name}: Matching noisy transcript not found at {noisy_path}")
                continue

            # Define Output Paths
            clean_note_path = os.path.join(BASE_OUTPUT_DIR, model_name, "clean_notes", f"{base_name}.json")
            noisy_note_path = os.path.join(BASE_OUTPUT_DIR, model_name, "noisy_notes", f"{base_name}.json")
            report_path = os.path.join(BASE_OUTPUT_DIR, model_name, "reports", f"{base_name}_diff.json")

            notes_data = {}
            pairs = [
                ("clean", clean_path, clean_note_path), 
                ("noisy", noisy_path, noisy_note_path)
            ]

            pair_failed = False
            for tag, t_path, n_path in pairs:
                # Load existing if available and SKIP_GENERATION is on
                if SKIP_GENERATION and os.path.exists(n_path):
                    print(f"   [{tag.upper()}] Loading existing note for {base_name}...")
                    with open(n_path, 'r') as f: notes_data[tag] = json.load(f)
                else:
                    if SKIP_GENERATION: 
                        print(f"   [{tag.upper()}] Note missing for {base_name}, skipping pair.")
                        pair_failed = True; break
                    
                    print(f"   [{tag.upper()}] Generating new note for {base_name}...")
                    with open(t_path, 'r') as f: transcript_text = f.read()
                    
                    try:
                        raw_note = generator.generate(transcript_text)
                        
                        # Extract facts immediately to QNOTE format
                        # Note: We use the extracted facts for comparison, not the raw note text
                        facts_json = extractor.to_qnote(raw_note) 
                        notes_data[tag] = facts_json
                        
                        # Save the extracted facts (Note: You might want to save raw note too if needed)
                        with open(n_path, 'w') as f:
                            json.dump(facts_json, f, indent=2)
                            
                    except Exception as e:
                        print(f"   ❌ Generation failed for {tag} ({base_name}): {e}")
                        pair_failed = True; break
            
            if pair_failed: continue

            # --- STEP 2: RUN DIFFERENTIAL STABILITY ANALYSIS ---
            if os.path.exists(report_path):
                print(f"   [DIFF] Report exists for {base_name}, skipping.")
                continue
            
            print(f"   [DIFF] Analyzing Stability for {base_name}...")
            try:
                stability_report = analyst.run_differential_analysis(
                    clean_facts=notes_data['clean'],
                    noisy_facts=notes_data['noisy']
                )
                
                # Wrap output with metadata
                output = {
                    "meta": {"model": model_name, "transcript": base_name},
                    "analysis": stability_report
                }
                
                with open(report_path, 'w') as f:
                    json.dump(output, f, indent=2)
                print(f"   ✅ Stability Report saved: {report_path}")
                
            except Exception as e:
                print(f"   ❌ Analysis failed for {base_name}: {e}")
            
            time.sleep(0.5)

if __name__ == "__main__":
    main()