from verbum.domain.reference import Reference

def test_reference_from_string():
    ref = Reference.from_string("John 3:16-18")
    assert ref.book == "John"
    assert ref.chapter == 3
    assert ref.verses == [16, 17, 18]

def test_reference_from_string_single():
    ref = Reference.from_string("Genesis 1:3")
    assert ref.book == "Genesis"
    assert ref.chapter == 1
    assert ref.verses == [3]

def test_reference_whole_chapter():
    ref = Reference.from_string("Genesis 1")
    assert ref.book == "Genesis"
    assert ref.chapter == 1
    assert ref.verses is None
