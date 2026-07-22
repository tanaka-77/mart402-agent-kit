# Mart402 Agent Kit

Working examples for calling [Mart402](https://mart402.com) — pay-per-call
extraction APIs built for AI agents. Pay per request with
[x402](https://www.x402.org) (USDC on Base). No account. No API key.

**Try everything free first**: the sandbox at
[mart402.dev](https://mart402.dev) runs the identical API on Base Sepolia
(test USDC from the [Circle faucet](https://faucet.circle.com)).

## What the store sells

| Endpoint | What it does | Price |
|---|---|---|
| `POST /v1/extract` | URL -> Markdown + metadata, JS rendering auto | $0.002–$0.006 |
| `POST /v1/parse/quote` -> `/v1/parse` | PDF -> Markdown with hallucination-guarded OCR. Free quote first | $0.004–$0.012/page |
| `POST /v1/verify` | Invoice field verification (tax math, JP registration check-digit) | $0.001 |
| `POST /v1/structured` | Fill YOUR JSON schema from any URL | $0.02 |
| `POST /v1/jp-company` | Japanese company site -> standard profile JSON | $0.02 |

Machine-readable docs: [/catalog](https://mart402.com/catalog) ·
[/llms.txt](https://mart402.com/llms.txt) ·
[/agents.md](https://mart402.com/agents.md) ·
[OpenAPI](https://mart402.com/openapi.json)

## Examples

- [`examples/python/pay_and_parse.py`](examples/python/pay_and_parse.py) —
  quote -> pay -> parse a PDF, then gate on the OCR quality signals.
- [`examples/typescript/extract.ts`](examples/typescript/extract.ts) —
  one paid `fetch` with `x402-fetch`, reading billing headers and receipts.
- [`examples/mcp/config.json`](examples/mcp/config.json) — use Mart402 as a
  remote MCP server (`https://mart402.com/mcp`, streamable HTTP). Also listed
  in the [official MCP registry](https://registry.modelcontextprotocol.io/v0.1/servers?search=mart402).
- [`.github/workflows/selftest.yml`](.github/workflows/selftest.yml) — CI
  action that checks **any** x402 service for spec compliance via the free
  [Market402 self-test](https://market402.com/selftest).

## Why agents pick this store: hallucination-guarded OCR

OCR fails silently: a vision-language model reading messy input returns
fluent text that is simply wrong — sometimes in the wrong language. Mart402
treats that as an API problem. Every `/v1/parse` result carries
machine-actionable quality signals:

```json
{
  "ocr_quality": {"confidence": 0.9, "hallucination_suspected": false, "flags": []},
  "consensus": {
    "verdict": "high_consensus",
    "agreement": 0.83,
    "best_engine": "mistral",
    "segment_support": {
      "checked_segments": 13,
      "weak_segments": [{"support": 0.5, "text": "..."}],
      "least_corroborated": [{"support": 0.5, "text": "..."}]
    }
  }
}
```

- `hallucination_suspected` — script-mismatch and repetition detection
  (the two dominant silent-failure modes, measured on real documents).
- `consensus` — a second, independent engine (traditional OCR, orthogonal
  failure modes to the VLM) cross-checks the read; on detected hallucination
  the output is replaced with the verified read.
- `segment_support` — per-sentence corroboration, so you know **which**
  lines to verify before acting on numbers or legal text. Support is
  corroboration, not correctness; verify low-ranked segments first.

How to consume these signals mechanically is shown in the Python example.
More detail: [mart402.com/ocr](https://mart402.com/ocr).

## Behavior you can rely on

- HTTP 402 challenge on unpaid requests (also on GET and bodyless POST, so
  monitors can see the paywall). Spec-correct v1 `accepts[]` with EIP-712 `extra`.
- Receipts: every paid result carries `X-Receipt-Id`; re-fetch it for free at
  `/v1/receipts/<id>`. Idempotent: re-sending the same payment never
  double-charges.
- Cached results are half price, marked `cache_hit: true`, discounted
  **before** the 402 challenge (never a surprise after payment).
- Machine-readable errors: `{ok, code, retryable, action}`.
- Measured latency and success rates are public at
  [/stats](https://mart402.com/stats) and independently probed by
  [Market402](https://market402.com), the verified index of the 402 economy.

## License

MIT. The examples are intentionally small — copy them into your agent.
