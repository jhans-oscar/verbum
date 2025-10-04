# Verbum Overview

## Purpose
Verbum is a terminal-first companion for reading the King James Version (KJV) Bible. It accepts natural reference syntax, resolves book names, and renders formatted output with Rich so that developers can explore scripture quickly without leaving the shell.

## Data Flow
User Input -> Reference Parser -> Bible IO -> Reader -> CLI Output

```
+------------+    +------------------+    +---------------+    +-------------+    +-----------+
| User Input | -> | Reference Parser | -> | Bible IO      | -> | Reader      | -> | CLI Output|
+------------+    +------------------+    +---------------+    +-------------+    +-----------+
       |
       v
  Navigation
     Cache
```

## Core Modules
**verbum/cli/main.py** - Hosts the interactive loop, tracks navigation state, and orchestrates calls into the core modules based on user commands.

**verbum/core/reference.py** - Normalizes free-form references, resolves fuzzy book names, and builds canonical strings for downstream processing.

**verbum/core/bible_io.py** - Loads the JSON dataset, exposes helpers for counting chapters and verses, and implements sequential navigation boundaries.

**verbum/core/reader.py** - Validates parsed references, retrieves the requested text, and streams Rich-formatted passages to the console.

**verbum/core/formatting.py** - Converts verse numbers into superscripts and composes the display strings reused across rendering paths.

## Example Session
```
$ verbum
Verbum CLI - type a reference (e.g., 'Genesis 1' or 'Exodus 2:1-10'). Type ':help' or ':quit'.

John 1:1-5
----------------------
[1] In the beginning was the Word, and the Word was with God, and the Word was God.
[2] The same was in the beginning with God.
[3] All things were made by him; and without him was not any thing made that was made.
[4] In him was life; and the life was the light of men.
[5] And the light shineth in darkness; and the darkness comprehended it not.
<- :prev     :next ->
```

## Extending Verbum
Developers can extend Verbum by swapping the JSON dataset via the `BIBLE_PATH` environment variable, or by introducing new rendering styles inside `verbum/core/formatting.py`. Additional commands can be added by wiring handlers into `verbum/cli/main.py` without disturbing the reader pipeline, provided they reuse the existing reference and Bible helpers.
