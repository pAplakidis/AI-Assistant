MAX_STEPS = 10

# MCP
MCP_PORT = 8000
MCP_URL = f"http://localhost:{MCP_PORT}/mcp"

# researcher
MAX_WORKERS = 3
MAX_ITERS = 10
MAX_TOOL_CALLS = 8
SEARCH_URL = "http://localhost:8888/search"
MAX_RESULTS = 10
MAX_CRAWLED_TEXT = 5000
MAX_CRAWLED_TEXT_DOCS = 12000
MAX_CRAWLED_TEXT_FORUMS = 8000
MIN_TEXT_CACHED = 200

# models
MISTRAL_INSTRUCT = "mistral:7b-instruct"
DEEPSEEK_CODER = "deepseek-coder:6.7b"
LLAMA_3_8BIT = "llama3.1:8b-instruct-q8_0"
LLAMA_3_4BIT = "llama3.1:8b-instruct-q4_K_M"
QWEN = "qwen2.5:3b"
TINY_LLAMA = "tinyllama:1.1b"
