from coordinator import CoordinatorAgent

# TODO: move to coordinator
from coder import CoderAgent  
from researcher import ResearcherAgent


def generate_code(user_prompt: str, execute=False):
  coder = CoderAgent()

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
  researcher = ResearcherAgent()
  researcher.research(user_prompt)
  query = researcher.create_search_query(user_prompt)
  return researcher.web_search(query)


if __name__ == "__main__":
  # TODO: use orchestrator to research and write code for:
  # cuda tiled matmul using python ctypes and nvrtc
  user_prompt = f"""
    Write a function that creates a pandas dataframe with 3 columns: 'Name', 'Age', 'City' and 5 rows of data. Then, filter the dataframe to only include rows where Age > 30 and return the filtered dataframe.
    Then run the function and save the returned dataframe to a CSV file named 'filtered_data.csv'.
  """
  generate_code(user_prompt)
  
  user_prompt = f"""
  I need documentation for python dotenv package. Can you find it for me?
  """
  result = web_search(user_prompt)
  print(result)
