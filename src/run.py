from message_bus import MessageBus
from agents.coordinator import CoordinatorAgent
from agents.coder import CoderAgent  
from agents.researcher import ResearcherAgent

MAX_STEPS = 10

def generate_code(user_prompt: str, execute=False):
  bus = MessageBus()
  coder = CoderAgent(bus=bus)

  # TODO: there should be a loop - generate, review, generate, execute, review/debug (inside coordinator?)
  code_v1 = coder.generate_code(user_prompt)
  print(code_v1)

  # if execute:
  #   exec_namespace = coder.execute_code(code_v1)
  #   print(exec_namespace)

  feedback, code_v2 = coder.reflect_on_code_and_regenerate(code_v1, user_prompt)
  print(feedback)
  print(code_v2)

  if execute:
    exec_namespace = coder.execute_code(code_v2)
    print(exec_namespace)

def web_search(user_prompt: str):
  bus = MessageBus()
  researcher = ResearcherAgent(bus=bus)
  return researcher.research(user_prompt)

def run_agentic_loop(user_prompt: str):
  bus = MessageBus()
  bus.set("goal", user_prompt)

  coordinator = CoordinatorAgent(bus=bus)
  coder = CoderAgent(bus=bus)
  researcher = ResearcherAgent(bus=bus)

  for step in range(MAX_STEPS):
    print(f"\n=== Step {step+1} ===")

    # assess completion before planning
    assessment = coordinator.assess_completion()
    if assessment.get("ready_to_finish"):
      bus.log(f"[coordinator] Assessment says task is complete: {assessment['reason']}")
      bus.record_step("finish", user_prompt, "Task assessed as complete.")
      return bus.state

    decision = coordinator.plan()
    action = decision["action"]

    if action == "research":
      result = researcher.research(decision["input"])
      bus.set("research_result", result)
      summary = result[:200] if isinstance(result, str) else str(result)[:200]
      bus.record_step("research", decision["input"], summary)
    elif action == "code":
      # TODO: execute code if necessary
      code = coder.generate_code(decision["input"])
      feedback, improved = coder.reflect_on_code_and_regenerate(code, decision["input"])
      bus.set("code", improved)
      bus.record_step("code", decision["input"], f"Code generated. Feedback: {feedback[:100]}")
    elif action == "finish":
      bus.record_step("finish", user_prompt, "Coordinator chose to finish.")
      return bus.state

  return "Max steps reached without finishing."


if __name__ == "__main__":
  # user_prompt = f"""
  #   Write a function that creates a pandas dataframe with 3 columns: 'Name', 'Age', 'City' and 5 rows of data. Then, filter the dataframe to only include rows where Age > 30 and return the filtered dataframe.
  #   Then run the function and save the returned dataframe to a CSV file named 'filtered_data.csv'.
  # """
  # generate_code(user_prompt)
  
  # user_prompt = f"""
  # I need documentation for python dotenv package. Can you find it for me?
  # """
  # result = web_search(user_prompt)
  # print(result)

  run_agentic_loop("Write a python script that performs tiled matrix multiplication on the GPU using CUDA. Use ctypes to interface with CUDA and nvrtc to compile CUDA code at runtime. The script should include functions for generating random matrices, performing tiled matrix multiplication, and validating the results against CPU matrix multiplication.")
