#!/usr/bin/env python3
from datasets import load_dataset
from pathlib import Path
import tempfile
import subprocess

def main():
    # データセットをロード
    dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")


    for d in dataset:
        print(d["instance_id"])

    return
    target_instance = "sympy__sympy-11400"
    instance = None
    
    for item in dataset:
        if item["instance_id"] == target_instance:
            instance = item
            break
    
    if not instance:
        print(f"❌ Instance {target_instance} not found")
        return

    repo_url = f"https://github.com/{instance['repo']}.git"
    repo_path = clone_repo(repo_url, instance['base_commit'])
    print(repo_path)

def clone_repo(repo_url: str, commit: str) -> Path:
    """リポジトリをクローンして特定のコミットにチェックアウト"""
    tmpdir = Path(tempfile.mkdtemp(prefix="swebench_"))
    
    print(f"📁 Cloning to: {tmpdir}")
    
    # クローン
    subprocess.run(
        ["git", "clone", repo_url, str(tmpdir)],
        check=True,
        capture_output=True
    )
    
    # チェックアウト
    subprocess.run(
        ["git", "checkout", commit],
        cwd=tmpdir,
        check=True,
        capture_output=True
    )
    
    return tmpdir
if __name__ == "__main__":
    main()