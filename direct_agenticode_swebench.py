"""
改良版：Agenticode でSWE-benchを実行
"""
import json
import subprocess
import tempfile
import shutil
import time
from pathlib import Path
from datasets import load_dataset


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


def run_claude_code_interactive(repo_path: Path, problem_statement: str) -> str:
    """インタラクティブにAgenticodeを実行（出力を見ながら）"""
    
    # より具体的で段階的なプロンプト
    prompt = f"""You are tasked with fixing a bug in this repository. Follow these steps:

1. First, use 'bash' to explore the repository structure with commands like 'ls', 'find', or 'tree'
2. Read any files mentioned in the bug description using 'readFile'
3. Understand the issue described below
4. Make the necessary changes using 'editFile'

BUG DESCRIPTION:
{problem_statement}

Start by exploring the repository to understand its structure."""
    
    print("\n🤖 Starting Agenticode...")
    print("=" * 80)
    
    process = subprocess.Popen(
        [
            "agenticode", "-p", prompt,
            # "--model", "claude-opus-4-20250514",
            "--max-turns", "20",  # より多くのターンを許可
            "--allowedTools", "readFile,bash,writeFile,editFile",
            "--permission-mode", "bypassPermissions",
            "--dangerously-skip-permissions"
        ],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1  # 行バッファリング
    )
    
    print(prompt)
    # 出力をリアルタイムで表示
    output_lines = []
    for line in process.stdout:
        print(line, end='')
        output_lines.append(line)
    
    process.wait()
    print("=" * 80)
    print(f"📊 Agenticode exit code: {process.returncode}")
    
    # diffを取得
    diff_result = subprocess.run(
        ["git", "diff"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    
    # 変更されたファイルを確認
    changed_files = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    
    if changed_files.stdout:
        print(f"\n✅ Changed files:")
        print(changed_files.stdout)
    else:
        print(f"\n❌ No files were changed")
        
        # git statusも確認
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        if status.stdout:
            print(f"\n📊 Git status:")
            print(status.stdout)
    
    return diff_result.stdout


def main():
    # データセットをロード
    dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    
    # 特定のインスタンスをフィルタ
    target_instance = "astropy__astropy-12907"
    instance = None
    
    for item in dataset:
        if item["instance_id"] == target_instance:
            instance = item
            break
    
    if not instance:
        print(f"❌ Instance {target_instance} not found")
        return
    
    print(f"🎯 Target: {instance['instance_id']}")
    print(f"📦 Repository: {instance['repo']}")
    print(f"🔖 Commit: {instance['base_commit'][:8]}")
    
    # 問題の説明を表示
    print(f"\n📋 Problem statement:")
    print("-" * 80)
    print(instance['problem_statement'])
    print("-" * 80)
    
    # ユーザーに確認
    print("Start Agenticode...")
    
    # リポジトリをクローン
    repo_url = f"https://github.com/{instance['repo']}.git"
    repo_path = clone_repo(repo_url, instance['base_commit'])
    
    try:
        # Agenticodeを実行
        start_time = time.time()
        diff = run_claude_code_interactive(repo_path, instance['problem_statement'])
        elapsed = time.time() - start_time
        
        print(f"\n⏱️  Execution time: {elapsed:.1f} seconds")
        
        if diff:
            print("\n✅ Generated patch:")
            print("-" * 80)
            print(diff)
            print("-" * 80)
            
            # パッチを保存
            output_file = Path("patches") / "agenticode" / f"{instance['instance_id']}.patch"
            with open(output_file, "w") as f:
                f.write(diff)
            print(f"\n📄 Patch saved to: {output_file}")
        else:
            print("\n❌ No patch was generated")
            
            # デバッグ情報
            print("\n🔍 Debug info:")
            print(f"Repository path: {repo_path}")
            print(f"You can manually inspect the repository before it's deleted")
            input("Press Enter to cleanup...")
            
    finally:
        # クリーンアップ
        shutil.rmtree(repo_path, ignore_errors=True)


if __name__ == "__main__":
    main()