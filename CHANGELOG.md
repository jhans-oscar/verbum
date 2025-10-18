# Changelog

All notable changes to this project will be documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and the project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-10-19

### Added

- `/lookup` API endpoint with search, pagination, and book filter.
- CLI command `:search` for word-based lookup.

### Fixed

- Pagination crash when `page_size=0`.
- `total_results` now reflects book-filtered searches.

## [0.2.0] - 2024-10-12

### Added

- Refactored CLI into domain/core/infrastructure layers.
- Added importlib.resources loading for bundled JSON datasets.
- Improved multi-word book parsing and navigation accuracy.
- Rich console output for all user-facing messages, including errors.

### Changed

- Standardized `Reference.verses` to always be `list[int] | None`.

### Removed

- Legacy procedural modules from the 0.1.x codebase.

## [0.1.0] - 2024-10-05

### Added

- Initial Rich-powered CLI for exploring the KJV Bible from the terminal.
- Navigation commands for chapters, single verses, and verse ranges.
- Persistent navigation history with `:next` and `:prev`.
- Fuzzy reference resolution and introductory documentation.
