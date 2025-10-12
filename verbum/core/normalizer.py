import re

def normalize_reference_raw(raw: str) -> str:
    """
    Normalize a human-entered Bible reference.

        | Input               | Output          |
        | ------------------- | ----------------|
        | "  john 3 : 16  "   | "john 3:16"     |
        | "John 3 : 16 - 18 " | "John 3:16-18"  |
        | "John 3:16,"        |  "John 3:16"    |
    """
    text = raw.strip()                      # "   Genesis1:1  " -> "Genesis1:1"
    text = re.sub(r"\s*:\s*", ":", text)    # "john 3 : 16" → "john 3:16"
    text = re.sub(r"\s*-\s*", "-", text)    # "John 3 : 16 - 18" → "John 3 : 16-18"
    text = text.rstrip(",.;:")
    text = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", text)
    text = re.sub(r"\s+", " ", text)        # "Genesis   1:1" -> "Genesis 1:1"
    return text
