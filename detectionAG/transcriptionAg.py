import os
import glob
import assemblyai as aai
from langchain_community.document_loaders import AssemblyAIAudioTranscriptLoader

# API key
ASSEMBLYAI_API_KEY = "318394b065994f7590a0c03059038d05"

# Input + output folders
input_dir = "E:/detectionAG/output/mixed_audio"
output_dir = "E:/detectionAG/output/transcriptions"
os.makedirs(output_dir, exist_ok=True)

# Configure diarization
config = aai.TranscriptionConfig(
    speaker_labels=True,
    speakers_expected=2
)

# Loop through all audio files
for audio_file in glob.glob(os.path.join(input_dir, "*.wav")):
    base = os.path.splitext(os.path.basename(audio_file))[0]
    output_file = os.path.join(output_dir, f"{base}.txt")

    # Skip if transcript already exists
    if os.path.exists(output_file):
        print(f"⏩ Skipping {audio_file} (transcript already exists)")
        continue

    print(f"Processing {audio_file}...")

    # Create loader
    loader = AssemblyAIAudioTranscriptLoader(
        file_path=audio_file,
        config=config,
        api_key=ASSEMBLYAI_API_KEY
    )

    docs = loader.load()
    utterances = docs[0].metadata.get("utterances", [])

    # Save transcript
    with open(output_file, "w", encoding="utf-8") as f:
        for utt in utterances:
            role = "Doctor" if utt["speaker"] == "A" else "Patient"
            f.write(f"{role}: {utt['text']}\n")

    print(f"✅ Saved transcript → {output_file}")   