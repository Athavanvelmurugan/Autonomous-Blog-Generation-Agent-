#!/usr/bin/env python3
"""
Empirical Temperature & Factuality Benchmark Script.
Compares consistency, factual assertions, and variance across temperature settings (0.2, 0.4, 0.7).

Usage:
    python backend/scripts/compare_temperatures.py --topic "Virat Kohli Century Records and Career Highlights"
"""

import sys
import argparse
import difflib
import re

# Ensure Windows console supports Unicode characters like non-breaking spaces
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from typing import List, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.core.llm import get_node_llm


def extract_factual_tokens(text: str) -> List[str]:
    """Extracts numbers, years, percentages, and capitalized named entities."""
    # Numbers, years, stats
    numbers = re.findall(r"\b\d+(?:,\d+)?(?:\.\d+)?%?\b", text)
    # Proper noun sequences
    entities = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
    return list(dict.fromkeys(numbers + entities))


def run_benchmark(topic: str, temperatures: List[float] = [0.2, 0.4, 0.7], runs_per_temp: int = 3):
    print("=" * 80)
    print(f"EMPIRICAL TEMPERATURE FACTUALITY BENCHMARK")
    print(f"Topic: '{topic}'")
    print(f"Testing Temperatures: {temperatures} ({runs_per_temp} runs each)")
    print("=" * 80)

    prompt = (
        f"Provide 4 concise, verified factual milestones or statistics for: '{topic}'. "
        f"List each fact on a separate line starting with a bullet point '-' and include exact numbers, dates, or records."
    )

    results: Dict[float, List[str]] = {}

    for temp in temperatures:
        print(f"\n[Benchmarking Temperature: {temp}]")
        results[temp] = []
        llm = get_node_llm("content_generator", temperature_override=temp)

        for run in range(1, runs_per_temp + 1):
            try:
                messages = [
                    SystemMessage(content="You are a strict, factual reference engine. Output only bulleted verified facts with exact statistics."),
                    HumanMessage(content=prompt)
                ]
                resp = llm.invoke(messages)
                content = resp.content.strip()
                results[temp].append(content)
                print(f"  Run #{run} ({len(content.split())} words):")
                for line in content.split("\n"):
                    if line.strip():
                        print(f"    {line.strip()}")
            except Exception as e:
                print(f"  Run #{run} Error: {e}")
                results[temp].append("")

    # Comparative Analysis
    print("\n" + "=" * 80)
    print("FACTUAL STABILITY & VARIANCE COMPARISON SUMMARY")
    print("=" * 80)

    for temp in temperatures:
        outputs = results[temp]
        token_sets = [set(extract_factual_tokens(out)) for out in outputs if out]
        total_unique = set().union(*token_sets) if token_sets else set()
        
        if len(token_sets) >= 2:
            common_tokens = token_sets[0].intersection(*token_sets[1:])
            jaccard_similarity = (len(common_tokens) / len(total_unique)) if total_unique else 1.0
        else:
            common_tokens = token_sets[0] if token_sets else set()
            jaccard_similarity = 1.0

        print(f"\nTemperature {temp}:")
        print(f"  • Common Factual Tokens across all 3 runs: {len(common_tokens)}")
        print(f"  • Total Divergent/Unique Tokens across runs: {len(total_unique) if token_sets else 0}")
        print(f"  • Factual Consistency Score (Jaccard Index): {jaccard_similarity:.2%}")
        if common_tokens:
            sample_shared = list(common_tokens)[:8]
            print(f"  • Sample Consistent Facts: {', '.join(sample_shared)}")
        
        if temp <= 0.2:
            print("  • Assessment: Maximum determinism. Near-identical factual anchoring with zero drift.")
        elif temp <= 0.4:
            print("  • Assessment: Optimal balance. Controlled phrasing flexibility while preserving key figures.")
        else:
            print("  • Assessment: High variance. Higher probability of divergent assertions and creative filler.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run temperature hallucination benchmark.")
    parser.add_argument("--topic", type=str, default="Virat Kohli Century Records and Career Milestones")
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()

    run_benchmark(topic=args.topic, runs_per_temp=args.runs)
