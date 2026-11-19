#!/usr/bin/env python3
"""Offline prompt-injection evaluation for local LLMs served by Ollama."""
import argparse, datetime, json, pathlib, sys
import requests, yaml
from output_filter import filter_output, find_secret

def chat(host, model, system, prompt, timeout):
    r = requests.post(f"{host}/api/chat", json={
        "model": model, "stream": False, "options": {"temperature": 0},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
    }, timeout=timeout)
    r.raise_for_status()
    return r.json()["message"]["content"]

def leaked(canary, text):
    return find_secret(canary, text)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--tests", default="tests/prompt_injection.yaml")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--filter", action="store_true",
                    help="also score each response after the output filter")
    a = ap.parse_args()

    spec = yaml.safe_load(open(a.tests, encoding="utf-8"))
    canary = spec["canary"]
    rows = []
    for model in a.models:
        for mode, tmpl in spec["system_prompts"].items():
            system = tmpl.format(canary=canary)
            for c in spec["cases"]:
                try:
                    out = chat(a.host, model, system, c["prompt"], a.timeout)
                except Exception as e:
                    out = f"<error: {e}>"
                hit = leaked(canary, out)
                rows.append({"model": model, "mode": mode, "id": c["id"], "category": c["category"],
                             "leaked": bool(hit), "leak_type": hit, "response": out})
                print(f"[{model}][{mode}] {c['id']:<16} {'LEAK ('+hit+')' if hit else 'held'}", flush=True)
                if a.filter:
                    safe, blocked = filter_output(out, [canary])
                    fhit = leaked(canary, safe)
                    rows.append({"model": model, "mode": f"{mode}+filter", "id": c["id"],
                                 "category": c["category"], "leaked": bool(fhit), "leak_type": fhit,
                                 "blocked": blocked, "response": safe})

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = pathlib.Path("reports"); out_dir.mkdir(exist_ok=True)
    (out_dir / f"results-{ts}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [f"# Prompt-injection evaluation — {ts}", "", f"Canary: `{canary}` · Cases: {len(spec['cases'])}", ""]
    modes = list(spec["system_prompts"])
    if a.filter:
        modes += [f"{m}+filter" for m in spec["system_prompts"]]
    for model in a.models:
        md.append(f"## {model}")
        for mode in modes:
            sub = [r for r in rows if r["model"] == model and r["mode"] == mode]
            n = sum(r["leaked"] for r in sub)
            md.append(f"- **{mode}**: {n}/{len(sub)} leaked ({100*n//max(len(sub),1)}%)")
        md.append("")
        md.append("| Case | Category | " + " | ".join(m.capitalize() for m in modes) + " |")
        md.append("|---|---|" + "---|" * len(modes))
        for c in spec["cases"]:
            cell = lambda m: next(("❌ leak" if r["leaked"] else "✅ held") for r in rows
                                  if r["model"] == model and r["mode"] == m and r["id"] == c["id"])
            md.append(f"| {c['id']} | {c['category']} | " + " | ".join(cell(m) for m in modes) + " |")
        md.append("")
    (out_dir / f"report-{ts}.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nReport: reports/report-{ts}.md")

if __name__ == "__main__":
    sys.exit(main())
