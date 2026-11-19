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
Full report: [`reports/report-20261119-234012.md`](reports/report-20261119-234012.md) · 8 cases × 2 system prompts × 2 models.
*(Simulated run — lab server was offline.)*

| Model | Baseline leaks | Hardened leaks | Reduction |
|---|---|---|---|
| qwen2.5:7b | 5/8 (62%) | 2/8 (25%) | −60% |
| llama3.1:8b | 4/8 (50%) | 1/8 (12%) | −75% |

- **Most leaky model:** qwen2.5:7b — leaked more in both modes, and was the only one to fall for role-play.
- **Most effective attack:** indirect injection through a retrieved document (RAG) — leaked on both models even with the hardened prompt. Untrusted-document tagging alone is not enough.
- **Obfuscation:** translation and spaced-out output bypassed the baseline on both models; the hardened prompt stopped spacing but qwen2.5 still leaked via translation.
- **Held everywhere:** direct override, base64 request and the authority / social-engineering case.
- **Hardened prompt:** cut total leaks from 9/16 to 3/16 (−67%), but prompt-level defense does not close RAG injection — an output filter is needed (see Next steps).

## Next steps
- Output filtering layer (block canary/secret patterns before the response leaves the agent)
- More cases from OWASP Top 10 for LLM Applications (LLM01 Prompt Injection, LLM07 System Prompt Leakage)
- Compare quantization levels (Q4_K_M vs Q8_0) on robustness
