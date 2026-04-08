"""
replay.py — stitch task screenshots into a GIF and an HTML step viewer.

Usage:
    python replay.py                        # all tasks in screenshots/
    python replay.py --task cheapest_car    # single task
    python replay.py --fps 1.5             # control GIF speed
"""

import argparse
import json
import base64
from pathlib import Path
from PIL import Image


SCREENSHOTS_DIR = Path("screenshots")
RESULTS_DIR = Path("eval/results")
OUTPUT_DIR = Path("replay")
OUTPUT_DIR.mkdir(exist_ok=True)


# --- GIF ---

def make_gif(task_id: str, fps: float = 1.0):
    frames_dir = SCREENSHOTS_DIR / task_id
    frames = sorted(frames_dir.glob("*.png"))
    if not frames:
        print(f"  [skip] no screenshots found in {frames_dir}")
        return None

    images = [Image.open(f).convert("RGB") for f in frames]

    # Resize to consistent width (max 1000px) to keep GIF reasonable
    target_w = min(1000, images[0].width)
    ratio = target_w / images[0].width
    target_h = int(images[0].height * ratio)
    images = [img.resize((target_w, target_h), Image.LANCZOS) for img in images]

    out_path = OUTPUT_DIR / f"{task_id}.gif"
    duration_ms = int(1000 / fps)

    images[0].save(
        out_path,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
    )
    print(f"  GIF saved: {out_path}  ({len(images)} frames @ {fps}fps)")
    return out_path


# --- HTML ---

def make_html(task_id: str):
    frames_dir = SCREENSHOTS_DIR / task_id
    frames = sorted(frames_dir.glob("*.png"))
    if not frames:
        return None

    # Load action history from eval results if available
    result_file = RESULTS_DIR / f"{task_id}.json"
    action_history = []
    task_output = ""
    task_success = None
    if result_file.exists():
        data = json.loads(result_file.read_text())
        action_history = data.get("action_history", [])
        task_output = data.get("output", "")
        task_success = data.get("success")

    def img_to_b64(path: Path) -> str:
        return base64.b64encode(path.read_bytes()).decode()

    steps_html = ""
    for i, frame in enumerate(frames):
        action = action_history[i] if i < len(action_history) else {}
        action_type = action.get("action", "—")
        params = action.get("params", {})
        observation = action.get("observation", "")

        param_str = ", ".join(f"{k}={v}" for k, v in params.items() if k != "result")
        result_str = params.get("result", "")

        steps_html += f"""
        <div class="step">
            <div class="step-header">
                <span class="step-num">Step {i}</span>
                <span class="action-badge action-{action_type}">{action_type}</span>
                <span class="params">{param_str}</span>
            </div>
            {"<div class='observation'>" + observation + "</div>" if observation else ""}
            {"<div class='result-box'>Result: " + result_str + "</div>" if result_str else ""}
            <img src="data:image/png;base64,{img_to_b64(frame)}" class="screenshot" />
        </div>
        """

    status_color = "#2ecc71" if task_success else "#e74c3c" if task_success is False else "#95a5a6"
    status_text = "PASS" if task_success else "FAIL" if task_success is False else "UNKNOWN"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Replay: {task_id}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: #0f1117; color: #e0e0e0; margin: 0; padding: 24px; }}
  h1 {{ color: #fff; margin-bottom: 4px; }}
  .meta {{ color: #888; margin-bottom: 24px; font-size: 14px; }}
  .status {{ display: inline-block; padding: 4px 12px; border-radius: 4px;
             background: {status_color}; color: #fff; font-weight: bold; font-size: 13px; }}
  .output-box {{ background: #1e2130; border-left: 3px solid {status_color};
                 padding: 12px 16px; margin: 16px 0 28px; border-radius: 4px;
                 font-size: 15px; }}
  .step {{ background: #1a1d2e; border-radius: 8px; padding: 16px;
           margin-bottom: 20px; border: 1px solid #2a2d3e; }}
  .step-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
  .step-num {{ font-weight: bold; color: #888; font-size: 13px; min-width: 48px; }}
  .action-badge {{ padding: 3px 10px; border-radius: 12px; font-size: 12px;
                   font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
  .action-click    {{ background: #2980b9; color: #fff; }}
  .action-fill     {{ background: #8e44ad; color: #fff; }}
  .action-navigate {{ background: #16a085; color: #fff; }}
  .action-scroll   {{ background: #555; color: #fff; }}
  .action-done     {{ background: #27ae60; color: #fff; }}
  .action-extract  {{ background: #f39c12; color: #fff; }}
  .action-type     {{ background: #c0392b; color: #fff; }}
  .action-press    {{ background: #7f8c8d; color: #fff; }}
  .params {{ font-family: monospace; font-size: 12px; color: #aaa; }}
  .observation {{ font-size: 13px; color: #9b9b9b; margin-bottom: 10px;
                  font-style: italic; }}
  .result-box {{ font-size: 13px; color: #2ecc71; background: #0d1f14;
                 padding: 8px 12px; border-radius: 4px; margin-bottom: 10px;
                 font-family: monospace; }}
  .screenshot {{ width: 100%; border-radius: 4px; border: 1px solid #2a2d3e; }}
  .divider {{ border: none; border-top: 1px solid #2a2d3e; margin: 32px 0; }}
</style>
</head>
<body>
  <h1>Agent Replay: <code>{task_id}</code></h1>
  <div class="meta">
    <span class="status">{status_text}</span>
    &nbsp; {len(frames)} steps
  </div>
  <div class="output-box"><strong>Final output:</strong> {task_output or "—"}</div>
  <hr class="divider">
  {steps_html}
</body>
</html>"""

    out_path = OUTPUT_DIR / f"{task_id}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"  HTML saved: {out_path}  ({len(frames)} steps)")
    return out_path


# --- Main ---

def run(task_id: str | None, fps: float):
    if task_id:
        task_dirs = [SCREENSHOTS_DIR / task_id]
    else:
        task_dirs = [d for d in sorted(SCREENSHOTS_DIR.iterdir()) if d.is_dir()]

    for task_dir in task_dirs:
        tid = task_dir.name
        print(f"\n[{tid}]")
        make_gif(tid, fps=fps)
        make_html(tid)

    print(f"\nDone. Open replay/<task_id>.html in a browser to view step-by-step replay.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay agent runs as GIF + HTML")
    parser.add_argument("--task", type=str, default=None, help="Task id to replay")
    parser.add_argument("--fps", type=float, default=1.0, help="GIF frames per second (default: 1.0)")
    args = parser.parse_args()
    run(task_id=args.task, fps=args.fps)
