import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from detectionAG.configs.set_4_prompts import FOLLOW_UP_QS_PROMPT


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
    """Generates follow-up questions based on a transcript and given DDx."""

    def __init__(self, model_name="gpt-4o-mini", temperature=0.5, prompt=None):
        self.llm = ChatOpenAI(model=model_name, temperature=1 if model_name == "o3" else temperature)
        self.prompt = prompt or FOLLOW_UP_QS_PROMPT

    def run(self, transcript: str, ddx_json: dict | list | str | None = None) -> dict:
        """Generate structured follow-up questions."""
        if isinstance(ddx_json, (dict, list)):
            ddx_str = json.dumps(ddx_json, indent=2)
        else:
            ddx_str = str(ddx_json or "")

        # If prompt is a ChatPromptTemplate, format properly
        if isinstance(self.prompt, ChatPromptTemplate):
            messages = self.prompt.format_messages(transcript=transcript, ddx=ddx_str)
            resp = self.llm.invoke(messages)
        else:
            prompt_input = self.prompt.format(transcript=transcript, ddx=ddx_str)
            resp = self.llm.invoke(prompt_input)
            
        
        return safe_json_parse(resp.content)


# ----------------------------------------------------------------
# PIPELINE — ONLY FOR FOLLOW-UP QUESTIONS
# ----------------------------------------------------------------
class ScribePipeline:
    """Simplified pipeline: uses transcript + DDx to generate follow-up questions."""

    def __init__(self, model_name="gpt-4o-mini", question_prompt=None):
        self.question_agent = QuestionAgent(model_name=model_name, prompt=question_prompt)

    def run(self, transcript: str, ddx: dict | list | str | None = None) -> dict:
        """Generate follow-up questions using pre-extracted DDx."""
        questions = self.question_agent.run(transcript, ddx)
        return {"questions": questions, "ddx_used": ddx}
