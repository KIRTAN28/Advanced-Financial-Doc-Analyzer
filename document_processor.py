"""
DRHP Capital Structure Drafting Agent — Core Pipeline
=====================================================
LangGraph-based pipeline that processes corporate filings through:
  1. Document Ingestion (PDF/MD/TXT → text)
  2. Document Classification (company name, doc type, event)
  3. Company Grouping (cluster by company → event)
  4. Capital Change Extraction (per company-event bundle)
  5. Output Assembly (standardized JSON → table)

Uses LangChain for LLM chains + LangGraph for orchestration.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from collections import defaultdict

from dotenv import load_dotenv
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage

from langgraph.graph import StateGraph, START, END

from schemas import (
    ClassifiedDocument,
    ClassificationResult,
    CapitalChangeRow,
    ExtractionResult,
    CompanyResult,
    PipelineOutput,
)

load_dotenv()

# ──────────────────────────────────────────────────────────────
# LLM Setup
# ──────────────────────────────────────────────────────────────

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# ──────────────────────────────────────────────────────────────
# LangGraph State Definition
# ──────────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    """State passed through the LangGraph pipeline."""
    # Input
    raw_documents: Dict[str, str]  # {filename: text_content}
    # After classification
    classifications: List[dict]
    # After grouping
    company_groups: Dict[str, Dict[str, List[str]]]  # {company: {event_key: [filenames]}}
    company_metadata: Dict[str, dict]  # {company: {cin, address}}
    # After extraction
    capital_changes: List[dict]
    # Final output
    pipeline_output: Optional[dict]
    # Error tracking
    errors: List[str]


# ──────────────────────────────────────────────────────────────
# Stage 1: Document Ingestion
# ──────────────────────────────────────────────────────────────

def ingest_from_folder(folder_path: str) -> Dict[str, str]:
    """Read all documents from a folder. Supports PDF, MD, TXT."""
    documents = {}
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    # Walk recursively through all subdirectories
    for file_path in sorted(folder.rglob("*")):
        if file_path.is_file():
            ext = file_path.suffix.lower()
            relative_name = str(file_path.relative_to(folder))

            if ext in (".md", ".txt"):
                try:
                    documents[relative_name] = file_path.read_text(encoding="utf-8")
                except Exception as e:
                    print(f"[WARN] Could not read {relative_name}: {e}")

            elif ext == ".pdf":
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(str(file_path))
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    doc.close()
                    if text.strip():
                        documents[relative_name] = text
                except Exception as e:
                    print(f"[WARN] Could not read PDF {relative_name}: {e}")

    return documents


def ingest_from_uploads(files: List[tuple]) -> Dict[str, str]:
    """Read uploaded file tuples of (filename, content_bytes)."""
    documents = {}
    for filename, content_bytes in files:
        ext = Path(filename).suffix.lower()

        if ext in (".md", ".txt"):
            try:
                documents[filename] = content_bytes.decode("utf-8")
            except Exception as e:
                print(f"[WARN] Could not decode {filename}: {e}")

        elif ext == ".pdf":
            try:
                import fitz
                doc = fitz.open(stream=content_bytes, filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                if text.strip():
                    documents[filename] = text
            except Exception as e:
                print(f"[WARN] Could not read PDF {filename}: {e}")
        else:
            # Try as text
            try:
                documents[filename] = content_bytes.decode("utf-8")
            except:
                pass

    return documents


# ──────────────────────────────────────────────────────────────
# Stage 2: Classification Node
# ──────────────────────────────────────────────────────────────

classification_parser = PydanticOutputParser(pydantic_object=ClassificationResult)

classification_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=(
        "You are a senior document classifier with 15+ years of experience in Indian corporate filings "
        "and investment banking. You specialize in DRHP (Draft Red Herring Prospectus) preparation.\n\n"
        "For EACH document below, determine:\n"
        "1. **company_name**: The FULL LEGAL name of the company (e.g., 'NEXUS BRIGHTLEARN SOLUTIONS PRIVATE LIMITED'). "
        "Look for it in CIN lines, headers, resolution text, or form fields.\n"
        "2. **document_type**: Exactly one of: 'SH-7', 'PAS-3', 'MOA', 'Board Resolution', "
        "'EGM Minutes', 'AGM Minutes', 'Notice of EGM', 'Notice of AGM', 'List of Allottees', "
        "'Certificate of Incorporation', 'Other'.\n"
        "3. **is_official_filing**: True for regulatory filings (SH-7, PAS-3), False for internal docs.\n"
        "4. **corporate_event**: Brief event description.\n"
        "5. **event_date**: The date of the meeting/event in DD/MM/YYYY format, or null if not found.\n\n"
        "IMPORTANT: Use the EXACT filename as given. Do NOT rename files."
    )),
    ("human",
     "Classify each of the following documents:\n\n"
     "{documents_content}\n\n"
     "{format_instructions}")
])

classification_chain = classification_prompt | llm | classification_parser


def classify_node(state: PipelineState) -> dict:
    """LangGraph node: classify all documents."""
    raw_docs = state["raw_documents"]
    errors = list(state.get("errors", []))

    # Build document content string
    doc_parts = []
    for filename, content in raw_docs.items():
        # Truncate very long documents to avoid token limits
        truncated = content[:8000] if len(content) > 8000 else content
        doc_parts.append(f"\n--- DOCUMENT: {filename} ---\n{truncated}")

    documents_content = "\n".join(doc_parts)

    try:
        result = classification_chain.invoke({
            "documents_content": documents_content,
            "format_instructions": classification_parser.get_format_instructions(),
        })
        classifications = [c.model_dump() for c in result.classifications]
    except Exception as e:
        errors.append(f"Classification failed: {str(e)}")
        # Fallback: create basic classifications from filenames
        classifications = []
        for filename in raw_docs.keys():
            doc_type = guess_doc_type(filename)
            classifications.append({
                "filename": filename,
                "company_name": "UNKNOWN",
                "document_type": doc_type,
                "is_official_filing": doc_type in ("SH-7", "PAS-3"),
                "corporate_event": "Unknown",
                "event_date": None,
            })

    return {"classifications": classifications, "errors": errors}


def guess_doc_type(filename: str) -> str:
    """Fallback: guess document type from filename."""
    fn = filename.lower()
    if "sh7" in fn or "sh-7" in fn:
        return "SH-7"
    elif "pas-3" in fn or "pas3" in fn:
        return "PAS-3"
    elif "moa" in fn or "memorandum" in fn:
        return "MOA"
    elif "board" in fn and "meeting" in fn:
        return "Board Resolution"
    elif "board" in fn and "allot" in fn:
        return "Board Resolution"
    elif "egm" in fn:
        return "EGM Minutes"
    elif "agm" in fn:
        return "AGM Minutes"
    elif "notice" in fn:
        return "Notice of EGM"
    elif "allottee" in fn:
        return "List of Allottees"
    elif "incorp" in fn or "certificate" in fn:
        return "Certificate of Incorporation"
    return "Other"


# ──────────────────────────────────────────────────────────────
# Stage 3: Company Grouping Node
# ──────────────────────────────────────────────────────────────

def normalize_company_name(name: str) -> str:
    """Normalize company name for grouping (handles minor LLM variations)."""
    name = name.upper().strip()
    name = re.sub(r'\s+', ' ', name)
    # Remove common suffixes variations
    name = name.replace("PVT LTD", "PRIVATE LIMITED")
    name = name.replace("PVT. LTD.", "PRIVATE LIMITED")
    name = name.replace("PVT. LTD", "PRIVATE LIMITED")
    name = name.replace("PVTLTD", "PRIVATE LIMITED")
    return name


def group_node(state: PipelineState) -> dict:
    """LangGraph node: group documents by company and corporate event."""
    classifications = state["classifications"]
    errors = list(state.get("errors", []))
    raw_docs = state["raw_documents"]

    company_groups = defaultdict(lambda: defaultdict(list))
    company_metadata = {}

    for cls in classifications:
        company = normalize_company_name(cls["company_name"])
        event_key = cls.get("event_date", "") or cls.get("corporate_event", "unknown")
        company_groups[company][event_key].append(cls["filename"])

        # Extract CIN and address from document content if available
        if company not in company_metadata:
            company_metadata[company] = {"cin": None, "address": None, "display_name": cls["company_name"]}

        # Try to extract CIN from document content
        if cls["filename"] in raw_docs and not company_metadata[company]["cin"]:
            cin_match = re.search(r'[A-Z]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}', raw_docs[cls["filename"]])
            if cin_match:
                company_metadata[company]["cin"] = cin_match.group()

            # Try to extract address
            addr_match = re.search(
                r'(?:registered\s+office|address)[:\s]+(.+?)(?:\n|$)',
                raw_docs[cls["filename"]], re.IGNORECASE
            )
            if addr_match and not company_metadata[company]["address"]:
                company_metadata[company]["address"] = addr_match.group(1).strip()[:200]

    # Convert defaultdicts to regular dicts for serialization
    company_groups_dict = {k: dict(v) for k, v in company_groups.items()}

    return {
        "company_groups": company_groups_dict,
        "company_metadata": company_metadata,
        "errors": errors,
    }


# ──────────────────────────────────────────────────────────────
# Stage 4: Extraction Node
# ──────────────────────────────────────────────────────────────

extraction_parser = PydanticOutputParser(pydantic_object=ExtractionResult)

extraction_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=(
        "You are a senior AI agent with 15+ years of investment banking experience at a top-tier firm, "
        "specializing in analyzing Indian corporate filings (SH-7, PAS-3, MOA, Board Resolutions) "
        "to extract capital structure data for Draft Red Herring Prospectuses (DRHPs).\n\n"
        "RULES:\n"
        "1. Extract ALL capital-related events found in the documents. This includes:\n"
        "   - Authorised Share Capital Changes (usually found in SH-7, Board Resolutions, EGM/AGM minutes)\n"
        "   - Allotment of Shares / Issued Capital (usually found in PAS-3, List of Allottees)\n"
        "   - Initial Incorporation Capital (usually found in MOA)\n"
        "2. Be precise — every number MUST trace to the source document text.\n"
        "3. If a field CANNOT be confirmed from the documents, add it to 'confidence_flags' "
        "   and write 'NA' as its value.\n"
        "4. Format capital descriptions in Indian numbering:\n"
        "   'Rs X,XX,XXX divided into N Equity Shares of Rs Y each'\n"
        "5. Do NOT hallucinate or invent numbers.\n"
        "6. The document_type field should indicate the PRIMARY regulatory form if available (e.g., 'SH-7', 'PAS-3', 'MOA'). If not, use the main internal document type.\n"
        "7. For incorporation events (MOA), set from_capital to 'NA' or '-', and meeting_type to 'Incorporation'.\n"
        "8. For share allotments (PAS-3), explain the allotment in the 'to_capital' field (e.g. 'Allotment of X shares...') and set 'from_capital' to 'NA' if not applicable.\n"
        "9. Each distinct capital event should be a separate row.\n"
        "10. company_name must be the FULL LEGAL name exactly as it appears in the documents.\n\n"
        "IMPORTANT: Extract ALL capital-related events you find across the documents."
    )),
    ("human",
     "Company: {company_name}\n\n"
     "Documents for this company:\n{documents_content}\n\n"
     "Extract ALL capital-related events.\n"
     "{format_instructions}")
])

extraction_chain = extraction_prompt | llm | extraction_parser


def extract_node(state: PipelineState) -> dict:
    """LangGraph node: extract capital changes for each company."""
    company_groups = state["company_groups"]
    company_metadata = state["company_metadata"]
    raw_docs = state["raw_documents"]
    errors = list(state.get("errors", []))

    all_changes = []

    batch_inputs = []
    company_names = []

    for company, event_groups in company_groups.items():
        display_name = company_metadata.get(company, {}).get("display_name", company)

        # Collect ALL documents for this company into one bundle
        all_filenames = set()
        for event_key, filenames in event_groups.items():
            all_filenames.update(filenames)

        # Build document content
        doc_parts = []
        for filename in sorted(all_filenames):
            if filename in raw_docs:
                content = raw_docs[filename]
                truncated = content[:8000] if len(content) > 8000 else content
                doc_parts.append(f"\n--- DOCUMENT: {filename} ---\n{truncated}")

        documents_content = "\n".join(doc_parts)

        if not documents_content.strip():
            errors.append(f"No readable content for company: {display_name}")
            continue

        batch_inputs.append({
            "company_name": display_name,
            "documents_content": documents_content,
            "format_instructions": extraction_parser.get_format_instructions(),
        })
        company_names.append(display_name)

    if batch_inputs:
        # Run batch extraction concurrently
        batch_results = extraction_chain.batch(batch_inputs, return_exceptions=True)
        
        for display_name, result in zip(company_names, batch_results):
            if isinstance(result, Exception):
                errors.append(f"Extraction failed for {display_name}: {str(result)}")
            else:
                for change in result.changes:
                    change_dict = change.model_dump()
                    # Ensure company name is consistent
                    change_dict["company_name"] = display_name
                    all_changes.append(change_dict)

    # Sort all changes by iso_date
    all_changes.sort(key=lambda c: (c.get("company_name", ""), c.get("iso_date", "9999")))

    return {"capital_changes": all_changes, "errors": errors}


# ──────────────────────────────────────────────────────────────
# Stage 5: Output Assembly Node
# ──────────────────────────────────────────────────────────────

def assemble_node(state: PipelineState) -> dict:
    """LangGraph node: assemble final standardized JSON output."""
    classifications = state["classifications"]
    capital_changes = state["capital_changes"]
    company_metadata = state["company_metadata"]
    raw_docs = state["raw_documents"]

    # Group by company
    companies_map = defaultdict(lambda: {
        "classifications": [],
        "capital_changes": [],
    })

    for cls in classifications:
        company = normalize_company_name(cls["company_name"])
        companies_map[company]["classifications"].append(cls)

    for change in capital_changes:
        company = normalize_company_name(change["company_name"])
        companies_map[company]["capital_changes"].append(change)

    # Build CompanyResult list
    company_results = []
    for company_key, data in companies_map.items():
        meta = company_metadata.get(company_key, {})
        display_name = meta.get("display_name", company_key)

        company_results.append({
            "company_name": display_name,
            "cin": meta.get("cin"),
            "registered_address": meta.get("address"),
            "documents_processed": data["classifications"],
            "capital_changes": sorted(
                data["capital_changes"],
                key=lambda c: c.get("iso_date", "9999")
            ),
        })

    pipeline_output = {
        "total_documents": len(raw_docs),
        "total_companies": len(company_results),
        "companies": company_results,
    }

    return {"pipeline_output": pipeline_output}


# ──────────────────────────────────────────────────────────────
# LangGraph Pipeline Assembly
# ──────────────────────────────────────────────────────────────

def build_pipeline():
    """Build and compile the LangGraph pipeline."""
    workflow = StateGraph(PipelineState)

    # Add nodes
    workflow.add_node("classify", classify_node)
    workflow.add_node("group", group_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("assemble", assemble_node)

    # Define edges (linear pipeline)
    workflow.add_edge(START, "classify")
    workflow.add_edge("classify", "group")
    workflow.add_edge("group", "extract")
    workflow.add_edge("extract", "assemble")
    workflow.add_edge("assemble", END)

    return workflow.compile()


# Create the compiled pipeline
pipeline = build_pipeline()


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────

def process_folder(folder_path: str) -> PipelineOutput:
    """Process all documents in a folder and return standardized JSON output."""
    raw_docs = ingest_from_folder(folder_path)

    if not raw_docs:
        return PipelineOutput(
            total_documents=0,
            total_companies=0,
            companies=[],
        )

    initial_state: PipelineState = {
        "raw_documents": raw_docs,
        "classifications": [],
        "company_groups": {},
        "company_metadata": {},
        "capital_changes": [],
        "pipeline_output": None,
        "errors": [],
    }

    result = pipeline.invoke(initial_state)

    # Convert dict output to PipelineOutput model
    return PipelineOutput(**result["pipeline_output"])


def process_uploads(files: List[tuple]) -> PipelineOutput:
    """Process uploaded files and return standardized JSON output."""
    raw_docs = ingest_from_uploads(files)

    if not raw_docs:
        return PipelineOutput(
            total_documents=0,
            total_companies=0,
            companies=[],
        )

    initial_state: PipelineState = {
        "raw_documents": raw_docs,
        "classifications": [],
        "company_groups": {},
        "company_metadata": {},
        "capital_changes": [],
        "pipeline_output": None,
        "errors": [],
    }

    result = pipeline.invoke(initial_state)

    return PipelineOutput(**result["pipeline_output"])


def output_to_markdown_table(output: PipelineOutput) -> str:
    """Convert PipelineOutput to a Markdown table string."""
    rows = output.to_flat_table()

    if not rows:
        return "No capital changes found.\n"

    md = "## Draft Authorised Share Capital Change\n\n"
    md += "| Company Name | Date of Meeting | Document Type | From Capital | To Capital | AGM/EGM | Source Documents | Confidence |\n"
    md += "|---|---|---|---|---|---|---|---|\n"

    for row in rows:
        md += (
            f"| {row['Company Name']} "
            f"| {row['Date of Meeting']} "
            f"| {row['Document Type']} "
            f"| {row['From Capital']} "
            f"| {row['To Capital']} "
            f"| {row['AGM/EGM']} "
            f"| {row['Source Documents']} "
            f"| {row['Confidence Flags']} |\n"
        )

    return md
