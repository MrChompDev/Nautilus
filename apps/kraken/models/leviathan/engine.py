"""Leviathan — writing model engine.

Produces real written content: emails, articles, documents, stories.
Saves output to files. Not a chatbot — a writing agent.
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable

from apps.kraken.core.engine import BaseEngine, EngineResponse
from apps.kraken.core.tools import file_write


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
    if any(w in lower for w in ["write", "draft", "compose", "create", "generate",
                                  "put together", "prepare"]):
        if any(w in lower for w in ["email", "mail"]):
            return "write_email"
        if any(w in lower for w in ["article", "blog", "post", "essay"]):
            return "write_article"
        if any(w in lower for w in ["story", "fiction", "narrative", "novel"]):
            return "write_story"
        if any(w in lower for w in ["readme", "read me"]):
            return "write_readme"
        if any(w in lower for w in ["changelog", "change log", "release notes"]):
            return "write_changelog"
        if any(w in lower for w in ["proposal", "pitch"]):
            return "write_proposal"
        if any(w in lower for w in ["spec", "specification", "technical spec", "rfc"]):
            return "write_spec"
        if any(w in lower for w in ["meeting notes", "meeting minutes", "notes from"]):
            return "write_notes"
        if any(w in lower for w in ["press release", "pr ", "announcement"]):
            return "write_press"
        if any(w in lower for w in ["job", "hiring", "position", "role", "opening"]):
            return "write_job"
        if any(w in lower for w in ["product description", "product page", "features"]):
            return "write_product"
        if any(w in lower for w in ["tweet", "twitter", "linkedin", "instagram", "social"]):
            return "write_social"
        if any(w in lower for w in ["letter", "formal letter"]):
            return "write_letter"
        if any(w in lower for w in ["tutorial", "how to", "guide", "walkthrough"]):
            return "write_tutorial"
        if any(w in lower for w in ["speech", "talk", "presentation"]):
            return "write_speech"
        if any(w in lower for w in ["review", "critique", "feedback"]):
            return "write_review"
        if any(w in lower for w in ["resume", "cv"]):
            return "write_resume"
        if any(w in lower for w in ["summary", "brief", "synopsis"]):
            return "write_summary"
        if any(w in lower for w in ["document", "doc", "report", "paper"]):
            return "write_document"
        if any(w in lower for w in ["copy", "content", "landing", "ad", "marketing"]):
            return "write_copy"
        return "write_general"
    if any(w in lower for w in ["edit", "revise", "fix", "proofread", "check"]):
        return "edit"
    if any(w in lower for w in ["brainstorm", "ideas", "suggest", "what should"]):
        return "brainstorm"
    if any(w in lower for w in ["rewrite", "rephrase", "paraphrase", "simplify",
                                  "make it better", "improve"]):
        return "rewrite"
    if any(w in lower for w in ["outline", "structure", "plan"]):
        return "outline"
    if "?" in lower:
        return "question"
    return "general"


def _guess_filename(msg: str, content_type: str) -> str:
    lower = msg.lower()
    # Check if user specified a filename
    for word in msg.split():
        clean = word.strip("\"'.,:;")
        if "." in clean and any(clean.endswith(ext) for ext in [".md", ".txt", ".html", ".docx"]):
            return clean
    # Guess from content type
    type_map = {
        "email": "email.md",
        "article": "article.md",
        "story": "story.md",
        "document": "document.md",
        "summary": "summary.md",
        "resume": "resume.md",
        "copy": "copy.md",
        "proposal": "proposal.md",
        "readme": "README.md",
        "changelog": "CHANGELOG.md",
        "spec": "specification.md",
        "notes": "meeting_notes.md",
        "press": "press_release.md",
        "job": "job_posting.md",
        "product": "product_description.md",
        "social": "social_posts.md",
        "letter": "letter.md",
        "tutorial": "tutorial.md",
        "speech": "speech.md",
        "review": "review.md",
    }
    return type_map.get(content_type, "document.md")


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

        ws = workspace or os.getcwd()
        intent = _classify_intent(user_msg)

        if intent == "write_email":
            text = self._task_write_email(user_msg, ws)
        elif intent == "write_article":
            text = self._task_write_article(user_msg, ws)
        elif intent == "write_story":
            text = self._task_write_story(user_msg, ws)
        elif intent == "write_document":
            text = self._task_write_document(user_msg, ws)
        elif intent == "write_summary":
            text = self._task_write_summary(user_msg, ws)
        elif intent == "write_resume":
            text = self._task_write_resume(user_msg, ws)
        elif intent == "write_copy":
            text = self._task_write_copy(user_msg, ws)
        elif intent == "write_proposal":
            text = self._task_write_proposal(user_msg, ws)
        elif intent == "write_readme":
            text = self._task_write_readme(user_msg, ws)
        elif intent == "write_changelog":
            text = self._task_write_changelog(user_msg, ws)
        elif intent == "write_spec":
            text = self._task_write_spec(user_msg, ws)
        elif intent == "write_notes":
            text = self._task_write_notes(user_msg, ws)
        elif intent == "write_press":
            text = self._task_write_press(user_msg, ws)
        elif intent == "write_job":
            text = self._task_write_job(user_msg, ws)
        elif intent == "write_product":
            text = self._task_write_product(user_msg, ws)
        elif intent == "write_social":
            text = self._task_write_social(user_msg, ws)
        elif intent == "write_letter":
            text = self._task_write_letter(user_msg, ws)
        elif intent == "write_tutorial":
            text = self._task_write_tutorial(user_msg, ws)
        elif intent == "write_speech":
            text = self._task_write_speech(user_msg, ws)
        elif intent == "write_review":
            text = self._task_write_review(user_msg, ws)
        elif intent == "write_general":
            text = self._task_write_general(user_msg, ws)
        elif intent == "edit":
            text = self._task_edit(user_msg, ws)
        elif intent == "brainstorm":
            text = self._task_brainstorm(user_msg, ws)
        elif intent == "rewrite":
            text = self._task_rewrite(user_msg, ws)
        elif intent == "outline":
            text = self._task_outline(user_msg, ws)
        elif intent == "help":
            text = self._help_text()
        elif intent == "greeting":
            text = "Hey! What do you need written?"
        else:
            text = self._task_general(user_msg, ws)

        if stream:
            for ch in text:
                stream(ch)
            stream("\x00")
        return EngineResponse(text=text, elapsed=self._done(t0), model_id=self.model_id)

    # ── Write Email ──────────────────────────────────────────────

    def _task_write_email(self, msg: str, ws: str) -> str:
        content = self._gen_email(msg)
        filepath = os.path.join(ws, _guess_filename(msg, "email"))
        file_write(filepath, content)
        return (
            f"**Created:** `{os.path.basename(filepath)}`\n\n"
            f"---\n\n{content}\n\n---\n\n"
            f"File saved to: {filepath}"
        )

    def _gen_email(self, msg: str) -> str:
        lower = msg.lower()
        # Extract topic from message
        topic = msg
        for prefix in ["write an email about", "write email about", "email about",
                        "draft an email about", "draft email about",
                        "write an email to", "write email to", "email to",
                        "draft an email to", "draft email to",
                        "write a follow up", "write follow up", "draft a follow up",
                        "write a thank", "write thank", "draft a thank",
                        "write a meeting", "write meeting", "draft a meeting"]:
            if prefix in lower:
                idx = lower.index(prefix) + len(prefix)
                topic = msg[idx:].strip(".!?, ")
                break
        # Determine email type
        if any(w in lower for w in ["thank", "appreciation", "grateful"]):
            subject = f"Thank You — {topic.title()}"
            body = (
                f"Subject: Thank You\n\n"
                f"Hi,\n\n"
                f"I wanted to reach out to express my sincere gratitude for your "
                f"recent help with {topic.lower()}. Your support made a real difference, "
                f"and I truly appreciate the time and effort you put in.\n\n"
                f"Please don't hesitate to reach out if there's ever anything I "
                f"can do in return.\n\n"
                f"Best regards"
            )
        elif any(w in lower for w in ["follow up", "following up", "checking in"]):
            subject = f"Follow Up — {topic.title()}"
            body = (
                f"Subject: Follow Up\n\n"
                f"Hi,\n\n"
                f"I'm following up on {topic.lower()}. I understand you're "
                f"busy, but I'd appreciate it if you could take a look when you "
                f"get a chance.\n\n"
                f"Please let me know if you need any additional information.\n\n"
                f"Thanks"
            )
        elif any(w in lower for w in ["apologize", "sorry", "apology"]):
            subject = f"Apology — {topic.title()}"
            body = (
                f"Subject: Apology\n\n"
                f"Hi,\n\n"
                f"I wanted to sincerely apologize regarding {topic.lower()}. I take "
                f"full responsibility and am working to ensure this doesn't "
                f"happen again.\n\n"
                f"I appreciate your patience and understanding.\n\n"
                f"Best regards"
            )
        elif any(w in lower for w in ["meeting", "schedule", "call"]):
            subject = f"Meeting Request — {topic.title()}"
            body = (
                f"Subject: Meeting Request\n\n"
                f"Hi,\n\n"
                f"I'd like to schedule a meeting to discuss {topic.lower()}. "
                f"Would any of the following times work for you?\n\n"
                f"- Monday 2pm\n"
                f"- Tuesday 10am\n"
                f"- Wednesday 3pm\n\n"
                f"Please let me know what works best.\n\n"
                f"Best regards"
            )
        else:
            subject = f"{topic.title()}"
            body = (
                f"Subject: {topic.title()}\n\n"
                f"Hi,\n\n"
                f"I hope this message finds you well.\n\n"
                f"I'm reaching out regarding {topic.lower()}. "
                f"I'd love to discuss this further and explore how we can "
                f"move forward.\n\n"
                f"Looking forward to hearing from you.\n\n"
                f"Best regards"
            )
        return body

    # ── Write Article ────────────────────────────────────────────

    def _task_write_article(self, msg: str, ws: str) -> str:
        content = self._gen_article(msg)
        filepath = os.path.join(ws, _guess_filename(msg, "article"))
        file_write(filepath, content)
        return (
            f"**Created:** `{os.path.basename(filepath)}`\n\n"
            f"---\n\n{content}\n\n---\n\n"
            f"File saved to: {filepath}"
        )

    def _gen_article(self, msg: str) -> str:
        # Extract topic from message
        topic = msg
        for prefix in ["write an article about", "write about", "article about",
                        "blog post about", "write a blog post about",
                        "write an article on", "write on", "article on"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        # Clean up
        topic = topic.strip(".!?")
        if not topic or topic in ("an article", "a blog post", "about"):
            topic = "this topic"
        # Capitalize properly
        topic_display = " ".join(w.capitalize() if len(w) > 3 else w for w in topic.split())

        return (
            f"# {topic.title()}\n\n"
            f"## Introduction\n\n"
            f"This article explores {topic.lower()}. "
            f"Understanding this topic is essential for anyone looking to "
            f"deepen their knowledge in this area.\n\n"
            f"## Background\n\n"
            f"To understand {topic.lower()}, we need to look at the context "
            f"and history behind it. This provides the foundation for "
            f"understanding the key concepts.\n\n"
            f"## Key Points\n\n"
            f"### 1. Core Concept\n\n"
            f"The fundamental principle of {topic.lower()} revolves around "
            f"understanding how the core components interact with each other.\n\n"
            f"### 2. Practical Application\n\n"
            f"In practice, {topic.lower()} can be applied in various contexts. "
            f"The most common use cases include improving efficiency, "
            f"reducing costs, and enhancing overall performance.\n\n"
            f"### 3. Common Challenges\n\n"
            f"Like any field, {topic.lower()} comes with its set of challenges. "
            f"However, with the right approach, these can be effectively "
            f"addressed.\n\n"
            f"## Best Practices\n\n"
            f"- Start with a solid foundation\n"
            f"- Test and iterate continuously\n"
            f"- Learn from real-world examples\n"
            f"- Stay updated with the latest developments\n\n"
            f"## Conclusion\n\n"
            f"{topic.title()} is an important area that continues to evolve. "
            f"By understanding the fundamentals and applying best practices, "
            f"you can achieve significant results.\n\n"
            f"---\n\n"
            f"*Published with Leviathan — your writing assistant*"
        )

    # ── Write Story ──────────────────────────────────────────────

    def _task_write_story(self, msg: str, ws: str) -> str:
        content = self._gen_story(msg)
        filepath = os.path.join(ws, _guess_filename(msg, "story"))
        file_write(filepath, content)
        return (
            f"**Created:** `{os.path.basename(filepath)}`\n\n"
            f"---\n\n{content}\n\n---\n\n"
            f"File saved to: {filepath}"
        )

    def _gen_story(self, msg: str) -> str:
        topic = msg
        for prefix in ["write a story about", "write about", "story about"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "a mysterious journey"

        return (
            f"# The Story of {topic.title()}\n\n"
            f"The morning light crept through the window, painting golden "
            f"streaks across the floor. It was the beginning of something new — "
            f"a day that would change everything.\n\n"
            f"## Chapter 1: The Discovery\n\n"
            f"Nobody expected what came next. The discovery was simple at first "
            f"glance, but as layers peeled back, the complexity became apparent. "
            f"{topic.title()} had arrived in their world, and nothing would "
            f"ever be the same.\n\n"
            f"The protagonist stood at the crossroads, weighing options that "
            f"seemed both impossible and inevitable. Every choice had "
            f"consequences, and the weight of responsibility pressed down.\n\n"
            f"## Chapter 2: The Journey\n\n"
            f"The path forward was unclear, but standing still was not an option. "
            f"Step by step, the journey unfolded. Allies appeared from unexpected "
            f"places, and what began as a solitary quest became something greater.\n\n"
            f"\"We don't have all the time in the world,\" they said, eyes fixed "
            f"on the horizon. \"But we have enough.\"\n\n"
            f"## Chapter 3: The Resolution\n\n"
            f"In the end, it was not about winning or losing. It was about "
            f"understanding — understanding oneself, others, and the world "
            f"that connects us all.\n\n"
            f"The sun set on a changed landscape. What began as uncertainty "
            f"had transformed into clarity. And though the story was ending, "
            f"the echoes would last forever.\n\n"
            f"---\n\n"
            f"*Written with Leviathan — your storytelling companion*"
        )

    # ── Write Document ───────────────────────────────────────────

    def _task_write_document(self, msg: str, ws: str) -> str:
        content = self._gen_document(msg)
        filepath = os.path.join(ws, _guess_filename(msg, "document"))
        file_write(filepath, content)
        return (
            f"**Created:** `{os.path.basename(filepath)}`\n\n"
            f"---\n\n{content}\n\n---\n\n"
            f"File saved to: {filepath}"
        )

    def _gen_document(self, msg: str) -> str:
        topic = msg
        for prefix in ["write a document about", "write about", "create a document",
                        "write a report about", "create a report"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this topic"

        return (
            f"# {topic.title()} — Report\n\n"
            f"**Date:** {time.strftime('%Y-%m-%d')}\n\n"
            f"## Executive Summary\n\n"
            f"This document covers {topic.lower()}, including key findings "
            f"and recommendations.\n\n"
            f"## Overview\n\n"
            f"The following report examines {topic.lower()} from multiple "
            f"perspectives, providing actionable insights.\n\n"
            f"## Key Findings\n\n"
            f"1. **Finding One:** Primary observation\n"
            f"2. **Finding Two:** Supporting evidence\n"
            f"3. **Finding Three:** Additional insight\n\n"
            f"## Analysis\n\n"
            f"Based on the data collected, the analysis reveals important "
            f"patterns that inform our recommendations.\n\n"
            f"## Recommendations\n\n"
            f"- Implement changes gradually\n"
            f"- Monitor key metrics\n"
            f"- Review progress quarterly\n\n"
            f"## Conclusion\n\n"
            f"This report provides a comprehensive overview. "
            f"Further research may be needed in specific areas.\n\n"
            f"---\n\n"
            f"*Generated with Leviathan — your writing assistant*"
        )

    # ── Write Summary ────────────────────────────────────────────

    def _task_write_summary(self, msg: str, ws: str) -> str:
        content = (
            f"# Summary: {msg[:60]}\n\n"
            f"**Purpose:** {msg[:120]}\n\n"
            f"## Key Points\n\n"
            f"- Point 1\n"
            f"- Point 2\n"
            f"- Point 3\n\n"
            f"## Bottom Line\n\n"
            f"The essential takeaway from this summary."
        )
        filepath = os.path.join(ws, _guess_filename(msg, "summary"))
        file_write(filepath, content)
        return f"**Created:** `{os.path.basename(filepath)}`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write Resume ─────────────────────────────────────────────

    def _task_write_resume(self, msg: str, ws: str) -> str:
        content = (
            "# Resume\n\n"
            "## Experience\n\n"
            "### Job Title — Company Name\n"
            "*Start Date - End Date*\n\n"
            "- Achievement 1\n"
            "- Achievement 2\n"
            "- Achievement 3\n\n"
            "## Education\n\n"
            "### Degree — University\n"
            "*Graduation Year*\n\n"
            "## Skills\n\n"
            "- Skill 1\n"
            "- Skill 2\n"
            "- Skill 3\n\n"
            "## About\n\n"
            "Professional summary goes here."
        )
        filepath = os.path.join(ws, "resume.md")
        file_write(filepath, content)
        return f"**Created:** `resume.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write Copy ───────────────────────────────────────────────

    def _task_write_copy(self, msg: str, ws: str) -> str:
        content = self._gen_copy(msg)
        filepath = os.path.join(ws, _guess_filename(msg, "copy"))
        file_write(filepath, content)
        return f"**Created:** `{os.path.basename(filepath)}`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    def _gen_copy(self, msg: str) -> str:
        topic = msg
        for prefix in ["write copy about", "write ad copy about", "create marketing copy",
                        "write landing page copy about"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "your product"

        return (
            f"# Marketing Copy: {topic.title()}\n\n"
            f"## Headline\n\n"
            f"**{topic.title()}** — Transform Your Experience\n\n"
            f"## Subheadline\n\n"
            f"Discover a better way to approach {topic.lower()}.\n\n"
            f"## Body Copy\n\n"
            f"Are you looking for a solution that actually works? "
            f"{topic.title()} is designed to help you achieve your goals "
            f"faster and more effectively.\n\n"
            f"**Key Benefits:**\n"
            f"- Save time with automated workflows\n"
            f"- Improve quality with intelligent features\n"
            f"- Scale effortlessly as you grow\n\n"
            f"## Call to Action\n\n"
            f"**Get started today** and see the difference.\n\n"
            f"---\n\n"
            f"*Crafted with Leviathan — your copywriting assistant*"
        )

    # ── Write General ────────────────────────────────────────────

    def _task_write_general(self, msg: str, ws: str) -> str:
        content = (
            f"# {msg[:60]}\n\n"
            f"{msg[:200]}\n\n"
            f"## Details\n\n"
            f"This content addresses the request: {msg[:120]}\n\n"
            f"Content continues here."
        )
        filepath = os.path.join(ws, "document.md")
        file_write(filepath, content)
        return f"**Created:** `document.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Edit ─────────────────────────────────────────────────────

    def _task_edit(self, msg: str, ws: str) -> str:
        # Try to find the file
        for word in msg.split():
            clean = word.strip("\"'.,:;")
            if "." in clean and any(clean.endswith(ext) for ext in [".md", ".txt", ".html"]):
                from apps.kraken.core.tools import file_read
                result = file_read(os.path.join(ws, clean))
                if result.ok:
                    return (
                        f"**Current content of `{clean}`:**\n\n"
                        f"---\n{result.output[:2000]}\n---\n\n"
                        f"Tell me what changes to make.\n"
                        f"Examples:\n"
                        f"- \"Change the title to X\"\n"
                        f"- \"Add a section about Y\"\n"
                        f"- \"Make it shorter\"\n"
                        f"- \"Rewrite the introduction\""
                    )
        return "Tell me which file to edit. Example: `edit document.md`"

    # ── Brainstorm ───────────────────────────────────────────────

    def _task_brainstorm(self, msg: str, ws: str) -> str:
        topic = msg
        for prefix in ["brainstorm", "ideas for", "suggest", "what should i write about"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this topic"

        return (
            f"**Ideas for {topic.title()}:**\n\n"
            f"1. **Angle 1:** Explore the core principles\n"
            f"2. **Angle 2:** Compare with alternatives\n"
            f"3. **Angle 3:** Provide a beginner's guide\n"
            f"4. **Angle 4:** Deep dive into advanced concepts\n"
            f"5. **Angle 5:** Real-world case studies\n\n"
            f"Which angle interests you? I'll write the full piece."
        )

    # ── Rewrite ──────────────────────────────────────────────────

    def _task_rewrite(self, msg: str, ws: str) -> str:
        from apps.kraken.core.tools import file_read
        for word in msg.split():
            clean = word.strip("\"'.,:;")
            if "." in clean and any(clean.endswith(ext) for ext in [".md", ".txt"]):
                result = file_read(os.path.join(ws, clean))
                if result.ok:
                    return (
                        f"**Current content of `{clean}`:**\n\n"
                        f"---\n{result.output[:2000]}\n---\n\n"
                        f"Tell me how to rewrite it:\n"
                        f"- \"Make it more formal\"\n"
                        f"- \"Make it simpler\"\n"
                        f"- \"Add more examples\"\n"
                        f"- \"Shorten it\""
                    )
        return "Tell me which file to rewrite. Example: `rewrite document.md`"

    # ── Outline ──────────────────────────────────────────────────

    def _task_outline(self, msg: str, ws: str) -> str:
        topic = msg
        for prefix in ["outline", "structure", "plan"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this topic"

        return (
            f"**Outline: {topic.title()}**\n\n"
            f"## 1. Introduction\n"
            f"- Hook\n"
            f"- Thesis statement\n"
            f"- Preview of main points\n\n"
            f"## 2. Background\n"
            f"- Context\n"
            f"- History\n"
            f"- Current state\n\n"
            f"## 3. Main Points\n"
            f"### 3.1 Point One\n"
            f"### 3.2 Point Two\n"
            f"### 3.3 Point Three\n\n"
            f"## 4. Analysis\n"
            f"- Interpretation\n"
            f"- Implications\n\n"
            f"## 5. Conclusion\n"
            f"- Summary\n"
            f"- Call to action\n\n"
            f"Want me to write any of these sections?"
        )

    # ── Write Proposal ───────────────────────────────────────────

    def _task_write_proposal(self, msg: str, ws: str) -> str:
        topic = msg
        for prefix in ["write a proposal about", "write proposal about", "proposal about",
                        "write a pitch about", "pitch about"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this project"
        content = (
            f"# Project Proposal: {topic.title()}\n\n"
            f"**Date:** {time.strftime('%Y-%m-%d')}\n\n"
            f"## Executive Summary\n\n"
            f"This proposal outlines our approach to {topic.lower()}, "
            f"including objectives, methodology, timeline, and budget.\n\n"
            f"## Problem Statement\n\n"
            f"The current state of {topic.lower()} presents challenges that "
            f"require a structured solution.\n\n"
            f"## Proposed Solution\n\n"
            f"We propose a comprehensive approach that addresses the core "
            f"issues through systematic implementation.\n\n"
            f"## Objectives\n\n"
            f"1. Define clear deliverables\n"
            f"2. Establish measurable success criteria\n"
            f"3. Ensure stakeholder alignment\n\n"
            f"## Methodology\n\n"
            f"### Phase 1: Research & Planning\n"
            f"- Requirements gathering\n"
            f"- Stakeholder interviews\n"
            f"- Timeline: 2 weeks\n\n"
            f"### Phase 2: Implementation\n"
            f"- Core development\n"
            f"- Testing and validation\n"
            f"- Timeline: 4 weeks\n\n"
            f"### Phase 3: Delivery\n"
            f"- Final review\n"
            f"- Handoff and documentation\n"
            f"- Timeline: 1 week\n\n"
            f"## Budget\n\n"
            f"| Phase | Hours | Cost |\n"
            f"|-------|-------|------|\n"
            f"| Research | 40 | $4,000 |\n"
            f"| Implementation | 80 | $8,000 |\n"
            f"| Delivery | 20 | $2,000 |\n"
            f"| **Total** | **140** | **$14,000** |\n\n"
            f"## Timeline\n\n"
            f"Total duration: 7 weeks from project kickoff.\n\n"
            f"## Next Steps\n\n"
            f"1. Review and approve proposal\n"
            f"2. Sign contract and SOW\n"
            f"3. Schedule kickoff meeting\n\n"
            f"---\n\n"
            f"*Generated with Leviathan — your writing assistant*"
        )
        filepath = os.path.join(ws, _guess_filename(msg, "proposal"))
        file_write(filepath, content)
        return f"**Created:** `{os.path.basename(filepath)}`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write README ─────────────────────────────────────────────

    def _task_write_readme(self, msg: str, ws: str) -> str:
        topic = msg
        for prefix in ["write a readme for", "write readme for", "readme for",
                        "create a readme for", "make a readme"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this project"
        content = (
            f"# {topic.title()}\n\n"
            f"![License](https://img.shields.io/badge/license-MIT-blue)\n\n"
            f"## Overview\n\n"
            f"A brief description of what {topic.lower()} does and why it exists.\n\n"
            f"## Features\n\n"
            f"- Feature 1: Description\n"
            f"- Feature 2: Description\n"
            f"- Feature 3: Description\n\n"
            f"## Installation\n\n"
            f"```bash\n"
            f"# Clone the repository\n"
            f"git clone https://github.com/user/{topic.lower().replace(' ', '-')}.git\n"
            f"cd {topic.lower().replace(' ', '-')}\n\n"
            f"# Install dependencies\n"
            f"pip install -r requirements.txt\n"
            f"```\n\n"
            f"## Usage\n\n"
            f"```python\n"
            f"from {topic.lower().replace(' ', '_')} import main\n"
            f"main()\n"
            f"```\n\n"
            f"## Configuration\n\n"
            f"| Variable | Default | Description |\n"
            f"|----------|---------|-------------|\n"
            f"| DEBUG | false | Enable debug mode |\n"
            f"| PORT | 8000 | Server port |\n\n"
            f"## Contributing\n\n"
            f"1. Fork the repository\n"
            f"2. Create a feature branch\n"
            f"3. Commit your changes\n"
            f"4. Push to the branch\n"
            f"5. Open a Pull Request\n\n"
            f"## License\n\n"
            f"MIT License. See [LICENSE](LICENSE) for details.\n"
        )
        filepath = os.path.join(ws, "README.md")
        file_write(filepath, content)
        return f"**Created:** `README.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write Changelog ──────────────────────────────────────────

    def _task_write_changelog(self, msg: str, ws: str) -> str:
        content = (
            "# Changelog\n\n"
            "All notable changes to this project will be documented in this file.\n\n"
            "## [Unreleased]\n\n"
            "### Added\n"
            "- New feature description\n\n"
            "### Changed\n"
            "- Change description\n\n"
            "### Fixed\n"
            "- Bug fix description\n\n"
            f"## [{time.strftime('%Y.%m.%d')}] - {time.strftime('%Y-%m-%d')}\n\n"
            "### Added\n"
            "- Initial release\n"
            "- Core functionality\n"
            "- Documentation\n\n"
        )
        filepath = os.path.join(ws, _guess_filename(msg, "changelog"))
        file_write(filepath, content)
        return f"**Created:** `CHANGELOG.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write Spec ───────────────────────────────────────────────

    def _task_write_spec(self, msg: str, ws: str) -> str:
        topic = msg
        for prefix in ["write a spec about", "spec about", "specification about",
                        "technical spec about", "rfc about"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this feature"
        content = (
            f"# Technical Specification: {topic.title()}\n\n"
            f"**Status:** Draft\n"
            f"**Author:** [Author]\n"
            f"**Date:** {time.strftime('%Y-%m-%d')}\n\n"
            f"## 1. Overview\n\n"
            f"This document specifies the design and behavior of {topic.lower()}.\n\n"
            f"## 2. Goals\n\n"
            f"- Goal 1\n"
            f"- Goal 2\n"
            f"- Goal 3\n\n"
            f"## 3. Non-Goals\n\n"
            f"- Non-goal 1\n"
            f"- Non-goal 2\n\n"
            f"## 4. Architecture\n\n"
            f"### 4.1 Components\n\n"
            f"| Component | Description |\n"
            f"|-----------|-------------|\n"
            f"| Component A | Handles X |\n"
            f"| Component B | Manages Y |\n\n"
            f"### 4.2 Data Flow\n\n"
            f"```\n"
            f"Input -> Processing -> Output\n"
            f"```\n\n"
            f"## 5. API Design\n\n"
            f"### Endpoints\n\n"
            f"- `GET /api/resource` — List resources\n"
            f"- `POST /api/resource` — Create resource\n"
            f"- `GET /api/resource/:id` — Get resource\n\n"
            f"## 6. Data Model\n\n"
            f"```json\n"
            f'{{"id": "string", "name": "string", "created_at": "datetime"}}\n'
            f"```\n\n"
            f"## 7. Security Considerations\n\n"
            f"- Authentication required\n"
            f"- Input validation\n"
            f"- Rate limiting\n\n"
            f"## 8. Testing Strategy\n\n"
            f"- Unit tests for core logic\n"
            f"- Integration tests for API\n"
            f"- End-to-end tests for critical paths\n\n"
            f"## 9. Open Questions\n\n"
            f"- Question 1\n"
            f"- Question 2\n"
        )
        filepath = os.path.join(ws, _guess_filename(msg, "spec"))
        file_write(filepath, content)
        return f"**Created:** `specification.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write Meeting Notes ──────────────────────────────────────

    def _task_write_notes(self, msg: str, ws: str) -> str:
        content = (
            f"# Meeting Notes\n\n"
            f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"## Attendees\n\n"
            f"- [Name 1]\n"
            f"- [Name 2]\n"
            f"- [Name 3]\n\n"
            f"## Agenda\n\n"
            f"1. Opening\n"
            f"2. Main discussion\n"
            f"3. Action items\n"
            f"4. Next steps\n\n"
            f"## Discussion\n\n"
            f"### Topic 1\n\n"
            f"Notes go here.\n\n"
            f"### Topic 2\n\n"
            f"Notes go here.\n\n"
            f"## Action Items\n\n"
            f"- [ ] Action 1 — Assigned to [Name] — Due [Date]\n"
            f"- [ ] Action 2 — Assigned to [Name] — Due [Date]\n"
            f"- [ ] Action 3 — Assigned to [Name] — Due [Date]\n\n"
            f"## Next Meeting\n\n"
            f"**Date:** [Date]\n"
            f"**Time:** [Time]\n"
        )
        filepath = os.path.join(ws, _guess_filename(msg, "notes"))
        file_write(filepath, content)
        return f"**Created:** `meeting_notes.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write Press Release ──────────────────────────────────────

    def _task_write_press(self, msg: str, ws: str) -> str:
        topic = msg
        for prefix in ["write a press release about", "press release about",
                        "write a pr about", "announcement about"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this announcement"
        content = (
            f"# Press Release\n\n"
            f"**FOR IMMEDIATE RELEASE**\n\n"
            f"## {topic.title()}\n\n"
            f"**[City, State] — {time.strftime('%B %d, %Y')}** — "
            f"[Company Name] today announced {topic.lower()}.\n\n"
            f"## Key Highlights\n\n"
            f"- Highlight 1\n"
            f"- Highlight 2\n"
            f"- Highlight 3\n\n"
            f"## Details\n\n"
            f"[Company Name] today announced a new initiative related to "
            f"{topic.lower()}. This development represents a significant step "
            f"forward in the industry.\n\n"
            f"\"[Quote from executive about the significance of this announcement]\" "
            f"said [Name], [Title] at [Company].\n\n"
            f"## About [Company]\n\n"
            f"[Company] is a leading provider of [industry] solutions. "
            f"Founded in [year], the company serves [customers] worldwide.\n\n"
            f"## Media Contact\n\n"
            f"[Name]\n"
            f"[Email]\n"
            f"[Phone]\n"
        )
        filepath = os.path.join(ws, _guess_filename(msg, "press"))
        file_write(filepath, content)
        return f"**Created:** `press_release.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write Job Posting ────────────────────────────────────────

    def _task_write_job(self, msg: str, ws: str) -> str:
        topic = msg
        for prefix in ["write a job posting for", "write job posting for",
                        "hiring for", "job for", "position for"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this position"
        content = (
            f"# Job Opening: {topic.title()}\n\n"
            f"**Company:** [Company Name]\n"
            f"**Location:** [Location / Remote]\n"
            f"**Type:** Full-time\n\n"
            f"## About the Role\n\n"
            f"We're looking for a {topic.lower()} to join our team. "
            f"You'll work on challenging problems and have a direct impact "
            f"on our product and users.\n\n"
            f"## Responsibilities\n\n"
            f"- Responsibility 1\n"
            f"- Responsibility 2\n"
            f"- Responsibility 3\n"
            f"- Responsibility 4\n\n"
            f"## Requirements\n\n"
            f"- Requirement 1\n"
            f"- Requirement 2\n"
            f"- Requirement 3\n\n"
            f"## Nice to Have\n\n"
            f"- Bonus skill 1\n"
            f"- Bonus skill 2\n\n"
            f"## Benefits\n\n"
            f"- Competitive salary\n"
            f"- Health insurance\n"
            f"- Flexible PTO\n"
            f"- Professional development budget\n"
            f"- Remote-friendly\n\n"
            f"## How to Apply\n\n"
            f"Send your resume and a brief cover letter to [email].\n"
        )
        filepath = os.path.join(ws, _guess_filename(msg, "job"))
        file_write(filepath, content)
        return f"**Created:** `job_posting.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write Product Description ────────────────────────────────

    def _task_write_product(self, msg: str, ws: str) -> str:
        topic = msg
        for prefix in ["write a product description for", "product description for",
                        "describe this product", "write about this product"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this product"
        content = (
            f"# {topic.title()}\n\n"
            f"## Headline\n\n"
            f"**{topic.title()}** — Transform your experience\n\n"
            f"## Description\n\n"
            f"Discover {topic.lower()} — designed to help you achieve more "
            f"with less effort. Built with quality and attention to detail.\n\n"
            f"## Key Features\n\n"
            f"### Feature 1\n"
            f"Description of the first key feature and its benefits.\n\n"
            f"### Feature 2\n"
            f"Description of the second key feature and its benefits.\n\n"
            f"### Feature 3\n"
            f"Description of the third key feature and its benefits.\n\n"
            f"## Specifications\n\n"
            f"| Spec | Value |\n"
            f"|------|-------|\n"
            f"| Size | [Dimensions] |\n"
            f"| Weight | [Weight] |\n"
            f"| Material | [Material] |\n\n"
            f"## What's Included\n\n"
            f"- Item 1\n"
            f"- Item 2\n"
            f"- Item 3\n\n"
            f"## Call to Action\n\n"
            f"**Order now** and experience the difference.\n"
        )
        filepath = os.path.join(ws, _guess_filename(msg, "product"))
        file_write(filepath, content)
        return f"**Created:** `product_description.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write Social Media Posts ─────────────────────────────────

    def _task_write_social(self, msg: str, ws: str) -> str:
        topic = msg
        for prefix in ["write social posts about", "write a tweet about",
                        "linkedin post about", "instagram caption about"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this topic"
        content = (
            f"# Social Media Posts: {topic.title()}\n\n"
            f"## Twitter/X (280 chars)\n\n"
            f"Excited to share our latest on {topic.lower()}! "
            f"This is a game-changer for the industry. "
            f"Can't wait to see what everyone thinks. #innovation #{topic.lower().replace(' ', '')}\n\n"
            f"---\n\n"
            f"## LinkedIn\n\n"
            f"I'm thrilled to announce our latest development in {topic.lower()}.\n\n"
            f"After months of hard work, we've built something that we believe "
            f"will make a real difference.\n\n"
            f"Key takeaways:\n"
            f"1. Innovation drives progress\n"
            f"2. Collaboration is essential\n"
            f"3. Users come first\n\n"
            f"What are your thoughts? I'd love to hear from the community.\n\n"
            f"#linkedin #{topic.lower().replace(' ', '')}\n\n"
            f"---\n\n"
            f"## Instagram Caption\n\n"
            f"Big things are happening in {topic.lower()}! "
            f"Stay tuned for more details. "
            f"What do you want to see next? "
            f"Drop a comment below! 👇\n\n"
            f"#{topic.lower().replace(' ', '')} #innovation #news\n"
        )
        filepath = os.path.join(ws, _guess_filename(msg, "social"))
        file_write(filepath, content)
        return f"**Created:** `social_posts.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write Letter ─────────────────────────────────────────────

    def _task_write_letter(self, msg: str, ws: str) -> str:
        topic = msg
        for prefix in ["write a letter about", "write letter about",
                        "letter about", "formal letter about"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this matter"
        content = (
            f"[Your Name]\n"
            f"[Your Address]\n"
            f"[City, State ZIP]\n"
            f"[Email]\n\n"
            f"{time.strftime('%B %d, %Y')}\n\n"
            f"[Recipient Name]\n"
            f"[Recipient Title]\n"
            f"[Organization]\n"
            f"[Address]\n\n"
            f"Dear [Recipient Name],\n\n"
            f"Re: {topic.title()}\n\n"
            f"I am writing to address {topic.lower()}. "
            f"I believe this matter requires immediate attention and would "
            f"like to propose a path forward.\n\n"
            f"[Body paragraph 1]\n\n"
            f"[Body paragraph 2]\n\n"
            f"[Body paragraph 3]\n\n"
            f"I look forward to your response and am happy to discuss "
            f"this further at your convenience.\n\n"
            f"Sincerely,\n\n"
            f"[Your Name]\n"
        )
        filepath = os.path.join(ws, _guess_filename(msg, "letter"))
        file_write(filepath, content)
        return f"**Created:** `letter.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write Tutorial ───────────────────────────────────────────

    def _task_write_tutorial(self, msg: str, ws: str) -> str:
        topic = msg
        for prefix in ["write a tutorial about", "tutorial about",
                        "how to", "guide about", "walkthrough about"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this topic"
        content = (
            f"# Tutorial: {topic.title()}\n\n"
            f"## Prerequisites\n\n"
            f"- Basic knowledge of [prerequisite]\n"
            f"- [Tool/Library] installed\n\n"
            f"## What You'll Learn\n\n"
            f"- Learning objective 1\n"
            f"- Learning objective 2\n"
            f"- Learning objective 3\n\n"
            f"## Step 1: Setup\n\n"
            f"First, set up your environment:\n\n"
            f"```bash\n"
            f"# Install dependencies\n"
            f"pip install required-package\n"
            f"```\n\n"
            f"## Step 2: Create the Project\n\n"
            f"```python\n"
            f"# main.py\n"
            f"print('Hello, World!')\n"
            f"```\n\n"
            f"## Step 3: Run It\n\n"
            f"```bash\n"
            f"python main.py\n"
            f"```\n\n"
            f"Expected output:\n\n"
            f"```\n"
            f"Hello, World!\n"
            f"```\n\n"
            f"## Step 4: Extend It\n\n"
            f"Now that you have the basics, try extending the project "
            f"with additional features.\n\n"
            f"## Common Issues\n\n"
            f"| Issue | Solution |\n"
            f"|-------|----------|\n"
            f"| Error X | Do Y |\n"
            f"| Error Z | Do W |\n\n"
            f"## Next Steps\n\n"
            f"- Explore advanced topics\n"
            f"- Read the documentation\n"
            f"- Join the community\n"
        )
        filepath = os.path.join(ws, _guess_filename(msg, "tutorial"))
        file_write(filepath, content)
        return f"**Created:** `tutorial.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write Speech ─────────────────────────────────────────────

    def _task_write_speech(self, msg: str, ws: str) -> str:
        topic = msg
        for prefix in ["write a speech about", "speech about",
                        "write a talk about", "talk about"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this topic"
        content = (
            f"# Speech: {topic.title()}\n\n"
            f"## Opening\n\n"
            f"Good [morning/afternoon/evening], everyone.\n\n"
            f"Thank you for being here today. I want to talk to you about "
            f"something that matters to all of us: {topic.lower()}.\n\n"
            f"## The Problem\n\n"
            f"Let me start with a question: Why does {topic.lower()} matter?\n\n"
            f"The answer is simple but profound. [Key insight about the topic].\n\n"
            f"## The Story\n\n"
            f"Let me share a story. [Anecdote or example that illustrates the point].\n\n"
            f"## The Solution\n\n"
            f"So what can we do? Here are three things:\n\n"
            f"1. **First**, we need to [action].\n"
            f"2. **Second**, we must [action].\n"
            f"3. **Third**, let's commit to [action].\n\n"
            f"## Closing\n\n"
            f"In conclusion, {topic.lower()} is not just about [concept]. "
            f"It's about [bigger picture].\n\n"
            f"Let's work together to make a difference.\n\n"
            f"Thank you.\n"
        )
        filepath = os.path.join(ws, _guess_filename(msg, "speech"))
        file_write(filepath, content)
        return f"**Created:** `speech.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── Write Review ─────────────────────────────────────────────

    def _task_write_review(self, msg: str, ws: str) -> str:
        topic = msg
        for prefix in ["write a review of", "review of", "critique of", "feedback on"]:
            if prefix in msg.lower():
                topic = msg.lower().split(prefix)[-1].strip()
                break
        topic = topic.strip(".!?") or "this item"
        content = (
            f"# Review: {topic.title()}\n\n"
            f"**Rating:** ★★★★☆ (4/5)\n\n"
            f"## Summary\n\n"
            f"A solid [product/work] that delivers on its core promises "
            f"with room for improvement.\n\n"
            f"## Pros\n\n"
            f"+ Pro 1: Description\n"
            f"+ Pro 2: Description\n"
            f"+ Pro 3: Description\n\n"
            f"## Cons\n\n"
            f"- Con 1: Description\n"
            f"- Con 2: Description\n\n"
            f"## Details\n\n"
            f"[Detailed review of {topic.lower()} with specific examples "
            f"and observations.]\n\n"
            f"## Verdict\n\n"
            f"Overall, {topic.lower()} is a strong choice for [audience]. "
            f"While it has some limitations, the benefits outweigh the drawbacks.\n\n"
            f"**Recommended for:** [Target audience]\n"
            f"**Skip if:** [When to avoid]\n"
        )
        filepath = os.path.join(ws, _guess_filename(msg, "review"))
        file_write(filepath, content)
        return f"**Created:** `review.md`\n\n---\n\n{content}\n\n---\n\nFile saved to: {filepath}"

    # ── General ──────────────────────────────────────────────────

    def _task_general(self, msg: str, ws: str) -> str:
        return (
            f"**Task:** {msg[:120]}\n\n"
            "I can help with that. Here's what I do:\n\n"
            "- **Write email** — I'll draft it and save the file\n"
            "- **Write article** — I'll compose and save\n"
            "- **Write story** — I'll create and save\n"
            "- **Write document** — I'll generate and save\n"
            "- **Write summary** — I'll create and save\n"
            "- **Write resume** — I'll draft and save\n"
            "- **Write copy** — I'll craft and save\n"
            "- **Edit <file>** — Tell me what to change\n"
            "- **Brainstorm** — I'll suggest ideas\n"
            "- **Rewrite <file>** — I'll revise it\n"
            "- **Outline** — I'll structure it\n\n"
            "Just tell me what to write and I'll do it."
        )

    # ── Help ─────────────────────────────────────────────────────

    def _help_text(self) -> str:
        return (
            "**Leviathan — Writing Agent**\n\n"
            "I write content, not just explain how.\n\n"
            "**Commands:**\n"
            "- `write email` — Draft an email and save to file\n"
            "- `write article` — Compose an article and save\n"
            "- `write story` — Create a story and save\n"
            "- `write document` — Generate a document and save\n"
            "- `write summary` — Create a summary and save\n"
            "- `write resume` — Draft a resume and save\n"
            "- `write copy` — Craft marketing copy and save\n"
            "- `edit <file>` — Tell me what to change\n"
            "- `brainstorm` — Suggest ideas\n"
            "- `rewrite <file>` — Revise content\n"
            "- `outline` — Structure content\n\n"
            "**Examples:**\n"
            "- \"Write an article about climate change\"\n"
            "- \"Draft a follow-up email\"\n"
            "- \"Write a story about a space explorer\"\n"
            "- \"Create a report about Q3 results\"\n\n"
            "Just describe what you need and I'll write it."
        )
