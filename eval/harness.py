import time
import json
import asyncio
import logging
from pathlib import Path
from agent.graph import run_agent

logger = logging.getLogger(__name__)

RESULTS_DIR = Path("eval/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


async def run_eval(task: dict) -> dict:
    """
    Run one task through the agent and score it.

    Returns:
    {
        task_id, success, steps, latency_s, output, failure_mode
    }
    """
    logger.info("Running task: %s", task["id"])
    start = time.time()
    error = None
    result = {}

    try:
        result = await run_agent(task)
    except Exception as e:
        error = str(e)
        logger.exception("Task %s raised an exception", task["id"])

    latency = round(time.time() - start, 1)
    output = result.get("output", "")
    agent_error = result.get("error") or error

    # Score
    try:
        success = bool(output) and task["success_fn"](output)
    except Exception:
        success = False

    # Determine failure mode
    failure_mode = None
    if not success:
        if agent_error:
            failure_mode = f"exception: {agent_error[:120]}"
        elif not output:
            failure_mode = "no output returned"
        elif result.get("steps", 0) >= task.get("max_steps", 15):
            failure_mode = "max steps reached"
        else:
            failure_mode = "output did not match success criteria"

    logger.info(
        "Task %s finished — success=%s steps=%d latency=%ss",
        task["id"], success, result.get("steps", 0), latency,
    )
    if failure_mode:
        logger.warning("Task %s failure mode: %s", task["id"], failure_mode)

    eval_result = {
        "task_id": task["id"],
        "success": success,
        "steps": result.get("steps", 0),
        "latency_s": latency,
        "output": output,
        "failure_mode": failure_mode,
        "action_history": result.get("action_history", []),
    }

    # Persist to disk
    out_file = RESULTS_DIR / f"{task['id']}.json"
    out_file.write_text(json.dumps(eval_result, indent=2))

    return eval_result


def print_eval_table(results: list[dict]):
    print("\n" + "=" * 72)
    print(f"{'TASK':<22} {'SUCCESS':<9} {'STEPS':<7} {'LATENCY':<10} {'FAILURE MODE'}")
    print("-" * 72)
    for r in results:
        status = "PASS" if r["success"] else "FAIL"
        fm = r["failure_mode"] or "-"
        if len(fm) > 28:
            fm = fm[:25] + "..."
        print(
            f"{r['task_id']:<22} {status:<9} {r['steps']:<7} {r['latency_s']:<10} {fm}"
        )
    print("=" * 72)

    total = len(results)
    passed = sum(1 for r in results if r["success"])
    avg_steps = round(sum(r["steps"] for r in results) / total, 1) if total else 0
    avg_latency = round(sum(r["latency_s"] for r in results) / total, 1) if total else 0
    print(f"\nSuccess rate : {passed}/{total}")
    print(f"Avg steps    : {avg_steps}")
    print(f"Avg latency  : {avg_latency}s")
    print(f"Results saved: eval/results/\n")
