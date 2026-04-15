# import os
# import glob
# import json
# import time
# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# from detectionAG.promptTemplate import USER_PROMPT_NOTES
# from detectionAG.configs.temp_check_note_prompt import NOTE_PROMPT

# # ---------------- CONFIG ---------------- #
# load_dotenv()

# transcript_dir = "data/babylon_data/babylonhealth primock57 main transcripts combined"

# # base output dirs (each model will get its own subfolder)
# base_output_dir_json = "detectionAG/results/temp_check/notes_json"
# base_output_dir_txt = "detectionAG/results/temp_check/notes_text"

# os.makedirs(base_output_dir_json, exist_ok=True)
# os.makedirs(base_output_dir_txt, exist_ok=True)

# # How many transcripts to process (set to None to process all)
# num_files = None

# # If True, skip calling the LLM for a transcript if either JSON or TXT output already exists.
# skip_existing = True

# # Small delay between calls to avoid bursting the API (seconds)
# call_delay = 0.6

# # ---- Models to run (in order you listed) ----
# models = [
#     "o3",            # note: replace names with actual model IDs if different in your environment
#     # "gpt-4o",
#     # "gpt-4.1",
#     # "gpt-4.1-mini",
#     # "gpt-5-nano",
#     # "gpt-5-mini",
#     # "gpt-5-thinking",
#     "gpt-5",
# ]

# # ---------------- Prompt setup (shared) ---------------- #
# system_prompt = NOTE_PROMPT
# user_prompt_template_string = USER_PROMPT_NOTES

# prompt = ChatPromptTemplate.from_messages([
#     ("system", system_prompt),
#     ("human", user_prompt_template_string),
# ])

# # ---------------- Collect input files ---------------- #
# all_files = sorted(glob.glob(os.path.join(transcript_dir, "*.txt")))
# if num_files:
#     input_files = all_files[:num_files]
# else:
#     input_files = all_files

# print(f"Found {len(all_files)} transcripts, processing {len(input_files)} per model.")

# # ---------------- MAIN ---------------- #
# api_key = os.getenv("OPENAI_API_KEY")
# if not api_key:
#     raise RuntimeError("OPENAI_API_KEY not found in environment. Set it (e.g., in .env) before running.")

# for model_name in models:
#     # make a filesystem-safe folder name for each model
#     model_safe = model_name.replace("/", "_").replace(" ", "_").lower()

#     model_json_dir = os.path.join(base_output_dir_json, model_safe)
#     model_txt_dir = os.path.join(base_output_dir_txt, model_safe)
#     os.makedirs(model_json_dir, exist_ok=True)
#     os.makedirs(model_txt_dir, exist_ok=True)

#     print("\n" + "=" * 50)
#     print(f"Processing model: {model_name} -> json folder: {model_json_dir}")
#     print("=" * 50)

#     # instantiate LLM for this model
#     try:
#         # llm = ChatOpenAI(model=model_name, temperature=0, api_key=api_key)
#         llm = ChatOpenAI(model=model_name, api_key=api_key)
#     except TypeError:
#         # fallback if your ChatOpenAI expects 'model_name' or 'openai_api_key' parameter names
#         llm = ChatOpenAI(model_name=model_name, openai_api_key=api_key)

#     chain = prompt | llm | StrOutputParser()
#     num_notes = 0
#     for idx, input_file in enumerate(input_files, start=1):
#         if num_notes > 5:
#             break
#         base_name = os.path.splitext(os.path.basename(input_file))[0]
#         out_json_path = os.path.join(model_json_dir, f"{base_name}.json")
#         out_txt_path = os.path.join(model_txt_dir, f"{base_name}.txt")

#         if skip_existing and (os.path.exists(out_json_path) or os.path.exists(out_txt_path)):
#             print(f"[{model_safe}] ({idx}/{len(input_files)}) Skipping {base_name} (output exists).")
#             continue

#         print(f"[{model_safe}] ({idx}/{len(input_files)}) Processing {base_name} ...")

#         try:
#             with open(input_file, "r", encoding="utf-8") as f:
#                 transcript_content = f.read()
#         except Exception as e:
#             print(f"Failed reading {input_file}: {e}")
#             continue

#         inputs = {
#             "transcript": transcript_content,
#             "output_format": "json",   # request JSON output (you can change to "markdown" if desired)
#             "consulting_service": "General Medicine"
#         }

#         try:
#             raw_out = chain.invoke(inputs)
#         except Exception as e:
#             print(f"LLM request failed for {base_name} with model {model_name}: {e}")
#             # optional: save error to a .err file
#             with open(os.path.join(model_txt_dir, f"{base_name}.err"), "w", encoding="utf-8") as ef:
#                 ef.write(str(e))
#             # don't crash whole loop; continue to next file
#             time.sleep(call_delay)
#             continue

#         # chain.invoke typically returns a string (StrOutputParser). Try parse JSON first.
#         is_json = False
#         try:
#             parsed = json.loads(raw_out)
#             is_json = True
#         except Exception:
#             parsed = None

#         # Save outputs
#         try:
#             if is_json and isinstance(parsed, dict):
#                 with open(out_json_path, "w", encoding="utf-8") as f:
#                     json.dump(parsed, f, indent=2, ensure_ascii=False)
#                 print(f"  ✅ Saved JSON → {out_json_path}")
#             else:
#                 # save raw string output
#                 with open(out_txt_path, "w", encoding="utf-8") as f:
#                     f.write(raw_out)
#                 print(f"  ✅ Saved raw text → {out_txt_path}")
#         except Exception as e:
#             print(f"Failed saving outputs for {base_name}: {e}")

#         # small delay to avoid bursts
#         num_notes += 1
#         time.sleep(call_delay)

# print("\nAll done.")





import os
import glob
import time
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# from detectionAG.promptTemplate import USER_PROMPT_NOTES
# from detectionAG.configs.temp_check_note_prompt import NOTE_PROMPT
from detectionAG.promptTemplate import USER_PROMPT_NOTES
from detectionAG.promptTemplate import NOTE_PROMPT

# ---------------- CONFIG ---------------- #
load_dotenv()

transcript_dir = "data/babylon_data/babylonhealth primock57 main transcripts combined"

# base output dir (TEXT ONLY)
base_output_dir_txt = "detectionAG/experiements/set1/"
os.makedirs(base_output_dir_txt, exist_ok=True)

# How many transcripts to process (None = all)
num_files = None

# Skip LLM call if output already exists
skip_existing = True

# Delay between API calls (seconds)
call_delay = 0.6

# ---- Models + reasoning settings ----
model_runs = {
    "o3": [
        {"label": "low", "reasoning": "low"},
        {"label": "high", "reasoning": "high"},
    ],
    "gpt-5": [
        {"label": "minimal", "reasoning": "minimal"},
        {"label": "low", "reasoning": "low"},
        {"label": "medium", "reasoning": "medium"},
        {"label": "high", "reasoning": "high"},
    ],
}

# ---------------- Prompt setup ---------------- #
prompt = ChatPromptTemplate.from_messages([
    ("system", NOTE_PROMPT),
    ("human", USER_PROMPT_NOTES),
])

# ---------------- Collect input files ---------------- #
all_files = sorted(glob.glob(os.path.join(transcript_dir, "*.txt")))
input_files = all_files[:num_files] if num_files else all_files

print(f"Found {len(all_files)} transcripts, processing {len(input_files)} per run.")

# ---------------- MAIN ---------------- #
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found in environment.")

for model_name, runs in model_runs.items():
    for run in runs:
        reasoning_effort = run["reasoning"]
        run_label = run["label"]

        model_safe = f"{model_name}_{run_label}".replace("/", "_").lower()
        model_txt_dir = os.path.join(base_output_dir_txt, model_safe)
        os.makedirs(model_txt_dir, exist_ok=True)

        print("\n" + "=" * 60)
        print(f"Model: {model_name} | reasoning.effort = {reasoning_effort}")
        print(f"Output dir: {model_txt_dir}")
        print("=" * 60)

        try:
            llm = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                model_kwargs={
                    "reasoning": {"effort": reasoning_effort}
                },
                # Optional for determinism:
                # temperature=0
            )
        except TypeError:
            llm = ChatOpenAI(
                model_name=model_name,
                openai_api_key=api_key,
                model_kwargs={
                    "reasoning": {"effort": reasoning_effort}
                }
                # temperature=0
            )

        chain = prompt | llm | StrOutputParser()
        num_notes = 0

        for idx, input_file in enumerate(input_files, start=1):
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            out_txt_path = os.path.join(model_txt_dir, f"{base_name}.txt")

            if skip_existing and os.path.exists(out_txt_path):
                print(f"[{model_safe}] ({idx}/{len(input_files)}) Skipping {base_name}")
                continue

            print(f"[{model_safe}] ({idx}/{len(input_files)}) Processing {base_name}")

            try:
                with open(input_file, "r", encoding="utf-8") as f:
                    transcript_content = f.read()
            except Exception as e:
                print(f"Failed reading {input_file}: {e}")
                continue

            inputs = {
                "transcript": transcript_content,
                "output_format": "text",
                "consulting_service": "General Medicine",
            }

            try:
                raw_out = chain.invoke(inputs)
            except Exception as e:
                print(f"LLM request failed for {base_name}: {e}")
                with open(
                    os.path.join(model_txt_dir, f"{base_name}.err"),
                    "w",
                    encoding="utf-8",
                ) as ef:
                    ef.write(str(e))
                time.sleep(call_delay)
                continue

            try:
                with open(out_txt_path, "w", encoding="utf-8") as f:
                    f.write(raw_out)
                print(f"  ✅ Saved → {out_txt_path}")
            except Exception as e:
                print(f"Failed saving output for {base_name}: {e}")

            num_notes += 1
            time.sleep(call_delay)

print("\nAll done.")
