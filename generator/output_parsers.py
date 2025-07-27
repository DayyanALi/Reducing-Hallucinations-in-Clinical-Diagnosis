from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser, JsonOutputParser
from langchain.output_parsers import EnumOutputParser
# from typing import Literal
from pydantic import BaseModel, Field
from typing import List, Dict, Literal

# ======================================================================================================
# ========================= Diagnosis Simple string output parser ======================================
# ======================================================================================================
def get_StrOutputParser() -> StrOutputParser:
    return StrOutputParser()

# ======================================================================================================
# ========================= Diagnosis pydantic output parser ===========================================
# # ======================================================================================================
# class DiagnosisOutput(BaseModel):
#     diagnosis: str = Field(..., description="The generated diagnosis")
#     rationale: str = Field(..., description="The rationale behind the diagnosis")

class DiagnosisOutput(BaseModel):
    diagnoses: Dict[str, str] = Field(
        ..., description="A dictionary where the key is diagnosis and the value is rationale"
    )

class SingleDiagnosis(BaseModel):
    diagnosis: str
    rationale: str

class DiagnosisList(BaseModel):
    diagnoses: List[SingleDiagnosis]
#     )

def get_diagnosis_PydanticOutputParser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=DiagnosisList)

# ======================================================================================================
# ========================= Diagnosis Json output parser ===============================================
# ======================================================================================================

def get_diagnoses_JsonOutputParser() -> JsonOutputParser:
    return JsonOutputParser(pydantic_object=DiagnosisList)

def get_JsonOutputParser() -> JsonOutputParser:
    return JsonOutputParser()


# ==================================== Detection output Parser ==========================================
class YesNoOutput(BaseModel):
    answer: Literal["Yes", "No"]

def get_YesNoOutputParser() -> StrOutputParser:
    return StrOutputParser(pydantic_object=YesNoOutput)
