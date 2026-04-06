# server.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import random
from fastapi.responses import HTMLResponse

app = FastAPI(title="Email Triage OpenEnv")

# ── Inline models (no separate import needed) ──────────────────
class Action(BaseModel):
    label: str  # "urgent", "normal", "spam"

class Observation(BaseModel):
    email_id: str
    subject: str
    body: str
    sender: str
    emails_remaining: int
    current_score: float

class Reward(BaseModel):
    value: float
    correct: bool
    explanation: str

# ── Email dataset ───────────────────────────────────────────────
EMAILS = [
    # URGENT emails (9)
    {"id":"e1","subject":"URGENT: Server is down!","body":"Production server crashed. Customers cannot access the site. Need immediate fix.","sender":"ops@company.com","label":"urgent"},
    {"id":"e2","subject":"Critical security vulnerability found","body":"A zero-day exploit has been found in our auth system. Patching required today.","sender":"security@company.com","label":"urgent"},
    {"id":"e3","subject":"Database backup failed","body":"Automated backup failed at 3am. Manual intervention required before data loss occurs.","sender":"alerts@company.com","label":"urgent"},
    {"id":"e4","subject":"Payment system is down","body":"Customers are unable to checkout. We are losing $10,000 per minute. Fix immediately.","sender":"cto@company.com","label":"urgent"},
    {"id":"e5","subject":"CEO needs report in 1 hour","body":"Board meeting in 60 minutes. CEO needs Q3 financial summary urgently. Please send now.","sender":"pa@company.com","label":"urgent"},
    {"id":"e6","subject":"Office fire alarm triggered","body":"Fire alarm went off in Building B. Evacuation in progress. All staff must leave now.","sender":"facilities@company.com","label":"urgent"},
    {"id":"e7","subject":"Client threatening to cancel contract","body":"Our biggest client called. They are extremely unhappy and threatening to cancel their $2M contract today.","sender":"sales@company.com","label":"urgent"},
    {"id":"e8","subject":"Employee collapsed in office","body":"An employee has collapsed on the 3rd floor. Ambulance has been called. Manager needed immediately.","sender":"hr@company.com","label":"urgent"},
    {"id":"e9","subject":"Website showing 500 error","body":"Our main website is showing a 500 internal server error to all visitors. Urgent fix needed.","sender":"webmaster@company.com","label":"urgent"},

    # NORMAL emails (9)
    {"id":"e10","subject":"Team lunch this Friday","body":"Hey everyone, we are doing team lunch at 1pm on Friday. Hope to see you there!","sender":"hr@company.com","label":"normal"},
    {"id":"e11","subject":"Monthly newsletter","body":"Here is what happened in tech this month. Read our top stories inside.","sender":"newsletter@techdigest.com","label":"normal"},
    {"id":"e12","subject":"Coffee machine is broken","body":"Just a heads up, the office coffee machine needs fixing. Someone call facilities.","sender":"john@company.com","label":"normal"},
    {"id":"e13","subject":"New office plants arrived","body":"Just letting everyone know the new plants have arrived and been placed in the lobby.","sender":"facilities@company.com","label":"normal"},
    {"id":"e14","subject":"Reminder: Submit timesheets","body":"Please remember to submit your timesheets by end of day Friday. Thank you.","sender":"payroll@company.com","label":"normal"},
    {"id":"e15","subject":"Welcome our new intern","body":"Please join us in welcoming Priya who is joining our team as a summer intern this week.","sender":"hr@company.com","label":"normal"},
    {"id":"e16","subject":"Q3 review meeting notes","body":"Attached are the notes from yesterday Q3 review meeting. Please review and add comments.","sender":"manager@company.com","label":"normal"},
    {"id":"e17","subject":"Office will be closed Monday","body":"Reminder that the office will be closed next Monday for a public holiday. Enjoy the long weekend!","sender":"admin@company.com","label":"normal"},
    {"id":"e18","subject":"Parking lot maintenance Saturday","body":"The parking lot will be closed this Saturday for resurfacing work. Please park on the street.","sender":"facilities@company.com","label":"normal"},

    #risky ones
    {"id":"e26","subject":"Following up on our discussion","body":"Hi, wanted to follow up on what we discussed. Please let me know your thoughts when you get a chance.","sender":"client@external.com","label":"normal"},
    {"id":"e27","subject":"Your account needs attention","body":"Please review your account settings and update your billing information at your earliest convenience.","sender":"billing@company.com","label":"normal"},
    {"id":"e28","subject":"Server performance degraded","body":"Server response times are slower than usual. Not critical yet but worth investigating this week.","sender":"monitoring@company.com","label":"normal"},
    {"id":"e29","subject":"Free training workshop Friday","body":"HR is offering a free professional development workshop this Friday. Limited seats available!","sender":"hr@company.com","label":"normal"},
    {"id":"e30","subject":"Exclusive offer for valued customer","body":"As a valued customer you have been selected for our premium plan upgrade at a special price.","sender":"offers@legitimatecompany.com","label":"normal"},
    
    
    # SPAM emails (7)
    {"id":"e19","subject":"You won $1,000,000!!!","body":"Congratulations! Click this link to claim your prize. Limited time offer!","sender":"noreply@totallylegit.xyz","label":"spam"},
    {"id":"e20","subject":"Buy cheap meds online","body":"Best prices on all medications. No prescription needed. Order now!","sender":"deals@pharmaspam.net","label":"spam"},
    {"id":"e21","subject":"Your account has been hacked","body":"Click here immediately to secure your account. Enter your password to verify identity.","sender":"security@fake-bank.com","label":"spam"},
    {"id":"e22","subject":"Make $5000 a day from home","body":"Our proven system lets you earn thousands daily. No experience needed. Join now free!","sender":"money@getrichfast.biz","label":"spam"},
    {"id":"e23","subject":"Enlarge your network today","body":"Connect with 10,000 professionals instantly. Buy our LinkedIn booster package now.","sender":"boost@socialspam.net","label":"spam"},
    {"id":"e24","subject":"Free iPhone 15 giveaway","body":"You have been selected for a free iPhone 15. Click to claim before it expires in 10 minutes!","sender":"promo@freestuffnow.xyz","label":"spam"},
    {"id":"e25","subject":"Nigerian Prince needs your help","body":"I am a prince with $50 million. I need your bank details to transfer funds. You keep 40 percent.","sender":"prince@nigeria-royal.com","label":"spam"},

]

# ── Environment state ───────────────────────────────────────────
class EnvState:
    def __init__(self):
        self.inbox = []
        self.index = 0
        self.scores = []

state = EnvState()

# ── Routes ──────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Email Triage OpenEnv is running!"}

@app.get("/ui", response_class=HTMLResponse)
def ui():
    return open("index.html").read()

@app.post("/reset")
def reset(difficulty: str = "easy"):
    inbox = EMAILS.copy()
    random.shuffle(inbox)
    limits = {"easy": 3, "medium": 5, "hard": 8}
    state.inbox = inbox[:limits.get(difficulty, 3)]
    state.index = 0
    state.scores = []
    email = state.inbox[0]
    return Observation(
        email_id=email["id"], subject=email["subject"],
        body=email["body"], sender=email["sender"],
        emails_remaining=len(state.inbox),
        current_score=0.0
    )

@app.post("/step")
def step(action: Action):
    email = state.inbox[state.index]
    correct = action.label == email["label"]

    if correct:
        reward = Reward(value=1.0, correct=True, explanation="Correct!")
    elif (action.label, email["label"]) in [("urgent","normal"),("normal","urgent")]:
        reward = Reward(value=0.3, correct=False, explanation=f"Wrong. Was {email['label']}")
    else:
        reward = Reward(value=0.0, correct=False, explanation=f"Wrong. Was {email['label']}")

    state.scores.append(reward.value)
    state.index += 1
    done = state.index >= len(state.inbox)

    if not done:
        next_email = state.inbox[state.index]
        obs = Observation(
            email_id=next_email["id"], subject=next_email["subject"],
            body=next_email["body"], sender=next_email["sender"],
            emails_remaining=len(state.inbox) - state.index,
            current_score=sum(state.scores)/len(state.scores)
        )
    else:
        obs = Observation(
            email_id="done", subject="", body="", sender="",
            emails_remaining=0,
            current_score=sum(state.scores)/len(state.scores)
        )

    return {"observation": obs, "reward": reward, "done": done,
            "info": {"correct_label": email["label"]}}

@app.get("/state")
def get_state():
    return {
        "total_emails": len(state.inbox),
        "emails_processed": state.index,
        "emails_remaining": len(state.inbox) - state.index,
        "current_score": sum(state.scores)/len(state.scores) if state.scores else 0,
    }

@app.get("/tasks")
def get_tasks():
    return {
        "tasks": [
            {
                "id": "easy",
                "name": "Basic Email Sorting",
                "difficulty": "easy",
                "description": "Sort 3 emails into urgent/normal/spam",
                "max_score": 1.0
            },
            {
                "id": "medium", 
                "name": "Mixed Inbox Triage",
                "difficulty": "medium",
                "description": "Sort 5 emails including ambiguous cases",
                "max_score": 1.0
            },
            {
                "id": "hard",
                "name": "Full Inbox Management", 
                "difficulty": "hard",
                "description": "Sort 8 varied emails with maximum accuracy",
                "max_score": 1.0
            }
        ]
    }

@app.get("/grade")
def grade(difficulty: str = "easy"):
    """Grader endpoint - runs a full task and returns score"""
    import random
    inbox = EMAILS.copy()
    random.shuffle(inbox)
    limits = {"easy": 3, "medium": 5, "hard": 8}
    test_inbox = inbox[:limits.get(difficulty, 3)]
    
    correct = 0
    total = len(test_inbox)
    details = []
    
    for email in test_inbox:
        # Use rule-based agent for grading
        subject_lower = email["subject"].lower()
        body_lower = email["body"].lower()
        sender_lower = email["sender"].lower()
        
        spam_keywords = ["won", "prize", "free", "cheap", "nigerian",
                        "giveaway", "prescription", "earn", "iphone"]
        urgent_keywords = ["urgent", "critical", "emergency", "crashed",
                          "failed", "security", "fire", "error", "patch"]
        
        predicted = "normal"
        for kw in spam_keywords:
            if kw in subject_lower or kw in body_lower or kw in sender_lower:
                predicted = "spam"
                break
        if predicted == "normal":
            for kw in urgent_keywords:
                if kw in subject_lower or kw in body_lower:
                    predicted = "urgent"
                    break
        
        is_correct = predicted == email["label"]
        if is_correct:
            correct += 1
            
        details.append({
            "email_id": email["id"],
            "predicted": predicted,
            "correct": email["label"],
            "match": is_correct
        })
    
    score = round(correct / total, 3) if total > 0 else 0.0
    
    return {
        "difficulty": difficulty,
        "score": score,
        "correct": correct,
        "total": total,
        "details": details
    }
