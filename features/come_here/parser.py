"""COME_HERE slot parsing."""

def parse_target(text: str) -> dict[str, str]:
    """The target of a come-here request is the speaker."""
    return {"target": "speaker"}
