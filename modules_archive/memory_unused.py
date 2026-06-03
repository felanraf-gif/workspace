# ARCHIWUM - Nieużywane metody z memory/memory.py
# Przeniesione: 2026-03-19
# Powód: Nigdy nie wywoływane w loop.py

# ===== get_daily_time() =====
# def get_daily_time(self, date_str=None):
#     """Pobiera czas pracy dla dnia."""
#     if date_str is None:
#         date_str = datetime.now().strftime("%Y-%m-%d")
#     
#     daily_file = os.path.join(self.decisions_path, f"time_{date_str}.json")
#     if os.path.exists(daily_file):
#         try:
#             with open(daily_file, 'r') as f:
#                 return json.load(f)
#         except:
#             pass
#     return {}

# ===== save_daily_time() =====
# def save_daily_time(self, project, duration):
#     """Zapisuje czas pracy projektu."""
#     date_str = datetime.now().strftime("%Y-%m-%d")
#     daily_file = os.path.join(self.decisions_path, f"time_{date_str}.json")
#     
#     data = {}
#     if os.path.exists(daily_file):
#         try:
#             with open(daily_file, 'r') as f:
#                 data = json.load(f)
#         except:
#             pass
#     
#     data[project] = data.get(project, 0) + duration
#     
#     with open(daily_file, 'w') as f:
#         json.dump(data, f, indent=2)

# ===== log_time_event() =====
# def log_time_event(self, event_type, task):
#     """Loguje zdarzenie czasowe."""
#     try:
#         with open(self.time_log_file, 'r') as f:
#             log = json.load(f)
#     except:
#         log = []
#     
#     log.append({
#         "timestamp": datetime.now().isoformat(),
#         "event": event_type,
#         "task": task
#     })
#     
#     if len(log) > 1000:
#         log = log[-1000:]
#     
#     with open(self.time_log_file, 'w') as f:
#         json.dump(log, f, indent=2)

# ===== archive_old_files() =====
# def archive_old_files(self):
#     """Archiwizuje stare plany."""
#     if not os.path.exists(self.decisions_path):
#         return
#     
#     today = datetime.now()
#     archive_month = os.path.join(self.archive_path, today.strftime("%Y-%m"))
#     os.makedirs(archive_month, exist_ok=True)
#     
#     for filename in os.listdir(self.decisions_path):
#         if filename.startswith("plan_") and filename.endswith(".json"):
#             filepath = os.path.join(self.decisions_path, filename)
#             try:
#                 with open(filepath, 'r') as f:
#                     data = json.load(f)
#                     date = data.get("created", "")[:10]
#                     if date and date < today.strftime("%Y-%m-%d"):
#                         import shutil
#                         shutil.move(filepath, os.path.join(archive_month, filename))
#             except:
#                 pass

# ===== clear_old_cache() =====
# def clear_old_cache(self):
#     """Czyści stary cache."""
#     cache_files = [
#         os.path.join(self.decisions_path, f"task_cache_{d}.json")
#         for d in range(1, 8)
#     ]
#     for f in cache_files:
#         if os.path.exists(f):
#             os.remove(f)
