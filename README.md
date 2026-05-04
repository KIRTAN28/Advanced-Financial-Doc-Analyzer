# DRHP Capital Structure Drafting Agent

An AI-driven system that ingests Indian company filings (SH-7, PAS-3, MOA, Board Resolutions) and produces a draft **Authorised Share Capital Change** table for a Draft Red Herring Prospectus (DRHP).

## Architecture

```
  Upload Files / Default Dataset
           |
    [Document Ingestion]
           |
    [Classification Chain]  -->  Identifies doc type, official/unofficial, corporate event
           |
    [Extraction Chain]      -->  Extracts capital change: From, To, Date, Meeting Type
           |
    [Table Renderer]        -->  Sorted, traceable Markdown / HTML table
```

## Tech Stack

| Component | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn |
| LLM Orchestration | LangChain (LCEL) |
| Output Parsing | `PydanticOutputParser` |
| LLM | OpenAI `gpt-4o-mini` |
| Schema Validation | Pydantic v2 |
| Frontend | Server-rendered HTML (dark glassmorphism UI) |

## Quick Start

```bash
# 1. Create & activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment variables
#    Create a .env file with your API key:
#    OPENAI_API_KEY="sk-..."

# 4. Generate the dummy dataset (4 SH-7 events + incorporation)
python generate_dataset.py

# 5a. Run the CLI agent
python agent.py

# 5b. OR run the FastAPI server
python -m uvicorn api:app --reload
#    Then open http://127.0.0.1:8000 in your browser
```

## Project Structure

```
S-45/
  requirements.txt
  generate_dataset.py     # Generates dummy SH-7 dataset
  agent.py                # CLI agent script
  api.py                  # FastAPI server with HTML frontend
  prompts.md              # Compiled list of prompts used
  system_design.md        # System design document
  README.md               # This file
  dataset/                # Generated dummy dataset
    incorporation/
    event_1/
    event_2/
    event_3/
    event_4/
  output_table.md         # Generated output
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Landing page with upload form |
| `POST` | `/process` | HTML response with classification + capital change table |
| `POST` | `/api/process` | Pure JSON response for programmatic access |
