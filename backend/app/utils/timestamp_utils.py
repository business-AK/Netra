def format_timestamp(seconds: float) -> str:
    """Formats seconds into HH:MM:SS or MM:SS format."""
    total_seconds = max(0.0, seconds)
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    secs = int(total_seconds % 60)
    millis = int((total_seconds - int(total_seconds)) * 10)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def parse_timestamp(timestamp_str: str) -> float:
    """Parses HH:MM:SS or MM:SS to seconds."""
    parts = timestamp_str.strip().split(":")
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 1:
        return float(parts[0])
    return 0.0

