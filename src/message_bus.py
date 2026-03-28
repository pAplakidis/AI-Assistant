import os
from datetime import datetime

LOGS_DIR = "logs/"

class MessageBus:
  def __init__(self):
    self.messages = []  # chat history/context
    self.state = {}     # structured state of agents
    self.logs = []      # for debugging
    self.logfile = os.path.join(LOGS_DIR, f"bus_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

  def __del__(self):
    print("[bus] Final state:", self.state)
    with open(self.logfile, 'w') as f:
      for log in self.logs:
        f.write(log + "\n")
    print(f"[bus] Logs saved to {self.logfile}")

  def add(self, role: str, content: str):
    self.messages.append({"role": role, "content": content})

  def set(self, key, value):
    self.state[key] = value

  def get(self, key, default=None):
    return self.state.get(key, default)

  def log(self, msg):
    msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(msg)
    self.logs.append(msg)
