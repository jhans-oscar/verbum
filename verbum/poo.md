Current Issues

verbum/cli/main.py:22-200 couples user input, Rich output, navigation state, and Bible lookups in a single loop, which makes the CLI the god-object and blocks reuse of the core logic by future web/mobile front ends.
verbum/core/reader.py:20-107 owns both parsing and rendering, so validation, autosuggest, and formatting are tightly bound to a Rich console; any alternate presentation (API JSON, TUI, speech) would have to reimplement the same rules.
verbum/domain/passage.py:5-61 and verbum/domain/reference.py:1-36 duplicate parsing/loading already handled in verbum/core and rely on reading KJV.json directly, creating conflicting entry points and guaranteeing drift between “domain” and actual runtime code.
Global singletons (console in verbum/cli/main.py:22 and verbum/core/reader.py:20, module-level open_bible() in verbum/core/bible_io.py:22) hide dependencies, complicate testing, and make it hard to swap in mocks or new data sources.
Procedural helpers like pass_next/pass_prev and the ad-hoc NavigationState dataclass lack a shared abstraction, so cross-layer navigation logic must constantly thread (book, chapter, verse) tuples, increasing chances of subtle bugs when adding features (e.g., bookmarking, reading plans).
Recommended Classes and Responsibilities

BibleRepository (interface) with JsonBibleRepository implementation encapsulates loading/counting/lookup logic now spread across bible_io; swapping in an API or database becomes a constructor change instead of a sweeping refactor.
ReferenceParser (service) wraps today’s parse_reference, resolve_book_name, and suggestion flow into a reusable component returning rich Reference objects, improving validation reuse outside the CLI.
PassageAssembler (domain service) converts references into Passage aggregates by coordinating the repository and formatter, separating business rules from presentation so new frontends can reuse it verbatim.
NavigationTracker (stateful class) evolves NavigationState plus pass_next/pass_prev into a cohesive object that can emit “next/prev” references, letting both CLI and future UI share sequential navigation without manual tuple juggling.
OutputFormatter family (RichFormatter, PlainTextFormatter, etc.) handles rendering decisions; the CLI composes a Rich formatter, while APIs could request JSON—maintainability improves by isolating presentation policies.
CommandRouter (CLI application service) interprets user commands (:next, :help, references), delegates to services, and keeps I/O minimal, making the CLI thin and easy to extend with new commands.
Proposed Structure

verbum/domain/ → dataclasses like Reference, Passage, Verse, NavigationSnapshot, delivering a single source of truth for Bible entities.
verbum/infrastructure/ → repositories/json_repository.py, later api_repository.py, isolating data access concerns.
verbum/core/services/ → reference_service.py, passage_service.py, navigation_service.py, housing orchestration logic independent of I/O.
verbum/presentation/ → formatters/rich.py, formatters/plain.py, renderers/cli.py, composing formatters with output channels.
verbum/cli/ → app.py (wires services & console), commands.py (CommandRouter), main.py (entry point that just bootstraps objects).
verbum/config/ → settings/bootstrap helpers (reading BIBLE_PATH, dependency wiring) so every interface shares the same initialization story.
Migration Plan

Introduce domain dataclasses (Reference, Passage, Verse) and update existing functions to use them internally while keeping function signatures backward-compatible.
Extract BibleRepository and move loading/counting logic there; refactor bible_io callers to depend on the repository interface.
Lift parsing and navigation logic into dedicated service classes, letting the CLI call through the new abstractions while tests cover the services directly.
Carve out rendering into formatters and presenters; update reader.get_passage to return domain objects and let the CLI handle formatting via injected strategies.
Replace the CLI loop with a CommandRouter that composes the new services; remove the legacy domain/ duplication once the new pipeline is stable, and expand tests to target each layer.
Only after the CLI is stable, introduce optional adapters (e.g., FastAPI blueprint) to prove the new architecture supports multiple front ends.
Justifications

Layered structure (domain → services → interface) keeps business rules independent from presentation, so adding web or AI interfaces becomes wiring, not rewriting.
Repository abstraction confines data-source knowledge, making future migrations (different translation, remote API) a low-risk change.
Service classes with explicit dependencies improve testability and readability; constructors show what each component needs, and mocks can replace concrete implementations.
Formatters/renderers split output concerns, letting Rich-specific code live beside terminal code without leaking into domain logic.
Command routing separates parsing of commands from side effects, enabling reusable interaction logic for chatbots, REST handlers, or GUIs.
✅ Refactor plan complete — ready for implementation.