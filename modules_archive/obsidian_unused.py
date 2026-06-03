# ARCHIWUM - Nieużywane metody z integrations/obsidian.py
# Przeniesione: 2026-03-19
# Powód: Nigdy nie wywoływane w loop.py

# ===== save_focus_task() =====
# def save_focus_task(self, focus_task):
#     """Zapisuje aktualny focus task."""
#     today = datetime.now().strftime("%Y-%m-%d")
#     filename = os.path.join(self.daily_dir, f"{today}_focus.md")
#     
#     if not focus_task:
#         content = "# Focus\n\nBrak aktywnego focus taska.\n"
#     else:
#         content = f"""# Focus
# 
# **Projekt:** {focus_task.get('project', 'N/A')}
# **Task:** {focus_task.get('task', 'N/A')}
# **Priorytet:** {focus_task.get('priority', 'LOW')}
# **Time:** {datetime.now().strftime('%H:%M')}
# 
# """
#     try:
#         with open(filename, 'w') as f:
#             f.write(content)
#     except:
#         pass

# ===== log_interaction() =====
# def log_interaction(self, action, task, message):
#     """Zapisuje interakcję."""
#     today = datetime.now().strftime("%Y-%m-%d")
#     filename = os.path.join(self.interactions_dir, f"{today}_interactions.md")
#     
#     content = f"\n## {datetime.now().strftime('%H:%M:%S')}\n\n"
#     content += f"**Akcja:** {action.upper()}\n"
#     if task:
#         content += f"**Task:** [{task.get('project', '')}] {task.get('task', '')}\n"
#     content += f"**Wiadomość:** {message}\n"
#     
#     try:
#         with open(filename, 'a') as f:
#             f.write(content)
#     except:
#         pass

# ===== create_project_note() =====
# def create_project_note(self, project_name, data):
#     """Tworzy notatkę projektu."""
#     filename = os.path.join(self.projects_dir, f"{project_name}.md")
#     
#     content = f"# {project_name}\n\n"
#     content += f"**Utworzono:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
#     
#     if data.get("status"):
#         content += f"**Status:** {data['status']}\n"
#     if data.get("last_update"):
#         content += f"**Ostatnia aktualizacja:** {data['last_update']}\n"
#     if data.get("issues"):
#         content += f"\n## Problemy\n"
#         for issue in data['issues']:
#             content += f"- {issue}\n"
#     
#     try:
#         with open(filename, 'w') as f:
#             f.write(content)
#     except:
#         pass
