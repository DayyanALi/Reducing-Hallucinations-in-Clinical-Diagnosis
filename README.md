# Reducing-Hallucinations-in-Clinical-Diagnosis

This repository contains a modular, LangChain‑powered pipeline for **differential diagnosis generation** from doctor–patient transcripts, with pluggable components for prompt templates, LLM backends, output parsing, and hallucination verification tools.

---

## 🚀 Project Overview

* **Objective**: Given a transcript of a clinical encounter, generate a structured list of possible diagnoses with rationales, and quantify the degree to which each rationale is supported by the transcript.

---

## 📁 Repository Structure

```plaintext
project_root/
├── scripts/               # Entry-point script (run_generation.py)
├── generator/             # Differential-diagnosis logic
│   ├── templates.py       # PromptTemplate definitions
│   ├── clients.py         # LLM registry 
│   ├── output_parsers.py  # Str and Pydantic parsers
│   ├── prompt_template.py # Contains prompt template
├── utils/                
├── .gitignore            
└── README.md             
```

---

## ⚙️ Installation & Setup

1. **Clone the repo**:

   ```bash
   git clone https://github.com/your-org/clinical-dx-pipeline.git
   ```

2. **Create a virtual environment** and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate    # macOS/Linux
   venv\\Scripts\\activate   # Windows
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** in a `.env` file:

   ```dotenv
   OPENAI_API_KEY=sk-...
   HUGGINGFACEHUB_API_TOKEN=hf_...
   ```
---

## ▶️ Quick Start

```bash
# From project root:
python -m scripts.run_generation
```