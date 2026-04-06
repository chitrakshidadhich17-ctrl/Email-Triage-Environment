# server.py
from fastapi import FastAPI
from models import Action
from environment import EmailTriageEnvironment
from fastapi.responses import HTMLResponse

app = FastAPI(title="Email Triage OpenEnv")

# One environment instance per session (simple version)
env = EmailTriageEnvironment()

@app.post("/reset")
def reset(difficulty: str = "easy"):
    global env
    env = EmailTriageEnvironment(task_difficulty=difficulty)
    obs = env.reset()
    return obs

@app.post("/step")
def step(action: Action):
    obs, reward, done, info = env.step(action)
    return {"observation": obs, "reward": reward, "done": done, "info": info}

@app.get("/state")
def state():
    return env.state()
