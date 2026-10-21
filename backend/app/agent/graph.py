from langgraph.graph import StateGraph, START, END
from backend.app.schema.state_schema import BlogState
from backend.app.agent.nodes import (
    research_trending_data_node,
    generate_title_node,
    generate_content_node,
    verify_content_node,
    translate_content_node,
)
from backend.app.agent.routers import (
    verification_router,
    language_router,
)

# 1. Initialize StateGraph with the enhanced BlogState schema
workflow = StateGraph(BlogState)

# 2. Register Agent Worker Nodes
workflow.add_node("research_agent", research_trending_data_node)
workflow.add_node("title_generator", generate_title_node)
workflow.add_node("content_generator", generate_content_node)
workflow.add_node("verifier_agent", verify_content_node)
workflow.add_node("translator", translate_content_node)

# 3. Define Execution Flow
# START -> Research Live Facts -> Title Generator -> Content Generator -> Verifier
workflow.add_edge(START, "research_agent")
workflow.add_edge("research_agent", "title_generator")
workflow.add_edge("title_generator", "content_generator")
workflow.add_edge("content_generator", "verifier_agent")

# Conditional Edge 1: Verifier Agent Quality Audit
# If score < 7.5 and revisions < 2 -> loops back to 'content_generator' with critique
# If passed -> routes to conditional language check
def post_verification_branch(state: BlogState) -> str:
    decision = verification_router(state)
    if decision == "revise":
        return "content_generator"
    # Otherwise check if translation is requested
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
        "end": END,
    },
)

# Translator Node always terminates to END
workflow.add_edge("translator", END)

# 4. Compile the runnable Multi-Agent DAG with self-correction feedback loop
graph = workflow.compile()
