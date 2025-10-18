from rich.console import Console
from rich.prompt import Prompt

from verbum.core.bible_service import EndOfBibleError, StartOfBibleError
from verbum.core.factory import build_service
from verbum.core.normalizer import normalize_reference_raw
from verbum.domain.reference import Reference

console = Console()

HELP_TEXT = """[bold gold1]Available commands[/bold gold1]
[dim]────────────────────────────[/dim]
[bold]:next[/bold]    Move forward to the next passage
[bold]:prev[/bold]    Return to the previous passage
[bold]:help[/bold]    Show this list
[bold]:quit[/bold], [bold]q[/bold]    Exit Verbum
[bold]:search [word][/bold]   Search for a word or phrase

You can enter any reference directly:
  [italic]John 3:16[/italic] — single verse
  [italic]Genesis 1[/italic] — full chapter
  [italic]Psalm 23:1-4[/italic] — range
"""


BANNER = """[bold gold1]📜  VERBUM[/bold gold1] — Scripture at your fingertips.
[dim]Type a reference (e.g. 'John 1' or 'Psalm 23:1-4')[/dim]
[dim]Commands: :help  |  :next / :prev  |  :quit[/dim]
"""


def render_passage(ref: Reference, text: str) -> None:
    console.rule(f"[bold cyan]📖 {ref.book} {ref.chapter}[/bold cyan]")
    console.print(text)
    console.rule() 
    
    if ref.verses is None:
        ref_str = f"{ref.book} {ref.chapter}"
    elif len(ref.verses) == 1:
        ref_str = f"{ref.book} {ref.chapter}:{ref.verses[0]}"
    else:
        ref_str = f"{ref.book} {ref.chapter}:{ref.verses[0]}-{ref.verses[-1]}"

    console.print(f"[dim]Current reference:[/dim] [bold yellow]{ref_str}[/bold yellow]")
    console.print("[dim]Tips: :next, :search [word], :prev, :help, :quit[/dim]\n")


def main():
    repo, service = build_service()

    console.print(BANNER)
    current_ref: Reference | None = None
    while True:
        user_input = Prompt.ask("[bold yellow]📖 Enter reference or command[/bold yellow]").strip()
        raw_cmd = user_input.strip()
        cmd = raw_cmd.lower()
        normalized = cmd.lstrip(":")

        if normalized in {"quit", "exit", "q"}:
            break

        elif normalized in {"help", "h", "?"}:
            console.print(HELP_TEXT)
            continue

        elif normalized == "next":
            if current_ref is None:
                console.print("\n[magenta]No current passage loaded.[/magenta] Type something like [italic]Genesis 1[/italic].\n")
                continue

            try:
                current_ref = service.get_next(current_ref)
                text = service.get_passage_text(current_ref)
                render_passage(current_ref, text)

            except EndOfBibleError:
                console.print("\n[red]You’ve reached the end of the Bible.[/red]\n")
            continue

        elif normalized in {"prev", "back"}:
            if current_ref is None:
                console.print("\n[magenta]No current passage loaded.[/magenta] Type something like [italic]Genesis 1[/italic].\n")
                continue

            try:
                current_ref = service.get_prev(current_ref)
                text = service.get_passage_text(current_ref)
                render_passage(current_ref, text)

            except StartOfBibleError:
                console.print("\n[red]You’re at the beginning of the Bible.[/red]\n")
            continue

        elif normalized.startswith("search"):
            parts = normalized.split(maxsplit=1)
            if len(parts) == 1:
                console.print("[red]Usage:[/red] :search [word or phrase]")
                continue

            query = parts[1].strip()
            results = repo.search(query)

            if not results:
                console.print(f"[dim]No results found for '{query}'.[/dim]")
                continue

            console.print(f"[bold cyan]🔍 Search results for '{query}'[/bold cyan]")
            for r in results:
                console.print(
                    f"[gold1]{r['book']} {r['chapter']}:{r['verse']}[/gold1] "
                    f"- {r['text']}"
                )
            console.rule()
            continue
                


        try:
            clean = normalize_reference_raw(raw_cmd)
            ref = Reference.from_string(clean)
            ref.book = service.suggest_book(ref.book)
            text = service.get_passage_text(ref)
            current_ref = ref
            render_passage(ref, text)
            
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}\n")

if __name__ == "__main__":
    main()
