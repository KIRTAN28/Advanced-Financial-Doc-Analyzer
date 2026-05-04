# System Design: DRHP Capital Structure Drafting Agent

## 1. Problem Statement

A Draft Red Herring Prospectus (DRHP) requires a precise table showing how a company's Authorised Share Capital has evolved over time. Currently, lawyers and bankers manually pull data from dozens of filings (SH-7, PAS-3, Board Resolutions, MOA) — a process that takes hours or days. This system automates that extraction while maintaining full traceability and flagging uncertainty.

## 2. High-Level Architecture

```
  Input Documents (SH-7, PAS-3, MOA, Board Resolutions)
           |
           v
  ┌─────────────────────────┐
  │   Document Ingestion    │  Reads .md files, groups by event folder
  └───────────┬─────────────┘
              v
  ┌─────────────────────────┐
  │  Classification Chain   │  LangChain LCEL: ChatPromptTemplate | ChatOpenAI | PydanticOutputParser
  │  (SystemMessage +       │  Output: DocumentClassification[] 
  │   HumanMessage)         │  → doc type, official/unofficial, corporate event
  └───────────┬─────────────┘
              v
  ┌─────────────────────────┐
  │   Extraction Chain      │  LangChain LCEL: ChatPromptTemplate | ChatOpenAI | PydanticOutputParser
  │  (SystemMessage +       │  Output: CapitalChange
  │   HumanMessage)         │  → date, from, to, meeting type, sources, flags
  └───────────┬─────────────┘
              v
  ┌─────────────────────────┐
  │   Table Renderer        │  Sorts chronologically, renders HTML + Markdown
  └─────────────────────────┘
```

## 3. Technology Choices

| Decision | Choice | Rationale |
|---|---|---|
| **LLM** | OpenAI `gpt-4o-mini` | Best balance of speed, cost, and structured output reliability. Gemini API key was suspended; Anthropic doesn't support native JSON mode as cleanly. |
| **Orchestration** | LangChain (LCEL) | Industry-standard for LLM pipelines. Expression Language (`prompt \| llm \| parser`) makes chains composable and testable. |
| **Output Parser** | `PydanticOutputParser` | Injects format instructions into prompt automatically. Parses raw LLM text into typed Pydantic models. Zero manual regex needed. |
| **API Framework** | FastAPI | Async-native, auto-generates OpenAPI docs, Pydantic-first. Perfect for this use case. |
| **Frontend** | Server-rendered HTML | No JS framework needed for a demo. Dark glassmorphism UI with Inter font for a premium feel. |

## 4. Two-Stage Pipeline Design

### Stage 1: Document Classification
**Why?** The assignment explicitly requires: *"Reads and classifies each document — figuring out what type it is, whether it's an official filing or an unofficial draft, and what corporate event it relates to."*

The classification chain receives all documents for an event and outputs a structured classification per document. This metadata is displayed in the UI and could be used downstream to weight source reliability (e.g., prioritize SH-7 over Board Meeting notes if numbers conflict).

### Stage 2: Capital Change Extraction
The extraction chain takes the same document bundle and extracts a single `CapitalChange` object per corporate event. The prompt enforces:
- **Traceability:** `source_documents` field lists exactly which files were used.
- **Honest AI:** `confidence_flags` field lists any data points that couldn't be confirmed. This directly addresses the assignment's core requirement: *"If something's missing or unclear, the system should say so."*
- **Indian numbering:** Capital descriptions follow the Rs X,XX,XXX convention used in actual DRHPs.

## 5. Traceability & Honest AI

This is the core differentiator of the system:

1. **Source Tracing:** Every row in the output table includes a `Source Documents` column listing the exact filenames from which data was extracted.
2. **Confidence Flags:** If the LLM cannot confirm a field from the provided documents, it adds the field name to `confidence_flags` and marks the value as `UNCONFIRMED`. These flags are displayed visually in the HTML table with warning icons.
3. **No Best Guesses:** The system prompt explicitly instructs: *"Do NOT hallucinate numbers."* Combined with the Pydantic schema enforcement, this prevents the LLM from filling in plausible-looking but unverified data.

## 6. API Design

| Endpoint | Method | Input | Output |
|---|---|---|---|
| `/` | GET | — | HTML landing page with upload form |
| `/generate-table` | POST | File uploads (optional) | HTML page with classification + capital change table |
| `/api/generate-table` | POST | File uploads (optional) | Pure JSON for programmatic access |

When no files are uploaded, the system falls back to the default `dataset/` directory and displays a warning message.

## 7. Scalability Considerations

- **Token Limits:** Currently all documents for one event are concatenated and sent as a single prompt. For massive documents (200+ page MOAs), a RAG layer with chunking would be needed.
- **Batch Processing:** The system processes event folders sequentially. For production, `asyncio.gather()` could parallelize LLM calls across events.
- **Conflict Resolution:** If an SH-7 states one number and a Board Resolution states another, a more advanced system would implement a "Debate" chain that explicitly compares values and prioritizes official filings.
- **PDF Support:** Currently the system accepts `.md` files. Adding `pdfplumber` or `PyMuPDF` for direct PDF ingestion would be a natural next step.

## 8. Conclusion

This system demonstrates that combining LangChain's structured output capabilities with a well-designed prompt engineering strategy can automate a significant portion of DRHP drafting — reducing hours of manual work to seconds, while being transparent about what it knows and what it doesn't.
