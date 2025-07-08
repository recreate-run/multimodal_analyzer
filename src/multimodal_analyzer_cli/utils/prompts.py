

class PromptManager:
    """Manages analysis prompts for different use cases."""
    
    DEFAULT_PROMPT = "Describe this image in detail, including what you see, the setting, colors, composition, and any notable features or elements."
    
    PROMPTS = {
        "detailed": "Provide a comprehensive description of this image, including all visible elements, colors, composition, lighting, mood, and any text or objects present.",
        "technical": "Analyze this image from a technical perspective, describing the composition, lighting, camera settings if apparent, and photographic techniques used.",
        "artistic": "Describe this image focusing on its artistic qualities, including style, mood, color palette, composition, and overall aesthetic impact.",
        "commercial": "Describe this image for commercial or marketing purposes, highlighting key features, benefits, and appeal to potential customers.",
        "accessibility": "Provide a detailed description of this image for accessibility purposes, including all visual elements that would help someone who cannot see the image understand its content.",
        "scientific": "Analyze this image from a scientific perspective, identifying and describing any scientific concepts, phenomena, or technical details visible.",
        "educational": "Describe this image in an educational context, explaining what can be learned from it and highlighting key educational elements.",
        "social": "Describe this image focusing on social aspects, including people, interactions, cultural elements, and social context."
    }
    
    @classmethod
    def get_prompt(cls, prompt_type: str | None = None, custom_prompt: str | None = None) -> str:
        """Get a prompt based on type or custom input."""
        
        if custom_prompt:
            return custom_prompt
        
        if prompt_type and prompt_type in cls.PROMPTS:
            return cls.PROMPTS[prompt_type]
        
        return cls.DEFAULT_PROMPT
    
    @classmethod
    def list_prompt_types(cls) -> list:
        """List available prompt types."""
        return list(cls.PROMPTS.keys())
    
    @classmethod
    def add_word_count_instruction(cls, prompt: str, word_count: int) -> str:
        """Add word count instruction to a prompt."""
        return f"{prompt} Please provide approximately {word_count} words in your description."


def get_default_audio_prompt() -> str:
    """Get the default prompt for audio analysis."""
    return "Analyze and describe the content of this audio transcript. Include key topics, themes, tone, and any notable information or insights from the spoken content."


def get_audio_prompt(prompt_type: str | None = None) -> str:
    """Get audio-specific prompts based on type."""
    
    audio_prompts = {
        "summary": "Provide a concise summary of the main points and topics discussed in this audio transcript.",
        "detailed": "Provide a comprehensive analysis of this audio transcript, including key topics, themes, tone, speaker insights, and detailed content breakdown.",
        "keywords": "Extract and list the key topics, themes, and important keywords from this audio transcript.",
        "sentiment": "Analyze the sentiment and emotional tone of this audio transcript, including the speaker's mood and overall feeling.",
        "meeting": "Analyze this meeting or discussion transcript, identifying key decisions, action items, and important points discussed.",
        "lecture": "Analyze this educational content, identifying main learning objectives, key concepts, and important information presented.",
        "interview": "Analyze this interview transcript, highlighting key insights, important quotes, and main topics covered.",
        "podcast": "Analyze this podcast transcript, summarizing the main discussion points, guest insights, and key takeaways.",
        "conversation": "Analyze this conversation, identifying main topics, relationship dynamics, and important points discussed."
    }
    
    if prompt_type and prompt_type in audio_prompts:
        return audio_prompts[prompt_type]
    
    return get_default_audio_prompt()