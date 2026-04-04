import json
from ollama import chat

from constants import *
from message_bus import MessageBus


class CoordinatorAgent:
  def __init__(self, bus: MessageBus, model=LLAMA_3_8BIT):
    self.model = model
    self.bus = bus

  def assess_completion(self):
    prompt = f"""
    You are a coordinator agent evaluating whether the accumulated work is sufficient to answer the user's original goal.

    Goal:
    {self.bus.get('goal')}

    Completed steps:
    {json.dumps(self.bus.history, indent=2)}

    Current state (research results, code, etc.):
    {json.dumps(self.bus.state, indent=2)}

    Evaluate: Is the current state sufficient to fully answer the user's goal?
    Respond only in JSON format:
    {{"ready_to_finish": true/false, "reason": "brief explanation"}}
    """

    self.bus.log("[coordinator] Assessing if task is complete...")
    response = chat(model=self.model, messages=[{"role": "user", "content": prompt}])
    try:
      return json.loads(response["message"]["content"])
    except:
      return {"ready_to_finish": False, "reason": "Failed to parse assessment."}

  def plan(self):
    history_summary = "\n".join(
      f"  Step {s['step']}: [{s['action']}] {s['result_summary'][:120]}..."
      for s in self.bus.history
    ) if self.bus.history else "  (no steps completed yet)"

    prompt = f"""
    You are a coordinator agent responsible for planning and orchestrating the actions of various specialized agents (e.g. coder, researcher) to accomplish complex tasks based on user prompts.

    Goal:
    {self.bus.get('goal')}

    Completed steps so far:
    {history_summary}

    Current state (research results, code, etc.):
    {json.dumps(self.bus.state, indent=2)}

    Decide the next step.

    CRITICAL RULES:
    1. Choose "finish" ONLY when you have a complete, working answer to the user's goal. If the code is written and research is done, choose "finish".
    2. Do NOT repeat research or coding steps that have already been completed. Check the completed steps history.
    3. The "input" field MUST be a plain string, NEVER a JSON object or nested dict.
    4. If you already have code and research results that address the goal, choose "finish" immediately.

    Available actions:
    - "research" — search the web for information
    - "code" — generate python code
    - "finish" — the task is complete, return the final answer

    Respond only in JSON format:
    {{
      "action": "one of the actions listed above",
      "reason": "brief explanation of why you chose this action",
      "input": "a plain string describing the input for the chosen action"
    }}
    """

    self.bus.log("[coordinator] Planning next action...")
    response = chat(model=self.model, messages=[{"role": "user", "content": prompt}])
    self.bus.log(f"[coordinator] Response: {response["message"]["content"]}")
    decision = json.loads(response["message"]["content"])
    decision["input"] = str(decision.get("input", ""))
    return decision
