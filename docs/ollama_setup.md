# Ollama Setup

SiteSage AI can run with Ollama for fully local LLM inference. This keeps procurement prompts and uploaded document context on the demo machine.

## Prerequisites

- Ollama installed on Windows
- A local model pulled, such as `qwen2.5:7b`
- Streamlit app dependencies installed in the project virtual environment

## Setup Steps

1. Open a terminal on the demo machine.
2. Start the Ollama service:

```powershell
ollama serve
```

3. Pull the recommended model:

```powershell
ollama pull qwen2.5:7b
```

4. Set the environment variables for SiteSage:

```powershell
$env:OLLAMA_MODEL="qwen2.5:7b"
$env:SITESAGE_USE_OLLAMA="1"
```

5. Start the app:

```powershell
..\.venv\Scripts\python.exe -m streamlit run app.py
```

## What To Say In The Demo

- “The app runs local inference through Ollama, so sensitive procurement data stays on the laptop.”
- “If Ollama is unavailable, the system falls back to cited document extraction so the demo still works.”
- “The answer is grounded in retrieved procurement chunks, not generic chatbot memory.”

## Verification

If Ollama is running correctly, the AI Agent page should answer questions from uploaded documents and cite the source chunk labels, for example `[sample_purchase_order.txt#c0]`.
