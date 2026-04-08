import asyncio
import logging
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from agent.browser import BrowserController
from agent.vision import analyze_screen

logger = logging.getLogger(__name__)


# --- State ---

class AgentState(TypedDict):
    task: str
    start_url: str
    screenshot: bytes
    action_history: list[dict]
    observation: str
    decision: dict
    result: str | None
    steps: int
    max_steps: int
    done: bool
    error: str | None


# --- Nodes ---

async def observe(state: AgentState, config: RunnableConfig) -> AgentState:
    """Take a screenshot and analyze it with GPT-4o."""
    browser: BrowserController = config["configurable"]["browser"]
    logger.debug("Step %d — taking screenshot", state["steps"])
    screenshot = await browser.screenshot(f"step_{state['steps']}")
    decision = analyze_screen(
        screenshot_bytes=screenshot,
        task=state["task"],
        action_history=state["action_history"],
    )
    logger.info(
        "Step %d observe — action=%s | observation: %s",
        state["steps"], decision["action"], decision["observation"][:120],
    )
    return {
        **state,
        "screenshot": screenshot,
        "observation": decision["observation"],
        "decision": decision,
    }


async def act(state: AgentState, config: RunnableConfig) -> AgentState:
    """Execute the action decided by the vision layer."""
    browser: BrowserController = config["configurable"]["browser"]
    decision = state["decision"]
    action = decision["action"]
    params = decision["params"]

    error = None
    result = None

    logger.info("Step %d act — action=%s params=%s", state["steps"], action, params)
    try:
        if action == "click":
            await browser.click(params["x"], params["y"])

        elif action == "type":
            await browser.type_text(params["text"])

        elif action == "fill":
            await browser.fill(params["selector"], params["text"])

        elif action == "scroll":
            await browser.scroll(params.get("direction", "down"))

        elif action == "press":
            await browser.press(params["key"])

        elif action == "navigate":
            await browser.navigate(params["url"])

        elif action in ("extract", "done"):
            result = params.get("result", "")
            logger.info("Step %d — task complete. Result: %s", state["steps"], result[:200])

    except Exception as e:
        error = str(e)
        logger.error("Step %d — action %s failed: %s", state["steps"], action, error)

    new_history = state["action_history"] + [{
        "step": state["steps"],
        "action": action,
        "params": params,
        "observation": state["observation"],
    }]

    done = action in ("extract", "done")

    return {
        **state,
        "action_history": new_history,
        "steps": state["steps"] + 1,
        "result": result,
        "done": done,
        "error": error,
    }


def should_continue(state: AgentState) -> str:
    """Routing: loop back to observe, or exit."""
    if state["done"]:
        return "end"
    if state["steps"] >= state["max_steps"]:
        logger.warning("Max steps (%d) reached — stopping.", state["max_steps"])
        return "end"
    # Loop detection: if last 3 actions are identical, abort
    history = state["action_history"]
    if len(history) >= 3:
        last3 = [(h["action"], str(h["params"])) for h in history[-3:]]
        if len(set(last3)) == 1:
            logger.warning("Loop detected — last 3 actions identical. Stopping.")
            return "end"
    return "observe"


# --- Graph builder ---

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("observe", observe)
    graph.add_node("act", act)
    graph.set_entry_point("observe")
    graph.add_edge("observe", "act")
    graph.add_conditional_edges(
        "act",
        should_continue,
        {"observe": "observe", "end": END},
    )
    return graph.compile()


# --- Runner ---

async def run_agent(task: dict) -> dict:
    """
    Run the full agent loop for a given task definition.

    task dict keys: id, goal, start_url, max_steps
    Returns: { output, steps, action_history, error }
    """
    screenshot_dir = f"screenshots/{task['id']}"
    async with BrowserController(headless=False, screenshot_dir=screenshot_dir) as browser:
        await browser.navigate(task["start_url"])
        # Give the page extra time to pass bot checks / render JS
        await asyncio.sleep(3)
        try:
            await browser.wait_for_load(timeout=8000)
        except Exception:
            pass
        # Dismiss cookie/GDPR banners before the agent loop starts
        await browser.dismiss_consent()
        await asyncio.sleep(1)

        initial_state: AgentState = {
            "task": task["goal"],
            "start_url": task["start_url"],
            "screenshot": b"",
            "action_history": [],
            "observation": "",
            "decision": {},
            "result": None,
            "steps": 0,
            "max_steps": task.get("max_steps", 15),
            "done": False,
            "error": None,
        }

        graph = build_graph()
        config = {"configurable": {"browser": browser}}
        final_state = await graph.ainvoke(initial_state, config=config)

        return {
            "output": final_state.get("result") or "",
            "steps": final_state["steps"],
            "action_history": final_state["action_history"],
            "error": final_state.get("error"),
        }
