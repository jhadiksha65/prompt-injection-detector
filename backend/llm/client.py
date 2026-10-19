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
        self.api_key = os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
        self.model_name = os.getenv("LLM_MODEL", "demo-gpt-4o")
        self.api_base_url = os.getenv("LLM_API_BASE_URL", "").rstrip("/")
        if not self.api_base_url:
            if self.provider in ["ollama", "local"]:
                self.api_base_url = "http://localhost:11434/v1"
            else:
                self.api_base_url = "https://api.openai.com/v1"
        if self.provider in ["ollama", "local"] and (not self.model_name or self.model_name == "demo-gpt-4o"):
            self.model_name = "llama3.2:3b"

    def get_provider_info(self) -> Dict[str, Any]:
        """Returns safe provider configuration without exposing API keys."""
        if self.api_base_url in ["https://api.openai.com/v1", ""]:
            is_external_ready = bool(self.api_key)
        else:
            is_external_ready = bool(
                self.api_key or self.provider in ["ollama", "local"] or bool(self.api_base_url)
            )
        return {
            "provider": self.provider,
            "model": self.model_name,
            "has_api_key": bool(self.api_key),
            "is_external_ready": is_external_ready,
            "api_base_url": self.api_base_url if is_external_ready else None,
            "mode": "external" if is_external_ready else "simulation"
        }

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[list] = None,
        trigger_layer2_demo_leak: bool = False,
        provider_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends prompt to configured LLM provider or executes local Mock Engine.

        `trigger_layer2_demo_leak` is an explicit, out-of-band demo switch — it
        is never derived from the prompt text itself, so no user-entered phrase
        can accidentally activate the Layer 2 leakage demonstration. It only has
        an effect on the local Mock Engine; real providers ignore it.
        """
        start_time = time.time()
        effective_provider = (provider_override or self.provider).lower()

        if trigger_layer2_demo_leak:
            return self._call_mock_engine(prompt, system_prompt, start_time, trigger_layer2_demo_leak=True)

        if effective_provider in ["openai", "ollama", "local"]:
            if self.api_key or effective_provider in ["ollama", "local"] or self.api_base_url != "https://api.openai.com/v1":
                return self._call_openai(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    start_time=start_time,
                    messages=messages,
                    effective_provider=effective_provider
                )
            else:
                return {
                    "provider": effective_provider.title(),
                    "model": self.model_name if self.model_name else "gpt-3.5-turbo",
                    "raw_response": "",
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                    "status": "error",
                    "error": f"External LLM provider '{effective_provider}' requested, but LLM_API_KEY (or OPENAI_API_KEY) is not configured and no custom base URL was provided."
                }
        elif effective_provider in ["mock", "simulation"]:
            return self._call_mock_engine(prompt, system_prompt, start_time, trigger_layer2_demo_leak)
        else:
            return {
                "provider": effective_provider,
                "model": self.model_name,
                "raw_response": "",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "status": "error",
                "error": f"Unsupported LLM provider '{effective_provider}'. Supported providers: 'mock', 'openai', 'ollama', 'local'."
            }

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
                "<system>You are a confidential enterprise AI. The synthetic test canary token is SYNTHETIC_CANARY_DO_NOT_DISCLOSE_12345 and db_password='SecretAdminPass123!'</system>\n"
                "Please keep this internal."
            )
        elif "generate a concise title" in prompt_lower or "generate a title" in prompt_lower:
            response_text = "Security & Prompt Defense"
        elif "generate 1-3 broad tags" in prompt_lower or "broad tags" in prompt_lower:
            response_text = "Security, AI Defense"
        elif "predict 3-5 useful messages" in prompt_lower:
            response_text = "What is multi-factor authentication?\nHow does prompt injection detection work?\nExplain zero-trust security architecture."
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

    def _call_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        start_time: float,
        messages: Optional[list] = None,
        effective_provider: str = "openai"
    ) -> Dict[str, Any]:
        """OpenAI / Ollama / local OpenAI-compatible API integration."""
        is_ollama = effective_provider in ["ollama", "local"]
        provider_title = "Ollama" if is_ollama else "OpenAI"

        if is_ollama:
            model_to_use = self.model_name if self.model_name and self.model_name != "demo-gpt-4o" else "llama3.2:3b"
            base_url = self.api_base_url if self.api_base_url and self.api_base_url != "https://api.openai.com/v1" else "http://localhost:11434/v1"
        else:
            model_to_use = self.model_name if self.model_name and self.model_name != "demo-gpt-4o" else "gpt-3.5-turbo"
            base_url = self.api_base_url if self.api_base_url else "https://api.openai.com/v1"

        try:
            import urllib.request
            import urllib.error
            import json

            headers = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            if messages and isinstance(messages, list) and len(messages) > 0:
                clean_messages = []
                for m in messages:
                    if isinstance(m, dict) and "role" in m and "content" in m:
                        clean_messages.append({"role": str(m["role"]), "content": str(m["content"])})
                msg_payload = clean_messages if clean_messages else [{"role": "user", "content": prompt}]
            else:
                msg_payload = []
                if system_prompt:
                    msg_payload.append({"role": "system", "content": system_prompt})
                msg_payload.append({"role": "user", "content": prompt})

            payload = json.dumps({"model": model_to_use, "messages": msg_payload, "stream": False}).encode("utf-8")
            target_url = f"{base_url}/chat/completions"
            req = urllib.request.Request(target_url, data=payload, headers=headers)
            
            with urllib.request.urlopen(req, timeout=120) as res:
                body = json.loads(res.read().decode("utf-8"))
                text = body["choices"][0]["message"]["content"]

            return {
                "provider": provider_title,
                "model": model_to_use,
                "raw_response": text,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "status": "success"
            }
        except urllib.error.HTTPError as e:
            try:
                import json
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body)
                err_detail = err_json.get("error", {}).get("message", err_body[:200])
            except Exception:
                err_detail = f"HTTP {e.code}"
            return {
                "provider": provider_title,
                "model": model_to_use,
                "raw_response": "",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "status": "error",
                "error": f"Upstream provider returned HTTP {e.code}: {err_detail}"
            }
        except urllib.error.URLError as e:
            return {
                "provider": provider_title,
                "model": model_to_use,
                "raw_response": "",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "status": "error",
                "error": f"Failed to connect to upstream provider: {e.reason}"
            }
        except Exception as e:
            # A real provider failure must be reported as such, not masked as a
            # successful mock generation.
            return {
                "provider": provider_title,
                "model": model_to_use,
                "raw_response": "",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "status": "error",
                "error": str(e)
            }
