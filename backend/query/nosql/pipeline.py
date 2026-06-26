"""MongoDB query pipeline."""
import os
import logging
from langgraph.graph import StateGraph, END
from backend.query.nosql.agents.generation import generation_agent
from backend.query.nosql.agents.validation import validation_agent
from backend.query.nosql.agents.execution import execution_agent
from backend.query.nosql.agents.formatting import formatting_agent

logger = logging.getLogger(__name__)
QUERY_RETRY_LIMIT = int(os.getenv("QUERY_RETRY_LIMIT", "2"))

def create_nosql_pipeline():
    graph = StateGraph(dict)

    graph.add_node("generation", generation_agent)
    graph.add_node("validation", validation_agent)
    graph.add_node("execution", execution_agent)
    graph.add_node("formatting", formatting_agent)

    graph.set_entry_point("generation")
    graph.add_edge("generation", "validation")

    graph.add_conditional_edges("validation", lambda state: (
        "execution" if state["valid"]
        else "generation" if state["retry_count"] < QUERY_RETRY_LIMIT
        else END
    ))

    graph.add_edge("execution", "formatting")
    graph.add_edge("formatting", END)

    return graph.compile()

nosql_pipeline = create_nosql_pipeline()

def run_nosql_pipeline(
    question: str,
    client,
    database_name: str,
    history: list = None,
    system_prompt: str = None,
) -> dict:
    """Run MongoDB query pipeline."""
    if history is None:
        history = []

    logger.info(f"[PIPELINE START] Question: {question[:100]}")
    logger.info(f"[PIPELINE] Client: {type(client).__name__}, DB: {database_name}")

    state = {
        "question": question,
        "history": history,
        "client": client,
        "database_name": database_name,
        "query": None,
        "query_type": None,
        "valid": False,
        "error": None,
        "result": None,
        "response": None,
        "retry_count": 0,
        "system_prompt": system_prompt,
    }

    result = nosql_pipeline.invoke(state)

    logger.info(f"[PIPELINE END] Valid: {result.get('valid')}, Query: {result.get('query', '')[:100] if result.get('query') else 'None'}")
    logger.info(f"[PIPELINE END] Error: {result.get('error')}")
    logger.info(f"[PIPELINE END] Retry Count: {result.get('retry_count')}")

    return result
