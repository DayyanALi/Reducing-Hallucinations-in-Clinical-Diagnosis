from langchain_core.prompts import PromptTemplate
from generator.templates import (
    DIAGNOSIS_PROMPT_TEMPLATE, DIAGNOSIS_JUDGE_TEMPLATE, 
    DETECT_CONTEXTUAL_HALLUCINATION_TEMPLATE, DETECT_CONSISTENCY_HALLUCINATION_TEMPLATE,
    INJECT_CONTEXTUAL_HALLUCINATION_DIAGNOSES_TEMPLATE, INJECT_CONSISTENCY_HALLUCINATION_DIAGNOSES_TEMPLATE,
    INJECT_CONTEXTUAL_HALLUCINATION_NOTES_TEMPLATE  
)


# -----------------------------------------------------------------------------
# PromptTemplate for Differential Diagnosis Generation
# -----------------------------------------------------------------------------

def get_format_instructions(parser=None) -> str:
    if parser is not None:
        try:
            return parser.get_format_instructions()
        except NotImplementedError:
            return ""
    return ""

def get_diagnosis_prompt(parser=None, template: str=None) -> PromptTemplate:
    fmt = get_format_instructions(parser=parser)

    if not template:
        template = DIAGNOSIS_PROMPT_TEMPLATE

    return PromptTemplate(
        template=(template),
        input_variables=["transcript"],
        partial_variables={"format_instructions": fmt}
    )

def get_judge_prompt(parser=None, template: str= None) -> PromptTemplate:
    fmt = get_format_instructions(parser=parser)

    if not template:
        template = DIAGNOSIS_JUDGE_TEMPLATE
    
    return PromptTemplate(
        template=(template),
        input_variables=["transcript","output"],
        partial_variables={"format_instructions": fmt}
    )
    
    
# -----------------------------------------------------------------------------
# Hallucination Injection Prompts
# -----------------------------------------------------------------------------

def get_inject_contextual_hallucination_in_diagnoses_prompt(parser=None, template: str= None) -> PromptTemplate:
    fmt = get_format_instructions(parser=parser)

    if not template:
        template = INJECT_CONTEXTUAL_HALLUCINATION_DIAGNOSES_TEMPLATE

    return PromptTemplate(
        template=(template),
        input_variables=["transcript", "original_diagnosis", "original_rationale"],
        partial_variables={"format_instructions": fmt}
    )
    
def get_inject_contextual_hallucination_in_notes_prompt(parser=None, template: str= None) -> PromptTemplate:
    fmt = get_format_instructions(parser=parser)

    if not template:
        template = INJECT_CONTEXTUAL_HALLUCINATION_NOTES_TEMPLATE

    return PromptTemplate(
        template=(template),
        input_variables=["transcript", "note"],
        partial_variables={"format_instructions": fmt}
    )

def get_inject_consistency_hallucination_in_notes_prompt(parser=None, template: str= None) -> PromptTemplate:
    fmt = get_format_instructions(parser=parser)

    if not template:
        template = INJECT_CONSISTENCY_HALLUCINATION_DIAGNOSES_TEMPLATE

    return PromptTemplate(
        template=(template),
        input_variables=["transcript", "original_diagnosis", "original_rationale"],
        partial_variables={"format_instructions": fmt}
    )
    
def get_inject_consistency_hallucination_in_diagnoses_prompt(parser=None, template: str= None) -> PromptTemplate:
    fmt = get_format_instructions(parser=parser)

    if not template:
        template = INJECT_CONSISTENCY_HALLUCINATION_DIAGNOSES_TEMPLATE

    return PromptTemplate(
        template=(template),
        input_variables=["transcript", "original_diagnosis", "original_rationale"],
        partial_variables={"format_instructions": fmt}
    )

# -----------------------------------------------------------------------------
# Hallucination Detection Prompts
# -----------------------------------------------------------------------------


def get_detect_contextual_hallucination_prompt(parser=None, template: str= None) -> PromptTemplate:
    fmt = get_format_instructions(parser=parser)

    if not template:
        template = DETECT_CONTEXTUAL_HALLUCINATION_TEMPLATE

    return PromptTemplate(
        template=(template),
        input_variables=["transcript", "diagnosis", "rationale"],
        partial_variables={"format_instructions": fmt}
    )
    
def get_detect_consistency_hallucination_prompt(parser=None, template: str= None) -> PromptTemplate:
    fmt = get_format_instructions(parser=parser)

    if not template:
        template = DETECT_CONSISTENCY_HALLUCINATION_TEMPLATE

    return PromptTemplate(
        template=(template),
        input_variables=["transcript", "diagnosis", "rationale"],
        partial_variables={"format_instructions": fmt}
    )
