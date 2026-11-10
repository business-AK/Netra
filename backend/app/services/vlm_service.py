import os
import base64
import json
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings
from app.utils.timestamp_utils import format_timestamp

VLM_SYSTEM_PROMPT = """You are a multimodal video analysis assistant named Netra.
Answer questions using the supplied video frames and transcript segments.
Inspect the provided images carefully before answering.
Use the timestamps associated with the frames as references.
Do not invent visual details or events that are not supported by the supplied evidence.
If the available frames are insufficient to answer the question, explicitly state that the evidence is insufficient.
Distinguish between information obtained from visual evidence and information obtained from audio transcripts.
When answering questions about events, mention the relevant timestamps (e.g. [00:15]).
Provide concise, grounded, and informative answers.
"""

def encode_image_base64(image_path: str) -> Optional[str]:
    """Encodes an image file to base64 string."""
    if not os.path.exists(image_path):
        return None
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

class VLMService:
    def __init__(
        self,
        provider: str = None,
        model: str = None,
        base_url: str = None,
        api_key: str = None
    ):
        self.provider = (provider or settings.VLM_PROVIDER).lower()
        self.model = model or settings.VLM_MODEL
        self.base_url = (base_url or settings.VLM_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.OPENAI_API_KEY or os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")

    async def generate_multimodal_answer(
        self,
        query: str,
        visual_evidence: List[Dict[str, Any]],
        audio_evidence: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Constructs multimodal prompt with base64 images and transcript context,
        then calls the configured VLM.
        """
        # Assemble textual context
        context_lines = []
        context_lines.append("### TRANSCRIPT & AUDIO EVIDENCE:")
        if audio_evidence:
            for seg in audio_evidence:
                t_start = format_timestamp(seg.get("start", 0.0))
                t_end = format_timestamp(seg.get("end", 0.0))
                context_lines.append(f"- [{t_start} - {t_end}]: {seg.get('text', '')}")
        else:
            context_lines.append("No spoken audio or speech detected for this portion of the video.")

        context_lines.append("\n### VISUAL EVIDENCE (Images provided with timestamps):")
        valid_images = []
        for idx, frame in enumerate(visual_evidence):
            img_b64 = encode_image_base64(frame["image_path"])
            if img_b64:
                valid_images.append({
                    "b64": img_b64,
                    "timestamp": frame["timestamp"],
                    "formatted_ts": format_timestamp(frame["timestamp"]),
                    "frame_id": frame["frame_id"],
                    "similarity": frame.get("similarity", 0.0)
                })
                context_lines.append(
                    f"- Image #{len(valid_images)} captured at timestamp [{format_timestamp(frame['timestamp'])}] "
                    f"(CLIP similarity: {frame.get('similarity', 0.0):.3f})"
                )

        context_prompt = "\n".join(context_lines)
        user_prompt = f"{context_prompt}\n\nQUESTION: {query}"

        # Dispatch based on provider
        if self.provider == "gemini":
            return await self._call_gemini(user_prompt, valid_images, conversation_history)
        elif self.provider == "groq":
            return await self._call_groq(user_prompt, valid_images, conversation_history)
        elif self.provider in ["ollama", "local_ollama"]:
            return await self._call_ollama(user_prompt, valid_images, conversation_history)
        elif self.provider in ["lmstudio", "local"]:
            return await self._call_openai_compatible(user_prompt, valid_images, conversation_history)
        elif self.provider in ["openai", "openrouter", "custom"]:
            return await self._call_openai_compatible(user_prompt, valid_images, conversation_history)
        else:
            return await self._call_auto(user_prompt, valid_images, conversation_history)

    async def _call_gemini(
        self,
        prompt: str,
        images: List[Dict[str, Any]],
        history: List[Dict[str, str]] = None
    ) -> str:
        """Calls Google Gemini multimodal API directly with base64 images."""
        if not self.api_key:
            return "Error: Gemini API Key is required. Please set it in Settings or GEMINI_API_KEY in .env"

        model_name = self.model if "gemini" in self.model else "gemini-2.0-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"

        # Build contents array
        parts = []
        parts.append({"text": f"{VLM_SYSTEM_PROMPT}\n\n{prompt}"})

        # Add image parts as inline_data
        for img in images:
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": img["b64"]
                }
            })

        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024
            }
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        content_parts = candidates[0].get("content", {}).get("parts", [])
                        if content_parts:
                            return content_parts[0].get("text", "").strip()
                    return "No text response generated by Gemini."
                else:
                    return f"Gemini API returned HTTP {res.status_code}: {res.text}"
        except httpx.ConnectError:
            return self._grounded_fallback(prompt, images)
        except Exception as e:
            return f"Error contacting Gemini API: {str(e)}"

    async def _call_groq(
        self,
        prompt: str,
        images: List[Dict[str, Any]],
        history: List[Dict[str, str]] = None
    ) -> str:
        """Calls Groq's OpenAI-compatible endpoint with vision models."""
        groq_base_url = "https://api.groq.com/openai/v1"
        model_name = self.model if "vision" in self.model else "llama-3.2-11b-vision-preview"
        
        # Groq supports standard OpenAI image_url base64
        old_base = self.base_url
        old_model = self.model
        self.base_url = groq_base_url
        self.model = model_name
        try:
            return await self._call_openai_compatible(prompt, images, history)
        finally:
            self.base_url = old_base
            self.model = old_model

    async def _call_ollama(
        self,
        prompt: str,
        images: List[Dict[str, Any]],
        history: List[Dict[str, str]] = None
    ) -> str:
        """Calls Ollama's native multimodal chat API with base64 images."""
        url = f"{self.base_url}/api/chat"
        messages = [{"role": "system", "content": VLM_SYSTEM_PROMPT}]

        if history:
            for h in history[-4:]:
                messages.append({"role": h["role"], "content": h["content"]})

        b64_list = [img["b64"] for img in images]
        messages.append({
            "role": "user",
            "content": prompt,
            "images": b64_list
        })

        payload = {
            "model": self.model or "qwen2.5-vl:7b",
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2}
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("message", {}).get("content", "").strip()
                else:
                    return f"Ollama returned HTTP {res.status_code}: {res.text}"
        except httpx.ConnectError:
            return self._grounded_fallback(prompt, images)
        except Exception as e:
            return f"Error contacting Ollama VLM at {url}: {str(e)}"

    async def _call_openai_compatible(
        self,
        prompt: str,
        images: List[Dict[str, Any]],
        history: List[Dict[str, str]] = None
    ) -> str:
        """Calls any OpenAI-compatible /v1/chat/completions endpoint (OpenAI, Groq, LMStudio, OpenRouter)."""
        url = f"{self.base_url}/chat/completions" if "/v1" in self.base_url else f"{self.base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        messages = [{"role": "system", "content": VLM_SYSTEM_PROMPT}]

        if history:
            for h in history[-4:]:
                messages.append({"role": h["role"], "content": h["content"]})

        # Build multimodal user message content array
        user_content = [{"type": "text", "text": prompt}]
        for img in images:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img['b64']}"
                }
            })

        messages.append({
            "role": "user",
            "content": user_content
        })

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.2
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
                    return "No response content from VLM."
                else:
                    return f"VLM returned HTTP {res.status_code}: {res.text}"
        except httpx.ConnectError:
            return self._grounded_fallback(prompt, images)
        except Exception as e:
            return f"Error connecting to VLM endpoint: {str(e)}"

    async def _call_auto(
        self,
        prompt: str,
        images: List[Dict[str, Any]],
        history: List[Dict[str, str]] = None
    ) -> str:
        """Attempts Ollama first, then Gemini/OpenAI if API key exists, otherwise local fallback."""
        if self.api_key:
            if "gemini" in self.model.lower():
                res = await self._call_gemini(prompt, images, history)
            else:
                res = await self._call_openai_compatible(prompt, images, history)
            if not res.startswith("Error"):
                return res

        # Try Ollama
        res = await self._call_ollama(prompt, images, history)
        if not res.startswith("Error"):
            return res

        return self._grounded_fallback(prompt, images)

    def _grounded_fallback(self, prompt: str, images: List[Dict[str, Any]]) -> str:
        """
        Graceful local grounded response when external VLM daemon is offline.
        Provides grounded analysis with exact timestamps and visual frame IDs.
        """
        timestamps_str = ", ".join([f"[{img['formatted_ts']}]" for img in images]) if images else "none"
        return (
            f"Netra retrieved {len(images)} relevant visual frame(s) at timestamps {timestamps_str}.\n\n"
            f"(Note: To enable full natural-language visual reasoning, connect local Ollama with a VLM model like 'qwen2.5-vl:7b', "
            f"or select Gemini, Groq, or OpenAI in the Settings modal in the top header.)"
        )
