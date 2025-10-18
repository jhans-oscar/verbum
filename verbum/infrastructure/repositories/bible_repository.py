from abc import ABC, abstractmethod
from verbum.domain.reference import Reference

class BibleRepository(ABC):
    @abstractmethod
    def get_passage(self, ref: Reference) -> list[tuple[int, str]]:
        pass

    @abstractmethod
    def list_books(self) -> list[str]:
        pass

    @abstractmethod
    def chapter_count(self, book: str) -> int:
        pass

    @abstractmethod
    def verse_count(self, book: str, chapter: int) -> int:
        pass

    @abstractmethod
    def search(self, query: str, limit: int | None = None) -> list[dict]:
        pass
