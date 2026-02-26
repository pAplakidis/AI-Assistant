import json
import inspect

def ensure_execute_python_tags(code: str) -> str:
  if not code.startswith("<execute_python>"):
    code = "<execute_python>\n" + code
  if not code.endswith("</execute_python>"):
    code = code + "\n</execute_python>"
  return code

def function_to_tool_schema(func):
    sig = inspect.signature(func)
    properties = {}
    required = []
    for name, param in sig.parameters.items():
      if name == "self":
        continue

      # naive type mapping
      ann = param.annotation
      if ann == int:
        t = "integer"
      elif ann == float:
        t = "number"
      elif ann == bool:
        t = "boolean"
      else:
        t = "string"

      properties[name] = {"type": t}
      if param.default is inspect._empty:
        required.append(name)

    return {
      "type": "function",
      "function": {
        "name": func.__name__,
        "description": (func.__doc__ or "").strip(),
        "parameters": {
          "type": "object",
          "properties": properties,
          "required": required,
        },
      },
    }