import asyncio
import argparse
import logging
from tasks.definitions import TASKS
from eval.harness import run_eval, print_eval_table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


async def main(task_id: str | None = None):
    logger.info("Browser GUI Agent — Eval Run")

    tasks_to_run = TASKS
    if task_id:
        tasks_to_run = [t for t in TASKS if t["id"] == task_id]
        if not tasks_to_run:
            logger.error("Unknown task id: %s", task_id)
            logger.info("Available: %s", [t["id"] for t in TASKS])
            return

    results = []
    for task in tasks_to_run:
        logger.info("[%s] Starting — goal: %s...", task["id"], task["goal"][:80])
        result = await run_eval(task)
        results.append(result)
        status = "PASS" if result["success"] else "FAIL"
        logger.info(
            "[%s] %s | steps=%d | latency=%ss | output: %s",
            task["id"], status, result["steps"], result["latency_s"], result["output"][:100],
        )
        if result["failure_mode"]:
            logger.warning("[%s] failure: %s", task["id"], result["failure_mode"])

    print_eval_table(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Browser GUI Agent")
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help=f"Run a single task by id. Options: {[t['id'] for t in TASKS]}",
    )
    args = parser.parse_args()
    asyncio.run(main(task_id=args.task))
