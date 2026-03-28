import json
from ollama import chat

from constants import *
from message_bus import MessageBus


class CoordinatorAgent:
  def __init__(self, bus: MessageBus, model=LLAMA_3_8BIT):
    self.model = model
    self.bus = bus

  def plan(self):
    prompt = f"""
    You are a coordinator agent responsible for planning and orchestrating the actions of various specialized agents (e.g. coder, researcher) to accomplish complex tasks based on user prompts.

    Goal:
    {self.bus.get('goal')}

    Current state:
    {json.dumps(self.bus.state, indent=2)}

    Decide next step.

    Available actions:
    - "research"
    - "code"
    - "finish"

    Respond only in JSON format:
    {{
      "action": "one of the actions listed above",
      "reason": "brief explanation of why you chose this action",
      "input":  "the input for the chosen action (e.g. research query or coding task)"
    }}
    """

    self.bus.log("[coordinator] Planning next action...")
    response = chat(model=self.model, messages=[{"role": "user", "content": prompt}])
    self.bus.log(f"[coordinator] Response: {response["message"]["content"]}")
    return json.loads(response["message"]["content"])
