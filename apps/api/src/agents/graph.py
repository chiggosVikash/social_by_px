from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from .state import GraphState
from .nodes import (
    research_agent,
    verification_agent,
    query_refinement_agent,
    content_generation_agent,
    slide_verification_agent,
    publishing_agent,
    rag_retrieval_agent
)

def should_refine(state: GraphState) -> str:
    """Determine if we need to refine queries or proceed to content generation."""
    approved_articles = state.get("approved_articles", [])
    retries = state.get("retries", 0)
    
    if not approved_articles and retries < 3:
        return "refine"
    elif approved_articles:
        return "rag_retrieval"
    else:
        return "end"

def is_content_valid(state: GraphState) -> str:
    """Determine if slides are valid or need regeneration."""
    approved_slides = state.get("approved_slides", {})
    # If any slide sets were approved, we can publish (or send to human approval).
    if approved_slides:
        return "publish"
    return "regenerate"

def build_graph() -> CompiledStateGraph[GraphState, None, GraphState, GraphState]:  # type: ignore[type-var]
    workflow = StateGraph[GraphState](GraphState)  # type: ignore[type-var]
    
    workflow.add_node("research", research_agent)
    workflow.add_node("verify", verification_agent)
    workflow.add_node("refine", query_refinement_agent)
    workflow.add_node("rag_retrieval", rag_retrieval_agent)
    workflow.add_node("generate", content_generation_agent)
    workflow.add_node("verify_slides", slide_verification_agent)
    workflow.add_node("publish", publishing_agent)
    
    workflow.set_entry_point("research")
    
    workflow.add_edge("research", "verify")
    
    workflow.add_conditional_edges(
        "verify",
        should_refine,
        {
            "refine": "refine",
            "rag_retrieval": "rag_retrieval",
            "end": END
        }
    )
    
    workflow.add_edge("refine", "research")
    workflow.add_edge("rag_retrieval", "generate")
    workflow.add_edge("generate", "verify_slides")
    
    workflow.add_conditional_edges(
        "verify_slides",
        is_content_valid,
        {
            "publish": "publish", # In reality, we stop before publishing for human approval.
            "regenerate": "generate"
        }
    )
    
    workflow.add_edge("publish", END)
    
    return workflow.compile()

app_graph = build_graph()
