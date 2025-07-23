#!/usr/bin/env python3
import json
from pathlib import Path

def create_predictions_for_agent(agent_name: str, patch_dir: str = "patches", output_dir: str = "predictions"):
    """指定されたエージェントのパッチから予測ファイルを作成"""
    patch_path = Path(patch_dir) / agent_name
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    predictions = []

    for patch_file in patch_path.glob("*.patch"):
        instance_id = patch_file.stem
        patch_content = patch_file.read_text()

        predictions.append({
            "instance_id": instance_id,
            "model_patch": patch_content,
            "model_name_or_path": agent_name
        })

        print(f"✅ Added: {instance_id}")

    output_file = output_path / f"{agent_name}.json"
    with open(output_file, "w") as f:
        json.dump(predictions, f, indent=2)

    print(f"\n📄 Created predictions file: {output_file}")
    print(f"📊 Total predictions: {len(predictions)}")

    return predictions

if __name__ == "__main__":
    import sys
    agent = sys.argv[1] if len(sys.argv) > 1 else "agenticode"
    create_predictions_for_agent(agent)
