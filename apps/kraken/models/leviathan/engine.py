"""Leviathan — writing model engine.

Provides prose and writing assistance with style awareness.
Uses intelligent template responses until models are trained large enough.
"""

from __future__ import annotations

from collections.abc import Callable

from apps.kraken.core.engine import BaseEngine, EngineResponse


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

        text = self._generate_response(user_msg)

        if stream:
            for ch in text:
                stream(ch)
            stream("\x00")
        return EngineResponse(text=text, elapsed=self._done(t0), model_id=self.model_id)

    def _generate_response(self, user_msg: str) -> str:
        lower = user_msg.lower()

        if any(w in lower for w in ["hello", "hi", "hey", "greetings"]):
            return (
                "Hello! I'm Leviathan, your writing assistant. I can help with:\n\n"
                "- **Drafting** — articles, emails, stories, essays\n"
                "- **Editing** — grammar, style, clarity, tone\n"
                "- **Rewriting** — rephrase, restructure, simplify\n"
                "- **Brainstorming** — ideas, outlines, angles\n"
                "- **Proofreading** — catch errors and inconsistencies\n\n"
                "What would you like to write today?"
            )

        if any(w in lower for w in ["help", "what can you do", "capabilities"]):
            return (
                "I'm Leviathan, a writing specialist. Here's what I can do:\n\n"
                "**Drafting** — Write articles, blog posts, emails, stories, essays, and more. Just tell me the topic and tone.\n\n"
                "**Editing** — Improve grammar, clarity, flow, and style. Paste your text and I'll refine it.\n\n"
                "**Rewriting** — Rephrase passages for different audiences, tones, or purposes.\n\n"
                "**Brainstorming** — Generate ideas, outlines, and creative angles.\n\n"
                "**Proofreading** — Find typos, awkward phrasing, and inconsistencies.\n\n"
                "What kind of writing do you need help with?"
            )

        if any(w in lower for w in ["write", "draft", "compose", "create"]):
            return (
                "I'd love to help you write that. To get started, tell me:\n\n"
                "1. **What** — What are you writing? (article, email, story, essay, etc.)\n"
                "2. **Audience** — Who will read it?\n"
                "3. **Tone** — Formal, casual, professional, friendly?\n"
                "4. **Length** — Quick paragraph or full piece?\n\n"
                "The more context you give me, the better I can tailor the writing to your needs."
            )

        if any(w in lower for w in ["edit", "proofread", "check", "review", "fix grammar"]):
            return (
                "I'll help you polish your writing. Please paste the text you'd like me to review.\n\n"
                "I'll check for:\n"
                "- Grammar and spelling errors\n"
                "- Awkward phrasing or unclear sentences\n"
                "- Consistency in tone and style\n"
                "- Flow and readability\n"
                "- Word choice improvements\n\n"
                "Go ahead and paste your text!"
            )

        if any(w in lower for w in ["rewrite", "rephrase", "reword", "simplify"]):
            return (
                "I can rewrite that for you. Please share the text, and let me know:\n\n"
                "- **Target tone** — More formal? More casual? More concise?\n"
                "- **Audience** — Who is this for?\n"
                "- **Goal** — What change are you trying to achieve?\n\n"
                "I'll rework it while keeping the core meaning intact."
            )

        if any(w in lower for w in ["brainstorm", "ideas", "suggest", "inspiration"]):
            return (
                "Let's brainstorm! Tell me the topic or problem, and I'll generate ideas.\n\n"
                "For best results, share:\n"
                "- The general area or theme\n"
                "- Any constraints (length, format, audience)\n"
                "- What's already been tried\n\n"
                "I'll come up with fresh angles and creative approaches."
            )

        if any(w in lower for w in ["email", "letter", "message", "reply"]):
            return (
                "I can help draft that communication. Tell me:\n\n"
                "- **Purpose** — What's the email about?\n"
                "- **Recipient** — Who's it to? (boss, client, colleague, friend)\n"
                "- **Tone** — Professional, friendly, urgent, formal?\n"
                "- **Key points** — What needs to be communicated?\n\n"
                "I'll draft something clear and effective."
            )

        if any(w in lower for w in ["story", "fiction", "narrative", "creative"]):
            return (
                "I'd love to help with your creative writing. Tell me:\n\n"
                "- **Genre** — Sci-fi, fantasy, mystery, literary, etc.?\n"
                "- **Setting** — Where and when does it take place?\n"
                "- **Characters** — Who are the main characters?\n"
                "- **Plot** — What's the core conflict or situation?\n\n"
                "I can write scenes, develop characters, or help with world-building."
            )

        # Default
        return (
            f"I understand you're asking about: \"{user_msg[:80]}\"\n\n"
            "I'm Leviathan, your writing assistant. I can help with:\n\n"
            "- **Drafting** — articles, emails, stories, essays\n"
            "- **Editing** — grammar, style, clarity\n"
            "- **Rewriting** — rephrase, restructure, simplify\n"
            "- **Brainstorming** — ideas, outlines, angles\n"
            "- **Proofreading** — catch errors and inconsistencies\n\n"
            "Try asking me to write something, edit a passage, or brainstorm ideas."
        )
