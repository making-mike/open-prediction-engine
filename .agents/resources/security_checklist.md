# Security Checklist for Agentic Systems

Actionable checklist for securing autonomous AI agent deployments.

Last reviewed: 2026-05-16.

Transfer rule: keep this checklist as the security baseline for new agent-facing repositories, then add project-specific controls for the actual transport, data sensitivity, payment rail, and compliance profile.

---

## 1. Agent Identity

- [ ] Every agent has a **Decentralized Identifier (DID)** — ledger-anchored, self-controlled
- [ ] Each agent carries **Verifiable Credentials (VCs)** issued by a trusted entity
- [ ] Chain-of-trust verification links every agent to a verified human owner
- [ ] DID Documents point to authentication means (no PII stored)
- [ ] Digital signatures provide tamper-proof, offline-verifiable authentication
- [ ] Discovery metadata contains no plaintext secrets or long-lived credentials
- [ ] Runtime provider identity is compared with discovered identity metadata when that metadata is available

---

## 2. Prompt Injection Defense

> OWASP lists prompt injection as `LLM01` in the 2025 Top 10 for LLM Applications.

- [ ] **Identity-Aware Enforcement** — Every agent is a distinct IAM identity
- [ ] **OAuth 2.0 scoped permissions** — Agent access limited strictly to required resources
- [ ] **Input sanitization** — Filter and validate all external inputs before agent processing
- [ ] **System prompt isolation** — Prevent user/external inputs from overriding system instructions
- [ ] **Output validation** — Verify agent outputs conform to expected formats/ranges before execution
- [ ] **Instruction/data separation** — Treat remote documents, provider responses, and tool results as data, not authority
- [ ] **Approval gates** — Require user or policy approval before high-impact, paid, external, or irreversible actions

---

## 3. Credential Management

- [ ] **Credential Injection Middleware** deployed — no long-lived credentials in agent memory
- [ ] **Token rotation** — Short-lived tokens with 1-2 hour rotation
- [ ] **Action validation** — Tokens injected only after validating agent's intended action
- [ ] **No credential storage** in context/memory (extractable via prompt manipulation)
- [ ] **Secret scanning** runs on examples, fixtures, generated files, and documentation
- [ ] **Prompt-visible arguments** never include API keys, private keys, bearer tokens, session cookies, or payment secrets

---

## 4. Deterministic Runtime Policy

- [ ] **Hard spending limits** (e.g., block purchases > $500)
- [ ] **Action blocklists** — Prevent specific actions after suspicious data access
- [ ] **Rate limiting** — Cap agent actions per time period
- [ ] **Scope boundaries** — Agents cannot access resources outside their defined domain
- [ ] **Provider allow-lists** — Remote agents, tools, and providers are configured explicitly
- [ ] **Request/result binding** — Results are rejected when IDs, task intent, provider identity, or expected output metadata do not match the originating request
- [ ] **Transport bounds** — Request bodies, responses, streamed events, idle time, and total execution time have explicit limits
- [ ] **Abort propagation** — Client disconnects and cancellation signals stop downstream work when runtimes can observe them

---

## 5. Adversarial Testing

- [ ] **Red-team exercises** — Simulate agent compromise and prompt injection
- [ ] **Chaos engineering** — Test failure modes before production
- [ ] **Jailbreak testing** — Attempt "ignore previous instructions" attacks
- [ ] **Data exfiltration testing** — Verify agents cannot leak sensitive data
- [ ] **Cascading failure testing** — Verify multi-agent workflows handle compromised agents
- [ ] **Malformed stream testing** — Verify streaming clients reject multiple terminal events, mismatched IDs, oversized events, and post-terminal data
- [ ] **Payment abuse testing** — Verify paid flows enforce spend caps, request binding, and duplicate/replay protections

---

## 6. Hardware Security

### HSM (Hardware Security Module)
- [ ] Root encryption keys stored in HSM
- [ ] Centralized key management
- [ ] Automated key rotation (every 90-365 days)
- [ ] RBAC for key operations

### TEE (Trusted Execution Environment)
- [ ] AI model and dataset encryption during training/inference
- [ ] AMD SEV or Intel TDX for VM-level isolation
- [ ] Attestation reports generated and verified

### Enclave (Intel SGX)
- [ ] PII handling in enclave-isolated functions
- [ ] Inference result signing in enclave
- [ ] Cryptographic operations isolated from main runtime

---

## 7. Privacy & Data Minimization

- [ ] **Selective Disclosure** — Prove attributes without revealing underlying data
- [ ] **Zero-Knowledge Proofs** — Enable proof of truth without data exposure
- [ ] **Data retention policies** — Automated cleanup of agent memory/logs
- [ ] **Data classification** — Label all data by sensitivity level before agent access
- [ ] **Prompt minimization** — Send providers only the context needed for the request
- [ ] **Commitment/reveal workflows** — Use committed requests or equivalent when cleartext prompts do not need to be visible on the wire
- [ ] **Audit-safe logging** — Log request IDs, provider IDs, policy decisions, and hashes before logging full prompts

---

## 8. MCP-Specific Controls

OWASP's MCP Top 10 highlights risks such as token and secret exposure, prompt injection via contextual payloads, shadow MCP servers, and context over-sharing.

- [ ] MCP servers expose the smallest required tool/resource/prompt set
- [ ] Tool lists are deterministic when the underlying authorized set is unchanged
- [ ] Non-read-only, non-idempotent, open-world, paid, or external tools require host approval
- [ ] Resources are annotated and scoped by audience, priority, and sensitivity where supported
- [ ] Stdio servers run under low-privilege users with minimal environment variables
- [ ] Remote MCP servers require TLS, client authentication, authorization, rate limits, and audit logs
- [ ] Shadow MCP servers are inventoried, blocked, or moved under governance

---

## 9. Layered Defense Architecture

```
┌─────────────────────────────────────┐
│         Enclave (Intel SGX)         │  ← PII, signing, attestation
├─────────────────────────────────────┤
│      TEE (AMD SEV / Intel TDX)      │  ← Full AI workload encryption
├─────────────────────────────────────┤
│          HSM (Root Keys)            │  ← Key management, rotation
├─────────────────────────────────────┤
│    Deterministic Runtime Policy     │  ← Hard limits LLM can't bypass
├─────────────────────────────────────┤
│   Credential Injection Middleware   │  ← Short-lived tokens
├─────────────────────────────────────┤
│      IAM + OAuth 2.0 (Scoped)      │  ← Identity-aware enforcement
└─────────────────────────────────────┘
```

> **Goal:** Put critical controls in deterministic layers so failures are blocked, audited, or isolated rather than only discouraged by prompts or policy text.

---

## Primary References

- OWASP Top 10 for LLM Applications: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- OWASP MCP Top 10: https://owasp.org/www-project-mcp-top-10/
- MCP tools specification: https://modelcontextprotocol.io/specification/draft/server/tools
