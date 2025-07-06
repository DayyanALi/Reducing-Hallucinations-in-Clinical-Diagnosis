from langchain_core.prompts import PromptTemplate
from generator.templates import DIAGNOSIS_PROMPT_TEMPLATE, DIAGNOSIS_JUDGE_TEMPLATE

# -----------------------------------------------------------------------------
# PromptTemplate for Differential Diagnosis Generation
# -----------------------------------------------------------------------------

def get_diagnosis_prompt(parser, template: str=None) -> PromptTemplate:
    try:
        fmt = parser.get_format_instructions()
    except NotImplementedError:
        fmt = ""  

    if not template:
        template = DIAGNOSIS_PROMPT_TEMPLATE

    return PromptTemplate(
        template=(template),
        input_variables=["transcript"],
        partial_variables={"format_instructions": fmt}
    )

def get_judge_prompt(parser, template: str= None) -> PromptTemplate:
    try:
        fmt = parser.get_format_instructions()
    except NotImplementedError:
        fmt = ""

    if not template:
        template = DIAGNOSIS_JUDGE_TEMPLATE
    
    return PromptTemplate(
        template=(template),
        input_variables=["transcript"],
        partial_variables={"format_instructions": fmt}
    )

