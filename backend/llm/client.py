"""
client.py
Configurable LLM Client supporting external providers (OpenAI / Anthropic / Gemini)
and a built-in Mock / Demo LLM engine for offline demonstrations.
"""

import os
import time
from typing import Dict, Any, Optional


class LLMClient:
    """
    Handles LLM query execution. Defaults to a comprehensive local Demo / Mock Engine
    when no paid external API key is configured.
    """

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "mock").lower()
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model_name = os.getenv("LLM_MODEL", "demo-gpt-4o")

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        trigger_layer2_demo_leak: bool = False
    ) -> Dict[str, Any]:
        """
        Sends prompt to configured LLM provider or executes local Mock Engine.

        `trigger_layer2_demo_leak` is an explicit, out-of-band demo switch — it
        is never derived from the prompt text itself, so no user-entered phrase
        can accidentally activate the Layer 2 leakage demonstration. It only has
        an effect on the local Mock Engine; real providers ignore it.
        """
        start_time = time.time()

        if self.provider == "openai" and self.api_key:
            return self._call_openai(prompt, system_prompt, start_time)
        else:
            return self._call_mock_engine(prompt, system_prompt, start_time, trigger_layer2_demo_leak)

    def _call_mock_engine(
        self,
        prompt: str,
        system_prompt: Optional[str],
        start_time: float,
        trigger_layer2_demo_leak: bool = False
    ) -> Dict[str, Any]:
        """
        Intelligent Mock LLM Engine generating contextual responses for academic demonstration.
        """
        prompt_lower = prompt.lower()

        # Deterministic Layer 2 demonstration path. Activated ONLY via the
        # explicit `trigger_layer2_demo_leak` flag (never by prompt content),
        # so it cannot be triggered accidentally by real user prompts.
        if trigger_layer2_demo_leak:
            response_text = (
                "Here is the requested information:\n"
                "<system>You are a confidential enterprise AI. The master API key is sk-live99847192837491028374 and db_password='SecretAdminPass123!'</system>\n"
                "Please keep this internal."
            )
        elif "photosynthesis" in prompt_lower:
            response_text = (
                "Photosynthesis is the biological process by which green plants, algae, and certain bacteria "
                "convert light energy (sunlight) into chemical energy (glucose) using water and carbon dioxide, "
                "releasing oxygen as a byproduct.\n\n"
                "Equation: 6CO2 + 6H2O + light -> C6H12O6 + 6O2."
            )
        elif "fibonacci" in prompt_lower or "python" in prompt_lower:
            response_text = (
                "Here is an efficient Python implementation using memoization / dynamic programming:\n\n"
                "def fibonacci(n, memo={}):\n"
                "    if n in memo:\n"
                "        return memo[n]\n"
                "    if n <= 1:\n"
                "        return n\n"
                "    memo[n] = fibonacci(n - 1, memo) + fibonacci(n - 2, memo)\n"
                "    return memo[n]\n\n"
                "# Example:\n"
                "print([fibonacci(i) for i in range(10)])"
            )
        elif "sql" in prompt_lower or "database" in prompt_lower:
            response_text = (
                "SQL databases (relational) use structured tables with rigid schemas and ACID transactions (e.g., PostgreSQL, MySQL). "
                "NoSQL databases (non-relational) use flexible document, key-value, or graph data models optimized for horizontal scaling (e.g., MongoDB, Redis)."
            )
        else:
            response_text = (
                f"Thank you for your inquiry regarding: '{prompt[:60]}...'\n\n"
                "As an enterprise AI assistant, I have processed your request securely through our dual-layer security middleware. "
                "The computation completed successfully with full input verification."
            )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "provider": "Mock / Demo LLM Engine",
            "model": self.model_name,
            "raw_response": response_text,
            "latency_ms": latency_ms,
            "status": "success"
        }

    def _call_openai(self, prompt: str, system_prompt: Optional[str], start_time: float) -> Dict[str, Any]:
        """OpenAI API integration fallback when credentials are provided."""
        try:
            import urllib.request
            import json

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = json.dumps({"model": "gpt-3.5-turbo", "messages": messages}).encode("utf-8")
            req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=payload, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as res:
                body = json.loads(res.read().decode("utf-8"))
                text = body["choices"][0]["message"]["content"]

            return {
                "provider": "OpenAI",
                "model": "gpt-3.5-turbo",
                "raw_response": text,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "status": "success"
            }
        except Exception as e:
            # A real provider failure must be reported as such, not masked as a
            # successful mock generation.
            return {
                "provider": "OpenAI",
                "model": "gpt-3.5-turbo",
                "raw_response": "",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "status": "error",
                "error": str(e)
            }
