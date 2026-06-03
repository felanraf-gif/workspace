"""
integrations/llm.py - Integracja z LLM (Groq / OpenAI / Anthropic)
Umożliwia lepsze rekomendacje oparte na AI
"""

import os
import json
from typing import Optional


class LLM:
    """Komunikuje się z LLM API dla inteligentnych rekomendacji."""
    
    PROVIDERS = {
        "groq": {
            "api_url": "https://api.groq.com/openai/v1/chat/completions",
            "default_model": "llama-3.1-8b-instant",
            "models": ["llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"]
        },
        "openai": {
            "api_url": "https://api.openai.com/v1/chat/completions",
            "default_model": "gpt-4o-mini",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
        },
        "anthropic": {
            "api_url": "https://api.anthropic.com/v1/messages",
            "default_model": "claude-3-5-sonnet-20241022",
            "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
        }
    }
    
    def __init__(self, provider: str = "groq"):
        self.provider = provider
        
        self.api_key = None
        configured_model = None
        
        try:
            from core.config import GROQ_API_KEY
            self.api_key = self.api_key or GROQ_API_KEY
        except (ImportError, AttributeError):
            pass
        
        try:
            from core.config import LLM_MODEL
            configured_model = LLM_MODEL
        except (ImportError, AttributeError):
            pass
        
        self.api_key = self.api_key or os.environ.get("GROQ_API_KEY")
        
        config = self.PROVIDERS.get(provider, self.PROVIDERS["groq"])
        self.model = configured_model or config["default_model"]
        self.api_url = config["api_url"]
        
        if not self.api_key:
            print("[LLM] ⚠️ Brak API key - ustaw GROQ_API_KEY w core/config.py")
            self.available = False
        else:
            self.available = True
    
    def is_available(self) -> bool:
        """Sprawdza czy LLM jest dostępny."""
        return self.available
    
    def generate_recommendation(self, context: dict) -> Optional[str]:
        """Generuje rekomendację na podstawie kontekstu."""
        if not self.available:
            return None
        
        prompt = self._build_recommendation_prompt(context)
        
        if self.provider == "groq":
            return self._call_groq(prompt)
        elif self.provider == "openai":
            return self._call_openai(prompt)
        else:
            return self._call_anthropic(prompt)
    
    def analyze_code(self, code: str, task: str) -> Optional[dict]:
        """Analizuje kod i zwraca sugestie."""
        if not self.available:
            return None
        
        prompt = f"""Przeanalizuj ten kod i zaproponuj konkretne ulepszenia:

Kod:
```{code}```

Zadanie: {task}

Odpowiedz w formacie JSON:
{{
    "suggestions": ["lista konkretnych sugestii"],
    "priority": "HIGH/MEDIUM/LOW",
    "estimated_minutes": liczba
}}"""
        
        if self.provider == "groq":
            response = self._call_groq(prompt)
        elif self.provider == "openai":
            response = self._call_openai(prompt)
        else:
            response = self._call_anthropic(prompt)
        
        if response:
            try:
                return json.loads(response)
            except:
                return {"suggestions": [response], "priority": "MEDIUM", "estimated_minutes": 30}
        
        return None
    
    def suggest_architecture(self, project_info: dict) -> Optional[str]:
        """Sugeruje architekturę dla projektu."""
        if not self.available:
            return None
        
        prompt = f"""Jako ekspert architektury oprogramowania, zaproponuj architekturę dla tego projektu:

Projekt: {project_info.get('name')}
Typ: {project_info.get('type', 'unknown')}
Struktura: {json.dumps(project_info.get('structure', {}), indent=2)}

Zapropuj:
1. Optymalną strukturę katalogów
2. Wzorce projektowe
3. Kluczowe komponenty
4. Technologie/pakiety które warto użyć

Bądź konkretny i praktyczny."""
        
        if self.provider == "groq":
            return self._call_groq(prompt)
        elif self.provider == "openai":
            return self._call_openai(prompt)
        else:
            return self._call_anthropic(prompt)
    
    def generate_roadmap(self, goal: str, constraints: dict) -> Optional[dict]:
        """Generuje roadmapę do osiągnięcia celu."""
        if not self.available:
            return None
        
        prompt = f"""Wygeneruj roadmapę do osiągnięcia tego celu:

Cel: {goal}

Ograniczenia: {json.dumps(constraints, indent=2)}

Odpowiedz w formacie JSON:
{{
    "milestones": [
        {{"name": "Nazwa", "tasks": ["lista zadań"], "priority": "HIGH"}}
    ],
    "estimated_days": liczba,
    "first_action": "konkretne pierwsze zadanie"
}}"""
        
        if self.provider == "groq":
            response = self._call_groq(prompt)
        elif self.provider == "openai":
            response = self._call_openai(prompt)
        else:
            response = self._call_anthropic(prompt)
        
        if response:
            try:
                return json.loads(response)
            except:
                return None
        
        return None
    
    def ask(self, question: str, system_prompt: str = "") -> Optional[str]:
        """Zadaje pytanie do LLM."""
        if not self.available:
            return None
        
        if system_prompt:
            prompt = f"<|system|>{system_prompt}</s>\n<|user|>{question}</s>"
        else:
            prompt = question
        
        if self.provider == "groq":
            return self._call_groq(prompt)
        elif self.provider == "openai":
            return self._call_openai(question)
        else:
            return self._call_anthropic(question)
    
    def _build_recommendation_prompt(self, context: dict) -> str:
        """Buduje prompt dla rekomendacji."""
        project_type = context.get("project_type", "unknown")
        issues = context.get("issues", [])
        progress = context.get("progress", {})
        goals = context.get("goals", "")
        
        prompt = f"""Jako produktywny asystent AI, daj mi JEDNĄ konkretną rekomendację na dziś.

Kontekst:
- Typ projektu: {project_type}
- Cel: {goals or 'brak określonego celu'}
- Postęp: {progress.get('status', 'unknown')}
- Problemy: {', '.join([i.get('issue', '') for i in issues[:3]]) or 'brak'}

Odpowiedz TYKO jedną rekomendacją w formacie:
ACC: [konkretna akcja do wykonania]
DLACZEGO: [krótkie uzasadnienie]
"""
        return prompt
    
    def _call_groq(self, prompt: str) -> Optional[str]:
        """Wywołuje Groq API."""
        try:
            import requests
            
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"[LLM] Groq error: {response.status_code} - {response.text[:100]}")
                return None
        except Exception as e:
            print(f"[LLM] Groq exception: {e}")
            return None
    
    def _call_openai(self, prompt: str) -> Optional[str]:
        """Wywołuje OpenAI API."""
        try:
            import requests
            
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"[LLM] OpenAI error: {response.status_code}")
                return None
        except Exception as e:
            print(f"[LLM] OpenAI exception: {e}")
            return None
    
    def _call_anthropic(self, prompt: str) -> Optional[str]:
        """Wywołuje Anthropic API."""
        try:
            import requests
            
            response = requests.post(
                self.api_url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            else:
                print(f"[LLM] Anthropic error: {response.status_code}")
                return None
        except Exception as e:
            print(f"[LLM] Anthropic exception: {e}")
            return None


class SmartAdvisor:
    """Wykorzystuje LLM do dawania inteligentnych rekomendacji."""
    
    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm if llm else LLM()
    
    def get_daily_recommendation(self, project_state: dict) -> str:
        """Zwraca rekomendację na dziś."""
        if not self.llm.is_available():
            return self._fallback_recommendation(project_state)
        
        context = {
            "project_type": project_state.get("type", "unknown"),
            "issues": project_state.get("issues", []),
            "progress": project_state.get("progress", {}),
            "goals": project_state.get("goals", "")
        }
        
        result = self.llm.generate_recommendation(context)
        
        if result and "ACC:" in result:
            return result
        else:
            return self._fallback_recommendation(project_state)
    
    def suggest_next_steps(self, project: dict, focus_task: dict) -> str:
        """Sugeruje następne kroki po ukończeniu focus taska."""
        if not self.llm.is_available():
            return "Ukończ focus task i przejdź do następnego."
        
        prompt = f"""Na podstawie obecnego focus taska, zaproponuj następny logicalny krok.

Obecny focus: {focus_task.get('task')}
Projekt: {project.get('name')}
Typ: {project.get('type')}

Bądź konkretny i praktyczny."""
        
        if self.llm.provider == "groq":
            result = self.llm._call_groq(prompt)
        elif self.llm.provider == "openai":
            result = self.llm._call_openai(prompt)
        else:
            result = self.llm._call_anthropic(prompt)
        
        return result if result else "Kontynuuj z następnym taskiem."
    
    def _fallback_recommendation(self, project_state: dict) -> str:
        """Fallback gdy LLM niedostępny."""
        issues = project_state.get("issues", [])
        
        high_priority = [i for i in issues if i.get("priority") == "HIGH"]
        if high_priority:
            return f"ACC: {high_priority[0].get('issue', 'Napraw najważniejszy problem')}\nDLACZEGO: To jest priorytet HIGH"
        
        return "ACC: Kontynuuj pracę nad bieżącym zadaniem\nDLACZEGO: Brak krytycznych problemów"
