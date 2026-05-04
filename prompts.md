# Compiled Prompts Used

All prompts below are used in `api.py` and `agent.py` via LangChain's `ChatPromptTemplate` + `PydanticOutputParser`.

---

## 1. Document Classification Prompt

**LLM:** OpenAI `gpt-4o-mini` (temperature=0)
**Output Parser:** `PydanticOutputParser(pydantic_object=ClassificationResult)`

```text
SYSTEM MESSAGE:
You are an expert document classifier for Indian corporate filings.
You will receive a bundle of documents. For EACH document, determine:
(1) the document type, (2) whether it is an official regulatory filing,
and (3) what corporate event it relates to.
Be precise and use the exact document names provided.

HUMAN MESSAGE:
Classify each of the following documents:

{documents_content}

{format_instructions}
```

**Why this prompt?** The assignment explicitly requires the system to "read and classify each document — figuring out what type it is, whether it's an official filing or an unofficial draft, and what corporate event it relates to." This prompt addresses requirement #2 directly.

---

## 2. Capital Change Extraction Prompt

**LLM:** OpenAI `gpt-4o-mini` (temperature=0)
**Output Parser:** `PydanticOutputParser(pydantic_object=CapitalChange)`

```text
SYSTEM MESSAGE:
You are an expert AI agent with 15+ years of investment banking experience,
specializing in analyzing Indian corporate filings (SH-7, PAS-3, MOA, Board Resolutions)
to extract 'Authorised Share Capital Change' data for Draft Red Herring Prospectuses (DRHPs).

RULES:
1. Be precise — every number must trace to a source document.
2. If a field CANNOT be confirmed from the provided documents, add it to 'confidence_flags'
   and write 'UNCONFIRMED' as its value.
3. Format the capital description in Indian numbering: Rs X,XX,XXX divided into N Equity
   Shares of Rs Y each (and N Preference Shares of Rs Y each, if applicable).
4. Do NOT hallucinate numbers.

HUMAN MESSAGE:
Below are the documents for a specific corporate event.

Documents:
{documents_content}

Extract the Authorised Share Capital change details.
{format_instructions}
```

**Why this prompt?** The core extraction prompt. It enforces:
- **Traceability** via `source_documents` field.
- **Honest AI** via `confidence_flags` — if something can't be confirmed, it's flagged rather than guessed.
- **Indian numbering** convention for DRHP compliance.

---

## 3. Output Parser: Why PydanticOutputParser?

We chose `PydanticOutputParser` over `StrOutputParser` or raw JSON parsing because:

1. **Automatic format injection:** It generates precise JSON formatting instructions and injects them into the prompt via `{format_instructions}`.
2. **Type safety:** The LLM output is parsed directly into a Pydantic model, catching schema violations at parse time.
3. **Deterministic structure:** Financial/legal tables demand zero ambiguity in output format. A string parser would require fragile regex/splitting logic.

---

## 4. Prompts Used During Development

**Dataset generation:**
> "Create a Python script that generates a dummy dataset of 4 SH-7 filings with 3 attachments each (Board Resolution, EGM/AGM Minutes, Notice), evolving share capital from Rs 1,00,000 to Rs 15,00,00,000 across 4 events."

**FastAPI pipeline:**
> "Build a FastAPI server with LangChain LCEL chains. Add a document classification step before extraction. Use PydanticOutputParser for structured output. Render results as a premium dark-mode HTML page with classification table and capital change table."
