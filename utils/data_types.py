from typing import List, Optional
from dataclasses import dataclass ,is_dataclass, asdict
from pathlib import Path

def to_serializable(o):
    if is_dataclass(o):
        return asdict(o)
    if isinstance(o, set):
        return list(o)
    if isinstance(o, Path):
        return str(o)
    raise TypeError(f"Type {type(o)} not serializable")

@dataclass(frozen=True)
class Diagnosis:
    diagnosis: str
    rationale: str

@dataclass(frozen=True)
class Transcript_Notes_record:
    transcript: str
    notes: str
    file: str

@dataclass(frozen=True)
class Hallucinated_Notes_record:
    transcript: str
    original_notes: str
    hallucinated_notes: str
    hallucination_types: List[str]
    file: str

