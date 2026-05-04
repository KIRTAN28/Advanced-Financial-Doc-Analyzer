"""
Standardized JSON Schemas for DRHP Capital Structure Drafting Agent
===================================================================
All Pydantic models used across the pipeline. These define the
canonical JSON output format for integration with downstream systems.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────
# Stage 1: Document Classification
# ──────────────────────────────────────────────────────────────

class ClassifiedDocument(BaseModel):
    """Classification result for a single uploaded document."""
    filename: str = Field(description="Original filename of the document.")
    company_name: str = Field(
        description="Full legal name of the company this document belongs to. "
                    "Extract from CIN line, header, or resolution text."
    )
    document_type: str = Field(
        description="One of: 'SH-7', 'PAS-3', 'MOA', 'Board Resolution', "
                    "'EGM Minutes', 'AGM Minutes', 'Notice of EGM', "
                    "'Notice of AGM', 'List of Allottees', 'Certificate of Incorporation', 'Other'."
    )
    is_official_filing: bool = Field(
        description="True if this is an official regulatory filing "
                    "(e.g., SH-7 filed with ROC, PAS-3 filed with MCA). False for internal docs."
    )
    corporate_event: str = Field(
        description="Brief description of the corporate event, e.g., "
                    "'Increase in Authorised Share Capital', 'Allotment of Shares', 'Incorporation'."
    )
    event_date: Optional[str] = Field(
        default=None,
        description="Date of the event in DD/MM/YYYY format if found in the document. None if not found."
    )


class ClassificationResult(BaseModel):
    """Wrapper for batch classification output."""
    classifications: List[ClassifiedDocument] = Field(
        description="One classification entry per input document."
    )


# ──────────────────────────────────────────────────────────────
# Stage 2: Capital Change Extraction
# ──────────────────────────────────────────────────────────────

class CapitalChangeRow(BaseModel):
    """A single row in the Authorised Share Capital Change table."""
    company_name: str = Field(
        description="Full legal name of the company."
    )
    meeting_date: str = Field(
        description="Date of the Shareholder's Meeting or event. "
                    "Format: 'Month DD, YYYY' (e.g., 'November 17, 2016') or 'On incorporation'."
    )
    meeting_type: str = Field(
        description="Type of meeting: 'AGM', 'EGM', or '-' if incorporation."
    )
    document_type: str = Field(
        description="Primary document type this row was extracted from: "
                    "'SH-7', 'PAS-3', 'MOA', 'Board Resolution', etc."
    )
    from_capital: str = Field(
        description="The 'From' capital description in Indian numbering format. "
                    "E.g., 'Rs 1,50,000 divided into 15,000 Equity Shares of Rs 10 each'. "
                    "Use '-' for incorporation. Use 'NA' if not found."
    )
    to_capital: str = Field(
        description="The 'To' capital description in Indian numbering format. "
                    "E.g., 'Rs 3,00,000 divided into 30,000 Equity Shares of Rs 10 each'. "
                    "Use 'NA' if not found."
    )
    source_documents: List[str] = Field(
        description="List of filenames used to extract this row."
    )
    confidence_flags: List[str] = Field(
        default_factory=list,
        description="Fields that could NOT be confirmed from the documents. "
                    "Empty list if everything is confirmed. E.g., ['meeting_type', 'from_capital']."
    )
    iso_date: str = Field(
        description="Date in YYYY-MM-DD format for chronological sorting. "
                    "Use '1900-01-01' for incorporation."
    )


class ExtractionResult(BaseModel):
    """Wrapper for extraction output per company-event bundle."""
    changes: List[CapitalChangeRow] = Field(
        description="One or more capital change rows extracted from the document bundle."
    )


# ──────────────────────────────────────────────────────────────
# Stage 3: Final Output — Standardized JSON
# ──────────────────────────────────────────────────────────────

class CompanyResult(BaseModel):
    """Complete result for a single company."""
    company_name: str = Field(description="Full legal name of the company.")
    cin: Optional[str] = Field(default=None, description="Corporate Identity Number if found.")
    registered_address: Optional[str] = Field(default=None, description="Registered office address if found.")
    documents_processed: List[ClassifiedDocument] = Field(
        description="All classified documents belonging to this company."
    )
    capital_changes: List[CapitalChangeRow] = Field(
        description="Chronologically sorted capital change rows for this company."
    )


class PipelineOutput(BaseModel):
    """
    The canonical JSON output of the entire pipeline.
    This is the standardized format for downstream integration.
    """
    total_documents: int = Field(description="Total number of documents processed.")
    total_companies: int = Field(description="Number of distinct companies found.")
    companies: List[CompanyResult] = Field(
        description="Results grouped by company, each with classifications and capital changes."
    )

    def to_flat_table(self) -> List[dict]:
        """Convert hierarchical output to flat table rows for display."""
        rows = []
        for company in self.companies:
            for change in company.capital_changes:
                rows.append({
                    "Company Name": company.company_name,
                    "CIN": company.cin or "NA",
                    "Date of Meeting": change.meeting_date,
                    "Document Type": change.document_type,
                    "From Capital": change.from_capital,
                    "To Capital": change.to_capital,
                    "AGM/EGM": change.meeting_type,
                    "Source Documents": ", ".join(change.source_documents),
                    "Confidence Flags": ", ".join(change.confidence_flags) if change.confidence_flags else "Confirmed",
                })
        return rows

    def to_nested_dict(self) -> dict:
        """
        Convert output to the exact nested format requested by the user:
        { "Company Name": { "SH-7": [ { ... } ], "PAS-3": [ { ... } ] } }
        """
        nested = {}
        for company in self.companies:
            comp_name = company.company_name
            nested[comp_name] = {}
            for change in company.capital_changes:
                doc_type = change.document_type
                if doc_type not in nested[comp_name]:
                    nested[comp_name][doc_type] = []
                
                # Exclude company_name and document_type since they are keys now
                change_dict = change.model_dump(exclude={"company_name", "document_type", "iso_date"})
                nested[comp_name][doc_type].append(change_dict)
        return nested

