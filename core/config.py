# Konfiguracja systemu Development Assistant V8

import os
from dotenv import load_dotenv

load_dotenv()

# Interwał skanowania w sekundach
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "60"))

# Priorytety zadań
TASK_PRIORITIES = ["HIGH", "MEDIUM", "LOW"]

# Integracja Obsidian
INTEGRATE_OBSIDIAN = os.getenv("INTEGRATE_OBSIDIAN", "true").lower() == "true"
OBSIDIAN_PATH = os.getenv("OBSIDIAN_PATH", "/home/felanraf/Dokumenty/Obsidian Vault/DevelopmentAssistant")

# Integracja Todoist
INTEGRATE_TODOIST = os.getenv("INTEGRATE_TODOIST", "true").lower() == "true"
TODOIST_PROJECT = os.getenv("TODOIST_PROJECT", "Development Assistant Tasks")
TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN", "")

# Limity i progi
MAX_TASKS_PER_PROJECT = int(os.getenv("MAX_TASKS_PER_PROJECT", "5"))
STAGNATION_DAYS = int(os.getenv("STAGNATION_DAYS", "2"))
WORK_SCORE_THRESHOLD = int(os.getenv("WORK_SCORE_THRESHOLD", "5"))
STAGNATION_THRESHOLD = int(os.getenv("STAGNATION_THRESHOLD", "2"))
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
ENABLE_TRENDS = os.getenv("ENABLE_TRENDS", "true").lower() == "true"

# Completion Pressure
COMPLETION_WARNING_THRESHOLD = int(os.getenv("COMPLETION_WARNING_THRESHOLD", "2"))
COMPLETION_CRITICAL_THRESHOLD = int(os.getenv("COMPLETION_CRITICAL_THRESHOLD", "4"))

# Interaction Engine
ENABLE_INTERACTION = os.getenv("ENABLE_INTERACTION", "true").lower() == "true"
INTERACTION_INTERVAL_MINUTES = int(os.getenv("INTERACTION_INTERVAL_MINUTES", "30"))

# Learning Engine
ENABLE_LEARNING = os.getenv("ENABLE_LEARNING", "true").lower() == "true"
LEARNING_HISTORY_DAYS = int(os.getenv("LEARNING_HISTORY_DAYS", "30"))

# Executor Lite
ENABLE_EXECUTOR_LITE = os.getenv("ENABLE_EXECUTOR_LITE", "true").lower() == "true"
EXECUTOR_LITE_SUGGESTIONS = os.getenv("EXECUTOR_LITE_SUGGESTIONS", "true").lower() == "true"

# Ścieżki główne
WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", ".")
MEMORY_PATH = os.getenv("MEMORY_PATH", "memory")
SYSTEM_PATH = os.getenv("SYSTEM_PATH", "system")
PROJECTS_PATH = os.getenv("PROJECTS_PATH", "workspace/projects")
TOOLS_PATH = os.getenv("TOOLS_PATH", "workspace/tools")

# Ścieżki skanowania projektów (z .env, oddzielone przecinkami)
def _parse_paths():
    env_paths = os.getenv("PROJECT_SCAN_PATHS", "")
    if env_paths:
        return [p.strip() for p in env_paths.split(",") if p.strip()]
    return ["workspace/projects", "/home/felanraf/Projekty"]

PROJECT_SCAN_PATHS = _parse_paths()

# Wykrywanie projektów
ENABLE_PROJECT_DISCOVERY = os.getenv("ENABLE_PROJECT_DISCOVERY", "true").lower() == "true"
PROJECT_DISCOVERY_INTERVAL = int(os.getenv("PROJECT_DISCOVERY_INTERVAL", "1440"))
ENABLE_PROJECT_AUTO_NOTES = os.getenv("ENABLE_PROJECT_AUTO_NOTES", "true").lower() == "true"

# Ścieżka do głównego kodu agenta
AGENT_CODE_PATH = os.getenv("AGENT_CODE_PATH", ".")

# LLM Integration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
