"""File-based wiki helpers. No network, deletion, inference, or model execution."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import quote, unquote, urlsplit
import uuid

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML is required: py -3 -m pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("theory", "quantitative", "reference", "observations", "agent")
KINDS = {
    "concept": "concepts", "entity": "entities", "synthesis": "syntheses",
    "procedure": "procedures", "note": "notes", "model": "models",
}
MARKER = "<!-- wiki-template:index -->"
STATUSES = {"draft", "stable", "deprecated"}
CLAIMS = {"source-report", "sourced-summary", "interpretation", "hypothesis",
          "personal-observation", "procedure"}
METHODS = {"reported", "observed", "derived", "modeled", "unavailable"}


class WikiError(ValueError):
    pass


class UniqueSafeLoader(yaml.SafeLoader):
    """Reject silent YAML key replacement; retain SafeLoader's tag restrictions."""


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise WikiError("YAML mapping keys must be strings")
        try:
            if key in result:
                raise WikiError(f"Duplicate YAML key: {key}")
            result[key] = loader.construct_object(value_node, deep=deep)
        except TypeError:
            raise WikiError("YAML keys must be scalar values")
    return result


UniqueSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise WikiError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"),
                      object_pairs_hook=unique_json)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() if hasattr(
            hashlib, "file_digest") else stream_digest(stream)


def stream_digest(stream):
    result = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        result.update(block)
    return result.hexdigest()


def body_digest(body):
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def review_digest(page):
    metadata = {key: value for key, value in page.metadata.items()
                if key not in {"generated", "verified", "review_basis"}}
    content = json.dumps({"metadata": metadata, "body": page.body},
                         sort_keys=True, ensure_ascii=False, default=str)
    return body_digest(content)


def within(path, root):
    return path.resolve().is_relative_to(root.resolve())


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_new(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def json_text(data):
    return json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def slug(text):
    value = re.sub(r"[^\w]+", "-", text.casefold(), flags=re.UNICODE).strip("-_")
    if not value or value in {"con", "prn", "aux", "nul"} or re.fullmatch(
            r"(?:com|lpt)[1-9]", value):
        raise WikiError("Choose a descriptive filename without Windows device names")
    return value


@dataclass
class Page:
    path: Path
    metadata: dict
    body: str


@dataclass
class Report:
    vault: Path
    config: dict = field(default_factory=dict)
    pages: list[Page] = field(default_factory=list)
    records: list[tuple[Path, dict]] = field(default_factory=list)
    captures: dict = field(default_factory=dict)
    issues: list[tuple[str, str]] = field(default_factory=list)

    def issue(self, level, path, message):
        name = str(path.relative_to(self.vault)) if within(path, self.vault) else str(path)
        self.issues.append((level, f"{name}: {message}"))

    @property
    def errors(self):
        return [message for level, message in self.issues if level == "ERROR"]


def read_page(path):
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise WikiError("Missing YAML frontmatter")
    closing = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if closing is None:
        raise WikiError("Unclosed YAML frontmatter")
    metadata = yaml.load("".join(lines[1:closing]), Loader=UniqueSafeLoader)
    if not isinstance(metadata, dict):
        raise WikiError("Frontmatter must be a mapping")
    return Page(path, metadata, "".join(lines[closing + 1:]))


def resolve_reference(vault, origin, reference):
    if not isinstance(reference, str) or not reference.strip():
        raise WikiError("Reference must be a nonempty string")
    reference = reference.strip().strip("<>")
    if re.match(r"^[A-Za-z]:[\\/]", reference) or "\\" in reference:
        raise WikiError("Use portable forward-slash relative paths")
    parts = urlsplit(reference)
    if parts.scheme or parts.netloc:
        return None
    if not parts.path:
        return origin
    root = vault / "wiki"
    target = root / unquote(parts.path.lstrip("/")) if parts.path.startswith(
        "/") else origin.parent / unquote(parts.path)
    target = target.resolve()
    if not within(target, vault):
        raise WikiError("Reference escapes the vault")
    return target


def check_reference(report, path, reference):
    try:
        target = resolve_reference(report.vault, path, reference)
        if target is not None and not target.exists():
            report.issue("ERROR", path, f"Missing reference: {reference}")
        return target
    except (WikiError, ValueError, OSError) as error:
        report.issue("ERROR", path, str(error))
        return None


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def check_timestamp(report, path, value):
    try:
        timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if timestamp.utcoffset() is None:
            raise ValueError("Timezone is required")
        return timestamp
    except (ValueError, TypeError):
        report.issue("ERROR", path, f"Invalid timezone-aware timestamp: {value}")
        return None


def markdown_without_code(body):
    body = re.sub(r"(?ms)^(?:\x60{3,}|~{3,})[^\n]*\n.*?^(?:\x60{3,}|~{3,})[^\n]*$", "", body)
    return re.sub(r"\x60[^\x60]*\x60", "", body)


def check_markdown(report, page, source_ids):
    text = markdown_without_code(page.body)
    if "[[" in text:
        report.issue("ERROR", page.path, "Use ordinary Markdown links instead of wikilinks")
    for match in re.finditer(r"\[[^\]]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\s*\)", text):
        check_reference(report, page.path, match.group(1))
    refs = {}
    for match in re.finditer(r"(?m)^\[(?!\^)([^\]]+)\]:\s*(<[^>]+>|[^\s]+)", text):
        refs[match.group(1).casefold()] = match.group(2)
        check_reference(report, page.path, match.group(2))
    for match in re.finditer(r"\[(?!\^)([^\]]+)\]\[([^\]]*)\]", text):
        name = (match.group(2) or match.group(1)).casefold()
        if name not in refs:
            report.issue("ERROR", page.path, f"Undefined link reference: {name}")
    definitions = re.findall(r"(?m)^\[\^([^\]]+)\]:", text)
    if len(definitions) != len(set(definitions)):
        report.issue("ERROR", page.path, "Duplicate footnote definitions")
    used = set(re.findall(r"\[\^([^\]]+)\](?!:)", text))
    for citation in sorted(used):
        if citation not in definitions or citation not in source_ids:
            report.issue("ERROR", page.path, f"Unresolved source footnote: {citation}")
    for citation in definitions:
        if citation not in source_ids:
            report.issue("ERROR", page.path, f"Footnote has no sources entry: {citation}")


def check_page(report, page):
    meta, path = page.metadata, page.path
    for key in ("type", "title", "description", "status", "ownership", "claim_kind"):
        if not nonempty(meta.get(key)):
            report.issue("ERROR", path, f"Missing or invalid {key}")
    if str(meta.get("status")) not in STATUSES:
        report.issue("ERROR", path, "Invalid status")
    if str(meta.get("ownership")) not in {"human", "collaborative", "agent"}:
        report.issue("ERROR", path, "Invalid ownership")
    if str(meta.get("claim_kind")) not in CLAIMS:
        report.issue("ERROR", path, "Invalid claim_kind")
    for key in ("aliases", "tags", "inputs"):
        if key in meta and (not isinstance(meta[key], list) or not all(
                nonempty(value) for value in meta[key])):
            report.issue("ERROR", path, f"{key} must be a list of nonempty strings")
    sources = meta.get("sources", [])
    if not isinstance(sources, list):
        report.issue("ERROR", path, "Sources must be a list")
        sources = []
    source_ids = set()
    for entry in sources:
        if not isinstance(entry, dict) or not nonempty(entry.get("resource")):
            report.issue("ERROR", path, "Every source needs a resource")
            continue
        source_id = entry.get("id")
        if not nonempty(source_id) or source_id in source_ids:
            report.issue("ERROR", path, "Every source needs a unique id")
        else:
            source_ids.add(source_id)
        check_reference(report, path, entry["resource"])
    personal = str(meta.get("claim_kind")) in {"hypothesis", "personal-observation"}
    if personal and not str(meta.get("author", "")).startswith("human:"):
        report.issue("ERROR", path, "Personal claims need a human author")
    if meta.get("type") == "source":
        check_reference(report, path, meta.get("resource"))
        capture_id = meta.get("capture_id")
        if capture_id and (not nonempty(capture_id) or capture_id not in report.captures):
            report.issue("ERROR", path, "Unknown capture_id")
        elif capture_id and meta.get("resource") != report.captures[capture_id]["resource"]:
            report.issue("ERROR", path, "Source resource differs from its captured version")
        if not capture_id:
            report.issue("WARN", path, "Source has no preserved capture")
    elif meta.get("status") == "stable" and not sources and not personal:
        report.issue("ERROR", path, "Stable sourced content needs provenance")
    if meta.get("status") == "draft":
        report.issue("WARN", path, "Draft needs editorial review")
    for key in ("generated", "verified"):
        events = meta.get(key)
        if events is None:
            continue
        events = events if isinstance(events, list) else [events]
        for event in events:
            if not isinstance(event, dict) or not nonempty(event.get("by")):
                report.issue("ERROR", path, f"Invalid {key} actor")
                continue
            actor = event["by"]
            if not (re.fullmatch(r"(human|process):\S+", actor) or re.fullmatch(r"\S+/\S+", actor)):
                report.issue("ERROR", path, f"Invalid actor convention: {actor}")
            if key == "verified" or "at" in event:
                check_timestamp(report, path, event.get("at"))
    if meta.get("verified"):
        if not meta.get("review_basis"):
            report.issue("WARN", path, "Review has no content revision hash")
        elif str(meta["review_basis"]).lower() != review_digest(page):
            report.issue("ERROR", path, "Review does not cover the current content")
    if "stale_after" in meta:
        timestamp = check_timestamp(report, path, meta["stale_after"])
        if timestamp and timestamp <= datetime.now(timezone.utc):
            report.issue("WARN", path, "Review date is due")
    for reference in meta.get("inputs", []) if isinstance(meta.get("inputs", []), list) else []:
        if nonempty(reference):
            check_reference(report, path, reference)
    relations = meta.get("relations", [])
    if not isinstance(relations, list):
        report.issue("ERROR", path, "Relations must be a list")
        relations = []
    for relation in relations:
        if not isinstance(relation, dict) or not nonempty(relation.get("kind")):
            report.issue("ERROR", path, "Relationship needs a kind and target")
            continue
        check_reference(report, path, relation.get("target"))
        if not personal and (not nonempty(relation.get("source_id")) or relation.get("source_id") not in source_ids):
            report.issue("ERROR", path, "Relationship needs a known source_id")
    check_markdown(report, page, source_ids)


def check_record(report, path, record, ids):
    if not isinstance(record, dict):
        report.issue("ERROR", path, "Observation must be one JSON object")
        return
    for key in ("id", "metric", "label", "unit", "period", "scope", "universe",
                "method", "source", "locator"):
        if not nonempty(record.get(key)):
            report.issue("ERROR", path, f"Missing or invalid observation {key}")
    record_id = record.get("id")
    if isinstance(record_id, str):
        if record_id in ids:
            report.issue("ERROR", path, f"Duplicate observation id: {record_id}")
        ids.add(record_id)
    value, low, high = (record.get(key) for key in ("value", "low", "high"))
    if "value" not in record or (value is not None and not finite(value)):
        report.issue("ERROR", path, "Value must be a finite number or null")
    has_range = "low" in record or "high" in record
    if has_range and (not finite(low) or not finite(high) or low > high):
        report.issue("ERROR", path, "Range needs finite ordered low and high")
    if finite(value) and finite(low) and finite(high) and not low <= value <= high:
        report.issue("ERROR", path, "Central value is outside the range")
    method = record.get("method")
    if str(method) not in METHODS:
        report.issue("ERROR", path, "Invalid observation method")
    if value is None and not has_range and (method != "unavailable" or not nonempty(record.get("notes"))):
        report.issue("ERROR", path, "Missing value needs method unavailable and an explanation")
    if method == "unavailable" and (value is not None or has_range):
        report.issue("ERROR", path, "Unavailable observation cannot contain a numeric value or range")
    if str(record.get("qualifier", "eq")) not in {"eq", "lt", "lte", "gt", "gte"}:
        report.issue("ERROR", path, "Invalid numeric qualifier")
    target = check_reference(report, path, record.get("source"))
    source_pages = {page.path.resolve(): page for page in report.pages}
    if (target is None or target.suffix != ".md" or not within(target, report.vault / "wiki" / "sources")
            or target not in source_pages or source_pages[target].metadata.get("type") != "source"):
        report.issue("ERROR", path, "Observation must reference a local source page")


def inspect_vault(vault, check_indexes=True):
    vault = Path(vault).resolve()
    report = Report(vault)
    if (not (vault / "config.json").is_file() or not (vault / "wiki").is_dir()
            or not within(vault / "config.json", vault) or not within(vault / "wiki", vault)):
        raise WikiError(f"No configured vault at {vault}. Run init for a new private wiki.")
    try:
        report.config = read_json(vault / "config.json")
        config = report.config
        if not isinstance(config, dict) or not nonempty(config.get("title")) or config.get("schema_version") != 1:
            raise WikiError("Config needs title and schema_version 1")
        if not isinstance(config.get("profiles"), list) or not config["profiles"] or any(
                profile not in PROFILES for profile in config["profiles"]):
            raise WikiError("Config needs known profiles")
        if config.get("save_answers") not in {"on_request", "reusable"}:
            raise WikiError("save_answers must be on_request or reusable")
    except (ValueError, OSError, TypeError) as error:
        report.issue("ERROR", vault / "config.json", str(error))
        report.config = {"title": "Invalid configuration"}
    manifest_path = vault / "raw" / "manifest.json"
    try:
        if not within(manifest_path, vault):
            raise WikiError("Manifest path escapes the vault")
        manifest = read_json(manifest_path)
        if not isinstance(manifest, dict) or manifest.get("version") != 1 or not isinstance(manifest.get("captures"), list):
            raise WikiError("Manifest needs version 1 and a captures list")
        for capture in manifest["captures"]:
            if not isinstance(capture, dict) or not nonempty(capture.get("id")):
                raise WikiError("Invalid capture record")
            capture_id = capture["id"]
            if capture_id in report.captures:
                report.issue("ERROR", manifest_path, f"Duplicate capture id: {capture_id}")
            report.captures[capture_id] = capture
            for key in ("source_key", "title", "resource", "original_name", "path", "sha256", "captured_at"):
                if not nonempty(capture.get(key)):
                    report.issue("ERROR", manifest_path, f"Capture {capture_id} needs {key}")
            if not nonempty(capture.get("path")):
                continue
            target = (vault / capture["path"]).resolve()
            if not within(target, vault / "raw") or not target.is_file():
                report.issue("ERROR", manifest_path, f"Capture {capture_id} has an invalid raw path")
                continue
            if digest(target) != capture.get("sha256") or target.stat().st_size != capture.get("bytes"):
                report.issue("ERROR", manifest_path, f"Capture {capture_id} bytes or hash changed")
            check_timestamp(report, manifest_path, capture.get("captured_at"))
    except (ValueError, OSError, TypeError) as error:
        report.issue("ERROR", manifest_path, str(error))
    for path in sorted((vault / "wiki").rglob("*.md")):
        if not within(path, vault / "wiki"):
            report.issue("ERROR", path, "Content path escapes the bundle")
            continue
        if path.name == "index.md":
            text = path.read_text(encoding="utf-8-sig")
            check_markdown(report, Page(path, {}, text), set())
            if path.parent != vault / "wiki" and text.startswith("---"):
                report.issue("ERROR", path, "Child indexes must not contain frontmatter")
            if path.parent == vault / "wiki" and text.startswith("---"):
                try:
                    index_meta = read_page(path).metadata
                    if set(index_meta) != {"okf_version"} or str(index_meta["okf_version"]) != "0.2":
                        raise WikiError("Root index may declare only okf_version 0.2")
                except (ValueError, yaml.YAMLError) as error:
                    report.issue("ERROR", path, str(error))
            continue
        if path.name == "log.md":
            headings = re.findall(r"(?m)^## (.+)$", path.read_text(encoding="utf-8-sig"))
            valid_dates = []
            for heading in headings:
                try:
                    value = datetime.strptime(heading, "%Y-%m-%d").date()
                    valid_dates.append(value)
                except ValueError:
                    report.issue("ERROR", path, "Log date headings must be YYYY-MM-DD")
            if valid_dates != sorted(valid_dates, reverse=True):
                report.issue("ERROR", path, "Log dates must be newest first")
            continue
        try:
            report.pages.append(read_page(path))
        except (ValueError, OSError, yaml.YAMLError) as error:
            report.issue("ERROR", path, str(error))
    for page in report.pages:
        check_page(report, page)
    ids = set()
    for path in sorted((vault / "wiki" / "observations").rglob("*.json")):
        if not within(path, vault / "wiki"):
            report.issue("ERROR", path, "Observation path escapes the bundle")
            continue
        try:
            record = read_json(path)
            check_record(report, path, record, ids)
            if isinstance(record, dict):
                report.records.append((path, record))
        except (ValueError, OSError) as error:
            report.issue("ERROR", path, str(error))
    if check_indexes and not report.errors:
        for path, expected in index_plan(report).items():
            if not path.exists():
                report.issue("WARN", path, "Index is missing; run index")
            elif MARKER in path.read_text(encoding="utf-8") and path.read_text(encoding="utf-8") != expected:
                report.issue("WARN", path, "Generated index is stale; run index")
    return report


def label(text):
    return " ".join(str(text).split()).replace("[", r"\[").replace("]", r"\]")


def index_plan(report):
    bundle = report.vault / "wiki"
    directories = {bundle} | {path for path in bundle.rglob("*") if path.is_dir() and within(path, bundle)}
    entries = {}
    for page in report.pages:
        entries[page.path] = (page.metadata.get("title"), page.metadata.get("description"))
    for path, record in report.records:
        entries[path] = (record.get("label"), f"{record.get('metric')} | {record.get('period')} | {record.get('universe')}")
    plan = {}
    for directory in sorted(directories):
        root = directory == bundle
        heading = report.config["title"] if root else directory.name.replace("-", " ").title()
        lines = ['---\nokf_version: "0.2"\n---\n'] if root else []
        lines += [MARKER, f"# {label(heading)}", ""]
        for child in sorted(directories):
            if child.parent == directory:
                lines.append(f"- [{label(child.name)}]({quote(child.name)}/index.md) - Browse this section.")
        for path, (title, description) in sorted(entries.items()):
            if path.parent == directory:
                lines.append(f"- [{label(title)}]({quote(path.name)}) - {label(description)}")
        if not any(line.startswith("- ") for line in lines):
            lines.append("No entries yet.")
        if root:
            lines += ["", "[Update log](log.md)."]
        plan[directory / "index.md"] = "\n".join(lines) + "\n"
    return plan


def require_valid(report):
    if report.errors:
        raise WikiError("\n".join(report.errors))


def build_indexes(vault):
    report = inspect_vault(vault, check_indexes=False)
    require_valid(report)
    plan = index_plan(report)
    for path in plan:
        if path.exists() and MARKER not in path.read_text(encoding="utf-8"):
            raise WikiError(f"Preserving unmarked index: {path}. Update it manually.")
    changed = 0
    for path, text in plan.items():
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            atomic_write(path, text)
            changed += 1
    return changed


def initialize(vault, title, profiles):
    vault = Path(vault).resolve()
    if not within(vault, ROOT / ".local"):
        raise WikiError("New private vaults must be inside this repository's .local directory")
    if not nonempty(title) or not profiles or any(profile not in PROFILES for profile in profiles):
        raise WikiError("Initialization needs a title and known profiles")
    if vault.exists() and any(vault.iterdir()):
        raise WikiError("Vault is not empty; existing content is preserved")
    folders = ["sources", *KINDS.values()]
    if "quantitative" in profiles or "observations" in profiles:
        folders.append("observations")
    for name in folders:
        (vault / "wiki" / name).mkdir(parents=True, exist_ok=True)
    (vault / "raw").mkdir(parents=True, exist_ok=True)
    write_new(vault / "config.json", json_text({
        "schema_version": 1, "title": title, "profiles": list(dict.fromkeys(profiles)),
        "save_answers": "on_request",
    }))
    write_new(vault / "raw" / "manifest.json", json_text({"version": 1, "captures": []}))
    write_new(vault / "wiki" / "log.md", "# Update log\n\nAdd meaningful ingests and revisions under ISO date headings, newest first.\n")
    build_indexes(vault)


def page_text(metadata, body):
    return "---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).rstrip() + "\n---\n" + body


def create_page(vault, kind, title, description):
    if not nonempty(title) or not nonempty(description):
        raise WikiError("A new page needs a title and description")
    report = inspect_vault(vault, check_indexes=False)
    require_valid(report)
    template = read_page(ROOT / "templates" / f"{kind}.md")
    meta = template.metadata.copy()
    meta.update(title=title, description=description, generated={"by": "process:wiki-template", "at": now()})
    target = report.vault / "wiki" / KINDS[kind] / f"{slug(title)}.md"
    if not within(target, report.vault / "wiki"):
        raise WikiError("New page path escapes the bundle")
    write_new(target, page_text(meta, template.body.replace("PAGE_TITLE", title)))
    return target


def capture_source(vault, supplied_file, source_key, title, resource=None):
    if not nonempty(title) or (resource is not None and (
            not nonempty(resource) or not urlsplit(resource).scheme)):
        raise WikiError("Capture needs a title and an original URL or URI, when supplied")
    report = inspect_vault(vault, check_indexes=False)
    require_valid(report)
    source = Path(supplied_file).resolve()
    if not source.is_file():
        raise WikiError("Supplied source is not a file")
    source_key = slug(source_key)
    sha = digest(source)
    capture_id = f"{source_key}--{sha[:16]}"
    resource = resource or f"urn:local:{source_key}"
    previous = report.captures.get(capture_id)
    if previous and (previous["sha256"] != sha or previous["resource"] != resource):
        raise WikiError("Capture identity or resource differs from the preserved version")
    extension = source.suffix.lower() if re.fullmatch(r"\.[a-zA-Z0-9]+", source.suffix) else ".bin"
    target = report.vault / "raw" / "captures" / capture_id / f"original{extension}"
    source_page = report.vault / "wiki" / "sources" / f"{capture_id}.md"
    if not within(target, report.vault / "raw") or not within(source_page, report.vault / "wiki"):
        raise WikiError("Capture destination escapes the vault")
    if not previous:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise WikiError(f"Unregistered existing capture is preserved: {target}")
        if shutil.disk_usage(target.parent).free < source.stat().st_size + 1024 * 1024:
            raise WikiError("Insufficient free space for the source capture")
        with source.open("rb") as original, target.open("xb") as destination:
            shutil.copyfileobj(original, destination)
        if digest(target) != sha:
            raise WikiError("Source changed during capture; copied bytes are retained for inspection")
        entry = {
            "id": capture_id, "source_key": source_key, "title": title, "resource": resource,
            "original_name": source.name, "path": target.relative_to(report.vault).as_posix(),
            "sha256": sha, "bytes": target.stat().st_size, "captured_at": now(),
        }
        manifest_path = report.vault / "raw" / "manifest.json"
        manifest = read_json(manifest_path)
        manifest["captures"].append(entry)
        atomic_write(manifest_path, json_text(manifest))
    if not source_page.exists():
        meta = read_page(ROOT / "templates" / "source.md").metadata
        meta.update(title=title, description=f"Preserved source: {title}.",
                    resource=resource, capture_id=capture_id,
                    generated={"by": "process:wiki-template", "at": now()})
        link = quote(os.path.relpath(target, source_page.parent).replace("\\", "/"))
        body = f"\n# {title}\n\n[Preserved original]({link}).\n\n## Summary\n\nNot yet ingested. Read the original before extracting claims.\n\n## Coverage and questions\n\nRecord scope, extraction coverage, useful locators, and unresolved questions.\n"
        write_new(source_page, page_text(meta, body))
    return capture_id, source_page, bool(previous)


def find_pages(report, query, include_deprecated=False):
    require_valid(report)
    terms = re.findall(r"\w+", query.casefold(), flags=re.UNICODE)
    if not terms:
        raise WikiError("Search needs at least one word")
    results = []
    for page in report.pages:
        meta = page.metadata
        if meta["status"] == "deprecated" and not include_deprecated:
            continue
        title = Counter(re.findall(r"\w+", " ".join([meta["title"], *meta.get("aliases", [])]).casefold()))
        metadata = Counter(re.findall(r"\w+", " ".join([meta["description"], *meta.get("tags", [])]).casefold()))
        body = Counter(re.findall(r"\w+", page.body.casefold()))
        if all(term in title or term in metadata or term in body for term in terms):
            score = sum(10 * title[term] + 3 * metadata[term] + body[term] for term in terms)
            results.append({"path": page.path.relative_to(report.vault / "wiki").as_posix(),
                            "title": meta["title"], "description": meta["description"], "score": score})
    return sorted(results, key=lambda result: (-result["score"], result["path"]))


def select_records(report, filters):
    require_valid(report)
    return [dict(record, path=path.relative_to(report.vault / "wiki").as_posix())
            for path, record in report.records
            if all(record.get(key) == value for key, value in filters.items())]


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, default=ROOT / ".local" / "vault")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Initialize an empty private vault")
    init.add_argument("--title", required=True)
    init.add_argument("--profile", choices=PROFILES, action="append", required=True)
    new = commands.add_parser("new", help="Create a blank draft without replacing files")
    new.add_argument("kind", choices=KINDS)
    new.add_argument("--title", required=True)
    new.add_argument("--description", required=True)
    capture = commands.add_parser("capture", help="Preserve local source bytes and a draft source page")
    capture.add_argument("file", type=Path)
    capture.add_argument("--source-id", required=True)
    capture.add_argument("--title", required=True)
    capture.add_argument("--resource")
    check = commands.add_parser("check", help="Check structural integrity and evidence references")
    check.add_argument("--strict", action="store_true")
    commands.add_parser("index", help="Rebuild tool-owned directory indexes")
    find = commands.add_parser("find", help="Keyword search over current pages")
    find.add_argument("query")
    find.add_argument("--include-deprecated", action="store_true")
    records = commands.add_parser("records", help="Return all matching structured observations")
    for key in ("metric", "period", "scope", "universe", "unit", "method"):
        records.add_argument(f"--{key}")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            initialize(args.vault, args.title, args.profile)
            print(f"Created empty private vault: {args.vault.resolve()}")
        elif args.command == "new":
            print(create_page(args.vault, args.kind, args.title, args.description))
        elif args.command == "capture":
            capture_id, page, reused = capture_source(args.vault, args.file, args.source_id, args.title, args.resource)
            print(json_text({"capture_id": capture_id, "source_page": str(page), "reused": reused}), end="")
        elif args.command == "index":
            print(f"Updated {build_indexes(args.vault)} directory indexes.")
        else:
            report = inspect_vault(args.vault)
            if args.command == "check":
                for level, message in report.issues:
                    print(f"{level}: {message}")
                warnings = sum(level == "WARN" for level, _ in report.issues)
                print(f"Checked {len(report.pages)} pages, {len(report.records)} observations, {len(report.captures)} captures: {len(report.errors)} errors, {warnings} warnings.")
                return 1 if report.errors or (args.strict and warnings) else 0
            if args.command == "find":
                results = find_pages(report, args.query, args.include_deprecated)
                print(json_text({"count": len(results), "results": results}), end="")
            elif args.command == "records":
                filters = {key: getattr(args, key) for key in ("metric", "period", "scope", "universe", "unit", "method")
                           if getattr(args, key) is not None}
                results = select_records(report, filters)
                print(json_text({"count": len(results), "records": results}), end="")
        return 0
    except (WikiError, OSError, yaml.YAMLError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
