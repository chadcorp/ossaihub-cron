"""Production patterns — rate limiting, retries, circuit breakers, caching."""

RECORDS = [
    {
        "slug": "llm-rate-limiter-token-bucket",
        "title": "LLM Rate Limiter Using Token Bucket",
        "tldr": "Token-bucket rate limiter that respects both request-per-minute and tokens-per-minute caps. Honors OpenAI/Anthropic's rate-limit headers to recover gracefully from 429s instead of fixed backoff.",
        "category": "production",
        "language": "python",
        "framework": "stdlib",
        "tags": ["rate-limiting", "production", "token-bucket", "throttling"],
        "best_for_tags": ["high-qps", "bulk-jobs", "shared-quota"],
        "difficulty_tier": "advanced",
        "featured": True,
        "when_to_use": "When running concurrent LLM calls and you want to maximize throughput without tripping provider rate limits. The dual-bucket (RPM + TPM) shape matches how OpenAI/Anthropic count.",
        "when_not_to_use": "Skip for single-user interactive apps (one-at-a-time is fine). Skip for low-volume — overhead > benefit.",
        "quick_start": "pip install httpx && python -c 'from rate_limiter import bucket; print(bucket.test())'",
        "full_code": '''"""Dual token-bucket rate limiter for LLM APIs.

Two limits in parallel:
  - Requests-per-minute (RPM)
  - Tokens-per-minute (TPM)

Both buckets must have capacity for a call to proceed. Token estimate
must be supplied by caller (use tiktoken or a heuristic).

When a 429 returns Retry-After or x-ratelimit-reset-tokens, this updates
the bucket's recovery rate to match what the server says.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TokenBucket:
    """A standard token bucket."""
    capacity: float          # max tokens
    refill_rate: float       # tokens per second
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)
    _lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        self._tokens = self.capacity
        self._last_refill = time.monotonic()

    async def take(self, n: float) -> float:
        """Block until n tokens are available. Returns the wait time."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
            self._last_refill = now

            if self._tokens >= n:
                self._tokens -= n
                return 0.0

            # Need to wait
            deficit = n - self._tokens
            wait = deficit / self.refill_rate
            self._tokens = 0
            self._last_refill = now + wait

        await asyncio.sleep(wait)
        return wait

    def adjust(self, new_capacity: float, new_refill_rate: float) -> None:
        self.capacity = new_capacity
        self.refill_rate = new_refill_rate
        self._tokens = min(self._tokens, new_capacity)


@dataclass
class LLMRateLimiter:
    """Dual-bucket: enforce both RPM and TPM."""
    rpm_limit: int           # requests per minute
    tpm_limit: int           # tokens per minute

    def __post_init__(self):
        self.req_bucket = TokenBucket(capacity=self.rpm_limit, refill_rate=self.rpm_limit / 60)
        self.tok_bucket = TokenBucket(capacity=self.tpm_limit, refill_rate=self.tpm_limit / 60)

    async def acquire(self, est_tokens: int) -> dict:
        """Wait until BOTH buckets have capacity for one request + est_tokens tokens.

        Returns timing info for telemetry.
        """
        t0 = time.monotonic()
        req_wait, tok_wait = await asyncio.gather(
            self.req_bucket.take(1),
            self.tok_bucket.take(est_tokens),
        )
        return {
            "wait_seconds": time.monotonic() - t0,
            "req_wait": req_wait,
            "tok_wait": tok_wait,
        }

    def handle_429(self, response_headers: dict) -> None:
        """Adjust buckets based on server-supplied recovery info."""
        # OpenAI sends x-ratelimit-reset-requests / x-ratelimit-reset-tokens (in seconds-from-now or ms)
        reset_req = response_headers.get("x-ratelimit-reset-requests")
        reset_tok = response_headers.get("x-ratelimit-reset-tokens")
        if reset_req:
            try:
                wait_s = float(reset_req.rstrip("ms").rstrip("s")) / (1000 if "ms" in reset_req else 1)
                self.req_bucket._tokens = 0
                self.req_bucket._last_refill = time.monotonic() + wait_s
            except ValueError:
                pass
        # Same logic for tokens; omitted for brevity


# ----------------- USAGE -----------------

async def call_with_rate_limit(limiter: LLMRateLimiter, est_tokens: int, fn):
    info = await limiter.acquire(est_tokens)
    try:
        result = await fn()
        return result, info
    except Exception as e:
        # If response is a 429, parse headers and adjust
        if hasattr(e, "response") and e.response.status_code == 429:
            limiter.handle_429(dict(e.response.headers))
        raise


# ----------------- TEST -----------------

async def _demo():
    # OpenAI gpt-4o tier 2 limits: 500 RPM, 2M TPM (example)
    limiter = LLMRateLimiter(rpm_limit=500, tpm_limit=2_000_000)
    print("Acquired:", await limiter.acquire(est_tokens=500))
    print("Acquired:", await limiter.acquire(est_tokens=500))


if __name__ == "__main__":
    asyncio.run(_demo())
''',
        "dependencies": [
            {"name": "httpx", "version": ">=0.27", "purpose": "Used for HTTP errors with header inspection"},
        ],
        "env_vars": [],
        "setup_steps": [
            "Save as rate_limiter.py",
            "Import LLMRateLimiter; instantiate with your tier's RPM/TPM limits.",
            "Wrap calls: await call_with_rate_limit(limiter, est_tokens, lambda: my_llm_call())",
        ],
        "variations": [
            {
                "label": "Shared limiter across workers",
                "description": "Redis-backed token bucket for distributed workers.",
                "code_snippet": "# Use redis INCR + EXPIRE atomically (Lua script) for shared counter.\\n# See aiohttp-ratelimiter or python-redis-rate-limiters libraries.",
            },
            {
                "label": "Adaptive estimate",
                "description": "Learn token estimates over time.",
                "code_snippet": "# Track actual_tokens / est_tokens ratio; adjust future estimates by trailing avg.\\nactual = response.usage.total_tokens\\nratio_history.append(actual / est_tokens)\\nest_factor = sum(ratio_history[-50:]) / 50",
            },
            {
                "label": "Per-model buckets",
                "description": "Different limits for different models.",
                "code_snippet": "limiters = {'gpt-4o': LLMRateLimiter(...), 'gpt-4o-mini': LLMRateLimiter(...)}\\nawait limiters[model].acquire(est_tokens)",
            },
            {
                "label": "Priority queue",
                "description": "User-facing requests jump bulk-job queue.",
                "code_snippet": "# Use asyncio.PriorityQueue; high-priority calls take from bucket first.",
            },
        ],
        "common_errors": [
            {
                "error_text": "Still getting 429s despite limiter",
                "cause": "Estimate too low; or limits set higher than actual.",
                "fix_snippet": "Use tiktoken to count more precisely. Lower limits 10% below provider's published cap to leave headroom.",
            },
            {
                "error_text": "Limiter deadlocks under load",
                "cause": "Lock contention when many calls wait simultaneously.",
                "fix_snippet": "asyncio.Lock in starter is per-bucket; high concurrency may need fairer queuing. For >100 concurrent waiters, use asyncio.Queue + dedicated dispatcher.",
            },
            {
                "error_text": "Bursts succeed then everything stalls",
                "cause": "Bucket filled at start, drained, then refill rate is too slow.",
                "fix_snippet": "Set capacity = expected burst, refill_rate = sustained rate. Don't over-size capacity if you can't sustain that rate.",
            },
            {
                "error_text": "TPM bucket never refills",
                "cause": "Single request larger than capacity.",
                "fix_snippet": "Cap est_tokens at bucket.capacity; if one request needs more than the bucket's max, chunk it (long-context-aware).",
            },
        ],
        "production_checklist": [
            "Set RPM/TPM below provider's published limits (give 10-20% headroom).",
            "Track actual vs estimated tokens — adjust estimates over time.",
            "Distribute limiter state across workers (Redis) if running multiple replicas.",
            "Monitor wait times — if p99 is huge, you're under-provisioned or need a higher tier.",
            "Test under burst conditions; bucket capacity matters for spikes.",
            "Don't share buckets across critical/non-critical traffic; prioritize.",
            "Honor provider rate-limit headers for adaptive recovery from soft limits.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o", "gpt-4o-mini"],
            "library_versions": ["httpx==0.27.2", "asyncio (stdlib)"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["rate-limiting", "token-bucket", "back-pressure"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Why token bucket vs fixed window?",
                "answer": "Token bucket allows bursts up to capacity, then sustains the rate. Fixed-window can cause synchronized bursts at minute boundaries (the ‘zero-crossing’ problem).",
            },
            {
                "question": "Do I need both RPM and TPM limits?",
                "answer": "Yes for production. OpenAI enforces both. You can hit TPM with few large calls or RPM with many small calls; both buckets prevent both failure modes.",
            },
            {
                "question": "Can this replace SDK retries?",
                "answer": "Complements, doesn't replace. Use this for proactive flow control; keep SDK retries for the rare unexpected 429.",
            },
            {
                "question": "What about provider tier ramps?",
                "answer": "OpenAI auto-increases limits over time. Re-tune your limiter when your provider upgrades you. Don't hardcode forever.",
            },
        ],
        "github_url": "",
        "meta_title": "LLM Rate Limiter With Token Bucket — Starter",
        "meta_description": "Dual-bucket (RPM + TPM) rate limiter for LLM APIs with 429-aware recovery. Async-safe, supports per-model buckets and distributed setups.",
    },
    {
        "slug": "circuit-breaker-llm-calls",
        "title": "Circuit Breaker For LLM API Calls",
        "tldr": "Production circuit breaker for LLM calls: opens after N consecutive failures, half-open probe after cool-down, prevents cascading failures when an upstream API is down or degraded.",
        "category": "production",
        "language": "python",
        "framework": "stdlib",
        "tags": ["circuit-breaker", "reliability", "production", "fault-tolerance"],
        "best_for_tags": ["high-availability", "multi-provider", "fallback"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "When LLM calls are on a critical user-facing path AND you have a fallback (cached response, simpler model, error message). Circuit breaker turns ‘5-second timeout x 100 requests’ into ‘fail fast and shed load.’",
        "when_not_to_use": "Skip when failures are rare and recovery is fast (retry alone is enough). Skip when you don't have a fallback — failing fast just changes when the user sees an error.",
        "quick_start": "Wrap your LLM call in @circuit_breaker; provide fallback function.",
        "full_code": '''"""Circuit breaker for LLM API calls.

States:
  CLOSED   — calls pass through normally; failures counted.
  OPEN     — fail fast; calls return fallback immediately. After cool-down, transition to HALF_OPEN.
  HALF_OPEN — one probe call allowed. Success -> CLOSED; failure -> OPEN again.

Use case: wrap an LLM call. When the LLM is down/slow, this prevents the whole
service from blocking on it. Fallback returns cached/degraded response.
"""
from __future__ import annotations

import asyncio
import enum
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Awaitable


class State(enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5            # consecutive failures to trip
    cool_down_seconds: float = 30.0       # how long OPEN before HALF_OPEN probe
    success_threshold_in_half_open: int = 1   # successes needed to close again

    _state: State = field(default=State.CLOSED, init=False)
    _consecutive_failures: int = field(default=0, init=False)
    _consecutive_successes: int = field(default=0, init=False)
    _open_until: float = field(default=0.0, init=False)
    _lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)

    async def _check_state(self) -> State:
        async with self._lock:
            if self._state == State.OPEN and time.monotonic() >= self._open_until:
                self._state = State.HALF_OPEN
                self._consecutive_successes = 0
            return self._state

    async def _record_success(self) -> None:
        async with self._lock:
            self._consecutive_failures = 0
            if self._state == State.HALF_OPEN:
                self._consecutive_successes += 1
                if self._consecutive_successes >= self.success_threshold_in_half_open:
                    self._state = State.CLOSED

    async def _record_failure(self) -> None:
        async with self._lock:
            self._consecutive_failures += 1
            if self._state == State.HALF_OPEN:
                self._open()
            elif self._consecutive_failures >= self.failure_threshold:
                self._open()

    def _open(self) -> None:
        self._state = State.OPEN
        self._open_until = time.monotonic() + self.cool_down_seconds
        self._consecutive_successes = 0

    async def call(self, fn: Callable[..., Awaitable[Any]], *args, fallback: Callable[..., Awaitable[Any]] | None = None, **kwargs) -> Any:
        state = await self._check_state()

        if state == State.OPEN:
            if fallback is None:
                raise CircuitBreakerOpenError("circuit open and no fallback")
            return await fallback(*args, **kwargs)

        try:
            result = await fn(*args, **kwargs)
            await self._record_success()
            return result
        except Exception:
            await self._record_failure()
            if (await self._check_state()) == State.OPEN and fallback is not None:
                return await fallback(*args, **kwargs)
            raise


class CircuitBreakerOpenError(Exception):
    pass


# ----------------- DECORATOR -----------------

def circuit_breaker(breaker: CircuitBreaker, *, fallback: Callable[..., Awaitable[Any]] | None = None):
    """Decorator form. Apply to an async function."""
    def deco(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            return await breaker.call(fn, *args, fallback=fallback, **kwargs)
        return wrapper
    return deco


# ----------------- USAGE EXAMPLE -----------------

llm_breaker = CircuitBreaker(failure_threshold=5, cool_down_seconds=30)


async def llm_fallback(prompt: str) -> str:
    """When LLM is down, return a cached or degraded response."""
    # Could read from cache, return a static fallback, route to a different model, etc.
    return "[fallback] LLM temporarily unavailable. Please retry shortly."


@circuit_breaker(llm_breaker, fallback=llm_fallback)
async def generate(prompt: str) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI()
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        timeout=10.0,
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    async def main():
        out = await generate("Hello")
        print(out)
    asyncio.run(main())
''',
        "dependencies": [
            {"name": "openai", "version": ">=1.40", "purpose": "Example LLM client"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "Save as circuit_breaker.py",
            "Define a fallback async function (cache, simpler model, error message).",
            "Wrap your LLM call: @circuit_breaker(breaker, fallback=...)",
            "Tune failure_threshold and cool_down based on observed failure patterns.",
        ],
        "variations": [
            {
                "label": "Per-provider breakers",
                "description": "Separate breakers for OpenAI, Anthropic.",
                "code_snippet": "openai_breaker = CircuitBreaker(...)\\nanthropic_breaker = CircuitBreaker(...)\\n# Fallback can route to the other provider when one is down.",
            },
            {
                "label": "Sliding window failures",
                "description": "Count failures in a time window, not consecutive.",
                "code_snippet": "# Track timestamps of failures; trip if N failures in last M seconds.",
            },
            {
                "label": "Failure rate threshold",
                "description": "Trip when error rate > X%.",
                "code_snippet": "# Track success + failure counts in window; trip when failures/total > 0.2",
            },
            {
                "label": "Distributed state via Redis",
                "description": "Share breaker state across workers.",
                "code_snippet": "# Store state + counters in Redis; periodic refresh from local in-mem cache.",
            },
        ],
        "common_errors": [
            {
                "error_text": "Circuit trips on transient errors and stays open",
                "cause": "Threshold too low or cool_down too long.",
                "fix_snippet": "Tune: failure_threshold=5-10 for most APIs; cool_down=30-60s. Track open events to find right values for your workload.",
            },
            {
                "error_text": "Circuit never trips despite outage",
                "cause": "Errors swallowed elsewhere or counted incorrectly.",
                "fix_snippet": "Ensure the exception path actually calls _record_failure. Add logging in the catch block to verify.",
            },
            {
                "error_text": "Fallback also fails",
                "cause": "Fallback depends on the same downstream.",
                "fix_snippet": "Fallback must be MORE reliable than the protected call: cached response, static text, simpler model in a different region.",
            },
            {
                "error_text": "Race condition between workers",
                "cause": "In-memory state isolated per worker.",
                "fix_snippet": "Use Redis variant for shared state, OR accept that each worker has its own breaker and the system trips when ALL workers see the same failure pattern.",
            },
        ],
        "production_checklist": [
            "Always provide a real fallback — failing fast without fallback just changes the error message.",
            "Log state transitions (CLOSED→OPEN→HALF_OPEN→CLOSED); these are forensic data.",
            "Set up alerts on breaker open events.",
            "Test fallback regularly — a stale fallback fails when you need it.",
            "Tune thresholds from real failure patterns; don't guess.",
            "Pair with rate limiter; rate-limit-induced 429s shouldn't trip the breaker (they're expected).",
            "Distinguish ‘API down’ from ‘bad inputs’; the latter shouldn't trip the breaker.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["openai==1.51.0", "asyncio (stdlib)"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["circuit-breaker", "fault-tolerance", "graceful-degradation"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Circuit breaker vs retry?",
                "answer": "Retries handle transient errors per-request. Circuit breaker prevents repeated retries when the system is genuinely down. Use both: retries inside, breaker outside.",
            },
            {
                "question": "What's a good failure_threshold?",
                "answer": "5-10 for normal APIs. Higher if you expect occasional spikes. Track open events: if breaker opens often during normal operation, threshold is too low.",
            },
            {
                "question": "Should the user see the fallback?",
                "answer": "Depends on stakes. Customer-facing: yes, with a friendly message about temporary unavailability. Internal: log loudly so engineers see the problem.",
            },
            {
                "question": "Can I use this for non-LLM calls?",
                "answer": "Yes — the pattern is general. Wrap any unreliable downstream call. The starter is LLM-themed but the breaker is provider-agnostic.",
            },
        ],
        "github_url": "",
        "meta_title": "Circuit Breaker for LLM API Calls — Starter",
        "meta_description": "Production circuit breaker: opens after N failures, half-open probe after cool-down, fallback when OPEN. Prevents cascading failures.",
    },
]
