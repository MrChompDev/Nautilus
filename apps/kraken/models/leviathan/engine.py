"""Leviathan — writing model engine.

Uses intent detection to generate quality writing assistance responses.
"""

from __future__ import annotations

from collections.abc import Callable

from apps.kraken.core.engine import BaseEngine, EngineResponse


def _classify_intent(msg: str) -> str:
    lower = msg.lower().strip()
    first_word = lower.split()[0] if lower.split() else ""
    if first_word in ("hello", "hi", "hey", "greetings"):
        if len(lower.split()) <= 4:
            return "greeting"
    if any(w in lower for w in ["what's up", "what's good"]):
        return "greeting"
    if any(w in lower for w in ["help", "what can you do", "capabilities"]):
        return "help"
    if any(w in lower for w in ["write", "draft", "compose", "create", "article", "blog", "post"]):
        return "write"
    if any(w in lower for w in ["edit", "proofread", "check grammar", "fix grammar", "review"]):
        return "edit"
    if any(w in lower for w in ["rewrite", "rephrase", "reword", "simplify", "condense"]):
        return "rewrite"
    if any(w in lower for w in ["brainstorm", "ideas", "suggest", "inspiration", "creative"]):
        return "brainstorm"
    if any(w in lower for w in ["email", "letter", "message", "reply", "respond"]):
        return "email"
    if any(w in lower for w in ["story", "fiction", "narrative", "creative writing", "novel"]):
        return "story"
    if any(w in lower for w in ["summary", "summarize", "tldr", "brief"]):
        return "summary"
    if any(w in lower for w in ["explain", "what does", "how does", "teach"]):
        return "explain"
    if any(w in lower for w in ["translate", "translation"]):
        return "translate"
    if any(w in lower for w in ["tone", "formal", "casual", "professional", "friendly"]):
        return "tone"
    if "?" in lower:
        return "question"
    return "general"


_RESPONSES = {
    "greeting": (
        "Hey! I'm Leviathan, your writing assistant. I can help with:\n\n"
        "- **Drafting** — articles, emails, stories, essays\n"
        "- **Editing** — grammar, style, clarity, tone\n"
        "- **Rewriting** — rephrase, restructure, simplify\n"
        "- **Brainstorming** — ideas, outlines, creative angles\n\n"
        "What would you like to write today?"
    ),
    "help": (
        "Here's what I can do:\n\n"
        "**Drafting** — Tell me the topic, audience, and tone, and I'll write it.\n"
        "  Example: \"Write a professional email to my team about the deadline\"\n\n"
        "**Editing** — Paste your text and I'll polish it.\n"
        "  Example: \"Edit this for clarity and flow\"\n\n"
        "**Rewriting** — Give me text and a target style.\n"
        "  Example: \"Rewrite this to be more concise\"\n\n"
        "**Brainstorming** — Give me a topic and I'll generate ideas.\n"
        "  Example: \"Give me 5 blog post ideas about AI\"\n\n"
        "**Proofreading** — I'll catch errors and inconsistencies.\n\n"
        "Just tell me what you need!"
    ),
    "write": lambda msg: (
        f"I'd be happy to help you write that. To get started, tell me:\n\n"
        f"1. **What** — What are you writing? (article, email, story, etc.)\n"
        f"2. **Audience** — Who will read it?\n"
        f"3. **Tone** — Formal, casual, professional, friendly?\n"
        f"4. **Length** — Quick paragraph or full piece?\n\n"
        f"**Your request:** {msg[:150]}\n\n"
        f"The more context you give me, the better I can tailor the writing.\n"
        f"Ready when you are!"
    ),
    "edit": lambda msg: (
        f"I'll help you polish that writing.\n\n"
        f"**Your request:** {msg[:150]}\n\n"
        f"Please paste the text you'd like me to review. I'll check for:\n\n"
        f"- **Grammar & Spelling** — Typos and grammatical errors\n"
        f"- **Clarity** — Unclear or confusing sentences\n"
        f"- **Flow** — Smooth transitions between ideas\n"
        f"- **Tone** — Consistent voice throughout\n"
        f"- **Word Choice** — Stronger, more precise language\n"
        f"- **Conciseness** — Remove unnecessary words\n\n"
        f"Paste your text and I'll get to work!"
    ),
    "rewrite": lambda msg: (
        f"I can rewrite that for you.\n\n"
        f"**Your request:** {msg[:150]}\n\n"
        f"Please share the text you want rewritten, and let me know:\n\n"
        f"- **Target tone** — More formal? More casual? More concise?\n"
        f"- **Audience** — Who is this for?\n"
        f"- **Goal** — What change are you trying to achieve?\n\n"
        f"I'll rework it while preserving the core meaning."
    ),
    "brainstorm": lambda msg: (
        f"Let's brainstorm!\n\n"
        f"**Your topic:** {msg[:150]}\n\n"
        f"I'll generate ideas for you. To get the best results, tell me:\n\n"
        f"- The general area or theme\n"
        f"- Any constraints (length, format, audience)\n"
        f"- What's already been tried\n\n"
        f"Ready to generate some creative ideas!"
    ),
    "email": lambda msg: (
        f"I'll help draft that communication.\n\n"
        f"**Your request:** {msg[:150]}\n\n"
        f"Please tell me:\n\n"
        f"- **Purpose** — What's the email about?\n"
        f"- **Recipient** — Who's it to? (boss, client, colleague, friend)\n"
        f"- **Tone** — Professional, friendly, urgent, formal?\n"
        f"- **Key points** — What needs to be communicated?\n"
        f"- **Call to action** — What should they do after reading?\n\n"
        f"I'll draft something clear and effective."
    ),
    "story": lambda msg: (
        f"I'd love to help with your creative writing!\n\n"
        f"**Your request:** {msg[:150]}\n\n"
        f"Tell me about your story:\n\n"
        f"- **Genre** — Sci-fi, fantasy, mystery, literary, etc.?\n"
        f"- **Setting** — Where and when does it take place?\n"
        f"- **Characters** — Who are the main characters?\n"
        f"- **Conflict** — What's the core tension or problem?\n"
        f"- **Tone** — Dark, light, epic, intimate?\n\n"
        f"I can write scenes, develop characters, or help with world-building."
    ),
    "summary": lambda msg: (
        f"I'll help summarize that.\n\n"
        f"**Your request:** {msg[:150]}\n\n"
        f"Please share the text you want summarized, and let me know:\n\n"
        f"- **Length** — One sentence, paragraph, or bullet points?\n"
        f"- **Focus** — Any particular aspect to emphasize?\n"
        f"- **Audience** — Who is this summary for?\n\n"
        f"I'll distill the key points clearly."
    ),
    "explain": lambda msg: (
        f"I can explain that concept.\n\n"
        f"**Your question:** {msg[:150]}\n\n"
        f"To give you the best explanation, please share:\n\n"
        f"- The text or concept you want explained\n"
        f"- Your experience level (beginner, intermediate, expert)\n"
        f"- What specifically confuses you\n\n"
        f"I'll break it down step by step."
    ),
    "translate": lambda msg: (
        f"I can help with that.\n\n"
        f"**Your request:** {msg[:150]}\n\n"
        f"Please share the text you want translated and specify:\n\n"
        f"- **Source language** — What language is it in?\n"
        f"- **Target language** — What language do you want it in?\n"
        f"- **Tone** — Formal, casual, technical?\n\n"
        f"I'll provide an accurate, natural-sounding translation."
    ),
    "tone": lambda msg: (
        f"I can help adjust the tone.\n\n"
        f"**Your request:** {msg[:150]}\n\n"
        f"Please share the text and tell me:\n\n"
        f"- **Current tone** — How does it sound now?\n"
        f"- **Target tone** — How should it sound?\n"
        f"- **Context** — Who is this for?\n\n"
        f"I'll rework it to match the desired voice."
    ),
    "question": lambda msg: (
        f"Great question!\n\n"
        f"**{msg[:150]}**\n\n"
        f"I'll do my best to answer. If you have specific text you want me "
        f"to analyze or work with, please share it.\n\n"
        f"What aspect would you like me to focus on?"
    ),
    "general": lambda msg: (
        f"I understand. Here's what I can help with:\n\n"
        f"**{msg[:100]}**\n\n"
        f"- **Draft** — Write articles, emails, stories, essays\n"
        f"- **Edit** — Polish grammar, style, and flow\n"
        f"- **Rewrite** — Rephrase for different tone or audience\n"
        f"- **Brainstorm** — Generate ideas and outlines\n"
        f"- **Proofread** — Catch errors and inconsistencies\n\n"
        f"Just describe what you need!"
    ),
}


class LeviathanEngine(BaseEngine):
    model_id = "leviathan"

    def __init__(self, cfg):
        self.cfg = cfg

    def respond(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: Callable[[str], None] | None = None,
        workspace: str | None = None,
    ) -> EngineResponse:
        t0 = self._tick()

        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = (m.get("content") or "").strip()
                break

        intent = _classify_intent(user_msg)
        handler = _RESPONSES.get(intent, _RESPONSES["general"])
        text = handler(user_msg) if callable(handler) else handler

        if stream:
            for ch in text:
                stream(ch)
            stream("\x00")
        return EngineResponse(text=text, elapsed=self._done(t0), model_id=self.model_id)
