from core.observer_policy import mutation, assert_write_path, scoped_open, scoped_remove, blocked
import os
import re
import ast
from datetime import datetime
from dataclasses import dataclass
from tools.file_tools import FileTools


@dataclass
class Patch:
    issue_type: str
    file: str
    description: str
    old_code: str | None
    new_code: str
    diff: str = ""
    confidence: float = 0.0
    backup_file: str | None = None
    applied: bool = False
    existed_before: bool = False


class PatchEngine:
    AUTO_CONFIDENCE = 0.85

    SECRET_PATTERNS = [
        (r'["\']api[_-]?key["\']\s*[:=]\s*["\'][^"\']+["\']', "API Key"),
        (r'(?:^|\s)(?:API_KEY|API_SECRET|CLIENT_SECRET)\s*=\s*["\'][^"\']+["\']', "API Key"),
        (r'password\s*=\s*["\'][^"\']+["\']', "Password"),
        (r'(?:^|\s)(?:PASSWORD|DB_PASSWORD|REDIS_PASSWORD)\s*=\s*["\'][^"\']+["\']', "Password"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "Secret"),
        (r'(?:^|\s)(?:SECRET|SECRET_KEY)\s*=\s*["\'][^"\']+["\']', "Secret"),
        (r'token\s*=\s*["\'][^"\']{20,}["\']', "Token"),
        (r'(?:^|\s)(?:TOKEN|AUTH_TOKEN|ACCESS_TOKEN)\s*=\s*["\'][^"\']{20,}["\']', "Token"),
    ]

    def __init__(self, file_tools: FileTools | None = None):
        self.ft = file_tools or FileTools()
        self.applied_patches: list[Patch] = []
        self._project_root: str = "."

    def suggest(self, issues: list[dict], project: dict | None = None) -> list[Patch]:
        patches: list[Patch] = []
        if project:
            self._project_root = project.get("path", ".")

        for issue in issues:
            issue_type = issue.get("type", "")
            priority = issue.get("priority", "")

            if issue_type == "security" and priority in ("HIGH", "MEDIUM"):
                for s in issue.get("secrets", []):
                    patch = self._fix_secret(s)
                    if patch:
                        patches.append(patch)

            if issue_type == "dependency":
                for unused in self._get_unused_imports(issue):
                    patch = self._fix_unused_import(unused)
                    if patch:
                        patches.append(patch)

            if issue_type == "code_quality":
                for func in issue.get("functions", []):
                    patch = self._fix_file_open(func)
                    if patch:
                        patches.append(patch)

            if issue_type == "structure":
                if "Brak punktu wejścia" in issue.get("issue", ""):
                    patch = self._fix_missing_entry(issue, project)
                    if patch:
                        patches.append(patch)

        if project:
            init_patches = self._fix_missing_init(project)
            patches.extend(init_patches)

        return patches

    # ── Fixers ──────────────────────────────────────────────

    def _fix_secret(self, secret: dict) -> Patch | None:
        filepath = secret.get("file", "")
        full_path = self._resolve_path(filepath)
        read = self.ft.read(full_path)
        if not read.get("success"):
            return None

        content = read["content"]
        secret_type = secret.get("type", "Secret")

        for pattern, _ in self.SECRET_PATTERNS:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            if not matches:
                continue

            for match in reversed(matches):
                line = match.group(0)
                var_match = re.match(r"""["']?(\w+)["']?\s*[:=]\s*""", line)
                var_name = var_match.group(1).strip("\"'") if var_match else secret_type.upper().replace(" ", "_")
                env_name = self._to_env_name(var_name)
                indent = re.match(r"^(\s*)", line).group(1)
                new_line = f'{indent}{var_name} = os.getenv("{env_name}")'
                content = content[:match.start()] + new_line + content[match.end():]

            needs_import = "import os" not in content and "from os" not in content
            if needs_import:
                first_import = re.search(r"^(import |from )", content, re.MULTILINE)
                if first_import:
                    insert_at = first_import.start()
                    content = content[:insert_at] + "import os\n" + content[insert_at:]
                else:
                    content = "import os\n\n" + content

            diff = self._generate_diff(filepath, read["content"], content)
            return Patch(
                issue_type="security",
                file=filepath,
                description=f"Zastąpiono {secret_type} zmienną środowiskową w {filepath}",
                old_code=read["content"],
                new_code=content,
                diff=diff,
                confidence=0.95,
            )

        return None

    def _fix_unused_import(self, unused: dict) -> Patch | None:
        filepath = unused.get("file", "")
        full_path = self._resolve_path(filepath)
        read = self.ft.read(full_path)
        if not read.get("success"):
            return None

        content = read["content"]
        names = set(unused.get("unused_names", []))
        if not names:
            return None

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return None

        module_ref = unused.get("module", "")
        expected_module = (
            module_ref.replace("\\", "/")
            .removesuffix(".py")
            .replace("/", ".")
            .strip(".")
        )
        if expected_module.endswith(".__init__"):
            expected_module = expected_module.removesuffix(".__init__")

        lines = content.splitlines(keepends=True)

        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue

            if node.level != 0 or not node.module:
                continue

            # Exact module matching. Never use substring matching here.
            if node.module != expected_module:
                continue

            # Star imports are too ambiguous for autonomous removal.
            if any(alias.name == "*" for alias in node.names):
                return None

            # Be conservative with multiline imports. They may contain
            # comments/formatting that a one-line rewrite could destroy.
            if node.end_lineno and node.end_lineno != node.lineno:
                return None

            bindings = []
            for alias in node.names:
                binding = alias.asname or alias.name
                if binding not in names:
                    bindings.append(alias)

            if len(bindings) == len(node.names):
                return None

            start_line = node.lineno - 1
            end_line = node.end_lineno or node.lineno

            if not bindings:
                new_lines = lines[:start_line] + lines[end_line:]
            else:
                original_line = lines[start_line]
                indent = original_line[:len(original_line) - len(original_line.lstrip())]

                # Avoid silently deleting an inline comment.
                if "#" in original_line:
                    return None

                rendered = ", ".join(
                    f"{alias.name} as {alias.asname}" if alias.asname else alias.name
                    for alias in bindings
                )
                replacement = f"{indent}from {node.module} import {rendered}\n"

                new_lines = (
                    lines[:start_line]
                    + [replacement]
                    + lines[end_line:]
                )

            new_content = "".join(new_lines)

            if new_content == read["content"]:
                return None

            diff = self._generate_diff(filepath, read["content"], new_content)
            return Patch(
                issue_type="dependency",
                file=filepath,
                description=(
                    f"Usunięto nieużywane importy w {filepath}: "
                    f"{', '.join(sorted(names))}"
                ),
                old_code=read["content"],
                new_code=new_content,
                diff=diff,
                confidence=0.90,
            )

        return None

    def _fix_file_open(self, func_info: dict) -> Patch | None:
        filepath = func_info.get("file", "")
        full_path = self._resolve_path(filepath)
        read = self.ft.read(full_path)
        if not read.get("success"):
            return None

        content = read["content"]
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return None

        lines = content.splitlines(keepends=True)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                continue
            if not isinstance(node.value, ast.Call):
                continue
            call = node.value
            if not isinstance(call.func, ast.Name) or call.func.id != "open":
                continue

            var_name = node.targets[0].id
            func_body = self._find_enclosing_function(tree, node.lineno)
            if not func_body:
                continue

            close_lineno = None
            for child in ast.walk(func_body):
                if isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
                    c = child.value
                    if (isinstance(c.func, ast.Attribute) and c.func.attr == "close"
                            and isinstance(c.func.value, ast.Name) and c.func.value.id == var_name):
                        if child.lineno and child.end_lineno:
                            close_lineno = child.lineno
                            break

            if close_lineno is None:
                continue

            open_line_idx = node.lineno - 1
            close_line_idx = close_lineno - 1

            indent = re.match(r"^(\s*)", lines[open_line_idx]).group(1)
            open_line = lines[open_line_idx].strip()
            args_start = open_line.index("(")
            args_end = open_line.rindex(")") + 1
            args_str = open_line[args_start:args_end]

            body_content = []
            for i in range(open_line_idx + 1, len(lines)):
                if i == close_line_idx:
                    continue
                if i > close_line_idx:
                    break
                body_content.append(lines[i])

            new_lines = (
                lines[:open_line_idx]
                + [f"{indent}with open{args_str} as {var_name}:\n"]
                + [f"{indent}    {l.lstrip()}" if l.strip() else "\n" for l in body_content]
                + lines[close_line_idx + 1:]
            )

            new_content = "".join(new_lines)
            if new_content == read["content"]:
                return None

            diff = self._generate_diff(filepath, read["content"], new_content)
            return Patch(
                issue_type="code_quality",
                file=filepath,
                description=f"Zamieniono open() na with open() w {filepath} (zmienna: {var_name})",
                old_code=read["content"],
                new_code=new_content,
                diff=diff,
                confidence=0.80,
            )

        return None

    def _fix_missing_entry(self, issue: dict, project: dict | None) -> Patch | None:
        if not project:
            return None
        project_path = project.get("path", ".")
        main_path = os.path.join(project_path, "main.py")

        if os.path.exists(main_path):
            return None

        project_name = project.get("name", "app")
        boilerplate = (
            f'"""\n{project_name} - Entry point\n"""\n'
            f'\n'
            f'def main():\n'
            f'    print("Hello from {project_name}!")\n'
            f'\n'
            f'\n'
            f'if __name__ == "__main__":\n'
            f'    main()\n'
        )

        diff = (
            f"--- /dev/null\n"
            f"+++ b/{os.path.join(os.path.basename(project_path), 'main.py')}\n"
            f"@@ -0,0 +1,8 @@\n"
        )
        for line in boilerplate.splitlines():
            diff += f"+{line}\n"

        return Patch(
            issue_type="structure",
            file="main.py",
            description=f"Utworzono brakujący punkt wejścia main.py dla {project_name}",
            old_code=None,
            new_code=boilerplate,
            diff=diff,
            confidence=0.90,
        )

    def _fix_missing_init(self, project: dict) -> list[Patch]:
        patches: list[Patch] = []
        project_path = project.get("path", ".")
        seen = set()

        for f in project.get("files", []):
            rel = f.get("path", "")
            dir_name = os.path.dirname(rel)
            if not dir_name or dir_name in seen:
                continue
            seen.add(dir_name)
            init_path = os.path.join(project_path, dir_name, "__init__.py")
            if os.path.exists(init_path):
                continue

            content = ""
            diff = (
                f"--- /dev/null\n"
                f"+++ b/{dir_name}/__init__.py\n"
                f"@@ -0,0 +1 @@\n"
                f"+{content}\n"
            )
            patches.append(Patch(
                issue_type="structure",
                file=f"{dir_name}/__init__.py",
                description=f"Utworzono brakujące {dir_name}/__init__.py",
                old_code=None,
                new_code=content,
                diff=diff,
                confidence=0.95,
            ))

        return patches

    # ── Verification ───────────────────────────────────────

    def verify_patch(self, patch: Patch) -> tuple[bool, str]:
        """Weryfikuje zmianę po zapisie, przed commitowaniem."""
        try:
            full_path = self._assert_write_path(self._resolve_path(patch.file))
        except (ValueError, OSError) as e:
            return False, str(e)

        if not os.path.exists(full_path):
            return False, "Plik docelowy nie istnieje po zapisie"

        read = self.ft.read(full_path)
        if not read.get("success"):
            return False, read.get("error", "Nie można odczytać pliku po zapisie")

        actual = read.get("content", "")

        if actual != patch.new_code:
            return False, "Zawartość pliku różni się od treści patcha"

        if patch.file.lower().endswith(".py"):
            try:
                ast.parse(actual, filename=patch.file)
            except SyntaxError as e:
                return False, f"Błąd składni Python: {e}"

        return True, "Weryfikacja OK"

    # ── Apply & Rollback ────────────────────────────────────

    @mutation("brain/patch_engine.py:apply_patch", controlled=True)
    def apply_patch(self, patch: Patch) -> bool:
        return bool(self.apply_patches([patch]))

    @mutation("brain/patch_engine.py:apply_patches", controlled=True)
    def apply_patches(self, patches: list[Patch], auto_confirm: bool = True) -> list[Patch]:
        """Validate the entire batch, then write and verify; never execute Git."""
        if auto_confirm is not True or not patches:
            return []
        prepared = []
        touched = []
        try:
            # Preflight all targets and syntax before the first backup or write.
            paths = [self._assert_write_path(self._resolve_path(p.file)) for p in patches]
            if len(set(paths)) != len(paths):
                return []
            for patch in patches:
                if patch.file.lower().endswith('.py'):
                    ast.parse(patch.new_code, filename=patch.file)
            for patch, path in zip(patches, paths):
                patch.existed_before = os.path.exists(path)
                patch.backup_file = None
                if patch.existed_before:
                    backup = f"{path}.backup.{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                    # Exclusive creation also refuses a pre-existing backup symlink.
                    with open(path, 'rb') as source, scoped_open(backup, 'xb') as dest:
                        dest.write(source.read())
                    patch.backup_file = backup
                touched.append(patch)
                if not self.ft.write(path, patch.new_code, backup=False).get('success'):
                    raise OSError('Patch write failed')
                valid, reason = self.verify_patch(patch)
                if not valid:
                    raise ValueError(reason)
                prepared.append(patch)
            for patch in prepared:
                patch.applied = True
            self.applied_patches.extend(prepared)
            return prepared
        except (OSError, ValueError, SyntaxError, RuntimeError):
            for patch in reversed(touched):
                if not self.rollback(patch):
                    raise RuntimeError('R1: rollback failed; manual recovery required')
            return []

    @mutation("brain/patch_engine.py:_git_commit_batch")
    def _git_commit_batch(self, patches: list[Patch]) -> bool:
        return blocked('patch.git_commit_batch')

    @mutation("brain/patch_engine.py:rollback", controlled=True)
    def rollback(self, patch: Patch) -> bool:
        try:
            path = self._assert_write_path(self._resolve_path(patch.file))
            if patch.existed_before:
                if not patch.backup_file:
                    return False
                backup = self._assert_write_path(patch.backup_file)
                with open(backup, 'rb') as source, scoped_open(path, 'wb') as dest:
                    dest.write(source.read())
            elif os.path.exists(path):
                scoped_remove(path)
            patch.applied = False
            return True
        except (OSError, ValueError, RuntimeError):
            return False

    def preview(self, patches: list[Patch]) -> str:
        lines = []
        for p in patches:
            lines.append(f"[{p.confidence:.0%}] {p.description}")
            lines.append(f"       diff: {p.diff.split(chr(10))[0] if p.diff else '(nowy plik)'}")
            lines.append("")
        return "\n".join(lines)

    # ── Helpers ─────────────────────────────────────────────

    def _resolve_path(self, filepath: str) -> str:
        if os.path.isabs(filepath):
            return filepath
        return os.path.join(self._project_root, filepath)

    def _assert_write_path(self, full_path: str) -> str:
        root = os.path.realpath(self._project_root)
        target = os.path.realpath(full_path)

        try:
            if os.path.commonpath([root, target]) != root:
                raise ValueError(f"Ścieżka poza project_root: {full_path}")
        except ValueError:
            raise ValueError(f"Ścieżka poza project_root: {full_path}")

        return assert_write_path(target)

    def _to_env_name(self, name: str) -> str:
        s = re.sub(r"[\"'\s]", "", name)
        s = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", s)
        s = s.upper().replace("-", "_")
        return s

    def _get_unused_imports(self, issue: dict) -> list[dict]:
        results = []
        for s in issue.get("suggestions", []):
            s_type = s.get("type", "")
            if s_type in ("unused_import", "import"):
                results.append({
                    "file": s.get("file", ""),
                    "module": s.get("module", ""),
                    "unused_names": s.get("unused_names", []),
                })

        return results

    def _generate_diff(self, filepath: str, old: str, new: str) -> str:
        old_lines = old.splitlines(True)
        new_lines = new.splitlines(True)

        import difflib
        diff_lines = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}",
            n=3,
        ))
        return "".join(diff_lines)

    def _find_enclosing_function(self, tree: ast.AST, lineno: int) -> ast.FunctionDef | None:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.lineno <= lineno <= (node.end_lineno or lineno):
                    return node
        return None

    @mutation("brain/patch_engine.py:_git_commit")
    def _git_commit(self, patch: Patch) -> bool:
        return blocked('patch.git_commit')
