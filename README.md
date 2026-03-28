# AI Assistant

Like ChatGPT, not as cool but local.

A local ecosystem for various LLM agents to interact and execute the user's queries.
Tested on Ubuntu 24.04 using an NVIDIA RTX 4060Ti 16GB

# Requirements

- [ollama](https://ollama.com/)
- [searxng docker setup](https://docs.searxng.org/admin/installation-docker.html)

# Setup

```bash
pip install -r requirements.txt
chmod +x fetch_models.sh
./fetch_models.sh
```

## TODO

- Summarization, reflection, explanation, background reasoning, RAG: LLAMA 3.1 8B Insttruct (8bit quant)
- For small tasks: TinyLLAMA 1.1B, QWEN 2.5 3B
- Wrap agentic ecosystem in a FastAPI backend and pack using docker
- React frontend for chatting

- Coder + Tools: DeepSeek - Coder 6.7B Instruct (DONE)
- Coordinator: LAMMA 3.1 8B Instruct (8bit quant) (DONE)
- Researcher: Mistral 7b Instruct (DONE)
