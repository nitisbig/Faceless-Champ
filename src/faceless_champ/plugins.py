"""Plugin registry: extend Faceless Champ from separate packages.

A plugin is a :class:`Plugin` value that adds themes, easings, components,
raster-source factories, kit shot templates and agent-discoverable
capabilities. Plugins are found in three ways:

1. Installed packages declare an entry point in the ``faceless_champ.plugins``
   group (pyproject.toml)::

       [project.entry-points."faceless_champ.plugins"]
       manimgl = "fc_manimgl:plugin"        # a Plugin, or a function returning one

2. Project-local modules listed in ``FACELESS_CHAMP_PLUGINS="pkg.mod:plugin,other:make"``.
3. ``register(Plugin(...))`` at runtime.

Built-in names always win; a plugin cannot replace a built-in theme or
easing. Discovery is lazy and runs once; a failing plugin is reported by
``plugin_report()`` instead of breaking rendering. Loading a plugin imports
its code, so only install plugins you trust.

Lookups: ``theme("name")`` / ``Theme.named``, easing names in ``rate_func``,
``component("name")``, ``source("name", **options)``, ``shot_template("name")``
and ``capabilities()`` (used by ``fc-agent capabilities``).
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from importlib import import_module
from types import MappingProxyType

ENTRY_POINT_GROUP = "faceless_champ.plugins"
ENV_VAR = "FACELESS_CHAMP_PLUGINS"


class PluginError(ValueError):
    """A plugin definition is invalid or conflicts with another plugin."""


@dataclass(frozen=True)
class Capability:
    """Agent-facing description of something a plugin provides."""

    name: str
    summary: str
    import_path: str | None = None
    example: str = ""
    tags: tuple[str, ...] = ()
    kind: str = "api"
    dependencies: tuple[str, ...] = ()

    def to_dict(self, plugin: str) -> dict:
        return {
            "id": f"plugin:{plugin}:{self.name}",
            "name": self.name,
            "kind": self.kind,
            "plugin": plugin,
            "import_path": self.import_path,
            "use_when": self.summary,
            "example": self.example,
            "tags": list(self.tags),
            "dependencies": list(self.dependencies),
        }


@dataclass(frozen=True)
class Plugin:
    """Everything a plugin contributes. All mappings are name -> object."""

    name: str
    version: str = "0"
    summary: str = ""
    themes: Mapping[str, object] = field(default_factory=dict)
    easings: Mapping[str, Callable[[float], float]] = field(default_factory=dict)
    components: Mapping[str, object] = field(default_factory=dict)
    sources: Mapping[str, Callable[..., object]] = field(default_factory=dict)
    shots: Mapping[str, type] = field(default_factory=dict)
    capabilities: tuple[Capability, ...] = ()
    requires: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip() or ":" in self.name:
            raise PluginError("Plugin.name must be a nonempty string without ':'")
        for kind in ("themes", "easings", "components", "sources", "shots"):
            mapping = getattr(self, kind)
            if not isinstance(mapping, Mapping):
                raise PluginError(f"Plugin.{kind} must be a mapping of names to objects")
            for key, value in mapping.items():
                if not isinstance(key, str) or not key or ":" in key:
                    raise PluginError(f"{self.name}: {kind} names must be nonempty strings without ':'")
                if kind in {"easings", "sources"} and not callable(value):
                    raise PluginError(f"{self.name}: {kind}[{key!r}] must be callable")
            object.__setattr__(self, kind, MappingProxyType(dict(mapping)))
        if self.themes:
            from .theme import Theme

            for key, value in self.themes.items():
                if not isinstance(value, Theme):
                    raise PluginError(f"{self.name}: themes[{key!r}] must be a faceless_champ Theme")
        if any(not isinstance(c, Capability) for c in self.capabilities):
            raise PluginError(f"{self.name}: capabilities must be Capability values")
        object.__setattr__(self, "capabilities", tuple(self.capabilities))
        object.__setattr__(self, "requires", tuple(self.requires))

    def describe(self) -> list[dict]:
        """Capabilities, including automatic entries for every contributed name."""
        records = [c.to_dict(self.name) for c in self.capabilities]
        declared = {r["name"] for r in records}
        for kind, label in (
            ("themes", "theme"),
            ("easings", "easing"),
            ("components", "component"),
            ("sources", "source"),
            ("shots", "shot"),
        ):
            for key, value in getattr(self, kind).items():
                if key in declared:
                    continue
                doc = (getattr(value, "__doc__", None) or "").strip().splitlines()
                summary = doc[0] if doc else f"{label} {key!r} from the {self.name} plugin"
                records.append(
                    Capability(key, summary, kind="plugin-" + label, tags=(label, self.name)).to_dict(self.name)
                )
        return records


_registered: dict[str, Plugin] = {}
_report: dict[str, dict] = {}
_discovered = False


def _builtin_names(kind):
    if kind == "themes":
        from .theme import THEMES

        return set(THEMES)
    if kind == "easings":
        from .easing import EASINGS

        return set(EASINGS)
    return set()


def register(plugin: Plugin, *, replace: bool = False) -> Plugin:
    """Register a plugin. Names must not clash with built-ins or other plugins."""
    if not isinstance(plugin, Plugin):
        raise PluginError("register() needs a Plugin")
    if plugin.name in _registered and not replace:
        raise PluginError(f"Plugin {plugin.name!r} is already registered")
    others = [p for name, p in _registered.items() if name != plugin.name]
    for kind in ("themes", "easings", "components", "sources", "shots"):
        names = set(getattr(plugin, kind))
        builtin = names & _builtin_names(kind)
        if builtin:
            raise PluginError(f"{plugin.name}: {kind} {sorted(builtin)} are built-in names; choose new names")
        for other in others:
            clash = names & set(getattr(other, kind))
            if clash:
                raise PluginError(f"{plugin.name}: {kind} {sorted(clash)} already provided by plugin {other.name!r}")
    _registered[plugin.name] = plugin
    _report[plugin.name] = {"name": plugin.name, "version": plugin.version, "status": "loaded", "origin": "register"}
    return plugin


def unregister(name: str) -> None:
    _registered.pop(name, None)
    _report.pop(name, None)


def _entry_points():
    from importlib.metadata import entry_points

    return list(entry_points(group=ENTRY_POINT_GROUP))


def _materialize(value, origin):
    plugin = value() if callable(value) and not isinstance(value, Plugin) else value
    if not isinstance(plugin, Plugin):
        raise PluginError(f"{origin} did not provide a faceless_champ Plugin")
    return plugin


def _load(origin, loader):
    try:
        plugin = _materialize(loader(), origin)
        register(plugin)
        _report[plugin.name]["origin"] = origin
    except Exception as exc:  # noqa: BLE001 - plugin failures are reported, never fatal
        _report[origin] = {
            "name": origin,
            "status": "failed",
            "origin": origin,
            "error": f"{type(exc).__name__}: {exc}",
        }


def discover(*, reload: bool = False) -> dict[str, Plugin]:
    """Load entry-point and FACELESS_CHAMP_PLUGINS plugins once; return all registered plugins."""
    global _discovered
    if _discovered and not reload:
        return dict(_registered)
    _discovered = True
    for entry in _entry_points():
        _load(f"entry-point:{entry.name}={entry.value}", entry.load)
    for spec in filter(None, (s.strip() for s in os.environ.get(ENV_VAR, "").split(","))):
        module, _, attribute = spec.partition(":")

        def loader(module=module, attribute=attribute or "plugin"):
            return getattr(import_module(module), attribute)

        _load(f"env:{spec}", loader)
    return dict(_registered)


def plugins() -> dict[str, Plugin]:
    """All registered plugins (runs discovery on first use)."""
    return discover()


def plugin_report() -> list[dict]:
    """Load status of every plugin, including failures with their error text."""
    discover()
    return [dict(item) for item in _report.values()]


def _lookup(kind, name):
    for plugin in discover().values():
        mapping = getattr(plugin, kind)
        if name in mapping:
            return mapping[name]
    return None


def _names(kind):
    return sorted(name for plugin in discover().values() for name in getattr(plugin, kind))


def theme(name: str):
    """A plugin theme by name, or None."""
    return _lookup("themes", name)


def easing(name: str):
    """A plugin easing by name, or None."""
    return _lookup("easings", name)


def component(name: str):
    """A plugin component (class or factory) by name."""
    value = _lookup("components", name)
    if value is None:
        raise PluginError(f"No plugin component {name!r}; installed: {', '.join(_names('components')) or 'none'}")
    return value


def source(name: str, **options):
    """Build a raster source from a plugin source factory: ``source("plasma", size=(640, 360))``."""
    factory = _lookup("sources", name)
    if factory is None:
        raise PluginError(f"No plugin source {name!r}; installed: {', '.join(_names('sources')) or 'none'}")
    return factory(**options)


def shot_template(name: str):
    """A plugin kit shot block class by name, or None."""
    return _lookup("shots", name)


def names(kind: str) -> list[str]:
    """Plugin-provided names of a kind: themes, easings, components, sources or shots."""
    if kind not in {"themes", "easings", "components", "sources", "shots"}:
        raise ValueError("kind must be themes, easings, components, sources or shots")
    return _names(kind)


def capabilities() -> list[dict]:
    """Agent-discoverable records for every registered plugin."""
    return [record for plugin in discover().values() for record in plugin.describe()]
