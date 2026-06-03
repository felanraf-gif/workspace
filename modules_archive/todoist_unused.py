# ARCHIWUM - Nieużywane metody z integrations/todoist.py
# Przeniesione: 2026-03-19
# Powód: Nigdy nie wywoływane w loop.py

# ===== sync_with_state() =====
# def sync_with_state(self, tasks):
#     """Synchronizuje taski ze stanem."""
#     active = self.get_active_tasks()
#     active_contents = {t.get("content") for t in active}
#     
#     created = []
#     for task in tasks:
#         content = f"[{task.get('project', '')}] {task.get('task', '')}"
#         if content not in active_contents:
#             priority = 4 if task.get("priority") == "HIGH" else 3 if task.get("priority") == "MEDIUM" else 2
#             task_id = self.create_task(content, priority=priority)
#             if task_id:
#                 created.append({"id": task_id, "content": content})
#     
#     return created
