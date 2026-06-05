#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SKILL_NAME = "JavaProjectAgentInstaller"
MANAGED_BEGIN = f"<!-- BEGIN {SKILL_NAME} -->"
MANAGED_END = f"<!-- END {SKILL_NAME} -->"
REVIEW_RELATIVE_PATH = Path("ProjectAgents/references/project-agents-onboarding-review.md")
SKIP_DIRS = {
    ".git",
    ".gradle",
    ".idea",
    ".mvn",
    ".svn",
    ".hg",
    ".settings",
    "build",
    "dist",
    "node_modules",
    "out",
    "target",
    "tmp",
    "__pycache__",
    "ProjectAgents",
}
SEARCH_SUFFIXES = {
    ".java",
    ".kt",
    ".groovy",
    ".gradle",
    ".kts",
    ".xml",
    ".toml",
    ".properties",
    ".yml",
    ".yaml",
    ".sql",
    ".proto",
    ".avsc",
    ".json",
}
SOURCE_SUFFIXES = {".java", ".kt", ".groovy"}
FRAMEWORK_PATTERNS = [
    (re.compile(r"@SpringBootApplication|org\.springframework\.boot", re.IGNORECASE), "Spring Boot"),
    (re.compile(r"spring-cloud", re.IGNORECASE), "Spring Cloud"),
    (re.compile(r"io\.micronaut|micronaut-", re.IGNORECASE), "Micronaut"),
    (re.compile(r"io\.quarkus|quarkus-", re.IGNORECASE), "Quarkus"),
    (re.compile(r"jakarta\.", re.IGNORECASE), "Jakarta EE"),
    (re.compile(r"io\.vertx|vertx", re.IGNORECASE), "Vert.x"),
    (re.compile(r"org\.projectlombok|lombok", re.IGNORECASE), "Lombok"),
    (re.compile(r"reactor\.core|spring-boot-starter-webflux", re.IGNORECASE), "Reactor / WebFlux"),
]
WEB_PATTERNS = [
    (re.compile(r"@RestController|@Controller", re.IGNORECASE), "Spring MVC @RestController / @Controller"),
    (re.compile(r"RouterFunction|coRouter", re.IGNORECASE), "functional router"),
    (re.compile(r"@Path\(|jakarta\.ws\.rs", re.IGNORECASE), "JAX-RS @Path"),
    (re.compile(r"io\.vertx\.ext\.web\.Router", re.IGNORECASE), "Vert.x Router"),
    (re.compile(r"io\.micronaut\.http\.annotation\.Controller", re.IGNORECASE), "Micronaut @Controller"),
]
MESSAGING_PATTERNS = [
    (re.compile(r"@KafkaListener|KafkaTemplate|spring-kafka", re.IGNORECASE), "Kafka"),
    (re.compile(r"@RabbitListener|RabbitTemplate|spring-rabbit", re.IGNORECASE), "RabbitMQ"),
    (re.compile(r"rocketmq", re.IGNORECASE), "RocketMQ"),
    (re.compile(r"pulsar", re.IGNORECASE), "Pulsar"),
    (re.compile(r"jms|@JmsListener", re.IGNORECASE), "JMS"),
    (re.compile(r"eventbus|DomainEvent|ApplicationEventPublisher", re.IGNORECASE), "in-process event bus"),
]
PERSISTENCE_PATTERNS = [
    (re.compile(r"JpaRepository|@Entity|hibernate", re.IGNORECASE), "Spring Data JPA / Hibernate"),
    (re.compile(r"@Mapper|mybatis", re.IGNORECASE), "MyBatis"),
    (re.compile(r"DSLContext|jooq", re.IGNORECASE), "jOOQ"),
    (re.compile(r"JdbcTemplate", re.IGNORECASE), "JdbcTemplate"),
    (re.compile(r"r2dbc", re.IGNORECASE), "R2DBC"),
]
DB_MIGRATION_PATTERNS = [
    (re.compile(r"flyway|db/migration", re.IGNORECASE), "Flyway"),
    (re.compile(r"liquibase|databaseChangeLog", re.IGNORECASE), "Liquibase"),
]
PLACEHOLDER_ORDER = [
    "PROJECT_NAME",
    "ROOT_BUILD_SYSTEM",
    "PRIMARY_RUNTIME_TARGET",
    "SECONDARY_RUNTIME_TARGET_OR_PROFILE",
    "ENTRY_MODULE",
    "CORE_SHARED_MODULE",
    "API_CONTRACT_MODULE",
    "INFRASTRUCTURE_MODULE",
    "FEATURE_MODULE_EXAMPLE_A",
    "FEATURE_MODULE_EXAMPLE_B",
    "FEATURE_MODULE_EXAMPLE_C",
    "FEATURE_MODULE_EXAMPLES",
    "INTEGRATION_MODULES",
    "SPECIAL_MODULE_OR_DEPENDENCY",
    "MODULE_WITH_LOCAL_AGENTS_EXAMPLES",
    "PACKAGE_NAMESPACE_EXAMPLES",
    "ROOT_BUILD_FILES",
    "MODULE_EXTRA_CONTEXT_FILES",
    "CONFIG_FILE_EXAMPLES",
    "TEST_DIRECTORY_EXAMPLES",
    "FRAMEWORK_STACK",
    "WEB_ENTRY_PATTERN",
    "MESSAGING_OR_EVENT_PATTERN",
    "PERSISTENCE_PATTERN",
    "DB_MIGRATION_PATTERN",
    "PLACEHOLDER",
]


@dataclass
class ModuleInfo:
    name: str
    path: Path
    build_file: Path | None
    build_system: str
    module_type: str


@dataclass
class SuggestedValue:
    value: str
    confidence: str
    reason: str


@dataclass
class FileAction:
    path: Path
    action: str
    detail: str
    incoming_path: Path | None = None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def normalize_text(content: str) -> str:
    return content.replace("\r\n", "\n").rstrip() + "\n"


def template_root() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "template"


def xml_root(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


def xml_local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def xml_child_text(node: ET.Element | None, name: str) -> str | None:
    if node is None:
        return None
    for child in node:
        if xml_local_name(child.tag) == name and child.text and child.text.strip():
            return child.text.strip()
    return None


def xml_findall_text(node: ET.Element | None, parent_name: str, child_name: str) -> list[str]:
    if node is None:
        return []
    for child in node:
        if xml_local_name(child.tag) != parent_name:
            continue
        values: list[str] = []
        for grandchild in child:
            if xml_local_name(grandchild.tag) == child_name and grandchild.text and grandchild.text.strip():
                values.append(grandchild.text.strip())
        return values
    return []


def maven_profile_ids(node: ET.Element | None) -> list[str]:
    if node is None:
        return []
    values: list[str] = []
    for child in node:
        if xml_local_name(child.tag) != "profiles":
            continue
        for profile in child:
            if xml_local_name(profile.tag) != "profile":
                continue
            value = xml_child_text(profile, "id")
            if value:
                values.append(value)
        break
    return values


def detect_project_name(project_root: Path) -> tuple[str, str]:
    for settings_name in ("settings.gradle.kts", "settings.gradle"):
        settings_path = project_root / settings_name
        if not settings_path.exists():
            continue
        text = read_text(settings_path)
        match = re.search(r'rootProject\.name\s*=\s*["\']([^"\']+)["\']', text)
        if match:
            return match.group(1).strip(), f"from `{settings_name}`"

    root_pom = project_root / "pom.xml"
    if root_pom.exists():
        root = xml_root(root_pom)
        for field in ("name", "artifactId"):
            value = xml_child_text(root, field)
            if value:
                return value, f"from root `pom.xml` <{field}>"

    return project_root.name, "from target directory name"


def root_module_name(project_root: Path, project_name: str) -> str:
    return f":{project_name or project_root.name}"


def iter_project_files(project_root: Path, allowed_suffixes: set[str] | None = None):
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [
            name
            for name in dirnames
            if name not in SKIP_DIRS and not name.startswith(".DS_Store")
        ]
        base_path = Path(dirpath)
        for filename in filenames:
            path = base_path / filename
            if allowed_suffixes and path.suffix not in allowed_suffixes:
                continue
            yield path


def detect_root_build_system(project_root: Path) -> SuggestedValue:
    has_gradle = any((project_root / name).exists() for name in ("settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts"))
    has_maven = any((project_root / name).exists() for name in ("pom.xml", "mvnw", "mvnw.cmd")) or (project_root / ".mvn").exists()
    if has_gradle and has_maven:
        return SuggestedValue("Gradle + Maven", "high", "detected root Gradle and Maven build files")
    if has_gradle:
        return SuggestedValue("Gradle", "high", "detected root Gradle build files")
    if has_maven:
        return SuggestedValue("Maven", "high", "detected root Maven build files")
    return SuggestedValue("TODO(确认项目使用 Gradle、Maven 或其它 JVM 构建体系)", "low", "no root Gradle or Maven files were detected")


def collect_gradle_module_names(project_root: Path) -> list[str]:
    module_names: list[str] = []
    for settings_name in ("settings.gradle.kts", "settings.gradle"):
        settings_path = project_root / settings_name
        if not settings_path.exists():
            continue
        text = read_text(settings_path)
        for token in re.findall(r":[A-Za-z0-9_.-]+(?:[:][A-Za-z0-9_.-]+)*", text):
            if token not in module_names:
                module_names.append(token)
    return module_names


def collect_maven_module_names(project_root: Path) -> list[str]:
    root_pom = project_root / "pom.xml"
    if not root_pom.exists():
        return []
    names: list[str] = []
    for module_path in xml_findall_text(xml_root(root_pom), "modules", "module"):
        module_name = ":" + module_path.strip("/").replace("/", ":").replace("\\", ":")
        if module_name not in names:
            names.append(module_name)
    return names


def root_has_sources(project_root: Path) -> bool:
    candidates = [
        project_root / "src" / "main",
        project_root / "src" / "test",
        project_root / "src" / "integrationTest",
        project_root / "src" / "it",
    ]
    return any(path.exists() for path in candidates)


def detect_module_build_file(module_path: Path) -> tuple[Path | None, str]:
    for candidate in ("build.gradle.kts", "build.gradle"):
        candidate_path = module_path / candidate
        if candidate_path.exists():
            return candidate_path, "gradle"
    pom_path = module_path / "pom.xml"
    if pom_path.exists():
        return pom_path, "maven"
    return None, "unknown"


def detect_gradle_module_type(build_file: Path) -> str:
    text = read_text(build_file).lower()
    if any(token in text for token in ("org.springframework.boot", "application", "io.quarkus", "micronaut.application", "shadow")):
        return "application"
    if "java-platform" in text:
        return "platform"
    if "java-library" in text or "kotlin(\"jvm\")" in text or "kotlin('jvm')" in text:
        return "library"
    if re.search(r"\bjava\b", text):
        return "library"
    return "unknown"


def detect_maven_module_type(build_file: Path) -> str:
    root = xml_root(build_file)
    packaging = (xml_child_text(root, "packaging") or "jar").lower()
    text = read_text(build_file).lower()
    artifact_id = (xml_child_text(root, "artifactId") or build_file.parent.name).lower()
    if packaging == "pom":
        if any(token in artifact_id for token in ("bom", "platform", "parent")) or "dependencymanagement" in text:
            return "platform"
        return "aggregator"
    if any(token in text for token in ("spring-boot-maven-plugin", "quarkus-maven-plugin", "micronaut-maven-plugin", "<mainclass>", "<mainClass>")):
        return "application"
    if packaging in {"war", "ear"}:
        return "application"
    return "library"


def detect_module_type(build_file: Path | None, build_system: str) -> str:
    if build_file is None or not build_file.exists():
        return "unknown"
    if build_system == "gradle":
        return detect_gradle_module_type(build_file)
    if build_system == "maven":
        return detect_maven_module_type(build_file)
    return "unknown"


def discover_modules(project_root: Path) -> list[ModuleInfo]:
    project_name, _ = detect_project_name(project_root)
    root_name = root_module_name(project_root, project_name)
    module_names: list[str] = []

    for name in collect_gradle_module_names(project_root) + collect_maven_module_names(project_root):
        if name not in module_names:
            module_names.append(name)

    if not module_names:
        for path in iter_project_files(project_root, allowed_suffixes={".gradle", ".kts", ".xml"}):
            if path.name not in {"build.gradle", "build.gradle.kts", "pom.xml"}:
                continue
            rel_parent = path.parent.relative_to(project_root)
            if rel_parent == Path("."):
                continue
            module_name = ":" + str(rel_parent).replace(os.sep, ":")
            if module_name not in module_names:
                module_names.append(module_name)

    if (not module_names and detect_module_build_file(project_root)[0]) or root_has_sources(project_root):
        module_names.append(root_name)

    modules: list[ModuleInfo] = []
    for module_name in module_names:
        module_path = project_root if module_name == root_name else project_root / module_name.lstrip(":").replace(":", os.sep)
        build_file, build_system = detect_module_build_file(module_path)
        modules.append(
            ModuleInfo(
                name=module_name,
                path=module_path,
                build_file=build_file,
                build_system=build_system,
                module_type=detect_module_type(build_file, build_system),
            )
        )
    return modules


def module_leaf(module_name: str) -> str:
    return module_name.split(":")[-1] or module_name


def score_module(module: ModuleInfo, keyword_scores: list[tuple[str, int]]) -> int:
    haystack = f"{module.name} {module_leaf(module.name)} {module.path.name}".lower()
    score = 0
    for keyword, value in keyword_scores:
        if keyword in haystack:
            score += value
    return score


def choose_best_module(
    modules: list[ModuleInfo],
    keyword_scores: list[tuple[str, int]],
    preferred_types: set[str] | None = None,
    exclude: set[str] | None = None,
) -> ModuleInfo | None:
    exclude = exclude or set()
    candidates = [module for module in modules if module.name not in exclude]
    if preferred_types:
        preferred = [module for module in candidates if module.module_type in preferred_types]
        if preferred:
            candidates = preferred
    if not candidates:
        return None
    ranked = sorted(candidates, key=lambda module: (score_module(module, keyword_scores), -len(module.name)), reverse=True)
    if score_module(ranked[0], keyword_scores) == 0:
        return None
    return ranked[0]


def format_module_name(module_name: str) -> str:
    return module_name


def format_module_list(modules: list[str]) -> str:
    return "、".join(format_module_name(module) for module in modules)


def detect_profile_names(project_root: Path) -> list[str]:
    profiles: list[str] = []
    pattern = re.compile(r"(?:application|bootstrap)-([A-Za-z0-9_.-]+)\.(?:ya?ml|properties)$")
    for path in iter_project_files(project_root):
        match = pattern.match(path.name)
        if match:
            value = match.group(1)
            if value not in profiles:
                profiles.append(value)
    root_pom = project_root / "pom.xml"
    if root_pom.exists():
        for profile_id in maven_profile_ids(xml_root(root_pom)):
            if profile_id not in profiles:
                profiles.append(profile_id)
    return profiles[:5]


def detect_runtime_targets(
    project_name: str,
    runtime_modules: list[ModuleInfo],
    profiles: list[str],
) -> tuple[SuggestedValue, SuggestedValue]:
    if runtime_modules:
        primary_module = runtime_modules[0]
        primary_value = f"{module_leaf(primary_module.name)}（{primary_module.name}）"
        primary_reason = "from the most likely runnable module"
    else:
        primary_value = project_name
        primary_reason = "fallback to project name because no runnable module was detected"

    if len(runtime_modules) > 1:
        secondary_value = f"{module_leaf(runtime_modules[1].name)}（{runtime_modules[1].name}）"
        secondary_reason = "from the second runnable module candidate"
        secondary_confidence = "medium"
    elif profiles:
        secondary_value = " / ".join(profiles[:3]) + " profile"
        secondary_reason = "from detected config or Maven profile names"
        secondary_confidence = "medium"
    else:
        secondary_value = "TODO(确认是否存在第二运行单元、worker、CLI 入口或 profile；如无则删掉这句)"
        secondary_reason = "no second runnable module or runtime profile was detected"
        secondary_confidence = "low"

    return (
        SuggestedValue(primary_value, "medium", primary_reason),
        SuggestedValue(secondary_value, secondary_confidence, secondary_reason),
    )


def detect_local_agent_modules(project_root: Path, modules: list[ModuleInfo]) -> list[str]:
    module_paths = sorted(
        [(module.path.resolve(), module.name) for module in modules if module.path.exists()],
        key=lambda item: len(str(item[0])),
        reverse=True,
    )
    hits: list[str] = []
    for path in iter_project_files(project_root):
        if path.name not in {"AGENTS.md", "CLAUDE.md"}:
            continue
        if path.parent == project_root or "ProjectAgents" in path.parts:
            continue
        resolved = path.parent.resolve()
        module_name = None
        for module_path, candidate_name in module_paths:
            if resolved == module_path or module_path in resolved.parents:
                module_name = candidate_name
                break
        module_name = module_name or ":" + str(path.parent.relative_to(project_root)).replace(os.sep, ":")
        if module_name not in hits:
            hits.append(module_name)
        if len(hits) >= 3:
            break
    return hits


def detect_package_namespaces(project_root: Path) -> list[str]:
    packages: Counter[str] = Counter()
    package_pattern = re.compile(r"^\s*package\s+([A-Za-z0-9_.]+)")
    for path in iter_project_files(project_root, allowed_suffixes=SOURCE_SUFFIXES):
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                for _ in range(20):
                    line = handle.readline()
                    if not line:
                        break
                    match = package_pattern.match(line)
                    if match:
                        packages[match.group(1)] += 1
                        break
        except OSError:
            continue
    return [name for name, _ in packages.most_common(3)]


def detect_root_build_files(project_root: Path) -> list[str]:
    candidates = [
        "settings.gradle.kts",
        "settings.gradle",
        "build.gradle.kts",
        "build.gradle",
        "gradle.properties",
        "gradle/libs.versions.toml",
        "buildSrc/",
        "build-logic/",
        "pom.xml",
        ".mvn/",
        "mvnw",
        "mvnw.cmd",
    ]
    hits: list[str] = []
    for item in candidates:
        path = project_root / item.rstrip("/")
        if path.exists():
            hits.append(item)
    return hits


def iter_limited_files(base: Path, max_depth: int):
    base_depth = len(base.parts)
    for dirpath, dirnames, filenames in os.walk(base):
        current = Path(dirpath)
        depth = len(current.parts) - base_depth
        if depth >= max_depth:
            dirnames[:] = []
        else:
            dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        for filename in filenames:
            yield current / filename


def detect_module_extra_context_files(project_root: Path, candidates: list[ModuleInfo]) -> list[str]:
    hits: list[str] = []
    interesting_name = re.compile(
        r"^(Dockerfile|docker-compose\.ya?ml|compose\.ya?ml|application.*|bootstrap.*|logback.*|openapi.*|jooq.*|.*\.graphqls?)$",
        re.IGNORECASE,
    )
    for module in candidates:
        if not module or not module.path.exists():
            continue
        for path in iter_limited_files(module.path, max_depth=3):
            if path.name in {"build.gradle", "build.gradle.kts", "pom.xml"}:
                continue
            if interesting_name.match(path.name):
                rel = path.relative_to(project_root).as_posix()
                if rel not in hits:
                    hits.append(rel)
            if len(hits) >= 5:
                return hits
    return hits


def detect_config_files(project_root: Path) -> list[str]:
    hits: list[str] = []
    pattern = re.compile(r"^(application|bootstrap)([-A-Za-z0-9_.]*)\.(ya?ml|properties)$", re.IGNORECASE)
    for path in iter_project_files(project_root):
        if pattern.match(path.name) or path.name in {"logback.xml", "logback-spring.xml"}:
            rel = path.relative_to(project_root).as_posix()
            if rel not in hits:
                hits.append(rel)
        if len(hits) >= 5:
            break
    return hits


def detect_test_directories(project_root: Path) -> list[str]:
    patterns = [
        ("src", "test", "java"),
        ("src", "test", "kotlin"),
        ("src", "test", "groovy"),
        ("src", "integrationTest", "java"),
        ("src", "integrationTest", "kotlin"),
        ("src", "it", "java"),
        ("src", "testFixtures", "java"),
    ]
    hits: list[str] = []
    for dirpath, dirnames, _filenames in os.walk(project_root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        rel = Path(dirpath).relative_to(project_root)
        for pattern in patterns:
            if len(rel.parts) >= len(pattern) and tuple(rel.parts[-len(pattern):]) == pattern:
                value = rel.as_posix()
                if value not in hits:
                    hits.append(value)
    return hits[:5]


def search_project_labels(project_root: Path, patterns: list[tuple[re.Pattern[str], str]], limit: int = 4) -> list[str]:
    hits: list[str] = []
    for path in iter_project_files(project_root, allowed_suffixes=SEARCH_SUFFIXES):
        try:
            if path.stat().st_size > 1_000_000:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern, label in patterns:
            if label in hits:
                continue
            if pattern.search(text):
                hits.append(label)
                if len(hits) >= limit:
                    return hits
    return hits


def build_placeholder_suggestions(project_root: Path) -> dict[str, SuggestedValue]:
    project_name, project_name_reason = detect_project_name(project_root)
    modules = discover_modules(project_root)
    build_system = detect_root_build_system(project_root)

    entry_keywords = [
        ("application", 14),
        ("app", 10),
        ("service", 10),
        ("server", 10),
        ("boot", 9),
        ("web", 8),
        ("gateway", 8),
        ("cli", 8),
        ("worker", 7),
        ("job", 7),
    ]
    core_keywords = [("common", 12), ("core", 11), ("shared", 10), ("base", 8), ("foundation", 8), ("kernel", 7)]
    api_keywords = [("api", 12), ("contract", 11), ("spi", 10), ("interface", 8), ("client", 7), ("model", 5)]
    infra_keywords = [("infra", 12), ("infrastructure", 12), ("data", 10), ("persistence", 10), ("repository", 9), ("storage", 8), ("dao", 7), ("db", 7)]
    feature_keywords = [("feature", 11), ("domain", 9), ("service", 8), ("business", 7), ("order", 4), ("user", 4), ("billing", 4)]
    integration_keywords = [("integration", 11), ("adapter", 10), ("gateway", 9), ("client", 8), ("mq", 8), ("kafka", 8), ("rpc", 8), ("feign", 7)]
    special_keywords = [("bom", 12), ("platform", 12), ("parent", 10), ("starter", 9), ("plugin", 8), ("legacy", 7), ("sdk", 7)]

    runtime_modules = [
        module
        for module in sorted(modules, key=lambda item: score_module(item, entry_keywords), reverse=True)
        if module.module_type == "application" or score_module(module, entry_keywords) > 0
    ]
    entry_module = choose_best_module(modules, entry_keywords, preferred_types={"application"}) or choose_best_module(modules, entry_keywords)
    if not entry_module and runtime_modules:
        entry_module = runtime_modules[0]
    if not entry_module and modules:
        entry_module = modules[0]

    chosen_names = {entry_module.name} if entry_module else set()
    core_module = choose_best_module(modules, core_keywords, exclude=chosen_names)
    if core_module:
        chosen_names.add(core_module.name)
    api_module = choose_best_module(modules, api_keywords, exclude=chosen_names)
    if api_module:
        chosen_names.add(api_module.name)
    infra_module = choose_best_module(modules, infra_keywords, exclude=chosen_names)
    if infra_module:
        chosen_names.add(infra_module.name)
    special_module = choose_best_module(modules, special_keywords, preferred_types={"platform", "aggregator"}, exclude=chosen_names) or choose_best_module(
        modules, special_keywords, exclude=chosen_names
    )

    feature_modules = [
        module.name
        for module in sorted(modules, key=lambda item: score_module(item, feature_keywords), reverse=True)
        if score_module(module, feature_keywords) > 0 and module.name not in chosen_names
    ][:3]
    if len(feature_modules) < 3:
        for module in modules:
            if module.name in chosen_names or module.name in feature_modules:
                continue
            feature_modules.append(module.name)
            if len(feature_modules) >= 3:
                break

    integration_modules = [
        module.name
        for module in sorted(modules, key=lambda item: score_module(item, integration_keywords), reverse=True)
        if score_module(module, integration_keywords) > 0
    ][:3]

    profiles = detect_profile_names(project_root)
    primary_target, secondary_target = detect_runtime_targets(project_name, runtime_modules or ([entry_module] if entry_module else []), profiles)
    local_agent_modules = detect_local_agent_modules(project_root, modules)
    package_namespaces = detect_package_namespaces(project_root)
    root_build_files = detect_root_build_files(project_root)
    module_extra_context_files = detect_module_extra_context_files(
        project_root,
        [module for module in [entry_module, core_module, api_module, infra_module] if module],
    )
    config_files = detect_config_files(project_root)
    test_directories = detect_test_directories(project_root)
    framework_stack = search_project_labels(project_root, FRAMEWORK_PATTERNS)
    web_patterns = search_project_labels(project_root, WEB_PATTERNS, limit=2)
    messaging_patterns = search_project_labels(project_root, MESSAGING_PATTERNS, limit=2)
    persistence_patterns = search_project_labels(project_root, PERSISTENCE_PATTERNS, limit=2)
    db_migration_patterns = search_project_labels(project_root, DB_MIGRATION_PATTERNS, limit=2)

    suggestions: dict[str, SuggestedValue] = {
        "PROJECT_NAME": SuggestedValue(project_name, "high", project_name_reason),
        "ROOT_BUILD_SYSTEM": build_system,
        "PRIMARY_RUNTIME_TARGET": primary_target,
        "SECONDARY_RUNTIME_TARGET_OR_PROFILE": secondary_target,
        "ENTRY_MODULE": module_suggestion(entry_module, "the best runnable entry module match", "TODO(确认主入口 module 或单体根模块)"),
        "CORE_SHARED_MODULE": module_suggestion(core_module, "the best common/core/shared match", "TODO(确认共享逻辑或基础能力模块)"),
        "API_CONTRACT_MODULE": module_suggestion(api_module, "the best api/contract/spi match", "TODO(确认 API / DTO / 契约模块)"),
        "INFRASTRUCTURE_MODULE": module_suggestion(infra_module, "the best infra/data/persistence match", "TODO(确认数据访问或基础设施模块)"),
        "FEATURE_MODULE_EXAMPLE_A": indexed_module_suggestion(feature_modules, 0, "feature-like module candidates"),
        "FEATURE_MODULE_EXAMPLE_B": indexed_module_suggestion(feature_modules, 1, "feature-like module candidates"),
        "FEATURE_MODULE_EXAMPLE_C": indexed_module_suggestion(feature_modules, 2, "feature-like module candidates"),
        "FEATURE_MODULE_EXAMPLES": list_suggestion(feature_modules, "feature-like module candidates", "TODO(补充 2 到 3 个业务模块示例)"),
        "INTEGRATION_MODULES": list_suggestion(integration_modules, "integration / adapter module candidates", "TODO(补充外部系统集成模块，例如 client / gateway / adapter)"),
        "SPECIAL_MODULE_OR_DEPENDENCY": module_suggestion(
            special_module,
            "the best bom/platform/parent/starter-style module match",
            "TODO(确认 parent BOM、starter、generated-code 模块或高隐式耦合依赖)",
        ),
        "MODULE_WITH_LOCAL_AGENTS_EXAMPLES": list_suggestion(
            local_agent_modules,
            "detected module-local `AGENTS.md` / `CLAUDE.md` files",
            "TODO(补充已确认存在 module 级 agent 文档的模块名)",
        ),
        "PACKAGE_NAMESPACE_EXAMPLES": file_list_suggestion(
            package_namespaces,
            "from the most common package declarations",
            "TODO(补充主包名或核心命名空间，例如 com.example.service)",
        ),
        "ROOT_BUILD_FILES": file_list_suggestion(
            root_build_files,
            "from detected root build and tooling files",
            "TODO(确认根级构建和装配文件，例如 settings.gradle.kts、pom.xml、gradle/libs.versions.toml)",
        ),
        "MODULE_EXTRA_CONTEXT_FILES": file_list_suggestion(
            module_extra_context_files,
            "from interesting module-level context files",
            "TODO(确认模块级额外上下文文件，例如 Dockerfile、application.yml、openapi.yaml)",
        ),
        "CONFIG_FILE_EXAMPLES": file_list_suggestion(
            config_files,
            "from detected config and logging files",
            "TODO(补充关键配置文件，例如 application.yml、application-prod.yml)",
        ),
        "TEST_DIRECTORY_EXAMPLES": file_list_suggestion(
            test_directories,
            "from detected test source directories",
            "TODO(补充关键测试目录，例如 src/test/java、src/integrationTest/java)",
        ),
        "FRAMEWORK_STACK": list_suggestion(
            framework_stack,
            "from source/build file keyword matches",
            "TODO(确认核心框架栈，例如 Spring Boot、Quarkus、Micronaut)",
        ),
        "WEB_ENTRY_PATTERN": list_suggestion(
            web_patterns,
            "from web-entry keyword matches",
            "TODO(确认 Web / RPC 入口方式，例如 @RestController、JAX-RS、RouterFunction)",
        ),
        "MESSAGING_OR_EVENT_PATTERN": list_suggestion(
            messaging_patterns,
            "from messaging/event keyword matches",
            "TODO(确认消息或事件机制，例如 Kafka、RabbitMQ、ApplicationEventPublisher)",
        ),
        "PERSISTENCE_PATTERN": list_suggestion(
            persistence_patterns,
            "from persistence keyword matches",
            "TODO(确认持久化实现，例如 JPA、MyBatis、jOOQ、JdbcTemplate)",
        ),
        "DB_MIGRATION_PATTERN": list_suggestion(
            db_migration_patterns,
            "from migration keyword matches",
            "TODO(确认数据库迁移方式，例如 Flyway、Liquibase)",
        ),
        "PLACEHOLDER": SuggestedValue("TODO(仍需人工确认的项目位)", "low", "generic fallback for any remaining placeholders"),
    }
    return suggestions


def module_suggestion(module: ModuleInfo | None, reason: str, low_todo: str) -> SuggestedValue:
    if not module:
        return SuggestedValue(low_todo, "low", "no confident module match was detected")
    return SuggestedValue(format_module_name(module.name), "medium", reason)


def indexed_module_suggestion(modules: list[str], index: int, reason: str) -> SuggestedValue:
    if index < len(modules):
        return SuggestedValue(format_module_name(modules[index]), "medium", reason)
    return SuggestedValue("TODO(补充业务模块示例)", "low", "fewer than the requested number of feature module candidates were detected")


def list_suggestion(values: list[str], reason: str, low_todo: str) -> SuggestedValue:
    if not values:
        return SuggestedValue(low_todo, "low", "no confident candidates were detected")
    return SuggestedValue(format_module_list(values), "medium", reason)


def file_list_suggestion(values: list[str], reason: str, low_todo: str) -> SuggestedValue:
    if not values:
        return SuggestedValue(low_todo, "low", "no confident candidates were detected")
    return SuggestedValue("、".join(values), "medium", reason)


def replace_placeholders(content: str, suggestions: dict[str, SuggestedValue]) -> str:
    rendered = content
    for name, suggestion in suggestions.items():
        rendered = rendered.replace(f"[{name}]", suggestion.value)
    return rendered


def contains_known_placeholders(content: str, suggestions: dict[str, SuggestedValue]) -> bool:
    return any(f"[{name}]" in content for name in suggestions)


def incoming_path_for(target_path: Path) -> Path:
    if target_path.suffix:
        return target_path.with_name(f"{target_path.stem}.incoming{target_path.suffix}")
    return target_path.with_name(f"{target_path.name}.incoming")


def install_entry_file(project_root: Path, relative_path: Path, rendered_text: str, block_text: str) -> FileAction:
    target_path = project_root / relative_path
    if not target_path.exists():
        write_text(target_path, normalize_text(rendered_text))
        return FileAction(relative_path, "created", "created the entry file from the template")

    existing = read_text(target_path)
    if "ProjectAgents/ProjectAgents.md" in existing:
        return FileAction(relative_path, "unchanged", "the entry file already points at `ProjectAgents/ProjectAgents.md`")

    managed_block = f"{MANAGED_BEGIN}\n{block_text}\n{MANAGED_END}"
    if MANAGED_BEGIN in existing and MANAGED_END in existing:
        updated = re.sub(
            re.escape(MANAGED_BEGIN) + r".*?" + re.escape(MANAGED_END),
            managed_block,
            existing,
            flags=re.DOTALL,
        )
    else:
        updated = existing.rstrip() + "\n\n" + managed_block + "\n"
    write_text(target_path, normalize_text(updated))
    return FileAction(relative_path, "updated", "appended an idempotent pointer block without overwriting existing instructions")


def install_generic_file(project_root: Path, relative_path: Path, rendered_text: str, suggestions: dict[str, SuggestedValue]) -> FileAction:
    target_path = project_root / relative_path
    if not target_path.exists():
        write_text(target_path, normalize_text(rendered_text))
        return FileAction(relative_path, "created", "created the file from the rendered template")

    if relative_path == Path("ProjectAgents/CHANGELOG.md"):
        return FileAction(relative_path, "unchanged", "preserved the existing changelog and will append a new entry if files change")

    existing = read_text(target_path)
    if normalize_text(existing) == normalize_text(rendered_text):
        return FileAction(relative_path, "unchanged", "already matches the rendered template")

    if contains_known_placeholders(existing, suggestions):
        updated = replace_placeholders(existing, suggestions)
        if normalize_text(updated) != normalize_text(existing):
            write_text(target_path, normalize_text(updated))
            return FileAction(relative_path, "updated", "filled placeholders in the existing file while preserving custom content")
        return FileAction(relative_path, "unchanged", "existing file only needed placeholder checks and required no changes")

    incoming_path = incoming_path_for(target_path)
    if incoming_path.exists():
        existing_incoming = read_text(incoming_path)
        if normalize_text(existing_incoming) == normalize_text(rendered_text):
            return FileAction(
                relative_path,
                "unchanged",
                "preserved the existing file; a matching `.incoming` merge candidate already exists",
                incoming_path=incoming_path.relative_to(project_root),
            )
    write_text(incoming_path, normalize_text(rendered_text))
    return FileAction(
        relative_path,
        "incoming",
        "preserved the existing file and wrote a rendered `.incoming` copy for manual merge",
        incoming_path=incoming_path.relative_to(project_root),
    )


def render_template_tree(project_root: Path, suggestions: dict[str, SuggestedValue]) -> list[FileAction]:
    actions: list[FileAction] = []
    root = template_root()
    file_paths = sorted(path for path in root.rglob("*") if path.is_file() and path.name != ".DS_Store")
    for source_path in file_paths:
        relative_path = source_path.relative_to(root)
        rendered_text = replace_placeholders(read_text(source_path), suggestions)
        if relative_path == Path("AGENTS.md"):
            actions.append(
                install_entry_file(
                    project_root,
                    relative_path,
                    rendered_text,
                    "请阅读 [ProjectAgents/ProjectAgents.md](ProjectAgents/ProjectAgents.md)。",
                )
            )
        elif relative_path == Path("CLAUDE.md"):
            actions.append(
                install_entry_file(
                    project_root,
                    relative_path,
                    rendered_text,
                    "@ProjectAgents/ProjectAgents.md",
                )
            )
        else:
            actions.append(install_generic_file(project_root, relative_path, rendered_text, suggestions))
    return actions


def git_user_name(project_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "config", "user.name"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return "unknown"
    value = result.stdout.strip()
    return value or "unknown"


def append_changelog_entry(project_root: Path, actions: list[FileAction]) -> None:
    changelog_path = project_root / "ProjectAgents/CHANGELOG.md"
    if not changelog_path.exists():
        return
    changed_paths = [f"`{action.path.as_posix()}`" for action in actions if action.action in {"created", "updated", "incoming"}]
    if not changed_paths:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git_user = git_user_name(project_root)
    entry_lines = [
        "",
        f"## {timestamp} | Codex | git: {git_user}",
        "",
        "- Files: " + ", ".join(changed_paths + [f"`{REVIEW_RELATIVE_PATH.as_posix()}`"]),
        "- Summary: Installed or updated ProjectAgents seed files via `$JavaProjectAgentInstaller`.",
        "- Summary: Generated onboarding review notes and placeholder suggestions for the target Java project.",
        "",
    ]
    with changelog_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(entry_lines))


def write_review_file(project_root: Path, suggestions: dict[str, SuggestedValue], actions: list[FileAction]) -> None:
    created = [action for action in actions if action.action == "created"]
    updated = [action for action in actions if action.action == "updated"]
    incoming = [action for action in actions if action.action == "incoming"]
    unresolved = [(name, suggestion) for name, suggestion in suggestions.items() if "TODO(" in suggestion.value]

    lines = [
        "# ProjectAgents Onboarding Review",
        "",
        f"- Generated at: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        f"- Skill: `$JavaProjectAgentInstaller`",
        f"- Target root: `{project_root}`",
        "",
        "## Outcome",
        "",
    ]

    if created:
        lines.append("- Created: " + ", ".join(f"`{action.path.as_posix()}`" for action in created))
    if updated:
        lines.append("- Updated: " + ", ".join(f"`{action.path.as_posix()}`" for action in updated))
    if incoming:
        lines.append(
            "- Preserved existing files and staged `.incoming` copies: "
            + ", ".join(f"`{action.incoming_path.as_posix()}`" for action in incoming if action.incoming_path)
        )
    if not any((created, updated, incoming)):
        lines.append("- No template files changed; the project already matched the rendered install output.")

    lines.extend(["", "## Placeholder Review", ""])
    for name in PLACEHOLDER_ORDER:
        suggestion = suggestions.get(name)
        if suggestion:
            lines.append(f"- `{name}`: {suggestion.value} (`{suggestion.confidence}`; {suggestion.reason})")

    lines.extend(
        [
            "",
            "## Compatibility Notes",
            "",
            "- Existing `AGENTS.md` / `CLAUDE.md` files are never replaced wholesale; the installer only appends a managed pointer block when needed.",
            "- Existing `ProjectAgents/*.md` files that still contain template placeholders are updated in place with best-effort substitutions.",
            "- Existing `ProjectAgents/*.md` files with custom content are preserved; rendered template copies are written as `.incoming.md` files for manual merge.",
            "",
            "## Follow-up",
            "",
            "- Fold confirmed stable facts from this review back into `ProjectAgents/ProjectAgents.md` and the relevant `ProjectAgents/references/*.md` files.",
            "- Resolve every `TODO(` item before treating the onboarding as complete.",
            "- Review every `.incoming.md` file and either merge it or delete it after the merge decision is made.",
        ]
    )

    if unresolved:
        lines.extend(["", "## Open Review Items", ""])
        for name, suggestion in unresolved:
            lines.append(f"- `{name}`: {suggestion.value}")

    write_text(project_root / REVIEW_RELATIVE_PATH, normalize_text("\n".join(lines)))


def ensure_java_project_hint(project_root: Path) -> str | None:
    build_system = detect_root_build_system(project_root)
    if build_system.confidence == "high":
        return None
    build_files = [path for path in iter_project_files(project_root, allowed_suffixes={".gradle", ".kts", ".xml"}) if path.name in {"build.gradle", "build.gradle.kts", "pom.xml"}]
    if build_files:
        return None
    return "Warning: no Gradle or Maven build files were detected. The installer can still copy the template, but every project-specific suggestion will be low confidence."


def copy_template_for_debug(_project_root: Path, destination: Path) -> None:
    source = template_root()
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the ProjectAgents Java guidance template into a target project.")
    parser.add_argument(
        "--project-root",
        default=os.getcwd(),
        help="Target Java project root. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--dump-template",
        help="Optional debug path. When set, copy the raw template tree to this path and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        raise SystemExit(f"Target project root does not exist: {project_root}")

    if args.dump_template:
        dump_path = Path(args.dump_template).resolve()
        copy_template_for_debug(project_root, dump_path)
        print(f"Copied template assets to {dump_path}")
        return 0

    warning = ensure_java_project_hint(project_root)
    suggestions = build_placeholder_suggestions(project_root)
    actions = render_template_tree(project_root, suggestions)
    write_review_file(project_root, suggestions, actions)
    append_changelog_entry(project_root, actions)

    if warning:
        print(warning)
    print(f"Installed ProjectAgents guidance into {project_root}")
    print(f"Review notes: {project_root / REVIEW_RELATIVE_PATH}")
    print(
        "Close or disable the `JavaProjectAgentInstaller` skill after installation; "
        "otherwise semantic auto-invocation may trigger it again in later tasks."
    )
    incoming_actions = [action for action in actions if action.action == "incoming"]
    if incoming_actions:
        print("Manual merge required for:")
        for action in incoming_actions:
            print(f"  - {action.incoming_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
