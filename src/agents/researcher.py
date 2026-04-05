import json
import ollama
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

from message_bus import MessageBus
from constants import *


class ResearcherAgent:
  """An agent that can search the web to get useful links and information based on user prompts. This agent can also use tools to enhance its capabilities."""

  def __init__(self, bus: MessageBus, model=MISTRAL_INSTRUCT):
    self.model = model
    self.query_model = QWEN
    self.messages = []  # local agent context
    self.bus = bus      # global agent context
    self._url_cache = {}      # url -> extracted text
    self._query_cache = {}    # query -> search results
    self._search_failed = set()  # queries that failed, don't retry

  def create_search_query(self, user_prompt: str):
    prompt = f"""
    You are a helpful assistant that generates concise search queries based on user prompts.

    User question:
    {user_prompt}

    Rules:
    - Return ONLY the raw search query string, nothing else
    - Maximum 8 words
    - Focus on key technical terms only
    - No punctuation, no "how to", no full sentences
    """

    self.bus.log("[researcher]: Generating search query...")
    response = ollama.chat(
      model=self.query_model,
      messages=[{"role": "user", "content": prompt}]
    )
    query = response["message"]["content"].strip().strip('"').strip("'")
    # enforce length
    words = query.split()
    if len(words) > 8:
      query = " ".join(words[:8])
    self.bus.log(f"[researcher] Query: {query}")
    return query

  # TODO: this could be moved to MCP server
  def web_search(self, search_query: str):
    """
    Uses searxng to get relevant links based on the search query.
    Results are cached per query.
    """
    # check cache
    if search_query in self._query_cache:
      self.bus.log(f"[researcher] Using cached results for: {search_query}")
      return self._query_cache[search_query]

    # don't retry failed queries
    if search_query in self._search_failed:
      self.bus.log(f"[researcher] Skipping previously failed query: {search_query}")
      return []

    self.bus.log(f"[researcher] Searching query: {search_query}")
    params = {
      "q": search_query,
      "format": "json"
    }
    headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "Accept": "application/json"
    }

    try:
      response = requests.get(SEARCH_URL, params=params, headers=headers, timeout=15)
      response.raise_for_status()
      data = response.json()
      results = [{"title": result["title"], "url": result["url"]} for result in data.get("results", [])[:MAX_RESULTS]]
      self.bus.log(f"[researcher] Search yielded {len(results)} results")
      self._query_cache[search_query] = results
      return results
    except Exception as e:
      self.bus.log(f"[researcher] Error during web search: {e}")
      self._search_failed.add(search_query)
      return []

  def filter_results(self, results, user_prompt, top_k=3):
    """
    Filters search results using the LLM to select the most relevant links.
    """

    if not results:
      return []

    prompt = f"""
    You are an expert research assistant.

    User question:
    {user_prompt}

    Here are search results:
    {json.dumps(results, indent=2)}

    Select the {top_k} most relevant results for answering the question.

    Return ONLY a JSON list of selected results in the same format:
    [
      {{"title": "...", "url": "..."}}
    ]
    """

    self.bus.log("[researcher] Filtering results...")
    response = ollama.chat(
      model=self.model,
      messages=[{"role": "user", "content": prompt}]
    )

    content = response["message"]["content"]
    try:
      filtered = json.loads(content)
      return filtered[:top_k]
    except:
      self.bus.log("[researcher] Failed to parse filter_results output, fallback to top_k")
      return results[:top_k]

  def _get_content_type(self, url: str) -> str:
    if "docs" in url or "documentation" in url or "reference" in url or "api" in url:
      return "docs"
    if "stackoverflow" in url or "forum" in url or "reddit" in url or "discuss" in url:
      return "forum"
    return "general"

  def _crawl_single(self, url: str) -> tuple:
    """Crawls a single URL and returns (url, text, content_type)."""
    self.bus.log(f"[researcher] Crawling: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
      response = requests.get(url, headers=headers, timeout=10)
      response.raise_for_status()
    except Exception as e:
      self.bus.log(f"[researcher] Error crawling {url}: {e}")
      return (url, "", "general")

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
      tag.decompose()

    article = soup.find("article")
    if article:
      text = article.get_text(separator=" ", strip=True)
    else:
      text = soup.get_text(separator=" ", strip=True)

    text = " ".join(text.split())

    content_type = self._get_content_type(url)
    limit = MAX_CRAWLED_TEXT_DOCS if content_type == "docs" else (MAX_CRAWLED_TEXT_FORUMS if content_type == "forum" else MAX_CRAWLED_TEXT)
    text = text[:limit]

    self.bus.log(f"[researcher] Crawled {url} ({content_type}, {len(text)} chars)")
    return (url, text, content_type)

  def crawl_webpage(self, url: str) -> str:
    """
    Crawls the webpage at the given URL and extracts the main textual content.
    Uses caching to avoid re-crawling.
    """
    if url in self._url_cache:
      self.bus.log(f"[researcher] Using cached content for: {url}")
      return self._url_cache[url]

    _, text, _ = self._crawl_single(url)
    self._url_cache[url] = text
    return text

  def crawl_parallel(self, urls: list, max_workers=MAX_WORKERS) -> dict:
    """Crawl multiple URLs in parallel and return {url: text} for successful crawls."""
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
      futures = {executor.submit(self._crawl_single, url): url for url in urls}
      for future in as_completed(futures):
        url, text, _ = future.result()
        if text and len(text) >= MIN_TEXT_CACHED:
          self._url_cache[url] = text
          results[url] = text
    return results

  def summarize_page(self, text: str, user_prompt: str = "") -> str:
    """
    Summarizes the crawled webpage content into key points relevant for answering a question.
    """
    context = f" to answer: {user_prompt}" if user_prompt else ""
    prompt = f"""
    Summarize the following webpage content into key points{context}.

    Content:
    {text}

    Provide:
    - A short summary
    - 3-5 key bullet points
    """

    response = ollama.chat(
      model=self.model,
      messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]

  def assess_research_quality(self, user_prompt: str, summaries: list) -> dict:
    """Evaluate whether the gathered research is sufficient."""
    prompt = f"""
    You are evaluating the quality and sufficiency of research gathered so far.

    User question:
    {user_prompt}

    Gathered sources:
    {json.dumps(summaries, indent=2)}

    Evaluate:
    1. Do these sources contain enough information to answer the user's question?
    2. Are there any critical gaps?

    Respond only in JSON:
    {{"sufficient": true/false, "gaps": "description of missing information or empty string", "need_more_search": true/false}}
    """

    self.bus.log("[researcher] Assessing research quality...")
    response = ollama.chat(
      model=self.model,
      messages=[{"role": "user", "content": prompt}]
    )

    try:
      return json.loads(response["message"]["content"])
    except:
      return {"sufficient": True, "gaps": "", "need_more_search": False}

  def _llm_fallback_answer(self, user_prompt: str) -> str:
    """When search is unavailable, answer from the model's own knowledge."""
    self.bus.log("[researcher] Falling back to internal knowledge...")
    prompt = f"""
    You are a senior researcher. Web search is currently unavailable.

    Answer the following question using your own knowledge. Be clear about what you know with confidence vs what you're less certain about.

    Question:
    {user_prompt}
    """

    response = ollama.chat(
      model=self.model,
      messages=[{"role": "user", "content": prompt}]
    )
    return "[From internal knowledge — web search unavailable]\n\n" + response["message"]["content"]

  # TODO: use this instead of static workflow research() method
  # Agentic research with tool-calling, limits, and self-check
  def research_agentic(self, user_prompt: str):
    from utils import function_to_tool_schema

    self.bus.log(f"[researcher] Starting agentic research for: {user_prompt}")

    tools = [
      function_to_tool_schema(self.create_search_query),
      function_to_tool_schema(self.web_search),
      function_to_tool_schema(self.filter_results),
      function_to_tool_schema(self.crawl_webpage),
      function_to_tool_schema(self.summarize_page),
    ]

    system_prompt = """
    You are an autonomous research agent.

    Your goal is to answer the user's question by using tools.

    You MUST follow this strategy:
    1. Generate a search query
    2. Search the web
    3. Filter relevant results
    4. Crawl webpages
    5. Summarize content
    6. Combine knowledge into a final answer

    HARD LIMITS:
    - Maximum {max_tool_calls} total tool calls. Use them wisely.
    - Prefer fewer high-quality sources (3 max per search round).
    - Once you have enough information, produce the final answer.
    - Do NOT call the same tool repeatedly with the same arguments.

    Final answer must be well-structured and reference sources (URLs).
    """.format(max_tool_calls=MAX_TOOL_CALLS)

    self.messages = [
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": user_prompt}
    ]

    tool_call_count = 0
    used_tools = set()  # track to avoid repeats

    for iteration in range(MAX_ITERS):
      response = ollama.chat(
        model=self.model,
        messages=self.messages,
        tools=tools
      )
      msg = response["message"]

      # no tool calls = final answer
      if "tool_calls" not in msg or not msg["tool_calls"]:
        self.messages.append(msg)
        self.bus.log(f"[researcher] Final answer after {iteration + 1} iterations, {tool_call_count} tool calls")
        return msg["content"]

      self.messages.append(msg)
      for tool_call in msg["tool_calls"]:
        func_name = tool_call["function"]["name"]
        args = tool_call["function"]["arguments"]

        # Ollama sometimes returns string args
        if isinstance(args, str):
          try:
            args = json.loads(args)
          except:
            args = {}

        # prevent infinite repeat loops
        tool_signature = f"{func_name}:{json.dumps(args, sort_keys=True)}"
        if tool_signature in used_tools:
          self.bus.log(f"[researcher] Skipping duplicate tool call: {tool_signature}")
          continue
        used_tools.add(tool_signature)

        tool_call_count += 1
        if tool_call_count > MAX_TOOL_CALLS:
          self.bus.log(f"[researcher] Max tool calls ({MAX_TOOL_CALLS}) reached, forcing final answer")
          # inject a system message telling the model to answer now
          self.messages.append({
            "role": "system",
            "content": "You have reached the maximum number of tool calls. Produce your final answer now based on what you have gathered."
          })
          response = ollama.chat(
            model=self.model,
            messages=self.messages
          )
          return response["message"]["content"]

        self.bus.log(f"[researcher]: tool call {func_name}({args})")
        method = getattr(self, func_name)
        try:
          if func_name == "filter_results":
            result = method(
              results=args.get("results", []),
              user_prompt=user_prompt,
              top_k=args.get("top_k", 3)
            )
          elif func_name == "summarize_page":
            result = method(
              text=args.get("text", ""),
              user_prompt=user_prompt
            )
          else:
            result = method(**args)
        except Exception as e:
          self.bus.log(f"[researcher] Tool error: {e}")
          result = ""

        self.bus.log(f"[researcher]: tool result: {str(result)[:200]}...")

        self.messages.append({
          "role": "tool",
          "name": func_name,
          "content": json.dumps(result) if not isinstance(result, str) else result
        })

    return "Failed to complete research within iteration limit."

  def research(self, user_prompt: str):
    self.bus.log(f"[researcher] Starting research for: {user_prompt}")

    # search the web
    query = self.create_search_query(user_prompt)
    results = self.web_search(query)

    # fallback when SearXNG is down
    if not results:
      return self._llm_fallback_answer(user_prompt)

    filtered = self.filter_results(results, user_prompt)
    if not filtered:
      filtered = results[:3]  # fallback

    # crawl in parallel
    urls = [res["url"] for res in filtered]
    crawled = self.crawl_parallel(urls)

    # summarize each crawled page
    summaries = []
    for res in filtered:
      url = res["url"]
      text = crawled.get(url, "")
      if not text:
        continue

      summary = self.summarize_page(text, user_prompt)
      summaries.append({
        "title": res["title"],
        "url": url,
        "summary": summary
      })

    if not summaries:
      return self._llm_fallback_answer(user_prompt)

    # assess quality — do a second search round if gaps exist
    quality = self.assess_research_quality(user_prompt, summaries)
    if quality.get("need_more_search") and quality.get("gaps"):
      self.bus.log(f"[researcher] Research has gaps: {quality['gaps']}")
      # second search round targeting the gap
      gap_query = self.create_search_query(f"{user_prompt} — specifically: {quality['gaps']}")
      gap_results = self.web_search(gap_query)
      if gap_results:
        gap_filtered = self.filter_results(gap_results, user_prompt, top_k=2)
        gap_urls = [res["url"] for res in gap_filtered]
        gap_crawled = self.crawl_parallel(gap_urls)
        for res in gap_filtered:
          url = res["url"]
          text = gap_crawled.get(url, "")
          if text:
            summary = self.summarize_page(text, user_prompt)
            summaries.append({
              "title": res["title"],
              "url": url,
              "summary": summary
            })

    # final answer
    final_prompt = f"""
    You are a senior researcher.

    User question:
    {user_prompt}

    Here are summarized sources:
    {json.dumps(summaries, indent=2)}

    Provide a well-structured, accurate answer based on the sources.
    Include references to sources where appropriate.
    """

    response = ollama.chat(
      model=self.model,
      messages=[{"role": "user", "content": final_prompt}]
    )
    response = response["message"]["content"]
    self.bus.log(f"[researcher] Final answer generated ({len(response)} chars)")
    return response
