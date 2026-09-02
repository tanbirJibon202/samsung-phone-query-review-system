"""Alias matching against the known, fixed catalog of ~15 phones.

Plain top-k vector similarity search over such a small corpus can easily
return two chunks about the same phone and miss the other side of a
comparison question (e.g. "How does the S23 compare to the S22?"). This module
lets the RAG chain force-include the exact phones a question names, in
addition to whatever the vector search returns.
"""

from __future__ import annotations

import re


def build_alias_map(names: list[str]) -> dict[str, str]:
    """Map every lowercase alias variant of a phone name back to its canonical
    (as-stored) name, e.g. "s23 ultra" / "s23ultra" -> "Samsung Galaxy S23 Ultra"."""
    aliases: dict[str, str] = {}
    for name in names:
        variants = {name}

        without_samsung = re.sub(r"(?i)^samsung\s+", "", name).strip()
        short = re.sub(r"(?i)^samsung galaxy\s+", "", name).strip()
        variants.add(without_samsung)
        variants.add(short)
        variants.update(
            {
                re.sub(r"(?i)\s*5g$", "", variant).strip()
                for variant in list(variants)
            }
        )

        for variant in list(variants):
            variants.add(variant.replace("+", " plus"))

        for variant in list(variants):
            variants.add(variant.replace(" ", ""))

        for variant in variants:
            cleaned = variant.strip().lower()
            if cleaned:
                # Never let a later, less exact model (notably S23+) steal a
                # base-model alias such as "s23". Plus models deliberately do
                # not get aliases with the '+' removed.
                aliases.setdefault(cleaned, name)

    return aliases


def resolve_alias(text: str, alias_map: dict[str, str]) -> str | None:
    key = text.strip().lower()
    return alias_map.get(key) or alias_map.get(key.replace(" ", ""))


def extract_mentioned_phones(question: str, alias_map: dict[str, str]) -> list[str]:
    """Find every known phone named in `question`, matching longest aliases
    first so e.g. "S23 Ultra" isn't shadowed by the shorter "S23"."""
    remaining = question.lower()
    matched: list[str] = []
    seen: set[str] = set()

    for alias in sorted(alias_map, key=len, reverse=True):
        pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
        match = re.search(pattern, remaining)
        if match:
            canonical = alias_map[alias]
            if canonical not in seen:
                matched.append(canonical)
                seen.add(canonical)
            remaining = remaining[: match.start()] + " " * (match.end() - match.start()) + remaining[match.end() :]

    return matched
