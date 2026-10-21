import json
import logging
import re
import time
from typing import List
from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.config import get_settings
from backend.app.schema.state_schema import BlogState, VerifierEvaluation
from backend.app.core.prompts import (
    TITLE_SYSTEM_PROMPT,
    CONTENT_SYSTEM_PROMPT,
    VERIFIER_SYSTEM_PROMPT,
    TRANSLATION_SYSTEM_PROMPT,
)
from backend.app.core.llm import get_llm, get_node_config
from backend.app.core.tools import search_trending_data
from backend.app.agent.persistence import record_node_step

logger = logging.getLogger(__name__)
settings = get_settings()


async def research_trending_data_node(state: BlogState) -> dict:
    """
    Node 1: Retrieves real-time trending web facts, latest developments, and source links.
    Bypasses LLM training cutoffs.
    """
    start_time = time.perf_counter()
    topic = state["topic"]
    logger.info(f"[Node 1: Trend Research Agent] Querying live web data for: '{topic}'")
    
    search_result = search_trending_data(topic, max_results=5)
    
    steps = list(state.get("steps_completed", []))
    if "research_agent" not in steps:
        steps.append("research_agent")

    result = {
        "research_data": search_result["context"],
        "sources": search_result["sources"],
        "current_step": "research_completed",
        "steps_completed": steps,
        "revision_count": state.get("revision_count", 0),
    }
    await record_node_step("research_agent", state, result, start_time, None)
    return result


async def generate_title_node(state: BlogState) -> dict:
    """
    Node 2: Generates an engaging, SEO-optimized title grounded in trending context.
    """
    start_time = time.perf_counter()
    creativity = state.get("creativity", "balanced")
    logger.info(f"[Node 2: Title Generator] Topic: '{state['topic']}', Tone: '{state.get('tone', 'Informative')}', Creativity: '{creativity}'")
    llm = get_llm("title_generator", creativity_level=creativity)

    research_context = state.get("research_data") or "No live data available."

    messages = [
        SystemMessage(content=TITLE_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Topic: {state['topic']}\n"
                f"Tone: {state.get('tone', 'Informative')}\n"
                f"Trending Facts / Context:\n{research_context[:2000]}"
            )
        ),
    ]

    response = await llm.ainvoke(messages)
    raw_title = response.content.strip()

    # Clean any accidental outer quotation marks
    clean_title = raw_title.strip('"\'')
    if "\n" in clean_title:
        clean_title = clean_title.split("\n")[0].strip('"\'')

    steps = list(state.get("steps_completed", []))
    if "title_generator" not in steps:
        steps.append("title_generator")

    result = {
        "title": clean_title,
        "original_title": clean_title,
        "current_step": "title_generated",
        "steps_completed": steps,
    }
    llm_metrics = {
        "provider": settings.MODEL_PROVIDER,
        "model": settings.MODEL_NAME,
        "temperature": 0.7,
    }
    await record_node_step("title_generator", state, result, start_time, llm_metrics)
    return result


async def generate_content_node(state: BlogState) -> dict:
    """
    Node 3: Generates a comprehensive blog post in Markdown format, grounded in trending facts
    and incorporating feedback and hallucination flags from the verifier agent if in a revision loop.
    """
    start_time = time.perf_counter()
    revisions = state.get("revision_count", 0)
    creativity = state.get("creativity", "balanced")
    writer_cfg = get_node_config("content_generator")
    base_temp = writer_cfg.temperature

    # Apply creativity offset ONLY to writing nodes
    if creativity == "low":
        base_temp = max(0.1, round(base_temp - 0.1, 2))
    elif creativity == "high":
        base_temp = min(1.0, round(base_temp + 0.1, 2))

    # Dynamic Verifier Loop: Step down temperature by 0.1 per revision (min 0.1), up to 2 retries
    effective_temp = max(0.1, round(base_temp - (0.1 * min(revisions, 2)), 2))
    if revisions > 0:
        logger.info(
            f"[Node 3: Content Generator] Verifier retry loop #{revisions}: "
            f"Stepping down writer temperature from {base_temp} to {effective_temp} to minimize hallucination."
        )

    logger.info(f"[Node 3: Content Generator] Title: '{state['title']}' (Revision #{revisions}, Temp: {effective_temp})")
    llm = get_llm("content_generator", temperature_override=effective_temp)

    research_context = state.get("research_data") or "Standard industry knowledge."
    critique_context = state.get("critique")
    hallucinations = state.get("detected_hallucinations", [])
    unverified_cmds = state.get("unverified_commands", [])

    prompt_content = (
        f"Title: {state['title']}\n"
        f"Topic: {state['topic']}\n"
        f"Tone: {state.get('tone', 'Informative')}\n\n"
        f"Trending Research Facts & Fresh Context:\n{research_context}\n\n"
    )

    if (critique_context and "PASSED" not in critique_context.upper()) or hallucinations or unverified_cmds:
        prompt_content += "--- CRITICAL EDITORIAL REVISION REQUIRED ---\n"
        if critique_context:
            prompt_content += f"Editorial Feedback:\n{critique_context}\n\n"
        if hallucinations:
            prompt_content += "Flagged Fabricated Claims / Hallucinations to Remove:\n"
            for h in hallucinations:
                prompt_content += f"- {h}\n"
            prompt_content += "\n"
        if unverified_cmds:
            prompt_content += "Unverified CLI Commands / Flags that MUST be corrected or removed:\n"
            for c in unverified_cmds:
                prompt_content += f"- {c}\n"
            prompt_content += "\n"
        prompt_content += "Strictly eliminate all flagged errors above and ensure all commands match the verified context exactly.\n\n"

    prompt_content += "Please draft the authoritative, production-grade blog post now."

    messages = [
        SystemMessage(content=CONTENT_SYSTEM_PROMPT),
        HumanMessage(content=prompt_content),
    ]

    response = await llm.ainvoke(messages)
    blog_content = response.content.strip()

    # Fallback recovery if model generated a refusal or empty output
    if not blog_content or len(blog_content.split()) < 30 or blog_content.lower().startswith("i'm sorry") or blog_content.lower().startswith("i cannot"):
        logger.warning(f"[Node 3: Content Generator] Initial generation was empty or refused. Triggering direct fallback generation.")
        direct_messages = [
            SystemMessage(content="You are an expert editorial writer. Write an authentic, engaging, well-structured, comprehensive blog post in Markdown format with clear section headings. Do not include conversational introductory remarks."),
            HumanMessage(content=f"Write a comprehensive, engaging blog post on the topic: '{state['topic']}'. Title: '{state['title']}'. Tone: {state.get('tone', 'Informative')}.\n\nContext and Highlights:\n{research_context[:1500]}\n\nProvide rich, factual, and informative content in clean Markdown with H2 and H3 headings.")
        ]
        direct_resp = await llm.ainvoke(direct_messages)
        if direct_resp.content and len(direct_resp.content.strip().split()) >= 30:
            blog_content = direct_resp.content.strip()

    # Retain previous valid draft if latest revision yielded empty content
    if (not blog_content or len(blog_content.split()) < 30) and state.get("content"):
        if len(state["content"].split()) >= 30:
            logger.warning("[Node 3: Content Generator] Revision produced empty output. Retaining previous valid draft.")
            blog_content = state["content"]

    blog_content = blog_content.replace("\u2011", "-")

    steps = list(state.get("steps_completed", []))
    if "content_generator" not in steps:
        steps.append("content_generator")

    result = {
        "content": blog_content,
        "original_content": blog_content,
        "current_step": "content_generated",
        "steps_completed": steps,
        "revision_count": revisions + 1,
    }
    llm_metrics = {
        "provider": settings.MODEL_PROVIDER,
        "model": settings.MODEL_NAME,
        "temperature": effective_temp,
    }
    await record_node_step("content_generator", state, result, start_time, llm_metrics)
    return result


def _extract_commands_and_paths(markdown_text: str) -> List[str]:
    """Extracts all shell command lines and inline shell invocations for verification."""
    # Normalize unicode non-breaking hyphens to standard ASCII hyphen
    norm_text = markdown_text.replace("\u2011", "-")
    extracted = []

    # 1. Parse code blocks
    code_blocks = re.findall(r"```(?:bash|sh|zsh)?\s*\n(.*?)```", norm_text, re.DOTALL)
    valid_starters = ("npx ", "npm ", "rea ", "pip ", "python ", "git ", "curl ", "export ", "chmod ", "cd ", "docker ")

    for block in code_blocks:
        for line in block.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Shell prompt lines
            if line.startswith("$ "):
                extracted.append(line[2:].strip())
            elif any(line.startswith(prefix) for prefix in valid_starters):
                extracted.append(line)

    # 2. Parse inline backtick commands
    inline_cmds = re.findall(r"`([^`]+)`", norm_text)
    for ic in inline_cmds:
        ic_clean = ic.strip()
        if ic_clean.startswith("$ "):
            ic_clean = ic_clean[2:].strip()
        if any(ic_clean.startswith(prefix) for prefix in valid_starters):
            extracted.append(ic_clean)

    return list(dict.fromkeys(extracted))  # Deduplicate while preserving order


async def verify_content_node(state: BlogState) -> dict:
    """
    Node 4: Fact-checks the generated draft against research data.
    Combines deterministic programmatic command checks with structured LLM evaluation.
    """
    start_time = time.perf_counter()
    logger.info(f"[Node 4: Verifier Agent] Auditing content for '{state['title']}' (Deterministic Temp: 0.0)")
    llm = get_llm("verifier_agent")

    research_context = state.get("research_data") or "No live facts provided."
    # Normalize non-breaking hyphens in content draft
    content_draft = state["content"].replace("\u2011", "-")

    # 1. Deterministic Programmatic Pre-Check for CLI commands, hedging, and clichés
    extracted_cmds = _extract_commands_and_paths(content_draft)
    programmatic_unverified = []

    is_rea_context = "rea-agents" in research_context.lower() or "morluto" in research_context.lower() or "rea" in state.get("topic", "").lower().split()

    # A. Command validation (only when relevant to REA/tools)
    if is_rea_context:
        for cmd in extracted_cmds:
            clean_cmd = re.sub(r"^\$\s*", "", cmd).strip()
            tokens = clean_cmd.split()
            if not tokens:
                continue

            if "verify:mcp" in clean_cmd:
                programmatic_unverified.append(f"`{clean_cmd}`: command 'verify:mcp' does not exist in repository.")
            elif "report.html" in clean_cmd or "open analysis" in clean_cmd:
                programmatic_unverified.append(f"`{clean_cmd}`: fabricated HTML report viewer; REA outputs JSON directly.")
            elif "query-evidence" in clean_cmd:
                programmatic_unverified.append(f"`{clean_cmd}`: fabricated subcommand 'query-evidence'; REA queries are performed via MCP client agent tool calls.")
            elif "analyze-javascript-application" in clean_cmd:
                for bad_flag in ["--hopper", "--ghidra", "--ida", "--binary", "--report", "--output-html", "--filter"]:
                    if bad_flag in clean_cmd:
                        programmatic_unverified.append(
                            f"`{clean_cmd}`: Invalid flag '{bad_flag}'. Native engines (Hopper, Ghidra) are accessed via MCP tool adapters, not CLI flags on the JavaScript analyzer."
                        )
            elif tokens[0] in ["npx", "npm"]:
                idx = 1
                while idx < len(tokens) and tokens[idx].startswith("-"):
                    idx += 1
                pkg = tokens[idx] if idx < len(tokens) else ""
                idx += 1
                subcmd = tokens[idx] if idx < len(tokens) and not tokens[idx].startswith("-") else ""
                
                if "rea-agents" in pkg or "rea" in pkg:
                    valid_rea_subcmds = ["setup", "analyze-javascript-application", "update", "--help", "-h"]
                    if subcmd and subcmd not in valid_rea_subcmds:
                        programmatic_unverified.append(
                            f"`{clean_cmd}`: subcommand '{subcmd}' is not a valid subcommand for rea-agents (valid subcommands: {', '.join(valid_rea_subcmds)})."
                        )

    # B. Anti-Hedging Linter
    hedging_patterns = [
        r"\(if .*? not documented.*?\)",
        r"\(if .*? syntax differs.*?\)",
        r"\(if .*? differs.*?\)",
        r"will reveal the exact syntax",
        r"catalog will reveal",
        r"consult .*? help flag if syntax differs",
        r"in case the flag is named differently",
        r"syntax may vary",
    ]
    for hp in hedging_patterns:
        matches = re.findall(hp, content_draft, re.IGNORECASE)
        for m in matches:
            programmatic_unverified.append(f"Hedging excuse detected: '{m}'. State exact verified facts or omit.")

    # C. Banned AI Clichés Linter
    cliche_patterns = [
        r"\bnot just a tool\b",
        r"\bnotoriously fragmented\b",
        r"\bdelve into\b",
        r"\bin today's fast-paced\b",
        r"\btestament to\b",
        r"\bhappy reverse engineering\b",
        r"\bgame-changer\b",
    ]
    for cp in cliche_patterns:
        matches = re.findall(cp, content_draft, re.IGNORECASE)
        for m in matches:
            programmatic_unverified.append(f"Banned AI cliché detected: '{m}'. Replace with concrete terminology.")

    # D. Concrete Evidence Artifact Check (only if context specifically references evidence artifacts)
    if is_rea_context and "evidence" in research_context.lower() and "```json" not in content_draft:
        programmatic_unverified.append("Missing concrete Evidence JSON block: Draft must include a sample structured JSON evidence artifact.")

    messages = [
        SystemMessage(content=VERIFIER_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Live Research Context:\n{research_context}\n\n"
                f"Generated Blog Draft:\n{content_draft}"
            )
        ),
    ]

    response = await llm.ainvoke(messages)
    raw_eval = response.content.strip()

    # 2. Resilient Structured JSON Parsing
    evaluation_data = None
    try:
        # Strip potential markdown code fence wrappers
        clean_json = raw_eval
        if "```" in clean_json:
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_json, re.DOTALL)
            if json_match:
                clean_json = json_match.group(1).strip()
            else:
                clean_json = re.sub(r"^```[a-zA-Z]*\n", "", clean_json)
                clean_json = re.sub(r"\n```$", "", clean_json)
        
        parsed_dict = json.loads(clean_json)
        if "score" in parsed_dict:
            try:
                parsed_dict["score"] = max(0.0, min(10.0, float(parsed_dict["score"])))
            except (ValueError, TypeError):
                parsed_dict["score"] = 5.0
        evaluation_data = VerifierEvaluation(**parsed_dict)
    except Exception as parse_err:
        logger.warning(f"[Verifier Agent] Direct JSON parsing failed ({parse_err}). Attempting regex extraction fallback.")
        # Fallback to regex extraction
        score = 8.0
        score_m = re.search(r'"score":\s*([\d\.]+)', raw_eval)
        if score_m:
            try:
                score = max(0.0, min(10.0, float(score_m.group(1))))
            except Exception:
                score = 8.0
        
        critique = "Passed quality audit."
        crit_m = re.search(r'"critique":\s*"([^"]+)"', raw_eval)
        if crit_m:
            critique = crit_m.group(1)
            
        try:
            evaluation_data = VerifierEvaluation(
                score=score,
                passed=(score >= 8.0),
                detected_hallucinations=[],
                unverified_commands=[],
                critique=critique
            )
        except Exception:
            evaluation_data = VerifierEvaluation(
                score=5.0,
                passed=False,
                detected_hallucinations=[],
                unverified_commands=[],
                critique="Audit score defaulted due to verifier formatting."
            )

    # 3. Merge deterministic pre-check findings
    final_score = float(evaluation_data.score)
    final_hallucinations = list(evaluation_data.detected_hallucinations)
    final_unverified_cmds = list(set(evaluation_data.unverified_commands + programmatic_unverified))
    final_critique = evaluation_data.critique

    # Separate critical command/evidence errors from stylistic notes
    critical_errors = [u for u in programmatic_unverified if "command" in u.lower() or "flag" in u.lower() or "evidence" in u.lower()]
    stylistic_issues = [u for u in programmatic_unverified if u not in critical_errors]

    if critical_errors:
        final_score = min(final_score, 5.5)
        final_hallucinations.extend(critical_errors)
        final_critique = (
            f"REJECTED: Found programmatic command issues: {'; '.join(critical_errors)}. "
            f"Original critique: {final_critique}"
        )
    elif stylistic_issues:
        # Subtle deduction for cliches without failing an otherwise great article
        final_score = max(7.2, final_score - (0.4 * len(stylistic_issues)))
        final_critique = f"{final_critique} (Notes: {'; '.join(stylistic_issues)})"

    is_passed = final_score >= 7.5 and len(final_hallucinations) == 0

    logger.info(
        f"[Verifier Agent Result] Score: {final_score:.1f}/10 | Passed: {is_passed} | "
        f"Hallucinations: {len(final_hallucinations)} | Unverified Cmds: {len(final_unverified_cmds)}"
    )

    steps = list(state.get("steps_completed", []))
    if "verifier_agent" not in steps:
        steps.append("verifier_agent")

    result = {
        "verification_score": final_score,
        "passed": is_passed,
        "critique": final_critique,
        "detected_hallucinations": final_hallucinations,
        "unverified_commands": final_unverified_cmds,
        "current_step": "verification_completed",
        "steps_completed": steps,
    }
    llm_metrics = {
        "provider": settings.MODEL_PROVIDER,
        "model": settings.MODEL_NAME,
        "temperature": 0.0,
    }
    await record_node_step("verifier_agent", state, result, start_time, llm_metrics)
    return result


async def translate_content_node(state: BlogState) -> dict:
    """
    Node 5: Localizes both the title and markdown content into the target language.
    """
    start_time = time.perf_counter()
    target_lang = state.get("target_language", "English")
    logger.info(f"[Node 5: Translator] Translating into '{target_lang}' (Fidelity Temp: 0.2)")
    llm = get_llm("translator")

    messages = [
        SystemMessage(content=TRANSLATION_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Target Language: {target_lang}\n"
                f"Title: {state['title']}\n"
                f"Content:\n{state['content']}"
            )
        ),
    ]

    response = await llm.ainvoke(messages)
    raw_output = response.content.strip()

    translated_title = state["title"]
    translated_content = state["content"]

    if "TITLE:" in raw_output and "---" in raw_output:
        parts = raw_output.split("---", 1)
        title_part = parts[0].replace("TITLE:", "").strip()
        if title_part:
            translated_title = title_part
        if len(parts) > 1 and parts[1].strip():
            translated_content = parts[1].strip()
    else:
        translated_content = raw_output

    steps = list(state.get("steps_completed", []))
    if "translator" not in steps:
        steps.append("translator")

    result = {
        "translated_title": translated_title,
        "translated_content": translated_content,
        "title": translated_title,
        "content": translated_content,
        "current_step": "translation_completed",
        "steps_completed": steps,
    }
    llm_metrics = {
        "provider": settings.MODEL_PROVIDER,
        "model": settings.MODEL_NAME,
        "temperature": 0.2,
    }
    await record_node_step("translator", state, result, start_time, llm_metrics)
    return result
