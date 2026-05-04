"""
DRHP Capital Structure Drafting Agent — FastAPI Server
======================================================
Premium web portal with drag-drop upload, multi-company support,
standardized JSON output, and interactive table rendering.

Tech: FastAPI + LangChain + LangGraph + OpenAI gpt-4o-mini
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from document_processor import process_folder, process_uploads, output_to_markdown_table
from schemas import PipelineOutput

load_dotenv()

app = FastAPI(
    title="DRHP Capital Structure Drafting Agent",
    description="AI-driven system for extracting Authorised Share Capital changes from company filings.",
    version="3.0.0",
)


# ──────────────────────────────────────────────────────────────
# HTML Builder
# ──────────────────────────────────────────────────────────────

def build_html(pipeline_output: Optional[PipelineOutput] = None, message: str = "", msg_type: str = "info") -> str:
    msg_colors = {
        "info": ("rgba(59,130,246,0.15)", "#3b82f6"),
        "success": ("rgba(34,197,94,0.15)", "#22c55e"),
        "warning": ("rgba(234,179,8,0.15)", "#eab308"),
        "error": ("rgba(239,68,68,0.15)", "#ef4444"),
    }
    bg, border = msg_colors.get(msg_type, msg_colors["info"])

    message_html = f'<div class="message" style="background:{bg};border-left:4px solid {border};">{message}</div>' if message else ""

    # Build results HTML
    results_html = ""
    json_output = "{}"

    if pipeline_output and pipeline_output.companies:
        json_output = json.dumps(pipeline_output.to_nested_dict(), indent=2, default=str)

        # Company tabs
        tab_buttons = ""
        tab_contents = ""
        for i, company in enumerate(pipeline_output.companies):
            active_btn = "active" if i == 0 else ""
            active_tab = 'style="display:block;"' if i == 0 else 'style="display:none;"'

            tab_buttons += f'<button class="tab-btn {active_btn}" onclick="switchTab({i})" id="tab-btn-{i}">{company.company_name}</button>'

            # Classification rows
            cls_rows = ""
            for doc in company.documents_processed:
                badge = "badge-official" if doc.is_official_filing else "badge-internal"
                label = "Official" if doc.is_official_filing else "Internal"
                cls_rows += f"""<tr>
                    <td>{doc.filename}</td>
                    <td><span class="badge badge-doc">{doc.document_type}</span></td>
                    <td><span class="badge {badge}">{label}</span></td>
                    <td>{doc.corporate_event}</td>
                    <td>{doc.event_date or 'NA'}</td>
                </tr>"""

            # Capital change rows
            cap_rows = ""
            for ch in company.capital_changes:
                mt = ch.meeting_type
                badge_cls = "badge-egm" if mt == "EGM" else ("badge-agm" if mt == "AGM" else "badge-inc")
                sources_html = " ".join(f'<span class="source-tag">{s}</span>' for s in ch.source_documents)
                flags_html = ""
                if ch.confidence_flags:
                    flags_html = '<br>' + ' '.join(f'<span class="flag">&#9888; {f}</span>' for f in ch.confidence_flags)
                else:
                    flags_html = '<span class="confirmed">✓</span>'

                cap_rows += f"""<tr>
                    <td>{ch.meeting_date}</td>
                    <td><span class="badge badge-doc">{ch.document_type}</span></td>
                    <td class="capital-cell">{ch.from_capital}</td>
                    <td class="capital-cell">{ch.to_capital}</td>
                    <td><span class="badge {badge_cls}">{mt}</span></td>
                    <td>{sources_html}</td>
                    <td>{flags_html}</td>
                </tr>"""

            if not cap_rows:
                cap_rows = '<tr><td colspan="7" class="empty-state">No capital changes extracted.</td></tr>'

            cin_display = f'<span class="meta-tag">CIN: {company.cin}</span>' if company.cin else ""

            tab_contents += f"""
            <div class="tab-content" id="tab-content-{i}" {active_tab}>
                <div class="company-header">
                    <h3>{company.company_name}</h3>
                    {cin_display}
                </div>

                <div class="card">
                    <h2>📋 Document Classification</h2>
                    <div class="table-wrap">
                    <table>
                        <thead><tr>
                            <th>Document</th><th>Type</th><th>Filing Status</th><th>Corporate Event</th><th>Event Date</th>
                        </tr></thead>
                        <tbody>{cls_rows}</tbody>
                    </table>
                    </div>
                </div>

                <div class="card">
                    <h2>📊 Authorised Share Capital Change</h2>
                    <div class="table-wrap">
                    <table>
                        <thead><tr>
                            <th>Date of Meeting</th><th>Doc Type</th><th>From Capital</th><th>To Capital</th><th>AGM/EGM</th><th>Source Documents</th><th>Confidence</th>
                        </tr></thead>
                        <tbody>{cap_rows}</tbody>
                    </table>
                    </div>
                </div>
            </div>"""

        results_html = f"""
        <div class="card stats-card">
            <div class="stat"><span class="stat-num">{pipeline_output.total_documents}</span><span class="stat-label">Documents</span></div>
            <div class="stat"><span class="stat-num">{pipeline_output.total_companies}</span><span class="stat-label">Companies</span></div>
            <div class="stat"><span class="stat-num">{sum(len(c.capital_changes) for c in pipeline_output.companies)}</span><span class="stat-label">Capital Events</span></div>
        </div>
        <div class="tabs">{tab_buttons}</div>
        {tab_contents}
        <div class="card">
            <h2>📦 Raw JSON Output</h2>
            <details><summary>Click to expand standardized JSON</summary>
            <pre class="json-output">{json_output}</pre>
            </details>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DRHP Capital Structure Drafting Agent</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    color: #e2e8f0; min-height: 100vh; padding: 2rem;
}}
.container {{ max-width: 1400px; margin: 0 auto; }}
.header {{ text-align: center; margin-bottom: 2.5rem; }}
.header h1 {{
    font-size: 2.2rem; font-weight: 700;
    background: linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}}
.header p {{ color: #94a3b8; font-size: 0.95rem; }}
.card {{
    background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(16px);
    border: 1px solid rgba(148, 163, 184, 0.12); border-radius: 16px;
    padding: 1.5rem 2rem; margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}}
.card h2 {{ font-size: 1.15rem; font-weight: 600; color: #f1f5f9; margin-bottom: 1rem; }}
.upload-zone {{
    border: 2px dashed rgba(148,163,184,0.3); border-radius: 12px;
    padding: 2rem; text-align: center; cursor: pointer;
    transition: all 0.3s; background: rgba(15,23,42,0.4);
}}
.upload-zone:hover {{ border-color: #60a5fa; background: rgba(59,130,246,0.05); }}
.upload-zone input {{ display: none; }}
.upload-zone p {{ color: #94a3b8; margin: 0.5rem 0; }}
.upload-zone .icon {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
.btn-row {{ display: flex; gap: 1rem; margin-top: 1rem; flex-wrap: wrap; justify-content: center; }}
.btn {{
    padding: 0.75rem 1.75rem; border: none; border-radius: 10px;
    font-weight: 600; font-size: 0.95rem; cursor: pointer; transition: all 0.2s;
}}
.btn-primary {{
    background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: #fff;
}}
.btn-primary:hover {{ transform: translateY(-1px); box-shadow: 0 4px 16px rgba(59,130,246,0.4); }}
.btn-secondary {{
    background: rgba(148,163,184,0.15); color: #94a3b8;
    border: 1px solid rgba(148,163,184,0.2);
}}
.btn-secondary:hover {{ background: rgba(148,163,184,0.25); color: #e2e8f0; }}
.message {{ padding: 1rem 1.25rem; border-radius: 10px; margin-bottom: 1.5rem; font-size: 0.9rem; color: #e2e8f0; }}
.stats-card {{ display: flex; gap: 2rem; justify-content: center; flex-wrap: wrap; }}
.stat {{ text-align: center; }}
.stat-num {{ display: block; font-size: 2rem; font-weight: 700; color: #60a5fa; }}
.stat-label {{ font-size: 0.85rem; color: #94a3b8; }}
.tabs {{ display: flex; gap: 0.5rem; margin-bottom: 0; flex-wrap: wrap; }}
.tab-btn {{
    padding: 0.6rem 1.2rem; border: 1px solid rgba(148,163,184,0.2);
    border-bottom: none; border-radius: 10px 10px 0 0; background: rgba(30,41,59,0.5);
    color: #94a3b8; font-weight: 500; cursor: pointer; font-size: 0.85rem; transition: all 0.2s;
}}
.tab-btn.active {{ background: rgba(30,41,59,0.9); color: #60a5fa; border-color: rgba(96,165,250,0.3); }}
.tab-content {{ animation: fadeIn 0.3s ease; }}
@keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
.company-header {{ display: flex; align-items: center; gap: 1rem; margin: 1rem 0; flex-wrap: wrap; }}
.company-header h3 {{ font-size: 1.1rem; color: #f1f5f9; }}
.meta-tag {{ padding: 0.2rem 0.6rem; background: rgba(59,130,246,0.1); border-radius: 6px; font-size: 0.75rem; color: #93c5fd; }}
.table-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 12px; border: 1px solid rgba(148,163,184,0.12); overflow: hidden; }}
th {{ background: rgba(59,130,246,0.15); color: #93c5fd; font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; padding: 0.85rem 1rem; text-align: left; border-bottom: 1px solid rgba(148,163,184,0.12); white-space: nowrap; }}
td {{ padding: 0.75rem 1rem; font-size: 0.85rem; color: #cbd5e1; border-bottom: 1px solid rgba(148,163,184,0.06); vertical-align: top; }}
tr:hover td {{ background: rgba(59,130,246,0.05); }}
tr:last-child td {{ border-bottom: none; }}
.capital-cell {{ max-width: 280px; }}
.badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.72rem; font-weight: 600; white-space: nowrap; }}
.badge-egm {{ background: rgba(234,179,8,0.15); color: #fbbf24; }}
.badge-agm {{ background: rgba(34,197,94,0.15); color: #4ade80; }}
.badge-inc {{ background: rgba(148,163,184,0.15); color: #94a3b8; }}
.badge-official {{ background: rgba(34,197,94,0.15); color: #4ade80; }}
.badge-internal {{ background: rgba(148,163,184,0.15); color: #94a3b8; }}
.badge-doc {{ background: rgba(139,92,246,0.15); color: #a78bfa; }}
.flag {{ color: #f87171; font-size: 0.78rem; }}
.confirmed {{ color: #4ade80; font-size: 0.85rem; }}
.source-tag {{ display: inline-block; padding: 0.12rem 0.45rem; background: rgba(148,163,184,0.1); border-radius: 4px; font-size: 0.72rem; margin: 0.1rem; color: #94a3b8; }}
.empty-state {{ text-align: center; color: #64748b; padding: 2rem !important; }}
.json-output {{ background: rgba(15,23,42,0.6); border: 1px solid rgba(148,163,184,0.1); border-radius: 8px; padding: 1rem; font-size: 0.75rem; color: #94a3b8; overflow-x: auto; max-height: 500px; line-height: 1.5; }}
details {{ margin-top: 0.5rem; }}
summary {{ cursor: pointer; color: #60a5fa; font-size: 0.9rem; padding: 0.5rem 0; }}
.file-list {{ margin: 0.5rem 0; padding: 0; list-style: none; }}
.file-list li {{ padding: 0.3rem 0.5rem; font-size: 0.85rem; color: #94a3b8; }}
.loading {{ display: none; text-align: center; padding: 3rem; }}
.loading.show {{ display: block; }}
.spinner {{ width: 40px; height: 40px; border: 3px solid rgba(96,165,250,0.2); border-top-color: #60a5fa; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 1rem; }}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>DRHP Capital Structure Drafting Agent</h1>
    </div>

    <div class="card">
        <h2>📁 Upload Documents</h2>
        <form id="uploadForm" action="/process" method="post" enctype="multipart/form-data">
            <div class="upload-zone" id="dropZone" onclick="document.getElementById('fileInput').click();">
                <div class="icon">📄</div>
                <p><strong>Drop files here</strong> or click to browse</p>
                <p style="font-size:0.8rem;">Supports PDF, MD, TXT &bull; Mixed companies auto-detected</p>
                <input type="file" id="fileInput" name="files" multiple accept=".md,.txt,.pdf" />
            </div>
            <ul class="file-list" id="fileList"></ul>
            <div class="btn-row">
                <button type="submit" class="btn btn-primary" id="processBtn">⚡ Process & Generate Table</button>
                <button type="button" class="btn btn-secondary" onclick="useDefault()">📦 Use Default Dataset</button>
            </div>
        </form>
    </div>

    <div class="loading" id="loadingState">
        <div class="spinner"></div>
        <p>Processing documents with AI pipeline...</p>
        <p style="font-size:0.8rem; color:#64748b;">Classifying → Grouping → Extracting → Assembling</p>
    </div>

    {message_html}
    {results_html}
</div>

<script>
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');

fileInput.addEventListener('change', updateFileList);
dropZone.addEventListener('dragover', e => {{ e.preventDefault(); dropZone.style.borderColor = '#60a5fa'; }});
dropZone.addEventListener('dragleave', () => {{ dropZone.style.borderColor = 'rgba(148,163,184,0.3)'; }});
dropZone.addEventListener('drop', e => {{
    e.preventDefault(); dropZone.style.borderColor = 'rgba(148,163,184,0.3)';
    fileInput.files = e.dataTransfer.files; updateFileList();
}});

function updateFileList() {{
    fileList.innerHTML = '';
    for (const f of fileInput.files) {{
        const li = document.createElement('li');
        li.textContent = '📄 ' + f.name + ' (' + (f.size/1024).toFixed(1) + ' KB)';
        fileList.appendChild(li);
    }}
}}

function useDefault() {{
    window.location.href = '/process?use_default=true';
}}

function switchTab(idx) {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
    document.getElementById('tab-btn-' + idx).classList.add('active');
    document.getElementById('tab-content-' + idx).style.display = 'block';
}}

document.getElementById('uploadForm').addEventListener('submit', function() {{
    document.getElementById('loadingState').classList.add('show');
}});
</script>
</body>
</html>"""


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home():
    """Landing page."""
    return HTMLResponse(content=build_html())


@app.get("/process", response_class=HTMLResponse)
async def process_default(use_default: Optional[str] = None):
    """Process default dataset."""
    if use_default:
        try:
            output = process_folder("dataset")
            msg = f"Processed {output.total_documents} documents across {output.total_companies} companies from default dataset."
            # Save outputs
            with open("output.json", "w", encoding="utf-8") as f:
                json.dump(output.to_nested_dict(), f, indent=2)
            with open("output_table.md", "w", encoding="utf-8") as f:
                f.write(output_to_markdown_table(output))
            return HTMLResponse(content=build_html(output, msg, "success"))
        except Exception as e:
            return HTMLResponse(content=build_html(None, f"Error: {e}", "error"))
    return HTMLResponse(content=build_html())


@app.post("/process", response_class=HTMLResponse)
async def process_upload(files: List[UploadFile] = File(None)):
    """Process uploaded files."""
    has_files = files and len(files) > 0 and files[0].filename != ""

    if not has_files:
        return HTMLResponse(content=build_html(None, "No files uploaded. Please select files or use the default dataset.", "warning"))

    try:
        file_tuples = []
        for f in files:
            content = await f.read()
            file_tuples.append((f.filename, content))

        output = process_uploads(file_tuples)

        # Save outputs
        with open("output.json", "w", encoding="utf-8") as f:
            json.dump(output.to_nested_dict(), f, indent=2)
        with open("output_table.md", "w", encoding="utf-8") as f:
            f.write(output_to_markdown_table(output))

        msg = f"Successfully processed {output.total_documents} documents across {output.total_companies} companies."
        return HTMLResponse(content=build_html(output, msg, "success"))
    except Exception as e:
        return HTMLResponse(content=build_html(None, f"Error during processing: {e}", "error"))


@app.post("/api/process")
async def api_process(files: List[UploadFile] = File(None)):
    """Pure JSON API endpoint — returns standardized PipelineOutput."""
    has_files = files and len(files) > 0 and files[0].filename != ""

    if has_files:
        file_tuples = []
        for f in files:
            content = await f.read()
            file_tuples.append((f.filename, content))
        output = process_uploads(file_tuples)
    else:
        output = process_folder("dataset")

    return JSONResponse(content=output.to_nested_dict())


@app.get("/api/process")
async def api_process_default():
    """JSON API with default dataset."""
    output = process_folder("dataset")
    return JSONResponse(content=output.to_nested_dict())


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "3.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
