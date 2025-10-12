from passage import Passage, open_bible
from reference import Reference
from verbum.infrastructure.config.container import make_repository
repo = make_repository()


ref = Reference.from_string(input("Enter reference (e.g. Genesis 1:1-3): "))
passage = Passage.from_bible(bible, ref)

print(passage)
# Step 8: Legacy scratch script; superseded by CLI + services. To be removed after refactor.
