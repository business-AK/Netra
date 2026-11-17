import re
import json
from typing import Dict, Any, Optional
from app.utils.timestamp_utils import parse_timestamp

class QueryRouter:
    """
    Intelligent Query Router and Preprocessor.
    Classifies queries into:
      1. SUMMARIZATION (Uniform timeline frame sampling + full transcripts)
      2. TEMPORAL_TARGET (Direct timestamp / position window retrieval)
      3. SEMANTIC_SEARCH (Refined visual query for CLIP + Sentence-Transformers)
    """

    SUMMARY_PATTERNS = [
        r"\b(summariz(e|ation)|summary|overview|recap|outline|rundown)\b",
        r"\bwhat (is|happens in) this (entire |whole )?video\b",
        r"\btell me about this (entire |whole )?video\b",
        r"\bmain (points|events|takeaways|story)\b",
        r"\bexplain the (whole |entire )?video\b",
    ]

    START_PATTERNS = [
        r"\b(at the |in the )?(beginning|start|opening|intro|commence(ment)?)\b",
        r"\bwhat happens first\b",
        r"\bhow does it (start|begin)\b",
    ]

    END_PATTERNS = [
        r"\b(at the |in the )?(end|ending|conclusion|finale|last scene|finally)\b",
        r"\bwhat happens last\b",
        r"\bhow does it (end|finish|conclude)\b",
    ]

    MIDDLE_PATTERNS = [
        r"\b(in the |at the )?middle\b",
        r"\bhalfway through\b",
    ]

    # Timestamp patterns like "at 02:15", "at 1:30", "around 00:45", "at 14 seconds", "at 2 minutes"
    TIMESTAMP_PATTERNS = [
        r"\b(?:at|around|timestamp|time|min|minute|from|near)\s+(\d{1,2}:\d{2}(?::\d{2})?)\b",
        r"\b(\d{1,2}:\d{2}(?::\d{2})?)\b",
        r"\b(\d+)\s*(?:sec|second|seconds)\b",
        r"\b(\d+)\s*(?:min|minute|minutes)\b",
    ]

    # Video intent patterns to distinguish video search from generic QA
    VIDEO_INTENT_PATTERNS = [
        r"\b(video|clip|scene|frame|screen|shot|camera|audio|sound|voice|speaker|transcript|shown|visible|display(ed)?|watch|look)\b",
        r"\b(what color|which color|what is .* wearing|who is .* wearing|where is|where are|is there a|is there an|are there|can you see|do you see|show me|looks? like)\b",
        r"\b(what happens? (when|after|before)|what happened|who entered|who left|did (he|she|they|anyone|the)|who speaks?|who said|what did (he|she|they) say)\b",
        r"\b(shirt|car|cat|dog|person|people|door|room|building|road|street|sign|background|foreground)\b",
    ]

    # Generic QA patterns (general knowledge, definitions, technical, tutorials, chit-chat)
    GENERIC_QA_PATTERNS = [
        # Generic definitions / encyclopedic questions
        r"^(what is|what are|what was|what were|define|meaning of|what does .* mean)\s+(a|an|the)?\s*([a-zA-Z0-9_\- ]+)\??$",
        # How-to tutorials / procedures not video-specific (e.g. how to detect cancer symptoms, how to learn python)
        r"^how (to|can (one|i|we)|do (you|we|people)|does one)\s+(detect|treat|prevent|diagnose|cure|learn|code|program|write|create|build|bake|cook|install|fix|solve|calculate)\b",
        # General technical / coding / algorithm questions
        r"\b(write|create|code|implement|generate)\s+.*(in\s+(python|javascript|typescript|c\+\+|java|rust|go|html|css)|code|script|function|program|algorithm|quicksort|regex)\b",
        r"\b(time complexity|space complexity|difference between|how does [a-zA-Z0-9_\-]+ work)\b",
        # Conversational explanations & follow-up clarifications (e.g., "can you explain what that means", "what does that mean", "why is that so")
        r"^(can you\s+)?(please\s+)?(explain|elaborate|clarify)\s+(what that means|that further|more about that|that concept)\b",
        r"\b(what does that mean|why is that so|tell me more about that)\b",
        # Greetings and general chit-chat
        r"^(hi|hello|hey|good (morning|afternoon|evening)|how are you|who are you|what can you do|thank you|thanks|bye|goodbye)\b",
        # Trivia / world knowledge
        r"^(who (is|was)|where is the capital of|what is the capital of|when did|when was|why is the sky blue)\b",
        r"\b(tell me a joke|tell me a story|write a poem|help me with homework)\b",
    ]

    CONVERSATIONAL_PREFIXES = [
        r"^(can you\s+)?(please\s+)?(tell me\s+)?(is there\s+|are there\s+)?(any\s+)?",
        r"^(what|where|who|how|why|which)\s+(is|are|was|were|do|does|did)\s+(the\s+)?",
        r"\b(in this video|in the video|in the scene|shown in the video|can you see)\b",
    ]

    @classmethod
    def route(cls, query: str, video_duration: float = 0.0) -> Dict[str, Any]:
        """
        Fast-path deterministic rule routing with semantic fallback.
        Returns a dict:
        {
            "strategy": "SUMMARIZATION" | "TEMPORAL_TARGET" | "SEMANTIC_SEARCH",
            "target_timestamp": float or None,
            "relative_position": "start" | "end" | "middle" | None,
            "visual_search_query": str,   # Preprocessed for CLIP
            "original_query": str
        }
        """
        q = query.strip()
        q_lower = q.lower()

        # 1. Check for Summarization Intent
        for pat in cls.SUMMARY_PATTERNS:
            if re.search(pat, q_lower):
                return {
                    "strategy": "SUMMARIZATION",
                    "target_timestamp": None,
                    "relative_position": None,
                    "visual_search_query": q,
                    "original_query": q,
                }

        # 2. Check for Specific Timestamp (e.g. "at 02:15", "1:30", "at 45 seconds")
        for pat in cls.TIMESTAMP_PATTERNS:
            match = re.search(pat, q_lower)
            if match:
                raw_time = match.group(1)
                # If it's a MM:SS string
                if ":" in raw_time:
                    target_sec = parse_timestamp(raw_time)
                elif "min" in match.group(0):
                    target_sec = float(raw_time) * 60.0
                else:
                    target_sec = float(raw_time)

                if video_duration > 0:
                    target_sec = min(max(0.0, target_sec), video_duration)

                return {
                    "strategy": "TEMPORAL_TARGET",
                    "target_timestamp": target_sec,
                    "relative_position": "specific_time",
                    "visual_search_query": cls.refine_visual_query(q),
                    "original_query": q,
                }

        # 3. Check for Relative Positions (Start, End, Middle)
        for pat in cls.START_PATTERNS:
            if re.search(pat, q_lower):
                return {
                    "strategy": "TEMPORAL_TARGET",
                    "target_timestamp": 0.0,
                    "relative_position": "start",
                    "visual_search_query": cls.refine_visual_query(q),
                    "original_query": q,
                }

        for pat in cls.END_PATTERNS:
            if re.search(pat, q_lower):
                target_sec = max(0.0, video_duration - 1.0) if video_duration > 0 else 0.0
                return {
                    "strategy": "TEMPORAL_TARGET",
                    "target_timestamp": target_sec,
                    "relative_position": "end",
                    "visual_search_query": cls.refine_visual_query(q),
                    "original_query": q,
                }

        for pat in cls.MIDDLE_PATTERNS:
            if re.search(pat, q_lower):
                target_sec = (video_duration / 2.0) if video_duration > 0 else 0.0
                return {
                    "strategy": "TEMPORAL_TARGET",
                    "target_timestamp": target_sec,
                    "relative_position": "middle",
                    "visual_search_query": cls.refine_visual_query(q),
                    "original_query": q,
                }

        # 4. Fit into Video Semantic Search if video-specific intent is detected
        has_video_intent = any(re.search(pat, q_lower) for pat in cls.VIDEO_INTENT_PATTERNS)
        if has_video_intent:
            refined_query = cls.refine_visual_query(q)
            return {
                "strategy": "SEMANTIC_SEARCH",
                "target_timestamp": None,
                "relative_position": None,
                "visual_search_query": refined_query,
                "original_query": q,
            }

        # 5. Check if the query is a Generic QA / General Knowledge question
        # (Least-touched route: only used when query does not relate to video)
        is_generic = any(re.search(pat, q_lower) for pat in cls.GENERIC_QA_PATTERNS)
        if is_generic:
            return {
                "strategy": "GENERIC_QA",
                "target_timestamp": None,
                "relative_position": None,
                "visual_search_query": q,
                "original_query": q,
            }

        # 6. Default Semantic Search with Visual Query Refinement
        refined_query = cls.refine_visual_query(q)
        return {
            "strategy": "SEMANTIC_SEARCH",
            "target_timestamp": None,
            "relative_position": None,
            "visual_search_query": refined_query,
            "original_query": q,
        }

    @classmethod
    def refine_visual_query(cls, query: str) -> str:
        """
        Refines a conversational user question into a concise descriptive phrase
        optimized for CLIP text-image contrastive embedding.
        
        Example:
          "is there a cat sitting on a car in this video?" -> "cat sitting on a car"
          "can you tell me what color shirt the boy is wearing?" -> "boy wearing shirt"
          "what objects can you see?" -> "objects"
        """
        text = query.strip()
        # Remove trailing question marks or punctuation
        text = re.sub(r"[?!.]+$", "", text).strip()

        # Remove common question openers
        for prefix in cls.CONVERSATIONAL_PREFIXES:
            text = re.sub(prefix, "", text, flags=re.IGNORECASE).strip()

        # Remove video filler words
        text = re.sub(r"\b(in the video|in this video|in the scene|in this clip|on screen)\b", "", text, flags=re.IGNORECASE).strip()
        
        # Clean double spaces
        text = re.sub(r"\s+", " ", text).strip()

        # Remove leading articles if left at start of phrase (e.g. "a cat sitting on a car" -> "cat sitting on a car")
        text = re.sub(r"^(a|an|the)\s+", "", text, flags=re.IGNORECASE).strip()

        # If stripping made it empty, fallback to the original query
        if len(text) < 2:
            return query.strip()

        return text
