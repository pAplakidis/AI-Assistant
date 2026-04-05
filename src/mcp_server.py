from fastmcp import FastMCP

from constants import *

mcp = FastMCP("Tool Server")

@mcp.tool()
def get_current_time() -> str:
  """Get the current time."""
  from datetime import datetime
  return datetime.now().strftime("%I:%M %p")

@mcp.tool()
def save_note(title: str, content: str) -> str:
  """Save a note to a file"""
  import os
  filename = f"notes/{title.replace(' ', '_')}.txt"
  os.makedirs("notes", exist_ok=True)
  with open(filename, "w") as f:
    f.write(content)
  return f"Note saved to {filename}"

@mcp.tool()
def list_notes() -> list:
  """List all saved notes"""
  import os
  if not os.path.exists("notes"):
    return []
  return os.listdir("notes")

# example mock database tool
@mcp.tool()
def search_users(name: str) -> list:
  """Search for users by name"""
  # Connect to your database
  # For demo, return fake data
  users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"}
  ]
  return [u for u in users if name.lower() in u["name"].lower()]

# TODO: this could be implemented inside researcher agent
@mcp.tool()
def summarize_pdf(file_path: str) -> str:
    """Create notes from PDF file"""
    pass


if __name__ == "__main__":
  mcp.run(transport="sse", port=MCP_PORT)
