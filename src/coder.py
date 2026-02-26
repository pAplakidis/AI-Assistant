import os
import re
import textwrap
import json
import ollama
from typing import Dict

import utils
from constants import *

DEBUG = int(os.getenv("DEBUG", 0))


class CoderAgent:
  """A coding assistant agent that generates and executes python code based on user prompts. This agent can also use tools to enhance its capabilities."""

  def __init__(self, model=DEEPSEEK_CODER):
    self.model = model

  def get_tools(self):
    pass

  # TODO: use tools first before generating code
  def generate_code(self, question):
    prompt = f"""
    You are a helpful assistant with a senior background that generates python code based on user prompts.

    Return your answer *strictly* in this format:

    <execute_python>
    # valid python code here
    </execute_python>

    User question:
    {question}

    Respond with python code that answers the user's question. Make sure to include any necessary imports and comments to explain your code.
    Return ONLY the code wrapped in <execute_python> tags.
    """

    print("[coder]: Generating code...")
    response = ollama.chat(
      model=self.model,
      messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]

  # TODO: execute code inside a sandbox (docker)
  def execute_code(self, code: str) -> Dict:
    print("[coder]: Executing code...")
    match = re.search(r"<execute_python>([\s\S]*?)</execute_python>", code)
    if not match:
      print("[coder]: No code found in the response.")
      return

    initial_code = match.group(1)
    cleaned_code = textwrap.dedent(initial_code).strip()
    exec_namespace = {}
    exec(cleaned_code, exec_namespace)
    return exec_namespace

  # TODO: maybe use a different LLM to reflect/debug code if execution fails
  def reflect_on_code_and_regenerate(self, code: str, user_prompt: str):
    print("[coder]: Reflecting on code and regenerating...")
    prompt = f"""
    You are a senior python developer, experienced in debugging and improving code.
    Your task is to review the original given code, identify any issues, and regenerate a corrected version of the code while providing feedback.

    Original code (for context):
    {code}

    OUTPUT FORMAT (STRICT):
    1) First line: a valid JSON object with ONLY the "feedback" field.
    Example: {{"feedback": "The legend is unclear and the axis labels overlap."}}

    2) After a newline, output ONLY the refined Python code wrapped in:
    <execute_python>
    ...
    </execute_python>

    3) Import all necessary libraries in the code. Don't assume any imports from the original code.

    HARD CONSTRAINTS:
    - Do NOT include Markdown, backticks, or any extra prose outside the two parts above.
    - Include all necessary import statements.

    Instruction:
    {user_prompt}
    """

    response = ollama.chat(
      model=self.model,
      messages=[{"role": "user", "content": prompt}]
    )

    # split first line (JSON) from the rest
    content = response["message"]["content"]
    first_line, _, rest = content.strip().partition("\n")
    try:
      feedback_obj = json.loads(first_line)
      feedback = feedback_obj.get("feedback", "").strip()
    except json.JSONDecodeError:
      feedback = "Failed to parse feedback JSON."

    m_code = re.search(r"<execute_python>([\s\S]*?)</execute_python>", content)
    refined_code_body = m_code.group(1).strip() if m_code else ""
    refined_code = utils.ensure_execute_python_tags(refined_code_body)
    return feedback, refined_code

  def run_workflow(self):
    pass
