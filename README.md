# Reducing-Hallucinations-in-Clinical-Diagnosis

This repository contains a modular, LangChain‑powered pipeline for **differential diagnosis generation** from doctor–patient transcripts, with pluggable components for prompt templates, LLM backends, output parsing, and hallucination verification tools.

---

## 🚀 Project Overview

* **Objective**: Given a transcript of a clinical encounter, generate a structured list of possible diagnoses with rationales, and quantify the degree to which each rationale is supported by the transcript.
* **Modularity**: Easily swap or add:

  * 📝 **Prompt Templates** (`generator/templates.py`)
  * 🤖 **LLM Clients** (OpenAI GPT, Me‑LLaMA, Mistral, etc.) via `generator/clients.py`
  * 📦 **Output Parsers** (`StrOutputParser`, `PydanticOutputParser`) in `generator/output_parsers.py`
  * 🔍 **Hallucination Verifiers** (entailment, QA checks) in `verifier/`
* **LangChain Runnables**: Compose prompt → model → parser → verifier into flexible chains or Agents.

---

## 📁 Repository Structure

```plaintext
project_root/
├── scripts/              # Entry-point scripts (run_generation.py)
├── generator/            # Differential-diagnosis logic
│   ├── templates.py      # PromptTemplate definitions
│   ├── clients.py        # LLM registry & factory functions
│   ├── output_parsers.py # Str and Pydantic parsers
│   ├── chain_factory.py  # General prompt|model|parser factory
│   └── registry.py       # Central model registry
├── verifier/             # Hallucination metric modules
│   ├── entailment.py     # NLI-based verifier
│   ├── qa_consistency.py # QA-based verifier
│   └── composite.py      # Composite scoring
├── utils/                # Helpers (transcript loader, config)
├── .gitignore            # Untracked files
└── README.md             # This file
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