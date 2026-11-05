"""Parsers for files commonly found in training-material repositories."""
import re

import yaml

from app.layer_3.plugins.shared.git_platform_client import FileNotFoundOnPlatformError

SITE_CONFIG_FILES = ("_quarto.yml", "_quarto.yaml", "mkdocs.yml", "mkdocs.yaml", "_config.yml", "_config.yaml")


class _LenientLoader(yaml.SafeLoader):
    """SafeLoader that ignores custom tags, e.g. !!python/name in mkdocs.yml."""


_LenientLoader.add_multi_constructor("", lambda loader, suffix, node: None)


def _names(value) -> list[str]:
    """Normalize an author value (text, dict, or list of either) into names."""
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, dict):
        return _names(value.get("name"))
    if isinstance(value, list):
        return [name for item in value for name in _names(item)]
    return []


def parse_site_config(file_name: str, content: str) -> dict:
    """Return title, description, authors, and language from a site config file."""
    try:
        data = yaml.load(content, Loader=_LenientLoader)
    except yaml.YAMLError:
        return {}
    if not isinstance(data, dict):
        return {}

    if file_name.startswith("mkdocs"):
        theme = data.get("theme") if isinstance(data.get("theme"), dict) else {}
        raw = {
            "title": data.get("site_name"),
            "description": data.get("site_description"),
            "authors": data.get("site_author"),
            "language": theme.get("language"),
        }
    elif file_name.startswith("_quarto"):
        project = {}
        for key in ("book", "website"):
            if isinstance(data.get(key), dict):
                project = data[key]
                break
        raw = {
            "title": project.get("title") or data.get("title"),
            "description": project.get("description") or data.get("description"),
            "authors": project.get("author") or data.get("author"),
            "language": data.get("lang"),
        }
    else:  # Jekyll or Jupyter Book
        raw = {
            "title": data.get("title"),
            "description": data.get("description"),
            "authors": data.get("author"),
            "language": data.get("lang") or data.get("language"),
        }

    result = {}
    for key in ("title", "description", "language"):
        if isinstance(raw[key], str) and raw[key].strip():
            result[key] = raw[key].strip()
    authors = _names(raw["authors"])
    if authors:
        result["authors"] = authors
    return result


def get_site_configs(client) -> list[dict]:
    """Parse every supported site config file in the repository root."""
    try:
        root = client.list_directory("")
    except FileNotFoundOnPlatformError:
        return []
    configs = []
    for entry in root:
        if entry.is_dir or entry.name.lower() not in SITE_CONFIG_FILES:
            continue
        content = client.get_file(entry.path).get_content()
        if content:
            parsed = parse_site_config(entry.name.lower(), content)
            if parsed:
                configs.append(parsed)
    return configs


def get_root_readme(client) -> str | None:
    """Return the README closest to the repository root."""
    readmes = sorted(client.get_readme_candidate_files(), key=lambda f: (f.path.count("/"), f.path))
    return readmes[0].get_content() if readmes else None


def _strip_code_blocks(markdown: str) -> str:
    return re.sub(r"^(```|~~~).*?^\1\s*$", "", markdown, flags=re.M | re.S)


def readme_title(markdown: str) -> str | None:
    """Return the text of the first level-1 Markdown heading."""
    match = re.search(r"^#[ \t]+(.+?)[ \t]*#*[ \t]*$", _strip_code_blocks(markdown), flags=re.M)
    return match.group(1).strip() if match else None


def readme_first_paragraph(markdown: str) -> str | None:
    """Return the first prose paragraph, skipping headings, badges, HTML, and lists."""
    for block in re.split(r"\n\s*\n", _strip_code_blocks(markdown)):
        text = " ".join(line.strip() for line in block.splitlines()).strip()
        if not text or text[0] in "#<|>-*+" or text.startswith(("![", "[![")) or text.startswith("---"):
            continue
        if len(text) >= 40:
            return text
    return None


def detect_learning_resource_types(paths: list[str]) -> list[str]:
    """Infer resource types from file and folder names."""
    lowered = [path.lower() for path in paths]
    parts = {part for path in lowered for part in path.split("/")}
    found = []
    if any(path.endswith(".ipynb") for path in lowered):
        found.append("notebook")
    if parts & {"slides", "slide", "presentations"} or any(path.endswith((".pptx", ".key")) for path in lowered):
        found.append("slides")
    if parts & {"exercises", "exercise", "practicals", "practical", "labs"}:
        found.append("exercise")
    if parts & {"tutorials", "tutorial", "episodes", "lessons", "_episodes"}:
        found.append("tutorial")
    return found
