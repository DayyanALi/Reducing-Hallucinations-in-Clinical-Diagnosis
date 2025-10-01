import os
import json
import pandas as pd
from dotenv import load_dotenv
from medicalEval import MedicalNoteEvaluator


def run_evaluation(ground_file: str, notes_dir: str, output_file: str, api_key: str):
    """
    Evaluate AI-generated medical notes against SOAP-format ground truth (JSON).
    """

    evaluator = MedicalNoteEvaluator(api_key=api_key)

    all_results = []

    # ---- Load SOAP ground truth JSON ---- #
    with open(ground_file, "r", encoding="utf-8") as f:
        ground_data = json.load(f)

    # List of AI-generated notes (still plain text files)
    note_files = sorted(os.listdir(notes_dir))

    # ---- Iterate and pair ground truth entries with AI notes ---- #
    for entry, note_file in zip(ground_data, note_files):
        ground_text = entry["SOAP"]  # use SOAP field from JSON
        note_path = os.path.join(notes_dir, note_file)

        print(f"Evaluating: {entry['consult_name']} vs {note_file} ...")

        try:
            # Load AI note text
            with open(note_path, "r", encoding="utf-8") as f:
                ai_note = f.read()

            # Pass raw strings to evaluator
            result_df = evaluator.evaluate_note_text(
                physician_note=ground_text,
                ai_note=ai_note
            )

            result_df["Consult_Name"] = entry["consult_name"]
            result_df["Note_File"] = note_file
            all_results.append(result_df)

        except Exception as e:
            print(f"Failed on {entry['consult_name']}, {note_file}: {e}")

    # ---- Save results ---- #
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        final_df.to_csv(output_file, index=False)
        print(f"\n Evaluation complete. Results saved to {output_file}")
    else:
        print("No results were generated.")


if __name__ == "__main__":
    ground_file = "output/notes_soap/Complete_Primock_SOAP_Notes.json"  # JSON file with SOAP notes
    notes_dir = "output/notes_text"  # AI-generated notes
    output_file = "scribe_results.csv"

    load_dotenv()

    run_evaluation(
        ground_file=ground_file,
        notes_dir=notes_dir,
        output_file=output_file,
        api_key=os.getenv("OPENAI_API_KEY")
    )
