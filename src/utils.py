
def ensure_execute_python_tags(code: str) -> str:
  if not code.startswith("<execute_python>"):
    code = "<execute_python>\n" + code
  if not code.endswith("</execute_python>"):
    code = code + "\n</execute_python>"
  return code