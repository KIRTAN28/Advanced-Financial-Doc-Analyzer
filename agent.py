"""
DRHP Capital Structure Drafting Agent — CLI
============================================
Usage:
    python agent.py                      # uses ./dataset
    python agent.py --path ./my_data     # custom path
    python agent.py --json               # output JSON only
"""

import os
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

from document_processor import process_folder, output_to_markdown_table

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="DRHP Capital Structure Drafting Agent - CLI")
    parser.add_argument("--path", default="dataset", help="Path to folder containing documents")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    parser.add_argument("--output", default=None, help="Output file path (default: stdout + output.json)")
    args = parser.parse_args()

    dataset_dir = Path(args.path)
    if not dataset_dir.exists():
        print(f"[ERROR] Path not found: {dataset_dir}")
        return

    print("=" * 65)
    print("  DRHP Capital Structure Drafting Agent")
    print("  LangChain + LangGraph Pipeline")
    print("=" * 65)
    print(f"\n[INPUT] Processing folder: {dataset_dir}")

    # Count files
    files = list(dataset_dir.rglob("*"))
    files = [f for f in files if f.is_file() and f.suffix.lower() in (".md", ".txt", ".pdf")]
    print(f"[INPUT] Found {len(files)} documents\n")

    # Run pipeline
    print("[PIPELINE] Running LangGraph pipeline...")
    print("  Stage 1: Document Ingestion...")
    print("  Stage 2: Classification (LLM)...")
    print("  Stage 3: Company Grouping...")
    print("  Stage 4: Capital Change Extraction (LLM)...")
    print("  Stage 5: Output Assembly...")

    output = process_folder(args.path)

    print(f"\n[RESULT] {output.total_documents} documents -> {output.total_companies} companies\n")

    if args.json:
        # JSON-only mode
        json_str = json.dumps(output.to_nested_dict(), indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"[SAVED] JSON -> {args.output}")
        else:
            print(json_str)
    else:
        # Print classifications
        print("-" * 65)
        print("  DOCUMENT CLASSIFICATION")
        print("-" * 65)
        for company in output.companies:
            print(f"\n  Company: {company.company_name}")
            if company.cin:
                print(f"  CIN: {company.cin}")
            for doc in company.documents_processed:
                official = "Official" if doc.is_official_filing else "Internal"
                print(f"    {doc.filename:<45} | {doc.document_type:<20} | {official:<10} | {doc.corporate_event}")

        # Print capital changes table
        print(f"\n{'-' * 65}")
        print("  AUTHORISED SHARE CAPITAL CHANGE TABLE")
        print("-" * 65)

        md_table = output_to_markdown_table(output)
        print(md_table)

        # Save outputs
        json_path = args.output or "output.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output.to_nested_dict(), f, indent=2)
        print(f"[SAVED] JSON -> {json_path}")

        with open("output_table.md", "w", encoding="utf-8") as f:
            f.write(md_table)
        print(f"[SAVED] Markdown -> output_table.md")

        # Print flat table summary
        flat = output.to_flat_table()
        print(f"\n[SUMMARY] {len(flat)} total capital change rows across {output.total_companies} companies")


if __name__ == "__main__":
    main()
