from coordinator import *
from coder import CoderAgent  # TODO: move to coordinator


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


if __name__ == "__main__":
  user_prompt = f"""
    Write a function that creates a pandas dataframe with 3 columns: 'Name', 'Age', 'City' and 5 rows of data. Then, filter the dataframe to only include rows where Age > 30 and return the filtered dataframe.
    Then run the function and save the returned dataframe to a CSV file named 'filtered_data.csv'.
  """
  generate_code(user_prompt)
