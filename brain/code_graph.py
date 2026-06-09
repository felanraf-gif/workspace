import os
import ast
from collections import defaultdict


class DependencyGraph:
    def __init__(self):
        self.graph: dict[str, set[str]] = {}
        self.reverse: dict[str, set[str]] = {}
        self._file_map: dict[str, str] = {}
        self._imports_per_file: dict[str, list[str]] = {}

    def build(self, project: dict) -> dict:
        self.graph = {}
        self.reverse = {}
        self._file_map = {}
        self._imports_per_file = {}

        files = project.get("files", [])
        if not files:
            return {"graph": {}, "dead_code": [], "cycles": [], "high_impact": []}

        for f in files:
            rel = f["path"].replace("\\", "/")
            self._file_map[rel] = f["full_path"]

        self._map_module_to_file(files)

        for f in files:
            if not f["name"].endswith(".py"):
                continue
            rel = f["path"].replace("\\", "/")
            imports = self._parse_imports(f["full_path"])
            self._imports_per_file[rel] = imports
            local_deps = self._resolve_local(imports, rel)
            self.graph[rel] = local_deps
            for dep in local_deps:
                self.reverse.setdefault(dep, set()).add(rel)

        entry_points = {"main.py", "__main__.py", "__init__.py"}

        dead_code = self._find_dead_code(entry_points)
        cycles = self._find_cycles()
        high_impact = self._find_high_impact()

        return {
            "graph": {k: sorted(v) for k, v in self.graph.items()},
            "dead_code": dead_code,
            "cycles": cycles,
            "high_impact": high_impact,
        }

    def _map_module_to_file(self, files):
        self._module_to_file = {}
        for f in files:
            if not f["name"].endswith(".py"):
                continue
            rel = f["path"].replace("\\", "/")
            module_path = rel.replace("/", ".").replace("\\", ".").removesuffix(".py")
            if module_path.endswith(".__init__"):
                module_path = module_path.removesuffix(".__init__")
            self._module_to_file[module_path] = rel

    def _parse_imports(self, filepath: str) -> list[str]:
        imports = []
        try:
            with open(filepath, encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
            return imports
        source_path = os.path.normpath(filepath)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    pkg_dir = os.path.dirname(source_path)
                    for _ in range(1, node.level):
                        pkg_dir = os.path.dirname(pkg_dir)
                    pkg_module = pkg_dir.replace("/", ".").replace("\\", ".")
                    if pkg_module.startswith("."):
                        pkg_module = pkg_module[1:]
                    if node.module:
                        imports.append(f"{pkg_module}.{node.module}")
                    else:
                        imports.append(pkg_module)
                elif node.module:
                    imports.append(node.module)
        return imports

    def _resolve_local(self, imports: list[str], source_file: str) -> set[str]:
        deps = set()
        for imp in imports:
            found = self._match_module_to_file(imp, source_file)
            if found:
                deps.add(found)
        return deps

    def _match_module_to_file(self, module: str, source_file: str) -> str | None:
        candidates = [module]
        parts = module.split(".")
        for i in range(len(parts) - 1, 0, -1):
            candidates.append(".".join(parts[:i]))

        visited = set()
        for mod in candidates:
            if mod in visited:
                continue
            visited.add(mod)
            found = self._module_to_file.get(mod)
            if found and found != source_file:
                return found

            try_path = mod.replace(".", "/") + ".py"
            for mpath, frel in self._module_to_file.items():
                if frel == try_path and frel != source_file:
                    return frel

        return None

    def _find_dead_code(self, entry_points: set) -> list[dict]:
        all_files = set(self.graph.keys())
        imported = set(self.reverse.keys())
        dead = []
        for f in sorted(all_files - imported):
            if os.path.basename(f) not in entry_points:
                dead.append({
                    "file": f,
                    "reason": "Brak importów z innych plików projektu",
                })
        return dead

    def _find_cycles(self) -> list[list[str]]:
        visited = set()
        stack = []
        cycles = []

        def dfs(node, path):
            if node in path:
                idx = path.index(node)
                cycle = path[idx:] + [node]
                cycles.append(cycle)
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            for neighbor in self.graph.get(node, set()):
                dfs(neighbor, path)
            path.pop()

        for node in self.graph:
            dfs(node, [])

        unique = []
        seen = set()
        for c in cycles:
            key = "->".join(sorted(c))
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    def _find_high_impact(self) -> list[dict]:
        scored = []
        for node, deps in sorted(self.reverse.items(), key=lambda x: len(x[1]), reverse=True):
            if len(deps) > 1:
                scored.append({
                    "file": node,
                    "dependant_count": len(deps),
                    "dependants": sorted(deps),
                })
        return scored

    def find_unused_imports(self, project: dict) -> list[dict]:
        results = []
        for f in project.get("files", []):
            if not f["name"].endswith(".py"):
                continue
            rel = f["path"].replace("\\", "/")
            try:
                with open(f["full_path"], encoding="utf-8") as fh:
                    tree = ast.parse(fh.read())
            except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
                continue

            local_imports_in_file = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.level or not node.module:
                        continue
                    matched = self._match_module_to_file(node.module, rel)
                    if matched:
                        names = [a.asname or a.name for a in node.names]
                        local_imports_in_file.setdefault(matched, []).extend(names)

            used = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used.add(node.id)
                elif isinstance(node, ast.Attribute):
                    used.add(node.attr)

            for module, names in local_imports_in_file.items():
                unused = [n for n in names if n not in used]
                if unused:
                    results.append({
                        "file": rel,
                        "module": module,
                        "unused_names": unused,
                    })
        return results

    def to_tree(self, root_file: str | None = None) -> str:
        lines = []
        if root_file:
            nodes = {root_file: self.graph.get(root_file, set())}
            names = {root_file}
            for dep in self.graph.get(root_file, set()):
                names.add(dep)
        else:
            nodes = self.graph
            names = set(self.graph.keys())

        roots = sorted(names - set(self.reverse.keys()) - {"__init__.py"}) or sorted(names)
        if not roots:
            roots = sorted(names)

        def _render(node, prefix="", is_last=True, visited=None):
            if visited is None:
                visited = set()
            marker = "└── " if is_last else "├── "
            connector = "    " if is_last else "│   "
            lines.append(f"{prefix}{marker}{node}")
            if node in visited:
                return
            visited.add(node)
            deps = sorted(self.graph.get(node, set()))
            for i, dep in enumerate(deps):
                _render(dep, prefix + connector, i == len(deps) - 1, visited)

        for i, root in enumerate(roots):
            if i > 0:
                lines.append("")
            _render(root, "", i == len(roots) - 1)

        return "\n".join(lines) if lines else "(brak plików Python)"

    def summary(self, project: dict) -> dict:
        result = self.build(project)
        return {
            "total_python_files": len(self.graph),
            "dead_code": result["dead_code"],
            "cycles": result["cycles"],
            "high_impact": result["high_impact"][:5],
            "tree": self.to_tree(),
        }

    def to_dict(self) -> dict:
        return {
            "graph": {k: sorted(v) for k, v in self.graph.items()},
            "reverse": {k: sorted(v) for k, v in self.reverse.items()},
        }

    def save(self, path: str):
        import json
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
