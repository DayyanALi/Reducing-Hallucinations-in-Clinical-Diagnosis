from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

# ======================================================================================================
# ========================= Diagnosis Simple string output parser ======================================
# ======================================================================================================
def get_StrOutputParser() -> StrOutputParser:
    return StrOutputParser()

# ======================================================================================================
# ========================= Diagnosis pydantic output parser ===========================================
# ======================================================================================================
class DiagnosisOutput(BaseModel):
    diagnosis: str = Field(..., description="The generated diagnosis")
    rationale: str = Field(..., description="The rationale behind the diagnosis")

class DiagnosisList(BaseModel):
    diagnoses: List[DiagnosisOutput] = Field(
        ..., description="A list of diagnosis + rationale entries"
    )

def get_diagnosis_PydanticOutputParser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=DiagnosisList)

# ======================================================================================================
# ========================= Diagnosis Json output parser ===============================================
# ======================================================================================================
def get_diagnosis_JsonOutputParser() -> JsonOutputParser:
    return JsonOutputParser()
