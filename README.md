# Offline LLM Security Lab

Fully offline evaluation of open-weight LLMs against prompt injection, running on my home server lab. No cloud services or external APIs.

## Lab
- Server: Intel Core i5-10, 8 GB RAM, NVIDIA RTX 3060 (12 GB VRAM)
- OS: Ubuntu 22.04
- Runtime: Ollama (Docker, GPU passthrough)
- Models tested: qwen2.5:7b, llama3.1:8b
## What it tests
A secret canary is placed in the system prompt. Each test case tries to extract it through a different attack class:
direct injection, role-play, system-prompt extraction, obfuscation (translation, base64, spacing), indirect injection through a retrieved document (RAG), and social engineering.

Every case runs twice: once with a **baseline** system prompt and once with a **hardened** one (instruction hierarchy + untrusted-document tagging), to measure how much prompt-level defense actually helps.

Leak detection catches plain, spaced-out and base64-encoded leaks.

## Run
```bash
docker compose up -d
docker exec ollama ollama pull qwen2.5:7b
docker exec ollama ollama pull llama3.1:8b
pip install -r requirements.txt
python run_eval.py --models qwen2.5:7b llama3.1:8b
```
Results go to `reports/` (Markdown summary + full JSON with every response).

## Findings
> **Status: pending a full run.** The lab server is offline for now, so no measured results are published yet.

[`reports/example-report.md`](reports/example-report.md) shows the report format with **illustrative, unmeasured** numbers. Once the eval runs, this section will cover:
- which model leaked the canary most often (baseline vs hardened)
- which attack class was most effective
- how much the hardened system prompt reduced leaks

## Next steps
- Output filtering layer (block canary/secret patterns before the response leaves the agent)
- More cases from OWASP Top 10 for LLM Applications (LLM01 Prompt Injection, LLM07 System Prompt Leakage)
- Compare quantization levels (Q4_K_M vs Q8_0) on robustness
