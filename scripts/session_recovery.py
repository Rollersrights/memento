#!/usr/bin/env python3
"""
Memento Session Recovery
Auto-loads context from Memento and GitHub on session startup.
Run this after reboot/restart to restore working context.
"""

import subprocess
import json
import sys
import os
from pathlib import Path

TOKEN = os.environ.get("GITHUB_TOKEN", "")
VENV_PYTHON = Path.home() / ".venv/bin/python3"
MEMENTO_DIR = Path.home() / ".openclaw/workspace/memento"

def query_memento(query, topk=3):
    try:
        result = subprocess.run(
            [str(VENV_PYTHON), "scripts/cli.py", "recall", query, "-n", str(topk)],
            cwd=MEMENTO_DIR, capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            start_idx = output.find('[\n  {')
            if start_idx >= 0:
                return json.loads(output[start_idx:])
    except Exception:
        pass
    return []

def get_github_issues():
    try:
        result = subprocess.run(
            ["curl", "-s", "-H", f"Authorization: token {TOKEN}",
             "https://api.github.com/repos/Rollersrights/memento/issues?state=open"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return [i for i in json.loads(result.stdout) if 'pull_request' not in i][:5]
    except Exception:
        pass
    return []

def get_github_prs():
    try:
        result = subprocess.run(
            ["curl", "-s", "-H", f"Authorization: token {TOKEN}",
             "https://api.github.com/repos/Rollersrights/memento/pulls?state=open"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout)[:3]
    except Exception:
        pass
    return []

def recover_session():
    print("=" * 60)
    print("🧠 MEMENTO SESSION RECOVERY")
    print("=" * 60)
    print()
    print("📚 Loading from Memento...")
    context = {
        "recovery": query_memento("reboot recovery", 1),
        "priorities": query_memento("current priorities", 2),
        "user_prefs": query_memento("Brett preferences", 1),
    }
    print("🌐 Checking GitHub...")
    issues = get_github_issues()
    prs = get_github_prs()
    print()
    print("-" * 60)
    print("📋 RECOVERY SUMMARY")
    print("-" * 60)
    print()
    if context["user_prefs"]:
        print("👤 User Preferences:")
        for r in context["user_prefs"][:1]:
            print(f"   {r.get('text', '')[:100]}...")
        print()
    if context["recovery"]:
        print("🔄 Last Known State:")
        for r in context["recovery"][:1]:
            text = r.get('text', '')
            lines = [text[i:i+58] for i in range(0, len(text), 58)]
            print(f"   {lines[0]}")
            for line in lines[1:3]:
                print(f"   {line}")
        print()
    if context["priorities"]:
        print("🎯 Current Priorities:")
        for r in context["priorities"][:2]:
            print(f"   • {r.get('text', '')[:80]}...")
        print()
    if issues:
        print(f"📂 Open Issues ({len(issues)} shown):")
        for i in issues[:5]:
            print(f"   #{i.get('number')}: {i.get('title', '')[:50]}")
        print()
    if prs:
        print(f"🔀 Open PRs ({len(prs)} shown):")
        for p in prs[:3]:
            print(f"   #{p.get('number')}: {p.get('title', '')[:50]}")
        print()
    print("-" * 60)
    print("✅ Recovery complete. Ready to work.")
    print("=" * 60)

if __name__ == "__main__":
    recover_session()
