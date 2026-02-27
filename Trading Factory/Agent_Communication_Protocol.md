## IV. Designing the Agent Communication Protocol
When building this with tools like Gemini 3.1 Pro Code Agent, we need to enforce strict JSON schemas for agent-to-agent communication. 
If the Quant Agent talks to the Risk Agent, the payload must be predictable.

### Example Standardized Signal Payload (JSON):

```
{
  "timestamp": "2026-02-27T17:00:00Z",
  "asset_class": "Equity",
  "ticker": "AAPL",
  "signal_type": "BUY",
  "conviction_score": 0.85,
  "proposed_allocation_usd": 50000,
  "stop_loss": 185.50,
  "take_profit": 198.00,
  "rationale": "Strong positive sentiment from upcoming earnings coupled with a MACD crossover on the 4H chart."
}
```

By standardizing this payload, the Risk Agent can programmatically 
check the proposed_allocation_usd and stop_loss against the portfolio rules 
without needing an LLM to "read" the rationale, saving tokens and vastly reducing latency. 

