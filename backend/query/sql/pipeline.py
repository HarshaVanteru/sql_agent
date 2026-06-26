"""SQL query pipeline (MySQL, PostgreSQL)."""
import os
from langgraph.graph import StateGraph, END
from backend.query.sql.agents.generation import generation_agent
from backend.query.sql.agents.validation import validation_agent
from backend.query.sql.agents.execution import execution_agent
from backend.query.sql.agents.formatting import formatting_agent

QUERY_RETRY_LIMIT = int(os.getenv("QUERY_RETRY_LIMIT", "2"))

def create_sql_pipeline():
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

sql_pipeline = create_sql_pipeline()

def run_sql_pipeline(question: str, history: list, engine=None, system_prompt: str = None, db_type: str = None, database_name: str = None) -> dict:
    state = {
        "question": question,
        "history": history,
        "sql": None,
        "valid": False,
        "error": None,
        "result": None,
        "response": None,
        "retry_count": 0,
        "engine": engine,
        "system_prompt": system_prompt,
        "db_type": db_type,
        "database_name": database_name,
    }
    return sql_pipeline.invoke(state)
