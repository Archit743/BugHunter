# ABH_Server - MCP Server Documentation

## Overview

**ABH_Server** (Agentic Bug Hunter Server) is a Model Context Protocol (MCP) server that provides tools for document retrieval and utility functions. It uses vector similarity search powered by the `BAAI/bge-base-en-v1.5` embedding model to retrieve relevant RDI documentation for bug detection in semiconductor test code.

---

## Server Configuration

| Property | Value |
|----------|-------|
| **Server Name** | `ABH_Server` |
| **Port** | `8003` |
| **Transport** | SSE (Server-Sent Events) |
| **Endpoint URL** | `http://localhost:8003/sse` |

---

## Available Tools

### 1. `search_documents`

**Purpose**: Searches the indexed RDI documentation using vector similarity retrieval. This is the primary tool for bug detection workflows.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | `string` | Yes | The search query string to find relevant documents. Can include function names, API patterns, or natural language descriptions. |

**Returns**: `list` of dictionaries containing:
| Field | Type | Description |
|-------|------|-------------|
| `text` | `string` | The retrieved document text content |
| `score` | `float` | Similarity score (0.0 to 1.0, higher is more relevant) |

**Example Request**:
```json
{
  "tool": "search_documents",
  "arguments": {
    "query": "rdi.smartVec().vecEditMode() correct usage"
  }
}
```

**Example Response**:
```json
[
  {
    "text": "Use only the VTT mode for editing vectors when rdi.smartVec().label().copyLabel() is used...",
    "score": 0.87
  },
  {
    "text": "vecEditMode accepts TA::VTT or TA::VECD as parameters...",
    "score": 0.72
  }
]
```

**Use Cases**:
- Query function signatures to validate API usage
- Search for parameter constraints and valid values
- Find lifecycle rules (e.g., `RDI_BEGIN`/`RDI_END` ordering)
- Retrieve correct code patterns for comparison

---

### 2. `add`

**Purpose**: Adds two integers together.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `a` | `int` | Yes | First integer operand |
| `b` | `int` | Yes | Second integer operand |

**Returns**: `int` - The sum of `a` and `b`

**Example**:
```json
{
  "tool": "add",
  "arguments": { "a": 5, "b": 3 }
}
// Returns: 8
```

---

### 3. `multiply`

**Purpose**: Multiplies two integers together.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `a` | `int` | Yes | First integer operand |
| `b` | `int` | Yes | Second integer operand |

**Returns**: `int` - The product of `a` and `b`

**Example**:
```json
{
  "tool": "multiply",
  "arguments": { "a": 4, "b": 7 }
}
// Returns: 28
```

---

### 4. `sine`

**Purpose**: Calculates the sine of an angle in degrees.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `a` | `int` | Yes | Angle in degrees |

**Returns**: `float` - The sine value of the angle

**Example**:
```json
{
  "tool": "sine",
  "arguments": { "a": 90 }
}
// Returns: 1.0
```

---

### 5. `list_files_and_folders`

**Purpose**: Lists all files and directories in the server's current working directory.

**Parameters**: None

**Returns**: `list` of strings - Names of files and folders in the current directory

**Example**:
```json
{
  "tool": "list_files_and_folders",
  "arguments": {}
}
// Returns: ["embedding_model", "storage", "mcp_server.py"]
```

---

## Integration with Agentic Systems

### Connecting via MCP Client

```python
from fastmcp import Client

async def connect_to_abh_server():
    client = Client("http://localhost:8003/sse")
    async with client:
        # Search for documentation
        result = await client.call_tool(
            "search_documents",
            {"query": "rdi.port().dc() vForce parameters"}
        )
        return result
```

### Recommended Workflow for Bug Detection

1. **Extract code context** from the input CSV (function names, API calls)
2. **Query `search_documents`** with relevant function signatures or error contexts
3. **Compare retrieved documentation** against the buggy code
4. **Identify discrepancies** (wrong parameters, incorrect order, invalid modes)
5. **Output bug explanation** with line numbers to the result CSV

### Query Optimization Tips

- Include function names explicitly: `"rdi.smartVec().label().copyLabel()"`
- Add context keywords: `"multi-port labels burst execute"`
- Search for specific patterns: `"TA::VTT vs TA::VECD mode"`
- Query error symptoms: `"lifecycle order RDI_BEGIN RDI_END"`

---

## Vector Store Details

| Property | Value |
|----------|-------|
| **Embedding Model** | `BAAI/bge-base-en-v1.5` |
| **Similarity Top-K** | 20 results |
| **Storage Location** | `./server/storage/` |
| **Index Type** | LlamaIndex Vector Store |

---

## Error Handling

The server logs all requests to stdout. If a tool encounters an error:
- `search_documents`: Returns empty list if no matches found
- `list_files_and_folders`: Returns `["Error: <message>"]` on failure
- Math operations: Standard Python exceptions for invalid inputs

---

## Notes

- The server uses SSE transport by default (can be changed to `stdio` if needed)
- All tools are synchronous from the caller's perspective
- The embedding model is loaded from local files in `./embedding_model/`
- Pre-indexed documents are stored in `./storage/` directory
