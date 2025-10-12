# test_repo.py
from verbum.infrastructure.repositories.json_bible_repository import JsonBibleRepository
from verbum.domain.reference import Reference

# Path to your JSON Bible file (update if needed)
path = "KJV.json"

repo = JsonBibleRepository(path)

# Try a few references
ref = Reference.from_string("John 3:16")
passage = repo.get_passage(ref)

print("✅ Book count:", len(repo.get_book()))
print("✅ Chapter count for John:", repo.get_chapter_count("John"))
print("✅ Verse count in John 3:", repo.get_verse_count("John", 3))
print("📜 Passage example:\n")
print(passage)
