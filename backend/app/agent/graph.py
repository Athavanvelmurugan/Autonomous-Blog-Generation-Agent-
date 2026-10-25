import logging
from langgraph.graph import StateGraph, START, END
from backend.app.schema.state_schema import BlogState
from backend.app.agent.nodes import (
    plan_queries_node,
    collect_node,
    clean_dedupe_node,
    extract_facts_node,
    generate_title_node,
    generate_content_node,
    verify_content_node,
    translate_content_node,
)
from backend.app.agent.routers import (
    source_gate_router,
    verification_router,
    language_router,
)

logger = logging.getLogger(__name__)


def fail_node(state: BlogState) -> dict:
    """Terminal failure sink node when sources or verification criteria fail."""
    error = state.get("error")
    if not error:
        critique = state.get("critique")
        score = state.get("verification_score")
        if critique:
            error = f"Verification failed after max revisions (Score: {score}/10): {critique}"
        else:
            error = "Pipeline terminated: factual verification or minimum source requirements not met."
    logger.error(f"[Fail Node] Pipeline halted with error: {error}")
    return {"error": error, "current_step": "failed"}


# 1. Initialize StateGraph with the enhanced BlogState schema
workflow = StateGraph(BlogState)

# 2. Register Agent Worker Nodes
workflow.add_node("plan_queries", plan_queries_node)
workflow.add_node("collect", collect_node)
workflow.add_node("clean_dedupe", clean_dedupe_node)
workflow.add_node("extract_facts", extract_facts_node)
workflow.add_node("title_generator", generate_title_node)
workflow.add_node("content_generator", generate_content_node)
workflow.add_node("verifier_agent", verify_content_node)
workflow.add_node("translator", translate_content_node)
workflow.add_node("fail_node", fail_node)

# 3. Define Execution Flow
# START -> Plan Queries -> Collect (Search API + RSS + HN) -> Clean & Dedupe
workflow.add_edge(START, "plan_queries")
workflow.add_edge("plan_queries", "collect")
workflow.add_edge("collect", "clean_dedupe")

# Conditional Edge 1: Minimum-Sources Gatekeeper
workflow.add_conditional_edges(
    "clean_dedupe",
    source_gate_router,
    {
        "extract_facts": "extract_facts",
        "plan_queries": "plan_queries",
        "fail_insufficient_sources": "fail_node",
    },
)

# Conditional Edge 2: Fact Gatekeeper (Proceed to write if verified facts or research sources are present)
def fact_gate_router(state: BlogState) -> str:
    facts = state.get("facts") or []
    sources = state.get("deduped_sources") or state.get("sources") or []
    if len(facts) >= 1 or len(sources) >= 1:
        return "title_generator"
    if state.get("error"):
        return "fail"
    return "title_generator"

workflow.add_conditional_edges(
    "extract_facts",
    fact_gate_router,
    {
        "title_generator": "title_generator",
        "fail": "fail_node",
    },
)

workflow.add_edge("title_generator", "content_generator")
workflow.add_edge("content_generator", "verifier_agent")


# Conditional Edge 2: Verifier Quality & Review Fallback Loop
def post_verification_branch(state: BlogState) -> str:
    decision = verification_router(state)
    if decision == "revise":
        return "content_generator"
    if decision == "fail_verification":
        return "fail"
    
    # "passed" or "flag_review": check language translation
    lang_decision = language_router(state)
    if lang_decision == "translate":
        return "translator"
    return "end"


workflow.add_conditional_edges(
    "verifier_agent",
    post_verification_branch,
    {
        "content_generator": "content_generator",
        "translator": "translator",
        "fail": "fail_node",
        "end": END,
    },
)

# Terminal Edges
workflow.add_edge("translator", END)
workflow.add_edge("fail_node", END)

# 4. Compile the runnable Multi-Agent DAG
graph = workflow.compile()
