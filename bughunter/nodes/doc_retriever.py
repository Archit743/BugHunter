"""doc_retriever node - queries the MCP server for RDI documentation."""

from __future__ import annotations

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from bughunter.config import MCP_SERVER_URL
from bughunter.state import BugHunterState


async def _search_mcp(queries: list[str]) -> list[dict]:
    """Connect to the ABH MCP server and search for each query."""
    all_results: list[dict] = []

    client = MultiServerMCPClient(
        {
            "abh_server": {
                "url": MCP_SERVER_URL,
                "transport": "sse",
            }
        }
    )

    tools = await client.get_tools()

    search_tool = None
    for tool in tools:
        if tool.name == "search_documents":
            search_tool = tool
            break

    if search_tool is None:
        print("  search_documents tool not found on MCP server")
        return []

    for query in queries:
        try:
            result = await search_tool.ainvoke({"query": query})
            if isinstance(result, str):
                all_results.append({"text": result, "score": 0.5, "query": query})
            elif isinstance(result, list):
                for doc in result:
                    entry = {"query": query}
                    if isinstance(doc, dict):
                        entry.update(doc)
                    else:
                        entry["text"] = str(doc)
                        entry["score"] = 0.5
                    all_results.append(entry)
            else:
                all_results.append(
                    {"text": str(result), "score": 0.5, "query": query}
                )
        except Exception as e:
            print(f"  MCP search failed for '{query}': {e}")

    return all_results


def doc_retriever_node(state: BugHunterState) -> dict:
    """Query the MCP server for documentation matching extracted APIs."""
    queries = state.get("search_queries", [])
    if not queries:
        apis = state.get("extracted_apis", [])
        queries = [api + " correct usage" for api in apis[:10]]

    if not queries:
        return {"doc_results": []}

    print(f"  Searching MCP server with {len(queries)} queries")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio  # type: ignore
            nest_asyncio.apply()
            results = loop.run_until_complete(_search_mcp(queries))
        else:
            results = asyncio.run(_search_mcp(queries))
    except RuntimeError:
        results = asyncio.run(_search_mcp(queries))

    seen: set[str] = set()
    unique: list[dict] = []
    for r in results:
        txt = r.get("text", "")[:200]
        if txt not in seen:
            seen.add(txt)
            unique.append(r)

    unique.sort(key=lambda x: float(x.get("score", 0)), reverse=True)
    unique = unique[:20]

    print(f"  Retrieved {len(unique)} unique doc chunks")
    return {"doc_results": unique}
