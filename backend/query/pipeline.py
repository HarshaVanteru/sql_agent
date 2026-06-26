from langgraph.graph import StateGraph, END
from backend.query.agents.generation import generation_agent
from backend.query.agents.validation import validation_agent
from backend.query.agents.execution import execution_agent
from backend.query.agents.formatting import formatting_agent

def create_pipeline():
    graph = StateGraph(dict)

    graph.add_node("generation", generation_agent)
    graph.add_node("validation", validation_agent)
    graph.add_node("execution", execution_agent)
    graph.add_node("formatting", formatting_agent)

    graph.set_entry_point("generation")
    graph.add_edge("generation", "validation")

    graph.add_conditional_edges("validation", lambda state: (
        "execution" if state["valid"]
        else "generation" if state["retry_count"] < 2
        else END
    ))

    graph.add_edge("execution", "formatting")
    graph.add_edge("formatting", END)

    return graph.compile()

pipeline = create_pipeline()

def run_pipeline(question: str, history: list, engine=None) -> dict:
    state = {
        "question": question,
        "history": history,
        "sql": None,
        "valid": False,
        "error": None,
        "result": None,
        "response": None,
        "retry_count": 0,
        "engine": engine
    }
    return pipeline.invoke(state)
