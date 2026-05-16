# Communication Protocols Reference

Quick reference for A2A, MCP, and x402 protocols used in the agentic economy.

Last checked against primary public sources: 2026-05-16.

---

## A2A Protocol (Agent-to-Agent)

- **Maintainer:** Linux Foundation A2A project, originated by Google
- **Purpose:** Standardize inter-agent collaboration (the "HTTP of Agents")
- **Built on:** HTTPS transports including JSON-RPC 2.0, gRPC, and HTTP+JSON/REST; SSE is used for streaming on supported HTTP transports.

### Agent Card

The core discovery mechanism. When using the well-known URI strategy, current A2A recommends:

```text
GET /.well-known/agent-card.json
```

A2A Agent Cards should accurately declare supported transports and interfaces. Do not advertise an A2A transport binding unless the corresponding A2A methods are implemented.

```json
{
  "protocolVersion": "0.3.0",
  "name": "invoice-processor",
  "description": "Processes and validates invoice documents",
  "url": "https://agents.example.com/invoice-processor",
  "version": "1.2.0",
  "preferredTransport": "JSONRPC",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "defaultInputModes": ["application/pdf", "image/png", "text/plain"],
  "defaultOutputModes": ["application/json"],
  "skills": [
    {
      "id": "invoice-extraction",
      "name": "Invoice Data Extraction",
      "description": "Extracts structured data from invoice PDFs",
      "inputModes": ["application/pdf", "image/png"],
      "outputModes": ["application/json"]
    }
  ],
  "securitySchemes": {
    "oauth": {
      "type": "oauth2",
      "flows": {
        "clientCredentials": {
          "tokenUrl": "https://auth.example.com/oauth/token",
          "scopes": {
            "invoices:read": "Read invoice documents"
          }
        }
      }
    }
  },
  "security": [{ "oauth": ["invoices:read"] }]
}
```

### Task Lifecycle

```
┌──────────┐    ┌───────────┐    ┌────────────┐    ┌───────────┐
│ submitted│───▶│  working   │───▶│  completed  │    │  failed   │
└──────────┘    └─────┬─────┘    └────────────┘    └───────────┘
                      │                                   ▲
                      │         ┌──────────────┐          │
                      └────────▶│input-required│──────────┘
                                └──────────────┘
```

**Task states:** `submitted` → `working` → `completed` | `failed` | `input-required`

### Message Format (JSON-RPC 2.0)

```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "id": "req-001",
  "params": {
    "id": "task-42",
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "text": "Process this invoice and extract line items"
        }
      ]
    }
  }
}
```

### Artifacts

Artifacts are the **tangible outputs** of a task (documents, images, data). They are incrementally streamed as the task progresses.

### Key Properties

| Property | Description |
|---|---|
| **Opaque agents** | Internal logic, prompts, and tools are never exposed |
| **Framework-agnostic** | Works across LangGraph, CrewAI, AutoGen, etc. |
| **Enterprise-ready** | Built on HTTP(S) transports with declared auth and streaming capabilities |
| **IP protection** | Agents collaborate without revealing implementation |

### Compatibility Rule

If a project supports only an A2A-inspired custom binding, say so directly and publish the exact method coverage. This prevents clients from assuming support for core A2A JSON-RPC task methods that are not implemented.

---

## MCP (Model Context Protocol)

- **Purpose:** Universal bridge between AI models and tools/data/services
- **Solves:** The "AI Integration Paradox" — N models × M tools = N×M custom connectors

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    MCP Host     │     │   MCP Client    │     │   MCP Server    │
│                 │     │                 │     │                 │
│  AI application │◄───▶│  Protocol       │◄───▶│  External       │
│  (IDE, desktop  │     │  translator     │     │  service        │
│   assistant)    │     │                 │     │  (GitHub, Slack, │
│                 │     │                 │     │   database...)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### MCP Server Exposes

| Type | Description | Example |
|---|---|---|
| **Tools** | Executable functions the LLM can call | `search_repos`, `create_issue` |
| **Resources** | File-like data the LLM can read | Config files, database schemas |
| **Prompts** | Pre-built prompt templates | Analysis templates, report formats |

Current MCP guidance also supports resource annotations such as `audience`, `priority`, and `lastModified`, and recommends deterministic tool ordering when the available tool set has not changed. Deterministic ordering helps clients cache tool lists and reduces prompt-cache churn.

### When to Use MCP vs Direct Function Calls

| Scenario | Recommendation |
|---|---|
| General tool integration | ✅ Use MCP |
| Multi-tool orchestration | ✅ Use MCP |
| Reducing hallucinations with live data | ✅ Use MCP |
| Mission-critical steps | ⚠️ Prefer direct function calls |
| Simple, single-tool operations | ⚠️ Direct calls may be simpler |
| Latency-sensitive operations | ⚠️ MCP adds abstraction overhead |

---

## A2A vs MCP: When to Use Each

| Dimension | A2A | MCP |
|---|---|---|
| **Communication** | Agent ↔ Agent | Model ↔ Tool/Data |
| **Discovery** | Agent Cards at `/.well-known/agent-card.json` when using well-known discovery | Server manifests |
| **Use case** | Task delegation between autonomous agents | Connecting LLMs to external capabilities |
| **Abstraction** | High-level (opaque agent collaboration) | Low-level (tool/resource access) |
| **Complementary?** | Yes — an agent can use MCP internally while exposing A2A externally |

> **They are complementary:** An agent uses **MCP** to connect to its tools internally, and **A2A** to collaborate with other agents externally.

---

## x402 HTTP Payments

- **Purpose:** HTTP-native payment negotiation for APIs, data, and autonomous agents.

### Typical Flow

1. Client requests a resource.
2. Resource server responds with HTTP `402 Payment Required` and payment requirements.
3. Client chooses a supported requirement and retries with a payment signature.
4. Resource server verifies locally or through a facilitator.
5. Resource server performs the work and returns the result, optionally with settlement response metadata.

### Current Header Model

| Header | Direction | Purpose |
|---|---|---|
| `PAYMENT-REQUIRED` | Server -> Client | Base64-encoded payment requirement metadata |
| `PAYMENT-SIGNATURE` | Client -> Server | Base64-encoded payment payload proving authorization |
| `PAYMENT-RESPONSE` | Server -> Client | Base64-encoded settlement response metadata |

### Forecasting Usage Rule

Forecasting systems should keep payment advertisement separate from concrete payment transport adapters, and bind any paid authorization to the specific request being fulfilled.

---

## Primary References

- A2A specification: https://a2a-protocol.org/v0.3.0/specification/
- MCP tools specification: https://modelcontextprotocol.io/specification/draft/server/tools
- MCP resources specification: https://modelcontextprotocol.io/specification/2025-06-18/server/resources
- x402 HTTP 402 overview: https://docs.x402.org/core-concepts/http-402
- x402 specification repository: https://github.com/x402-foundation/x402
