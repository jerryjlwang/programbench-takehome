#!/usr/bin/env python3
"""Run the mini-SWE-agent ProgramBench scaffold on the local Lua cleanroom."""

from __future__ import annotations

import argparse
import copy
import os
import sys
import time
import traceback
from pathlib import Path

from minisweagent.config import builtin_config_dir, get_config_from_spec
from minisweagent.environments import get_environment
from minisweagent.models import get_model
from minisweagent.run.benchmarks.programbench import ProgramBenchAgent, copy_submission
from minisweagent.utils.log import add_file_handler, logger
from minisweagent.utils.serialize import UNSET, recursive_merge


INSTANCE_ID = "lua__lua.c6b4848"
DEFAULT_MODEL = "gemini/gemini-3.5-flash"
DEFAULT_CONFIG = builtin_config_dir / "benchmarks" / "programbench.yaml"
GEMINI_KEYS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY")


class ConsoleProgress:
    def update_instance_status(self, instance_id: str, status: str) -> None:
        print(f"[{time.strftime('%H:%M:%S')}] {instance_id}: {status}", flush=True)


def require_model_credentials(model: str) -> None:
    if "gemini" in model.lower() and not any(os.getenv(key) for key in GEMINI_KEYS):
        keys = ", ".join(GEMINI_KEYS)
        raise SystemExit(
            f"Refusing to start Gemini run: none of {keys} is set in this shell. "
            "Export a key, then rerun this command."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="programbench-lua-cleanroom:local")
    parser.add_argument("--output", type=Path, default=Path(f"runs/lua_miniswe_{int(time.time())}"))
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL)
    parser.add_argument("--model-class", default="litellm")
    parser.add_argument("--config", action="append", default=[], help="Extra mini-SWE config spec.")
    parser.add_argument("--step-limit", type=int, default=1000)
    parser.add_argument("--cost-limit", type=float, default=0.0)
    parser.add_argument("--wall-time-limit-seconds", type=int, default=21600)
    parser.add_argument("--cpus", default="4")
    parser.add_argument("--memory", default="8g")
    parser.add_argument("--redo-existing", action="store_true")
    parser.add_argument("--skip-key-check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.skip_key_check:
        require_model_credentials(args.model)

    instance_dir = args.output / INSTANCE_ID
    traj_path = instance_dir / f"{INSTANCE_ID}.traj.json"
    submission_path = instance_dir / "submission.tar.gz"
    if submission_path.exists() and not args.redo_existing:
        raise SystemExit(f"{submission_path} already exists; pass --redo-existing to replace it.")

    args.output.mkdir(parents=True, exist_ok=True)
    instance_dir.mkdir(parents=True, exist_ok=True)
    add_file_handler(args.output / "minisweagent.log")

    configs = [get_config_from_spec(DEFAULT_CONFIG), *(get_config_from_spec(spec) for spec in args.config)]
    configs.append(
        {
            "agent": {
                "step_limit": args.step_limit,
                "cost_limit": args.cost_limit,
                "wall_time_limit_seconds": args.wall_time_limit_seconds,
            },
            "environment": {
                "image": args.image,
                "run_args": [
                    "--platform",
                    "linux/amd64",
                    "--rm",
                    "--network",
                    "none",
                    "--cpus",
                    args.cpus,
                    "--memory",
                    args.memory,
                    "--memory-swap",
                    args.memory,
                    "--user",
                    "agent",
                    "--cap-drop",
                    "SYS_PTRACE",
                ],
            },
            "model": {
                "model_name": args.model,
                "model_class": args.model_class or UNSET,
                "cost_tracking": "ignore_errors",
            },
        }
    )
    config = recursive_merge(*configs)

    agent = None
    exit_status = None
    extra_info: dict[str, str] = {}
    try:
        model = get_model(config=copy.deepcopy(config.get("model", {})))
        env = get_environment(copy.deepcopy(config.get("environment", {})), default_type="docker")
        env.execute({"command": 'git config user.name "mini-swe-agent" && git config user.email "mini-swe-agent@proton.me"'})

        agent_config = dict(config.get("agent", {}))
        agent_config["output_path"] = traj_path
        agent = ProgramBenchAgent(
            model,
            env,
            progress_manager=ConsoleProgress(),
            instance_id=INSTANCE_ID,
            **agent_config,
        )
        agent.extra_template_vars = {
            "instance": {
                "instance_id": INSTANCE_ID,
                "image_name": args.image,
                "source": "local-reproduced-lua-cleanroom",
            }
        }
        exit_status = agent.run().get("exit_status")
    except Exception as exc:
        logger.error("Error processing %s: %s", INSTANCE_ID, exc, exc_info=True)
        exit_status = type(exc).__name__
        extra_info = {"traceback": traceback.format_exc(), "exception_str": str(exc)}
        if agent is None:
            print(extra_info["traceback"], file=sys.stderr)
    finally:
        if agent is not None:
            try:
                copy_submission(agent.env, submission_path)
            except Exception as exc:
                logger.error("Failed to copy submission for %s: %s", INSTANCE_ID, exc, exc_info=True)
                extra_info["submission_copy_error"] = str(exc)
            agent.save(traj_path, {"info": {"exit_status": exit_status, **extra_info}, "instance_id": INSTANCE_ID})
            agent.env.cleanup()

    print(f"exit_status={exit_status}")
    print(f"trajectory={traj_path}")
    print(f"submission={submission_path if submission_path.exists() else 'not-created'}")
    return 0 if submission_path.exists() else 1


if __name__ == "__main__":
    raise SystemExit(main())
