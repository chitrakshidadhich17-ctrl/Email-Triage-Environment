# inference.py
import subprocess
import sys

# Auto-install required packages before anything else
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "requests", "openai", "pydantic"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

import os
import requests
from openai import OpenAI

# ── Required environment variables ──────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-3.5-turbo")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
BASE_URL = "https://chitrakshi404-email-triage-env.hf.space"

# ── OpenAI client ────────────────────────────────────────────────
client = OpenAI(
    api_key=HF_TOKEN if HF_TOKEN else "dummy-key",
    base_url=API_BASE_URL
)

def ask_llm(subject: str, body: str, sender: str) -> str:
    try:
        if not HF_TOKEN:
            return rule_based_agent(subject, body, sender)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{
                "role": "user",
                "content": f"""Classify this email as exactly one of: urgent, normal, spam

Subject: {subject}
From: {sender}
Body: {body}

Reply with ONLY one word: urgent, normal, or spam"""
            }],
            max_tokens=5,
            temperature=0
        )
        label = response.choices[0].message.content.strip().lower()
        if label not in ["urgent", "normal", "spam"]:
            return "normal"
        return label
    except Exception:
        return rule_based_agent(subject, body, sender)

def rule_based_agent(subject: str, body: str, sender: str) -> str:
    subject_lower = subject.lower()
    body_lower = body.lower()
    sender_lower = sender.lower()

    spam_keywords = ["won", "prize", "free", "click here", "cheap",
                     "make money", "nigerian", "giveaway", "no prescription",
                     "earn $", "claim", "iphone", "selected", "million"]
    spam_domains = [".xyz", ".biz", "spam", "fake", "pharmaspam",
                    "getrichfast", "socialspam", "freestuff"]

    for keyword in spam_keywords:
        if keyword in subject_lower or keyword in body_lower:
            return "spam"
    for domain in spam_domains:
        if domain in sender_lower:
            return "spam"

    urgent_keywords = ["urgent", "critical", "emergency", "immediately",
                       "crashed", "down", "failed", "security", "breach",
                       "fix now", "collapsed", "fire alarm", "error",
                       "vulnerability", "cancel", "losing", "zero-day",
                       "patch", "exploit", "ambulance"]
    for keyword in urgent_keywords:
        if keyword in subject_lower or keyword in body_lower:
            return "urgent"

    return "normal"

def run_task(difficulty: str) -> dict:
    print(f"[START] task={difficulty}")
    try:
        response = requests.post(
            f"{BASE_URL}/reset?difficulty={difficulty}",
            timeout=30
        )
        response.raise_for_status()
        obs = response.json()
    except Exception as e:
        print(f"[ERROR] Failed to reset: {e}")
        return {"difficulty": difficulty, "emails": 0, "score": 0.0}

    rewards = []
    done = False
    step_num = 0

    while not done:
        step_num += 1
        subject = obs.get("subject", "")
        body = obs.get("body", "")
        sender = obs.get("sender", "")

        if not subject:
            break

        label = ask_llm(subject, body, sender)

        try:
            result = requests.post(
                f"{BASE_URL}/step",
                json={"label": label},
                timeout=30
            ).json()
        except Exception as e:
            print(f"[ERROR] Failed to step: {e}")
            break

        reward_value = result["reward"]["value"]
        correct_label = result["info"]["correct_label"]
        correct = result["reward"]["correct"]
        done = result["done"]
        rewards.append(reward_value)

        print(f"[STEP] email_id={obs.get('email_id')} action={label} reward={reward_value} correct={correct_label}")

        if not done:
            obs = result["observation"]

    score = round(sum(rewards) / len(rewards), 3) if rewards else 0.0
    print(f"[END] task={difficulty} score={score}")
    return {"difficulty": difficulty, "emails": len(rewards), "score": score}

if __name__ == "__main__":
    print("\n🤖 Email Triage OpenEnv — Inference Script")
    print(f"   API_BASE_URL: {API_BASE_URL}")
    print(f"   MODEL_NAME:   {MODEL_NAME}")
    print(f"   HF_TOKEN:     {'set' if HF_TOKEN else 'not set - using rule-based agent'}")

    results = []
    for difficulty in ["easy", "medium", "hard"]:
        try:
            result = run_task(difficulty)
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Task {difficulty} failed: {e}")
            results.append({"difficulty": difficulty, "emails": 0, "score": 0.0})

    print(f"\n{'='*50}")
    print("  BASELINE RESULTS SUMMARY")
    print(f"{'='*50}")
    print(f"  {'Task':<10} {'Emails':<10} {'Score'}")
    print(f"  {'-'*30}")
    for r in results:
        print(f"  {r['difficulty']:<10} {r['emails']:<10} {r['score']}")

    if results:
        avg = round(sum(r['score'] for r in results) / len(results), 3)
        print(f"\n  Average Score: {avg}")
    print(f"{'='*50}\n")
