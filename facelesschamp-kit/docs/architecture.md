# Architecture decision: one engine, independent framework

Dependency direction: project / explicitly imported pack → facelesschamp-kit → faceless-champ. The engine remains independently installable. Neither private engine state nor a second frame evaluator is used.

A fresh build loads configuration, imports the selected factory in a temporary project namespace, resolves resources during construction/composition, measures blocks, normalizes placement and motion events, and compiles a master Scene through add/play/remove/at/wait_until. CompiledVideo production methods use Kit rendering services over public Core export/preview and renderer interfaces. Agent delegates its exact compiled object to these services. Kit-authored segments share one absolute clock; captions and audio start at zero. Core-authored compositions pass through intact.

Definitions contain block props and deferred animation callbacks. Concrete components exist only within compilation. Initial entrance visibility is set before the core snapshot, then source values are restored so callbacks retain normal core semantics. Events sort by time, then removal, addition, and animation. Same-time ordering is stable. Core validation remains authoritative for track conflicts. A complete compilation is required before publishing CompiledVideo.

The kit supports existing primitive types. New renderable primitives require engine/renderer support. Custom blocks merely compose primitives; they do not register drawing code. Package resources use durable local materialization. There are no global mutable theme defaults, automatic plugin discovery, network providers, watch service, or persistent frame caches in the kit.

Release boundaries: versioned report schema 1, Python-first public authoring API, private normalized events, independent wheel and sdist. V2 compatibility is Core >=2.0.0rc1,<3.0.0. Focused local Linux wheel/sdist lanes passed on Python 3.12 and 3.13; see the M5 implementation record for the actual coverage. Public publishing and licensing are separate decisions.

## External geometry and declared tools

ArchCanvas composes Kit ArchChamp authoring over public Core native geometry/source integrations. Mesh asset checksums and geometry content fingerprints join reports, with installed project dependency versions. Requirements come from standard project pyproject.toml; build checks them before imports, and never installs tools. Core owns the offscreen native render sessions. See [ArchChamp](archchamp.md).
