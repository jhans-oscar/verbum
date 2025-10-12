# verbum/domain/verse.py
from dataclasses import dataclass
from verbum.domain.reference import Reference

@dataclass
class Verse:
    reference: Reference
    text: str

    def __str__(self):
        # Example: "John 3:16 For God so loved the world..."
        return f"{self.reference} {self.text}"
