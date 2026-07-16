"""The agent loop: give the model tools and let it work until it has an answer."""
import logging
import os

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq

import backend.config  # noqa: F401  -- loads backend/.env before GROQ_API_KEY is read
from backend.query.agent.prompts import get_agent_prompt
from backend.query.agent.tools import build_tools

logger = logging.getLogger(__name__)

# Hard bound on tool-calling rounds. Without it a model that keeps calling tools
# never returns, and every round is an LLM call the user waits on.
MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "8"))

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

_EMPTY_RESULT = {"columns": [], "rows": []}


def _text_of(response) -> str:
    """Pull plain text out of a model response, which may be blocks or a string."""
    content = response.content
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content if isinstance(b, dict)]
        return "\n".join(p for p in parts if p).strip()
    return ""


def _failure(error: str) -> dict:
    return {"valid": False, "error": error, "query": None, "result": None, "message": None}


def run_agent(
    question: str,
    history: list,
    engine,
    db_type: str | None = None,
    database_name: str | None = None,
) -> dict:
    """Answer `question` against `engine`, returning the last query the agent ran.

    Returns valid / query / result / error / message. `query` and `result` are
    None when the agent answered without needing data (a greeting or a refusal);
    `message` carries its reply in that case.
    """
    if engine is None:
        return _failure("Database connection not provided")

    tools, recorder = build_tools(engine)
    model = llm.bind_tools(tools)
    tools_by_name = {t.name: t for t in tools}

    messages = [
        SystemMessage(content=get_agent_prompt(db_type, database_name)),
        *history,
        HumanMessage(content=question),
    ]

    iterations = 0
    stopped_early = False
    final_text = ""

    for iterations in range(1, MAX_ITERATIONS + 1):
        response = model.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            final_text = _text_of(response)
            break

        for call in response.tool_calls:
            tool = tools_by_name.get(call["name"])
            if tool is None:
                output = f"Unknown tool: {call['name']}"
            else:
                try:
                    output = tool.invoke(call["args"])
                except Exception as e:
                    # Tools catch their own errors; this is a bad-arguments case,
                    # which the model can correct on the next round.
                    logger.warning(f"Tool {call['name']} raised: {e}")
                    output = f"Error: {e}"

            messages.append(ToolMessage(content=str(output), tool_call_id=call["id"]))
    else:
        stopped_early = True
        logger.warning(f"Agent hit the {MAX_ITERATIONS}-iteration cap")

    if not recorder.has_result:
        # No data, but the agent did reply: a greeting, a refusal, or a request
        # to clarify. That is a real answer, not a failure.
        if final_text:
            logger.info(f"Agent answered without a query: {final_text[:120]}")
            return {
                "valid": True,
                "error": None,
                "query": None,
                "result": _EMPTY_RESULT,
                "message": final_text,
            }

        error = (
            f"The agent stopped after {MAX_ITERATIONS} steps without an answer."
            if stopped_early
            else "The agent produced no answer for this question."
        )
        logger.error(f"Agent produced no result: {error}")
        return _failure(error)

    logger.info(f"Agent finished in {iterations} iteration(s): {recorder.query[:200]}")
    return {
        "valid": True,
        "error": None,
        "query": recorder.query,
        "result": {"columns": recorder.columns, "rows": recorder.rows},
        "message": final_text or None,
    }
