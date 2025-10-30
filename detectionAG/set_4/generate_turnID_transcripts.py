import os
import re
import glob

"""
Adds Turn IDs to transcripts based on speaker changes. 
Consecutive lines by the same speaker are merged into the same Turn ID. 
Empty dialogues are ignored.
"""

# Input and output folders
input_folder = "data/babylon_data/babylonhealth primock57 main transcripts combined"                 # folder containing original transcripts
output_folder = "detectionAG/set_4/transcripts_with_turns"      # folder to save annotated files

os.makedirs(output_folder, exist_ok=True)  # create if not exists

pattern = re.compile(r"^(Doctor|Patient):\s*(.*)")

for file_path in glob.glob(os.path.join(input_folder, "*.txt")):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    turn_id = 1
    current_speaker = None
    output_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = pattern.match(line)
        if match:
            speaker, text = match.groups()
            if speaker != current_speaker:
                output_lines.append(f"[ Turn ID {turn_id}] {speaker}: {text}")
                current_speaker = speaker
                turn_id += 1
            else:
                # continuation of same speaker
                output_lines[-1] += " " + text
        else:
            if output_lines:
                output_lines[-1] += " " + line

    # Save annotated transcript
    filename = os.path.basename(file_path)
    output_path = os.path.join(output_folder, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        for line in output_lines:
            f.write(line + "\n")

    print(f"Annotated: {filename}")

print(f"\nAll annotated transcripts saved in: '{output_folder}'")
