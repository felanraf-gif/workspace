"""
core/loop.py - Główna pętla Towarzysza V9
OBSERVE → SCOUT → ANALYZE → PLAN → BUILD → CRITIQUE → REFLECT

V9 Architecture:
- Observer: Wykrywa zmiany w plikach
- RoleManager: Scout → Architect → Builder → Critic
- Executor: Wykonuje zadania narzędziami
- Memory: Short + Long + Vector (ChromaDB)
- Skills: Reusable strategies
"""

import time
import os
import sys
from datetime import datetime

sys_path = os.path.dirname(os.path.dirname(__file__))
if sys_path not in __import__('sys').path:
    __import__('sys').path.insert(0, sys_path)

from core.config import MEMORY_PATH, OBSIDIAN_PATH, INTEGRATE_OBSIDIAN, INTEGRATE_TODOIST, WORKSPACE_PATH, PROJECT_SCAN_PATHS, ENABLE_PROJECT_DISCOVERY, ENABLE_PROJECT_AUTO_NOTES
from core.constants import CHECKIN_INTERVAL_MINUTES, SCAN_INTERVAL_SECONDS, MAX_DAILY_TASKS
from memory.memory import Memory
from brain.analyzer import Analyzer
from brain.planner import Planner
from brain.assistant import Assistant
from brain.alerts import Alerts
from brain.code_graph import DependencyGraph
from integrations.obsidian import Obsidian
from integrations.todoist import Todoist
from integrations.standup import Standup

try:
    from brain.roles.manager import RoleManager
    from brain.executor import Executor
    from brain.observer import Observer
    from brain.project_discovery import ProjectDiscovery
    from brain.project_tracker import ProjectTracker
    from brain.project_recommender import ProjectRecommender
    from brain.project_manager import ProjectManager
    from memory.project_memory import ProjectMemory, MultiProjectMemory
    V9_AVAILABLE = True
except ImportError as e:
    V9_AVAILABLE = False
    RoleManager = None
    Executor = None
    Observer = None
    ProjectDiscovery = None
    ProjectTracker = None
    ProjectRecommender = None
    ProjectManager = None
    ProjectMemory = None
    MultiProjectMemory = None


def safe_print(*args, **kwargs):
    """Bezpieczne printowanie - ignoruje BrokenPipeError i loguje do pliku."""
    msg = " ".join(str(a) for a in args)
    try:
        print(*args, **kwargs)
    except BrokenPipeError:
        _log_to_file(f"[CONSOLE_IGNORED] {msg}")
    except OSError as e:
        if e.errno == 32:  # Broken pipe
            _log_to_file(f"[CONSOLE_IGNORED] {msg}")
        else:
            _log_to_file(f"[OS_ERROR {e.errno}] {msg}")


def _log_to_file(msg):
    """Loguje do pliku jako fallback."""
    try:
        log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "daemon.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass


def main_loop():
    """Główna pętla systemu V9 z pełnym cyklem autonomous agent."""
    
    safe_print("=" * 50)
    safe_print("TOWARZYSZ V9 - Autonomous Agent")
    safe_print("=" * 50)
    
    memory = Memory()
    analyzer = Analyzer()
    planner = Planner()
    assistant = Assistant(memory_path=MEMORY_PATH, obsidian_path=OBSIDIAN_PATH)
    alerts = Alerts()
    obsidian = Obsidian(vault_path=OBSIDIAN_PATH)
    todoist = Todoist()
    standup = Standup(vault_path=OBSIDIAN_PATH)
    
    state = memory.get_state()
    state["status"] = "running"
    state["version"] = "9.0"
    memory.save_state(state)
    
    role_manager = None
    executor = None
    observer = None
    project_discovery = None
    project_tracker = None
    project_recommender = None
    project_manager = None
    multi_project_memory = None
    
    if V9_AVAILABLE:
        try:
            executor = Executor()
            role_manager = RoleManager(executor=executor)
            observer = Observer(watch_paths=[WORKSPACE_PATH])
            project_components = []
            if ENABLE_PROJECT_DISCOVERY:
                project_discovery = ProjectDiscovery(scan_paths=PROJECT_SCAN_PATHS)
                project_discovery.discover_all()
                project_tracker = ProjectTracker()
                project_recommender = ProjectRecommender()
                project_manager = ProjectManager(projects_cache=project_discovery.discovered_projects)
                multi_project_memory = MultiProjectMemory()
                project_components = ["ProjectDiscovery", "ProjectManager"]
            safe_print(f"[V9] Initialized: RoleManager, Executor, Observer{', ' + ', '.join(project_components) if project_components else ''}")
        except Exception as e:
            import traceback
            safe_print(f"[V9] Init warning: {e}")
            safe_print(traceback.format_exc()[:500])
            role_manager = None
    else:
        safe_print(f"[V8] Falling back to V8 mode (V9 modules not available)")
    
    safe_print(f"[OK] Memory: {MEMORY_PATH}")
    safe_print(f"[OK] Obsidian: {OBSIDIAN_PATH}")
    safe_print("=" * 50)
    
    doc_file = os.path.join(OBSIDIAN_PATH, "Projects", "towarzysz_dokumentacja.md")
    if not os.path.exists(doc_file):
        saved = obsidian.save_agent_documentation()
        if saved:
            safe_print(f"[DOCS] 📚 Dokumentacja zapisana")
    
    cycle_count = 0
    last_project_scan = state.get("last_project_scan")
    last_project_scan_date = state.get("last_project_scan_date", "") if state else ""
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        while True:
            cycle_count += 1
            
            state = memory.get_state()
            state["cycle"] = cycle_count
            
            # ═══════════════════════════════════════════════════════
            # FAZA 0: OBSERVE (V9) - Wykryj zmiany w plikach
            # ═══════════════════════════════════════════════════════
            if observer:
                state["current_module"] = "observer"
                memory.save_state(state)
                
                try:
                    observation = observer.observe()
                    changes_summary = observer.get_changes_summary()
                    safe_print(f"[OBSERVE] {changes_summary}")
                    state["last_observation"] = observation.get("timestamp")
                except Exception as e:
                    safe_print(f"[OBSERVE] Warning: {e}")
                    observation = {"changes": [], "new_files": [], "modified_files": []}
            else:
                observation = {"changes": [], "new_files": [], "modified_files": []}
            
            # ═══════════════════════════════════════════════════════
            # FAZA 0b: PROJECT DISCOVERY - Raz dziennie
            # ═══════════════════════════════════════════════════════
            project_recommendations = []
            all_project_progress = []
            
            if project_discovery and project_tracker and project_recommender and project_manager:
                if last_project_scan_date != today:
                    state["current_module"] = "project_discovery"
                    
                    try:
                        safe_print(f"[PROJECTS] 🆕 Skanowanie projektów ({today})...")
                        discovered = project_discovery.discover_all()
                        
                        if discovered:
                            project_manager.projects_cache = discovered
                            progress_report = project_tracker.track_projects(discovered)
                            all_project_progress = progress_report
                            project_recommendations = project_recommender.generate_recommendations(progress_report)
                            
                            summary = project_discovery.get_status_summary()
                            safe_print(f"[PROJECTS] Wykryto {summary.get('total', 0)} projektów:")
                            safe_print(f"  Typy: {summary.get('by_type', {})}")
                            
                            for progress in progress_report:
                                name = progress.get("name")
                                project_manager.update_project_state(name, {
                                    "status": progress.get("status"),
                                    "last_analysis": datetime.now().isoformat(),
                                    "recommendations": [r for r in project_recommendations if r.get("project") == name]
                                })
                                
                                if multi_project_memory:
                                    pm = multi_project_memory.get_project_memory(name)
                                    pm.add_history_entry({
                                        "cycle": cycle_count,
                                        "status": progress.get("status"),
                                        "recommendations_count": len([r for r in project_recommendations if r.get("project") == name])
                                    })
                                
                                if ENABLE_PROJECT_AUTO_NOTES and INTEGRATE_OBSIDIAN:
                                    obsidian.save_project_note(name, progress, [r for r in project_recommendations if r.get("project") == name])
                            
                            if INTEGRATE_OBSIDIAN:
                                obsidian.save_multi_project_dashboard(project_manager.get_summary())
                            
                            high_priority = [r for r in project_recommendations if r.get('priority') == 'HIGH']
                            if high_priority:
                                safe_print(f"[PROJECTS] 🚨 {len(high_priority)} pilnych rekomendacji!")
                                for rec in high_priority[:2]:
                                    safe_print(f"  - {rec.get('title', '?')}")
                            
                            attention = project_manager.get_projects_needing_attention()
                            if attention:
                                safe_print(f"[PROJECTS] ⚠️ {len(attention)} projektów wymaga uwagi")
                            
                            state["projects_discovered"] = len(discovered)
                            state["project_recommendations"] = len(project_recommendations)
                            state["last_project_scan"] = time.time()
                            state["last_project_scan_date"] = today
                    except Exception as e:
                        import traceback
                        safe_print(f"[PROJECTS] Warning: {e}")
                else:
                    safe_print(f"[PROJECTS] ✅ Skanowanie już dziś ({today}), pomijam")
                    if project_manager and project_manager.projects_cache:
                        all_project_progress = project_tracker.track_projects(project_manager.projects_cache)
                        project_recommendations = [r for p in all_project_progress for r in p.get("recommendations", [])]
            
            # ═══════════════════════════════════════════════════════
            # FAZA 0c: PER-PROJECT CYCLES
            # ═══════════════════════════════════════════════════════
            if project_manager and all_project_progress:
                focus_projects = project_manager.get_project_focus_order()[:2]
                
                for proj in focus_projects:
                    proj_name = proj.get("name")
                    if not project_manager.should_run_cycle(proj_name, interval_hours=24):
                        continue
                    
                    safe_print(f"[PROJECT:{proj_name}] Uruchamianie cyklu...")
                    
                    project_manager.update_project_state(proj_name, {
                        "last_cycle": datetime.now().isoformat(),
                        "v9_status": "RUNNING"
                    })
                    
                    project_recommendations = [r for r in project_recommendations if r.get("project") == proj_name]
                    
                    high_recs = [r for r in project_recommendations if r.get("priority") == "HIGH"]
                    medium_recs = [r for r in project_recommendations if r.get("priority") == "MEDIUM"]
                    
                    safe_print(f"[PROJECT:{proj_name}] Rekomendacje: {len(high_recs)} HIGH, {len(medium_recs)} MEDIUM")
                    
                    project_manager.update_project_state(proj_name, {
                        "v9_status": "COMPLETED",
                        "recommendations": project_recommendations
                    })
            
            # ═══════════════════════════════════════════════════════
            # FAZA 1: V9 ROLE CYCLE (Scout → Architect → Builder → Critic)
            # ═══════════════════════════════════════════════════════
            v9_result = None
            if role_manager:
                state["current_module"] = "roles"
                memory.save_state(state)
                
                try:
                    safe_print("[ROLES] Running Scout → Architect → Builder → Critic cycle...")
                    v9_result = role_manager.run_cycle(focus_on_agent=True)
                    
                    scout = v9_result.get("roles", {}).get("scout", {})
                    architect = v9_result.get("roles", {}).get("architect", {})
                    builder = v9_result.get("roles", {}).get("builder", {})
                    critic = v9_result.get("roles", {}).get("critic", {})
                    
                    safe_print(f"  [Scout] Files: {scout.get('files_scanned', 0)}, Changes: {scout.get('changes_found', 0)}")
                    safe_print(f"  [Architect] Goals: {architect.get('goals_count', 0)}, Tasks: {architect.get('tasks_count', 0)}")
                    safe_print(f"  [Builder] Success: {builder.get('success_rate', 0):.0%}, Failed: {builder.get('failed_count', 0)}")
                    safe_print(f"  [Critic] Verdict: {critic.get('verdict', 'N/A')}, Score: {critic.get('score', 0)}")
                    
                    if v9_result.get("reflections"):
                        safe_print(f"  [Reflections] {len(v9_result['reflections'])} recommendations")
                    
                    state["v9_cycle"] = v9_result.get("cycle_id", 0)
                    state["v9_status"] = v9_result.get("overall_status", "UNKNOWN")
                    
                except Exception as e:
                    safe_print(f"[ROLES] Error: {e}")
                    v9_result = None
            
            # ═══════════════════════════════════════════════════════
            # FAZA 1b: ANALYZE - ANALIZUJ WŁASNY KOD (V8 compatibility)
            # ═══════════════════════════════════════════════════════
            state["current_module"] = "analyzer"
            memory.save_state(state)
            
            safe_print("[ANALYZE] Analizuję własny kod...")
            agent_intel = analyzer.analyze_agent_code()
            
            if agent_intel:
                issues = agent_intel.get("issues", [])
                structure = agent_intel.get("structure", {})
                architecture = agent_intel.get("architecture", {})
                summary = agent_intel.get("summary", "")
                
                safe_print(f"  Pliki: {structure.get('metrics', {}).get('python_files', 0)} Python")
                safe_print(f"  Linie: {structure.get('metrics', {}).get('total_lines', 0)}")
                safe_print(f"  Typ: {architecture.get('type', 'unknown')}")
                safe_print(f"  Issues: {len(issues)}")
                
                for issue in issues:
                    if issue.get("priority") in ["HIGH", "MEDIUM"]:
                        safe_print(f"    [{issue['priority']}] {issue['issue'][:70]}")

                dep_issues = [i for i in issues if i.get("type") == "dependency"]
                if dep_issues:
                    dead = [i for i in dep_issues if "Martwy kod" in i.get("issue", "")]
                    cycles = [i for i in dep_issues if "Cykliczna" in i.get("issue", "")]
                    high = [i for i in dep_issues if "Wysoki wpływ" in i.get("issue", "")]
                    if dead:
                        safe_print(f"  [GRAPH] Martwy kod: {len(dead)} plików")
                    if cycles:
                        safe_print(f"  [GRAPH] Cykle: {len(cycles)}")
                    if high:
                        safe_print(f"  [GRAPH] Wysoki wpływ: {len(high)} modułów")
            else:
                issues = []
                summary = ""
            
            # Daily Standup o 6:00
            if INTEGRATE_OBSIDIAN and standup.should_run() and not standup.was_run_today():
                tasks = planner.create_tomorrow_plan_from_intelligence(agent_intel) if agent_intel else []
                focus = planner.select_focus_task(tasks)
                standup.generate(focus, [], {"overall_status": "ANALYZING"}, planner)
                safe_print(f"[STANDUP] 🌅 Wygenerowano")
            
            # ═══════════════════════════════════════════════════════
            # FAZA 2: PLAN - GENERUJ TASKI Z ANALIZY
            # ═══════════════════════════════════════════════════════
            state["current_module"] = "planner"
            memory.save_state(state)
            
            if agent_intel:
                tasks = planner.create_tomorrow_plan_from_intelligence(agent_intel)
                focus_task = planner.select_focus_task(tasks)
                
                if focus_task:
                    focus_message = planner.generate_message("LOW_PROGRESS", {"projects": {"towarzysz": {"status": "REAL_WORK", "score": 5}}}, tasks)
                else:
                    focus_message = "Brak konkretnych zadań do wykonania."
            else:
                tasks = []
                focus_task = None
                focus_message = "Analiza nie powiodła się."
            
            if focus_task:
                planner.save_focus_log(focus_task, focus_message, "LOW_PROGRESS")
                safe_print(f"[FOCUS] {focus_task.get('task', 'brak')}")
            
            # ═══════════════════════════════════════════════════════
            # FAZA 3: ALERTS
            # ═══════════════════════════════════════════════════════
            work_data = {
                "overall_status": "LOW_PROGRESS",
                "overall_score": len(issues),
                "projects": {"towarzysz": {"status": "REAL_WORK", "score": len(issues), "stagnation_days": 0}}
            }
            alert_list = alerts.check(work_data, focus_task, state)
            
            if issues:
                high_issues = [i for i in issues if i.get("priority") == "HIGH"]
                if high_issues:
                    safe_print(f"[ALERT] 🚨 {len(high_issues)} HIGH priority issues!")
            
            # ═══════════════════════════════════════════════════════
            # FAZA 4: SAVE (Obsidian)
            # ═══════════════════════════════════════════════════════
            if INTEGRATE_OBSIDIAN and agent_intel:
                state["current_module"] = "obsidian"
                memory.save_state(state)
                
                obsidian.save_daily_note(
                    focus_task, 
                    focus_message, 
                    "LOW_PROGRESS", 
                    [], 
                    tasks,
                    summary=summary,
                    agent_intel=agent_intel
                )
                safe_print(f"[OBSIDIAN] 📝 Zapisano daily note")
            
            # ═══════════════════════════════════════════════════════
            # FAZA 5: SYNC (Todoist)
            # ═══════════════════════════════════════════════════════
            if INTEGRATE_TODOIST and tasks and memory.can_send_more_tasks(max_daily=MAX_DAILY_TASKS):
                state["current_module"] = "todoist"
                memory.save_state(state)
                
                sent = planner.send_to_todoist(tasks)
                memory.set_daily_tasks_sent(len(sent))
                
                if sent:
                    safe_print(f"[TODOIST] ✅ Wysłano {len(sent)} tasków:")
                    for s in sent:
                        content = planner._build_detailed_task_content(s['task_data'])
                        safe_print(f"    - {content[:70]}")
                        
                    safe_print(f"[TODOIST] 🏷️ Oznaczono FOCUS")
                else:
                    safe_print(f"[TODOIST] ⚠️ Nie wysłano żadnych tasków (sprawdź log)")
            
            if memory.can_check_todoist_again(minutes=15):
                memory.set_last_todoist_check()
                todoist_stats = todoist.get_stats()
                safe_print(f"[TODOIST] Aktywne: {todoist_stats['active_count']}, Dziś: {todoist_stats['completed_today']}")
            
            # ═══════════════════════════════════════════════════════
            # FAZA 6: INTERACT (rekomendacje)
            # ═══════════════════════════════════════════════════════
            recs = assistant.get_recommendations()
            for rec in recs:
                if rec.get("priority") == "high" and "llm" in rec.get("type", ""):
                    safe_print(f"[REKOMENDACJA] {rec.get('message', '')}")
            
            # ═══════════════════════════════════════════════════════
            # KONIEC CYKLU
            # ═══════════════════════════════════════════════════════
            state["current_module"] = "sleep"
            state["last_analysis"] = time.time()
            state["focus_task"] = focus_task
            memory.save_state(state)
            
            v9_status = v9_result.get("overall_status", "N/A") if v9_result else "DISABLED"
            safe_print(f"\n[{datetime.now().strftime('%H:%M')}] Cycle {cycle_count} | V9: {v9_status} | Issues: {len(issues)} | Tasks: {len(tasks)}")
            safe_print("-" * 50)
            
            time.sleep(SCAN_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        memory.save_state({"status": "stopped"})
        safe_print("\n[STOP] Towarzysz zatrzymany.")
    except Exception as e:
        memory.save_state({"status": "error", "error": str(e)})
        safe_print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main_loop()
