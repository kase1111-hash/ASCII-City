# Agentic Security Audit v3.0 — ShadowEngine (ASCII-City)

```
AUDIT METADATA
  Project:       ShadowEngine (ASCII-City)
  Date:          2026-03-12
  Auditor:       claude-opus-4-6
  Commit:        8036c5da17f8bb115a8c09e520e88133d72348a0
  Strictness:    STANDARD
  Context:       PROTOTYPE

PROVENANCE ASSESSMENT
  Vibe-Code Confidence:   72%
  Human Review Evidence:  MINIMAL

LAYER VERDICTS
  L1 Provenance:       WARN
  L2 Credentials:      PASS
  L3 Agent Boundaries: WARN
  L4 Supply Chain:     PASS
  L5 Infrastructure:   PASS
```

---

## L1: PROVENANCE & TRUST ORIGIN — WARN

### 1.1 Vibe-Code Detection

- [x] **No security config**: No `.env.example`, no secrets management docs, no auth middleware
- [x] **AI boilerplate**: 113 tutorial-style comments ("Step 1:", "Here we define"), 96 section divider comments (`# ====`), 443 formulaic test docstrings
- [x] **Rapid commit history**: 83/128 commits (65%) authored by "Claude" with formulaic messages ("Add X", "Fix Y", "Phase N: Z"). Zero reverts, near-zero debugging commits
- [x] **Polished README, hollow periphery**: Honest status table in README, but 40K+ lines in `_deferred/` that are fully built, fully tested, and completely disconnected from any running code path
- [x] **Robotic naming uniformity**: 500+ classes all PascalCase, 48 factory functions all `create_` prefix, zero naming drift across 267 files — inhuman consistency for a multi-contributor project

**Not triggered:**
- [ ] **No tests**: 3,879 test functions exist (though quality is uneven)
- [ ] **Bloated deps**: Only pytest required; optional deps properly commented out

**Severity:** WARN — Multiple vibe-code indicators present, but no credentials/PII/payment handling. The core engine (LLM client, command routing, memory, dialogue) has genuine depth. Peripheral systems are decorative.

### 1.2 Human Review Evidence

- [x] Security-focused commits exist (vibe-check remediation in commits `2361808`, `19864a3`)
- [ ] No security tooling in CI/CD — no CI/CD exists at all
- [x] `.gitignore` excludes `saves/`, `*.save`, `.coverage`, IDE files, `__pycache__`
- [ ] `.gitignore` does NOT exclude `.env` files (though none are committed)

**Evidence:** 45 commits from "Kase" / "Kase Branham" (merge commits + some direct). Prior vibe-check audit exists (`VIBE_CHECK_REPORT.md`) with remediation completed. This shows at least one cycle of human-directed review.

### 1.3 The "Tech Preview" Trap

- [ ] No production traffic or real users — this is a local terminal game
- [ ] No real credentials handled in normal operation (OpenAI key is optional, read from env)
- [ ] No disclaimers shifting security responsibility

**Assessment:** Not applicable. This is a prototype terminal game, not a deployed service.

---

## L2: CREDENTIAL & SECRET HYGIENE — PASS

### 2.1 Secret Storage

- [x] **No plaintext credentials in files**: Zero hardcoded API keys, tokens, or passwords found in source
- [x] **No secrets in git history**: No committed `.env` files, no API keys in any source file
- [x] **API key read from environment**: `LLMConfig.from_env()` reads `OPENAI_API_KEY` from `os.environ` only (`llm/client.py:49`)
- [ ] No `.env.example` documenting expected environment variables

**Evidence scanned:**
- All 116 source files searched for patterns: `sk-`, `api_key =`, `password =`, `token =`, `secret =`
- Only hits are in the `LLMConfig` dataclass field declaration (`api_key: Optional[str] = None`) and the `os.environ.get("OPENAI_API_KEY")` call — both correct patterns
- No `.env` files committed (confirmed via glob)

### 2.2 Credential Scoping & Lifecycle

- [x] API key is optional (Ollama backend is default and requires no key)
- [x] Key is scoped to a single client instance (`OpenAIClient`)
- [ ] No rotation mechanism (not needed for a local game)
- [x] No credential aggregation risk — single-user terminal application

### 2.3 Machine Credential Exposure

- [x] API key transmitted only over HTTPS to `api.openai.com` (`client.py:245`)
- [x] Key stored only in memory (from env var), never serialized to disk
- [ ] No spend limits or billing alerts — but this is the user's own API key for a local game
- [x] No OAuth tokens, no shared master keys

**Finding:**

```
[LOW] — Missing .env.example for environment variables
Layer:     2
Location:  project root (missing file)
Evidence:  LLMConfig.from_env() reads 7 environment variables but no .env.example documents them
Risk:      Developer confusion; no guidance on which env vars are expected
Fix:       Add .env.example listing LLM_BACKEND, LLM_MODEL, OLLAMA_HOST, OPENAI_API_KEY,
           LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_TIMEOUT with placeholder values
```

---

## L3: AGENT BOUNDARY ENFORCEMENT — WARN

### 3.1 Agent Permission Model

This layer evaluates the LLM integration as the "agent" — the game's LLM backend generates locations, dialogue, and interprets free-form player commands.

- [x] **Default permissions: constrained** — LLM output is parsed as JSON and validated against schemas before use (`validation.py:20-76`). LLM cannot execute arbitrary code.
- [x] **No privilege escalation**: LLM responses are validated through `validate_location_response()`, `validate_npc()`, `validate_hotspot()`, `validate_free_exploration_response()`. Invalid responses fall back to templates.
- [x] **Bounded capabilities**: LLM can only generate text within predefined schemas. File system access is limited to save/load in `saves/` directory.
- [ ] **No human-in-the-loop gates**: LLM-generated locations and NPCs are accepted automatically after schema validation. No human confirmation step.

### 3.2 Prompt Injection Defense

- [x] **Player input sanitized**: `sanitize_player_input()` (`validation.py:194-225`) truncates to 500 chars, strips control characters, detects 10 injection marker phrases
- [x] **Output validated against schemas**: `safe_parse_json()` extracts JSON and applies validators
- [x] **System/user separation**: System prompts and player input are passed as separate parameters to LLM (`client.py:144-146`)
- [ ] **Limited injection marker list**: Only 10 phrases detected. Advanced jailbreak techniques (role-play injection, language switching, encoded payloads) are not covered
- [ ] **Injection only logged, not blocked**: When injection is detected, input is prefixed with `[player typed the following game command]:` but still sent to LLM (`validation.py:221-222`)

**Findings:**

```
[MEDIUM] — Prompt injection detected but not blocked
Layer:     3
Location:  src/shadowengine/llm/validation.py:217-222
Evidence:  When injection markers are detected, the input is prefixed with a warning
           tag but still forwarded to the LLM: text = f"[player typed the following
           game command]: {text}"
Risk:      Sophisticated injection payloads can still reach the LLM. In a game context,
           the impact is limited (LLM can only produce JSON within schema), but the
           defense is incomplete.
Fix:       Consider rejecting inputs with injection markers entirely, or add a stronger
           framing prompt that instructs the LLM to treat all player input as
           in-character dialogue only.
```

```
[LOW] — Limited prompt injection marker coverage
Layer:     3
Location:  src/shadowengine/llm/validation.py:180-191
Evidence:  Only 10 English injection phrases covered. No coverage for: Unicode
           homoglyphs, base64-encoded instructions, role-play injection ("pretend
           you are"), language-switching attacks, or token-boundary exploits.
Risk:      Low for a local game — attacker is the player themselves. But if the game
           ever accepts external input (multiplayer, shared scenarios), this becomes
           significant.
Fix:       Acceptable for current prototype context. Document the limitation.
```

### 3.3 Memory Poisoning

- [x] **Long-term memory exists**: Three-layer memory system (world, character, player) persists across sessions via save/load
- [ ] **No source attribution on memories**: Memory entries don't track whether they came from LLM generation, player action, or system events
- [x] **Memory can be audited**: Save files are JSON and human-readable
- [ ] **No memory isolation**: All LLM-generated content (locations, NPC dialogue) feeds into the same memory pool that shapes future LLM prompts

**Finding:**

```
[LOW] — LLM-generated content feeds back into LLM context without provenance tracking
Layer:     3
Location:  src/shadowengine/world_state.py, src/shadowengine/memory/
Evidence:  LLM-generated locations, NPC dialogue, and events are recorded in memory
           and fed back as context for future LLM calls. No distinction between
           system-established facts and LLM-hallucinated content.
Risk:      In a game context this is by design (emergent storytelling). But it means
           a single bad LLM generation can cascade through future generations.
Fix:       Consider tagging memory entries with source (system vs. generated) and
           weighting system-established facts higher in context.
```

### 3.4 Agent-to-Agent Trust

Not applicable — single LLM backend, no multi-agent architecture.

---

## L4: SUPPLY CHAIN & DEPENDENCY TRUST — PASS

### 4.1 Plugin/Skill Supply Chain

Not applicable — no plugin system in active code. The deferred modding system (`_deferred/modding/`) exists but is disconnected.

### 4.2 MCP Server Trust

Not applicable — no MCP servers.

### 4.3 Dependency Audit

- [x] **Minimal dependencies**: Only `pytest>=7.0.0` and `pytest-cov>=4.0.0` required
- [x] **Core game has zero external runtime dependencies** — Python stdlib only
- [ ] **Version ranges used** (`>=7.0.0`), not pinned versions — acceptable for a prototype
- [ ] **No `pip-audit` or equivalent in CI** — no CI exists
- [x] **Optional deps properly commented out**: numpy, sounddevice, whisper, openai, pyttsx3, coqui-tts
- [ ] **No lock file** (`requirements.lock` or equivalent)

**Finding:**

```
[LOW] — No dependency lock file
Layer:     4
Location:  requirements.txt
Evidence:  Dependencies use >= version ranges with no lock file for reproducible builds
Risk:      Non-reproducible installs; transitive dependency changes could introduce
           vulnerabilities. Low risk given only 2 runtime deps (pytest ecosystem).
Fix:       Add pip-compile or pip freeze output for reproducible testing environments.
```

---

## L5: INFRASTRUCTURE & RUNTIME — PASS

### 5.1 Database Security

Not applicable — no database. Game state stored as local JSON files in `saves/`.

**Save file security:**
- [x] Config deserialization uses allowlist: `GameConfig.load()` filters through `_VALID_FIELDS` (`config.py:114-136`)
- [x] Memory bank load validates required keys (added in remediation commit `2361808`)
- [ ] No file integrity verification (hash/checksum) on save files

```
[LOW] — Save files accepted without integrity verification
Layer:     5
Location:  src/shadowengine/config.py:124-136, src/shadowengine/memory/memory_bank.py
Evidence:  Save files are loaded and parsed without verifying integrity. A tampered
           save file with valid JSON structure but malicious content would be accepted.
Risk:      Low — this is a single-player local game. The attacker would be tampering
           with their own save file. Schema validation mitigates the worst cases.
Fix:       Optional: add HMAC or checksum to save files for integrity verification.
```

### 5.2 BaaS Configuration

Not applicable — no BaaS.

### 5.3 Network & Hosting

- [x] **HTTPS for OpenAI**: `OpenAIClient` defaults to `https://api.openai.com/v1` (`client.py:245`)
- [ ] **HTTP for Ollama**: Default `http://localhost:11434` — acceptable for localhost
- [x] **Timeouts enforced**: 5s for availability checks, configurable (default 30s) for generation (`client.py:122,157`)
- [ ] **No rate limiting** on LLM calls — acceptable for local single-user game
- [x] **No error message information leakage to external parties** — terminal-only output

### 5.4 Deployment Pipeline

- [ ] **No CI/CD pipeline** — no `.github/workflows/`, no Jenkins, no GitLab CI
- [ ] **No automated testing on push**
- [ ] **No automated security scanning**

```
[MEDIUM] — No CI/CD pipeline or automated testing
Layer:     5
Location:  project root (missing .github/workflows/)
Evidence:  No CI/CD configuration exists. Tests run manually only. No automated
           security scanning (semgrep, bandit, pip-audit).
Risk:      Regressions and security issues can be introduced without detection.
           Given the 92% AI-authored commit history, automated checks are
           especially important as a safety net.
Fix:       Add GitHub Actions workflow with: pytest, pip-audit, basic linting.
```

### 5.5 Regulatory Compliance

Not applicable — no PII, no medical/financial data, no deployed service.

---

## FINDINGS SUMMARY

| # | Severity | Title | Layer | Location |
|---|----------|-------|-------|----------|
| 1 | **MEDIUM** | Prompt injection detected but not blocked | L3 | `validation.py:217-222` |
| 2 | **MEDIUM** | No CI/CD pipeline or automated testing | L5 | project root |
| 3 | LOW | Missing `.env.example` for environment variables | L2 | project root |
| 4 | LOW | Limited prompt injection marker coverage | L3 | `validation.py:180-191` |
| 5 | LOW | LLM output feeds back into context without provenance | L3 | `world_state.py`, `memory/` |
| 6 | LOW | No dependency lock file | L4 | `requirements.txt` |
| 7 | LOW | Save files accepted without integrity verification | L5 | `config.py`, `memory_bank.py` |

**CRITICAL findings: 0**
**HIGH findings: 0**

---

## CONTEXT-ADJUSTED ASSESSMENT

This audit evaluates ShadowEngine as a **PROTOTYPE** — a local, single-player terminal game with optional LLM integration. The threat model is:

- **Attacker = Player**: The only external input comes from the player typing commands. There is no network-facing attack surface (except outbound LLM API calls).
- **No multi-user**: No authentication, no authorization, no shared state.
- **No deployment**: No hosting, no CI/CD, no production environment.
- **LLM is the agent**: The Ollama/OpenAI backend generates game content. Its output is schema-validated before use.

Given this context:

**What's working well:**
- Zero hardcoded secrets. API key read from env only.
- Prompt injection defense exists and is tested (even if imperfect).
- LLM responses validated against schemas with fallbacks.
- Config deserialization uses an allowlist.
- All file I/O uses context managers. Zero leaked handles.
- Minimal dependency footprint (stdlib + pytest).
- Honest documentation about what works and what doesn't.

**What needs attention before any production/multiplayer use:**
- Prompt injection defense should block rather than tag-and-forward.
- CI/CD with automated testing and security scanning.
- Memory provenance tracking for LLM-generated vs. system content.
- `.env.example` and dependency pinning for reproducible setups.

**Vibe-code reality check:**
The previous audit (`VIBE_CHECK_REPORT.md`) scored vibe-code confidence at 47%. After reviewing the full commit history (now 128 commits, 65% Claude-authored), the tutorial-style comments, and the 40K+ lines of deferred dead code, I assess **72% vibe-code confidence**. The core engine is genuine and functional, but the bulk of the codebase was AI-generated without deep human review. The remediation cycle from the v2.0 audit shows the owner is actively addressing this — which is the right trajectory.

---

## INCIDENT RELEVANCE CHECK

| Incident | Relevance to ShadowEngine |
|----------|--------------------------|
| Moltbook DB exposure | **Not relevant** — no database, no Supabase, no RLS |
| OpenClaw supply chain | **Not relevant** — no plugin marketplace, no unsigned skills |
| Moltbook agent-to-agent | **Not relevant** — single LLM backend, no multi-agent |
| SCADA prompt injection | **Low relevance** — prompt injection defense exists but is incomplete. No physical equipment risk. |
| MCP sampling exploits | **Not relevant** — no MCP servers |
| ZombAI botnet recruitment | **Not relevant** — LLM is outbound only, no agent autonomy beyond schema-validated game content |

---

*Audit performed using the [Agentic Security Audit v3.0](https://github.com/kase1111-hash/Claude-prompts/blob/main/vibe-check.md) framework. CC0 1.0 Universal.*
