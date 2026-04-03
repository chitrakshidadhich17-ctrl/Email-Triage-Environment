# tasks.py
from environment import EmailTriageEnvironment
from models import Action

def run_task(difficulty: str) -> float:
    """
    Runs a task and returns a final score between 0.0 and 1.0
    This is the GRADER - it scores the agent's full performance
    """
    env = EmailTriageEnvironment(task_difficulty=difficulty)
    obs = env.reset()
    done = False
    all_rewards = []

    while not done:
        # Rule-based agent
        subject_lower = obs.subject.lower()
        body_lower = obs.body.lower()
        sender_lower = obs.sender.lower()

        spam_keywords = ["won", "prize", "free", "cheap", "nigerian",
                        "giveaway", "prescription", "earn", "iphone"]
        urgent_keywords = ["urgent", "critical", "emergency", "crashed",
                          "failed", "security", "fire", "error", "patch"]

        label = "normal"
        for kw in spam_keywords:
            if kw in subject_lower or kw in body_lower or kw in sender_lower:
                label = "spam"
                break
        if label == "normal":
            for kw in urgent_keywords:
                if kw in subject_lower or kw in body_lower:
                    label = "urgent"
                    break

        action = Action(label=label)
        obs, reward, done, info = env.step(action)
        all_rewards.append(reward.value)

    final_score = sum(all_rewards) / len(all_rewards) if all_rewards else 0.0
    return round(final_score, 3)


# Task definitions (metadata)
TASKS = {
    "easy": {
        "name": "Basic Email Sorting",
        "description": "Sort 3 emails into urgent / normal / spam",
        "difficulty": "easy",
        "max_score": 1.0,
    },
    "medium": {
        "name": "Mixed Inbox Triage",
        "description": "Sort 5 emails, including ambiguous cases",
        "difficulty": "medium",
        "max_score": 1.0,
    },
    "hard": {
        "name": "Full Inbox Management",
        "description": "Sort all 8 emails with maximum accuracy",
        "difficulty": "hard",
        "max_score": 1.0,
    }
}


if __name__ == "__main__":
    for difficulty in ["easy", "medium", "hard"]:
        score = run_task(difficulty)
        print(f"Task: {difficulty} → Score: {score}")