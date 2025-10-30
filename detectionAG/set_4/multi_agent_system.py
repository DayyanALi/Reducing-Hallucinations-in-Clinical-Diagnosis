# agents/question_agent.py
import json
from langchain_openai import ChatOpenAI
from detectionAG.configs.set_4_prompts import QUESTION_PROMPT, DDX_PROMPT, NOTE_PROMPT, BASELINE_NOTE_PROMPT

# config.py
# Allowed configurations
CONFIGS = {
    "A": {"questions": False,  "ddx": False,  "note": True},
    "B": {"questions": False, "ddx": True,  "note": True},
    "C": {"questions": True,  "ddx": True, "note": False},
    "D": {"questions": False, "ddx": False, "note": True, "baseline": True},
    "E" : {"questions": False, "ddx" : True, "note" : False}
}

# ----------------------------------------------------------------
# Safe JSON Parser
# ----------------------------------------------------------------
def safe_json_parse(text: str):
    """Parse JSON safely and fall back to raw text on failure."""
    if not text:
        return {"error": "Empty response"}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        return {"raw_response": text}

# ----------------------------------------------------------------
# QUESTION AGENT
# ----------------------------------------------------------------

class QuestionAgent:
    """
    Generates follow-up questions based on a transcript.
    Can optionally take DDx context to refine questioning.
    """

    def __init__(self, model_name="gpt-4o-mini", temperature=0.5, prompt: str = None):
        self.llm = ChatOpenAI(model=model_name)
        self.prompt = prompt or QUESTION_PROMPT

    def run(self, transcript: str, ddx_json: dict | list | str | None = None) -> dict:
        """
        Args:
            transcript: conversation text
            ddx_json: optional differential diagnoses (dict/list/str)
        Returns:
            dict: structured JSON with question groups
        """
        # If DDx context exists → include both transcript and DDx
        if ddx_json:
            if isinstance(ddx_json, (dict, list)):
                ddx_str = json.dumps(ddx_json, indent=2)
            else:
                ddx_str = str(ddx_json)
            prompt_input = self.prompt.format(transcript=transcript, ddx=ddx_str)
        else:
            # Otherwise → only transcript
            prompt_input = self.prompt.format(transcript=transcript, ddx="")

        resp = self.llm.invoke(prompt_input)
        return safe_json_parse(resp.content)


# ----------------------------------------------------------------
# DIFFERENTIAL DIAGNOSIS AGENT
# ----------------------------------------------------------------
class DDxAgent:
    """
    Generates differential diagnoses.
    Can work from transcript alone or use question context to refine.
    """

    def __init__(self, model_name="gpt-4o-mini", temperature=0.5, prompt:str=None):
        self.llm = ChatOpenAI(model=model_name)
        if prompt is None:
            self.prompt = DDX_PROMPT
        else:
            self.prompt = prompt

    def run(self, transcript: str, questions_json: dict | list | str | None = None) -> list:
        """
        Args:
            transcript: conversation text
            questions_json: optional question set (dict/list/str)
        Returns:
            list: list of diagnoses with likelihoods and evidence
        """
        if isinstance(questions_json, (dict, list)):
            questions_str = json.dumps(questions_json, indent=2)
        elif isinstance(questions_json, str) and questions_json.strip():
            questions_str = questions_json
        else:
            questions_str = ""  # empty list if no questions

        resp = self.llm.invoke(
            self.prompt.format(transcript=transcript, questions=questions_str)
        )
        return safe_json_parse(resp.content)

    
class NoteAgent:
    def __init__(self, model_name="gpt-4o-mini", prompt=BASELINE_NOTE_PROMPT,temperature=0.5):
        self.llm = ChatOpenAI(model=model_name)
        self.prompt = prompt
    
    def run(self, transcript: str, questions: dict = None, ddx: list = None, baseline: bool = False) -> dict:
        if ddx is None:
            resp = self.llm.invoke(self.prompt.format(transcript=transcript))
            # print("Using baseline note prompt.",resp)
        else:
            ddx_json = json.dumps(ddx) if ddx is not None else "[]"
            resp = self.llm.invoke(self.prompt.format(transcript=transcript, ddx=ddx_json))
        return resp.content

class ScribePipeline:
    def __init__(self, config_key: str, model_name:str="gpt-4o-mini", note_prompt: str = None, question_prompt: str= None, ddx_prompt: str=None):
        cfg = CONFIGS.get(config_key)
        if not cfg:
            raise ValueError(f"Invalid config '{config_key}'")
        self.cfg = cfg
        self.question_agent = QuestionAgent(model_name=model_name,prompt=question_prompt)
        self.ddx_agent = DDxAgent(model_name=model_name,prompt=ddx_prompt)
        self.note_agent = NoteAgent(model_name=model_name,prompt=note_prompt) if note_prompt else NoteAgent()
    
    def run(self, transcript: str) -> dict:
        questions = None
        ddx = None
        note = None

        # ddx
        if self.cfg.get("ddx"):
            # pass empty dict if no questions
            ddx = self.ddx_agent.run(transcript)
        
        # questions
        if self.cfg.get("questions"):
            questions = self.question_agent.run(transcript, ddx)
        
        # note
        if self.cfg.get("note"):
            note = self.note_agent.run(
                transcript,
                questions=questions,
                ddx=ddx,
                baseline=self.cfg.get("baseline", False)
            )
        
        return {
            "config": self.cfg,
            "questions": questions,
            "ddx": ddx,
            "note": note
        }