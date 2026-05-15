from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

import requests


class LLMAssistant:
    """Helper for OpenAI-compatible LLM APIs."""

    DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
    DEFAULT_API_BASE = "https://openrouter.ai/api/v1"
    DEFAULT_FALLBACK_MODELS = ["poolside/laguna-m.1:free"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        system_prompt: Optional[str] = None,
        timeout: int = 120,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.api_base = (api_base or os.environ.get("OPENAI_API_BASE") or self.DEFAULT_API_BASE).rstrip("/")
        self.model = model
        self.fallback_models = self._build_fallback_models()
        self.timeout = timeout
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.history: List[Dict[str, str]] = []

    def _default_system_prompt(self) -> str:
        return (
            "당신은 Android/Linux 커널 디버깅 전문가입니다. "
            "ramdump, vmlinux, 커널 패닉, 레지스터 분석에 능합니다. "
            "기술 용어는 영문 그대로 사용하고, 응답은 한국어로 합니다. "
            "증거 부족 시 추정이라고 명시하세요."
        )

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def reset(self):
        self.history = []

    def ask(self, question: str, context: str = "") -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            messages.append(
                {
                    "role": "user",
                    "content": f"[분석 컨텍스트]\n{context}\n\n[질문]\n{question}",
                }
            )
        else:
            messages.append({"role": "user", "content": question})

        result = self._request_chat(messages)
        return result["content"] if result["ok"] else self._format_error(result)

    def chat(self, message: str) -> str:
        self.history.append({"role": "user", "content": message})
        messages = [{"role": "system", "content": self.system_prompt}, *self.history]
        result = self._request_chat(messages)
        if result["ok"]:
            self.history.append({"role": "assistant", "content": result["content"]})
            return result["content"]
        return self._format_error(result)

    def analyze_findings(self, findings: Dict[str, object], task: str = "이 dump의 핵심 이상 징후를 분석해줘.") -> str:
        context = self._format_findings_context(findings)
        return self.ask(task, context=context)

    def generate_analysis_plan(self, findings: Dict[str, object]) -> str:
        prompt = (
            "이 분석 결과를 바탕으로 다음 단계 조사 계획을 작성해줘. "
            "우선순위, 필요한 추가 데이터, 자동화 가능한 항목을 구분해줘."
        )
        context = self._format_findings_context(findings)
        return self.ask(prompt, context=context)

    def generate_analysis_script(self, task: str, findings: Optional[Dict[str, object]] = None) -> str:
        prompt = (
            "다음 작업을 수행하는 Python 스크립트를 생성해줘. "
            "코드만 출력하고 설명은 주석으로 짧게 달아줘.\n\n"
            f"작업: {task}"
        )
        context = self._format_findings_context(findings) if findings else ""
        return self.ask(prompt, context=context)

    def _format_findings_context(self, findings: Dict[str, object]) -> str:
        return json.dumps(findings, ensure_ascii=False, indent=2)

    def _format_error(self, result: Dict[str, object]) -> str:
        return f"[API 호출 실패] {result.get('error', 'unknown error')}"

    def _build_fallback_models(self) -> List[str]:
        models = []
        env_fallback = os.environ.get("OPENAI_FALLBACK_MODEL", "").strip()
        if env_fallback:
            models.append(env_fallback)
        models.extend(self.DEFAULT_FALLBACK_MODELS)

        deduped = []
        for candidate in models:
            if candidate and candidate != self.model and candidate not in deduped:
                deduped.append(candidate)
        return deduped

    def _request_chat(self, messages: List[Dict[str, str]]) -> Dict[str, object]:
        if not self.api_key:
            return {
                "ok": False,
                "error": "OPENAI_API_KEY is not configured",
                "status_code": None,
                "content": "",
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.3,
        }

        return self._request_with_model_sequence(payload, headers)

    def _request_with_model_sequence(self, payload: Dict[str, object], headers: Dict[str, str]) -> Dict[str, object]:
        models_to_try = [self.model, *self.fallback_models]
        errors = []

        for model_name in models_to_try:
            attempt_payload = dict(payload)
            attempt_payload["model"] = model_name
            result = self._request_single_model(attempt_payload, headers)
            if result["ok"]:
                if model_name != self.model:
                    result["content"] = f"[fallback model: {model_name}]\n{result['content']}"
                return result
            errors.append(f"{model_name}: {result['error']}")

        return {
            "ok": False,
            "error": " | ".join(errors),
            "status_code": None,
            "content": "",
        }

    def _request_single_model(self, payload: Dict[str, object], headers: Dict[str, str]) -> Dict[str, object]:
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return {
                "ok": True,
                "error": None,
                "status_code": response.status_code,
                "content": content,
                "raw": data,
            }
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            body = ""
            if exc.response is not None:
                body = exc.response.text[:400]
            return {
                "ok": False,
                "error": f"HTTP {status_code}: {body or str(exc)}",
                "status_code": status_code,
                "content": "",
            }
        except requests.exceptions.RequestException as exc:
            return {
                "ok": False,
                "error": str(exc),
                "status_code": None,
                "content": "",
            }


def analyze_registers(ai: LLMAssistant, registers: Dict[str, str]) -> str:
    context = "레지스터 덤프:\n" + "\n".join(f"  {reg}: {val}" for reg, val in registers.items())
    return ai.ask("이 레지스터 상태에서 이상 징후를 분석해줘.", context)


def analyze_callstack(ai: LLMAssistant, callstack: str) -> str:
    return ai.ask("이 콜스택을 분석해서 문제의 원인을 추정해줘.", callstack)


def analyze_kernel_panic(ai: LLMAssistant, panic_log: str) -> str:
    return ai.ask("커널 패닉 로그를 분석해서 root cause를 추정해줘.", panic_log)


def generate_analysis_script(ai: LLMAssistant, task: str) -> str:
    return ai.generate_analysis_script(task)
