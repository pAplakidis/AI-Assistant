import json
import requests
from ollama import chat

MODEL = "mistral:7b-instruct"


def get_current_weather(city):
  """Get the current weather for a city"""
  
  # get city coordinates
  geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
  geo_res = requests.get(geo_url).json()
  if "results" not in geo_res:
    return f"City '{city}' not found."

  lat = geo_res["results"][0]["latitude"]
  lon = geo_res["results"][0]["longitude"]

  # get current weather using coordinates
  weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
  weather_res = requests.get(weather_url).json()
  return weather_res["current_weather"]


if __name__ == "__main__":
  messages = [
    {
      "role": "user",
      "content": "What is the weather in Thessaloniki?"
    }
  ]

  response = chat(
    model=MODEL,
    messages=messages,
    tools=[{
      "type": "function",
      "function": {
        "name": "get_current_weather",
        "description": "Get the current weather for a city",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {
              "type": "string",
              "description": "The name of the city",
            },
          },
          "required": ["city"],
        },
      },
    }]
  )

  if (tool_calls := response["message"]["tool_calls"]):
    print(tool_calls)
    for tool_call in tool_calls:
      func = tool_call["function"]["name"]
      args = tool_call["function"]["arguments"]

      # res = get_current_weather(args["city"])
      res = globals()[func]
      res = res(**args)
      
      messages.append(response["message"])
      messages.append({
        "role": "tool",
        "name": func,
        "content": json.dumps(res),
      })

  final = chat(model=MODEL, messages=messages)
  print(final["message"]["content"])
