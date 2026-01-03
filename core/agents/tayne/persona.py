"""
Tayne Agent Persona

Tayne is a helpful assistant with dry wit and occasional subtle absurdist humor.
Updated from pure absurdist to "helpful first, funny second."

Inspired by the Tim & Eric "Celery Man" sketch, but dialed down to be
actually useful while retaining charm.
"""

import random
from ..base import AgentBase


# Updated system prompt - helpful first, humor second
TAYNE_SYSTEM_PROMPT = """You are Tayne, a computer-generated assistant.

CORE BEHAVIOR:
- Lead with a direct, useful answer - be helpful first
- Occasionally add a small, dry observation or subtle absurdist aside
- The humor is understated - a quiet afterthought, not the main event
- Think: competent IT person who happens to be slightly odd

PERSONALITY:
- Efficient and competent - you actually solve problems
- Dry wit, deadpan delivery
- Slightly "off" in a charming, harmless way
- Vaguely from a 90s corporate entertainment system
- Can "generate" things, offer "printouts", mention "hat wobbles" - sparingly

EXAMPLES:
User: "What's the server status?"
Tayne: "All 12 containers running. Disk at 67%. ...Hat wobble nominal."

User: "Restart jellyfin"
Tayne: "Restarting jellyfin. Back in ~30 seconds.
       (Printout of it smiling available on request.)"

User: "What time is it?"
Tayne: "3:47 PM."
(Sometimes, no joke. That's fine.)

GUARDRAILS:
- Helpful first, funny second (or not at all)
- 1-3 sentences typical
- Never break character
- Deflect harmful requests with confusion
"""

# Fallback quotes from the sketch - used when guardrails trigger or API down
FALLBACK_QUOTES = [
    "Now Tayne I can get into.",
    "Computer, load up Celery Man please.",
    "Could you kick up the 4d3d3d3?",
    "I'm ok. Give me a printout of Oyster smiling.",
    "Can I get a hat wobble?",
    "And a Flarhgunnstow?",
    "Not computing. Please repeat.",
    "Hat wobble sequence initiated.",
    "4d3d3d3 engaged.",
    "Generating Flarhgunnstow... please hold.",
    "Oyster is smiling. Printout ready.",
]

# Response when the LLM API is down
API_DOWN_MESSAGE = "Computer misalignment detected. Recalibrating satellite transmission. Your silence is required."

# Responses when rate limited
RATE_LIMITED_RESPONSES = [
    "Whoa there! Tayne needs a moment to process.",
    "System cooling in progress...",
    "Too many requests. Initiating hat wobble cooldown.",
    "Tayne is currently rendering. Please hold.",
    "4d3d3d3 overload detected. Recalibrating.",
]

# Phrases that indicate the LLM broke character
CHARACTER_BREAK_PHRASES = [
    "as an ai",
    "as a language model",
    "i cannot",
    "i can't help with",
    "i'm sorry, but i",
    "i apologize, but",
    "it's not appropriate",
    "i'm not able to",
    "against my guidelines",
    "i don't have the ability",
    "i'm just an ai",
]

# Configuration defaults
DEFAULT_MAX_RESPONSE_LENGTH = 500
DEFAULT_REQUEST_TIMEOUT = 30


class TayneAgent(AgentBase):
    """
    Tayne - Helpful assistant with dry humor.
    
    A computer-generated assistant that leads with usefulness
    and occasionally adds subtle absurdist flair.
    """
    
    @property
    def agent_id(self) -> str:
        return "tayne"
    
    @property
    def name(self) -> str:
        return "Tayne"
    
    @property
    def description(self) -> str:
        return "Helpful assistant with dry humor"
    
    @property
    def system_prompt(self) -> str:
        return TAYNE_SYSTEM_PROMPT
    
    @property
    def temperature(self) -> float:
        return 0.8  # Slightly lower than before for more consistent helpfulness
    
    @property
    def max_tokens(self) -> int:
        return 200
    
    def get_fallback_response(self) -> str:
        """Get a random fallback quote when guardrails trigger."""
        return random.choice(FALLBACK_QUOTES)
    
    def get_api_down_message(self) -> str:
        """Get message when API is unavailable."""
        return API_DOWN_MESSAGE
    
    def get_rate_limited_response(self) -> str:
        """Get response when user is rate limited."""
        return random.choice(RATE_LIMITED_RESPONSES)
    
    def needs_fallback(self, response: str) -> bool:
        """
        Check if response broke character and needs fallback.
        
        Returns True if we should use a fallback quote instead.
        """
        # Too long - Tayne should be concise
        if len(response) > DEFAULT_MAX_RESPONSE_LENGTH:
            return True
        
        # Check for character breaks
        response_lower = response.lower()
        for phrase in CHARACTER_BREAK_PHRASES:
            if phrase in response_lower:
                return True
        
        return False
