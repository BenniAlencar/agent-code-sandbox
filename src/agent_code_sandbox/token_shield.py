"""
Adaptive Stdout/Stderr Token Shield.
Prevents terminal log dumps from blowing out LLM agent context windows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ShieldedOutput:
    text: str
    original_chars: int
    shielded_chars: int
    original_tokens_est: int
    shielded_tokens_est: int
    tokens_saved_est: int
    was_truncated: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "original_chars": self.original_chars,
            "shielded_chars": self.shielded_chars,
            "original_tokens_est": self.original_tokens_est,
            "shielded_tokens_est": self.shielded_tokens_est,
            "tokens_saved_est": self.tokens_saved_est,
            "was_truncated": self.was_truncated,
        }


class TokenShield:
    """
    Guards context windows by adaptively truncating massive command outputs.
    Preserves critical head and tail output while omitting repetitive middle noise.
    """

    def __init__(self, max_lines: int = 50, max_chars: int = 4000, head_ratio: float = 0.6) -> None:
        self.max_lines = max_lines
        self.max_chars = max_chars
        self.head_ratio = head_ratio

    def shield(self, raw_output: str) -> ShieldedOutput:
        original_len = len(raw_output)
        original_tokens = original_len // 4

        lines = raw_output.splitlines(keepends=True)
        total_lines = len(lines)

        if total_lines <= self.max_lines and original_len <= self.max_chars:
            return ShieldedOutput(
                text=raw_output,
                original_chars=original_len,
                shielded_chars=original_len,
                original_tokens_est=original_tokens,
                shielded_tokens_est=original_tokens,
                tokens_saved_est=0,
                was_truncated=False,
            )

        # Truncate by lines
        head_count = int(self.max_lines * self.head_ratio)
        tail_count = self.max_lines - head_count

        head_lines = lines[:head_count]
        tail_lines = lines[-tail_count:] if tail_count > 0 else []
        omitted_lines = total_lines - (len(head_lines) + len(tail_lines))

        banner = f"\n[... Output Truncated by agent-code-sandbox: {omitted_lines} lines omitted to protect LLM context window ...]\n"
        shielded_text = "".join(head_lines) + banner + "".join(tail_lines)

        shielded_len = len(shielded_text)
        shielded_tokens = shielded_len // 4
        tokens_saved = max(0, original_tokens - shielded_tokens)

        return ShieldedOutput(
            text=shielded_text,
            original_chars=original_len,
            shielded_chars=shielded_len,
            original_tokens_est=original_tokens,
            shielded_tokens_est=shielded_tokens,
            tokens_saved_est=tokens_saved,
            was_truncated=True,
        )
