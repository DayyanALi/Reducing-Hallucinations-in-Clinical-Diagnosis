# combine_transcripts.py
from __future__ import annotations
from pathlib import Path
import sys

# ---- your helpers (from your message) ----
import re
import textgrid

def strip_transcript_tags(text: str) -> str:
    tags = ["<UNSURE>", "</UNSURE>", "<UNIN/>", "<INAUDIBLE_SPEECH/>"]
    for t in tags:
        text = text.replace(t, "")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_utterances_textgrid(tg_path: str):
    tg = textgrid.TextGrid()
    tg.read(tg_path)
    utterances = []
    for tier in tg.tiers:
        for interval in tier.intervals:
            if interval.mark:
                utterances.append(
                    {"text": interval.mark, "from": interval.minTime, "to": interval.maxTime}
                )
    return utterances

def get_combined_transcript(transcript_path_doctor: str, transcript_path_patient: str):
    utterances_doctor = get_utterances_textgrid(transcript_path_doctor)
    utterances_patient = get_utterances_textgrid(transcript_path_patient)
    for u in utterances_doctor:
        u["speaker"] = "Doctor"
    for u in utterances_patient:
        u["speaker"] = "Patient"
    combined = sorted(utterances_doctor + utterances_patient, key=lambda x: x["from"])
    return [f"{u['speaker']}: {strip_transcript_tags(u['text'])}" for u in combined]
# ------------------------------------------

def main(in_dir: str = "data/babylon_data/babylonhealth primock57 main transcripts textgrid", out_dir: str = "data/babylon_data/babylonhealth primock57 main transcripts combined") -> None:
    in_path = Path(in_dir)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    doctor_files = sorted(in_path.glob("*doctor.TextGrid"))
    if not doctor_files:
        print(f"No *doctor.TextGrid files found in {in_path.resolve()}", file=sys.stderr)
        sys.exit(1)

    written = 0
    missing_pairs = []

    for doc_tg in doctor_files:
        pat_tg = Path(str(doc_tg).replace("doctor.TextGrid", "patient.TextGrid"))
        if not pat_tg.exists():
            missing_pairs.append((doc_tg.name, pat_tg.name))
            continue

        lines = get_combined_transcript(str(doc_tg), str(pat_tg))

        out_file = out_path / doc_tg.name.replace("_doctor.TextGrid", ".txt")
        out_file.write_text("\n".join(lines), encoding="utf-8")
        written += 1

    print(f"Combined transcripts written: {written} → {out_path.resolve()}")
    if missing_pairs:
        print("WARNING: missing patient files for:", file=sys.stderr)
        for d, p in missing_pairs:
            print(f"  {d} ↛ {p}", file=sys.stderr)

if __name__ == "__main__":
    # change args if you keep your TextGrids elsewhere:
    # main("path/to/TextGrids", "path/to/transcripts_combined")
    main()
