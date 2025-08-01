#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path
import sys

PREDICTIONS_DIR = Path("predictions")
LOGS_DIR = Path("logs")
DEFAULT_INSTANCE_IDS = [
    # "astropy__astropy-12907",
    # "sympy__sympy-11400",
    "django__django-15814",
]

def discover_agents():
    return sorted([p.stem for p in PREDICTIONS_DIR.glob("*.json")])

def validate_agents(agents):
    available = discover_agents()
    unknown = [a for a in agents if a not in available]
    if unknown:
        print(f"❌ Unknown agent(s): {', '.join(unknown)}")
        print(f"✅ Available agents: {', '.join(available)}")
        sys.exit(1)

def run_evaluation(agent, instance_ids, dataset, split, max_workers, timeout):
    predictions_path = PREDICTIONS_DIR / f"{agent}.json"
    run_id_prefix = f"{agent}_eval"

    for instance_id in instance_ids:
        print(f"\n🚀 Evaluating {agent} on {instance_id}...")

        result = subprocess.run([
            "python", "-m", "swebench.harness.run_evaluation",
            "--predictions_path", str(predictions_path),
            "--dataset_name", dataset,
            "--split", split,
            "--instance_ids", instance_id,
            "--max_workers", str(max_workers),
            "--run_id", f"{run_id_prefix}_{instance_id}",
            "--timeout", str(timeout)
        ], capture_output=True, text=True)

        log_file = LOGS_DIR / f"{run_id_prefix}_{instance_id}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text(result.stdout + "\n" + result.stderr)

        if result.returncode == 0:
            print(f"✅ Done: {agent} on {instance_id}")
        else:
            print(f"❌ Failed: {agent} on {instance_id} (see {log_file})")

def main():
    parser = argparse.ArgumentParser(description="Evaluate multiple agents on SWE-bench")
    parser.add_argument("--agents", nargs="+", required=True,
                        help="List of agent names or 'all' to run all available agents")
    parser.add_argument("--instance_ids", nargs="+", default=DEFAULT_INSTANCE_IDS,
                        help="List of instance IDs to run")
    parser.add_argument("--dataset_name", default="princeton-nlp/SWE-bench_Lite")
    parser.add_argument("--split", default="test")
    parser.add_argument("--max_workers", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=900)

    args = parser.parse_args()

    if args.agents == ["all"]:
        agents = discover_agents()
        print(f"📦 Running all agents: {', '.join(agents)}")
    else:
        validate_agents(args.agents)
        agents = args.agents

    for agent in agents:
        run_evaluation(agent, args.instance_ids, args.dataset_name, args.split, args.max_workers, args.timeout)

if __name__ == "__main__":
    main()
