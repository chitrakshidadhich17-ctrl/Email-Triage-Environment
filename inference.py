
# This script runs an AI agent (GPT-3.5) against your environment
# and produces reproducible baseline scores for all 3 tasks.

import os
import requests

# ── Configuration ───────────────────────────────────────────────
BASE_URL = "https://chitrakshi404-email-triage-env.hf.space"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ── Ask GPT to classify an email ────────────────────────────────
def ask_gpt(subject: str, body: str, sender: str) -> str:
    """Send email to GPT-3.5 and get a label back"""

    if not OPENAI_API_KEY:
        # If no API key, use a simple rule-based fallback agent
        return rule_based_agent(subject, body, sender)

    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
You are an email triage assistant.
Classify this email as exactly ONE of: urgent, normal, spam

Subject: {subject}
From: {sender}
Body: {body}

Rules:
- urgent = needs immediate attention (server down, security issues, emergencies)
- normal = regular work email (meetings, announcements, reminders)  
- spam = unwanted/suspicious email (prizes, cheap products, scams)

Reply with ONLY one word: urgent, normal, or spam
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=5,
        temperature=0
    )
    label = response.choices[0].message.content.strip().lower()

    # Make sure label is valid
    if label not in ["urgent", "normal", "spam"]:
        label = "normal"

    return label


# ── Simple rule-based agent (works without API key) ──────────────
def rule_based_agent(subject: str, body: str, sender: str) -> str:
    """
    A simple rule-based agent that doesn't need an API key.
    Good for testing the environment works correctly.
    """
    subject_lower = subject.lower()
    body_lower = body.lower()
    sender_lower = sender.lower()

    # Spam signals
    spam_keywords = ["won", "prize", "free", "click here", "cheap",
                     "make money", "nigerian", "giveaway", "enlarge",
                     "no prescription", "earn $", "claim"]
    spam_domains = [".xyz", ".biz", "spam", "fake", "legit"]

    for keyword in spam_keywords:
        if keyword in subject_lower or keyword in body_lower:
            return "spam"

    for domain in spam_domains:
        if domain in sender_lower:
            return "spam"

    # Urgent signals
    urgent_keywords = ["urgent", "critical", "emergency", "immediately",
                       "crashed", "down", "failed", "security", "breach",
                       "asap", "fix now", "collapsed", "fire", "error",
                       "vulnerability", "cancel", "losing"]

    for keyword in urgent_keywords:
        if keyword in subject_lower or keyword in body_lower:
            return "urgent"

    # Everything else is normal
    return "normal"


# ── Run one full task ────────────────────────────────────────────
def run_task(difficulty: str) -> dict:
    """Run one complete task and return score"""
    
    # START log
    print(f"[START] task={difficulty}")

    response = requests.post(f"{BASE_URL}/reset?difficulty={difficulty}")
    obs = response.json()

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

        result = requests.post(
            f"{BASE_URL}/step",
            json={"label": label}
        ).json()

        reward_value = result["reward"]["value"]
        correct_label = result["info"]["correct_label"]
        correct = result["reward"]["correct"]
        done = result["done"]
        rewards.append(reward_value)

        # STEP log
        print(f"[STEP] email_id={obs.get('email_id')} action={label} reward={reward_value} correct={correct_label}")

        if not done:
            obs = result["observation"]

    score = round(sum(rewards) / len(rewards), 3) if rewards else 0.0

    # END log
    print(f"[END] task={difficulty} score={score}")
    
    return {"difficulty": difficulty, "emails": len(rewards), "score": score}

# ── Main ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🤖 Email Triage OpenEnv — Baseline Inference Script")
    print("────────────────────────────────────────────────────")

    if OPENAI_API_KEY:
        print("✅ OpenAI API key found — using GPT-3.5")
    else:
        print("⚠️  No OpenAI API key — using Rule-Based Agent instead")
        print("   (Set OPENAI_API_KEY environment variable to use GPT-3.5)")

    # Run all 3 tasks
    results = []
    for difficulty in ["easy", "medium", "hard"]:
        result = run_task(difficulty)
        results.append(result)

    # Print summary
    print(f"\n{'='*50}")
    print("  📋 BASELINE RESULTS SUMMARY")
    print(f"{'='*50}")
    print(f"  {'Task':<10} {'Emails':<10} {'Score':<10} {'Agent'}")
    print(f"  {'-'*45}")
    for r in results:
        print(f"  {r['difficulty']:<10} {r['total_emails']:<10} "
              f"{r['final_score']:<10} {r['agent']}")

    avg = round(sum(r['final_score'] for r in results) / len(results), 3)
    print(f"\n  🏆 Average Score across all tasks: {avg}")
    print(f"{'='*50}\n")
