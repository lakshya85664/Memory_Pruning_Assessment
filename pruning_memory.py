
from dataclasses import dataclass
from typing import List
import re


@dataclass(frozen=True)
class MemoryItem:
    """Represents one memory record."""

    id: str
    text: str
    importance: float
    age: int

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Memory ID must be a non-empty string.")

        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("Memory text must be a non-empty string.")

        if isinstance(self.importance, bool) or not isinstance(
            self.importance, (int, float)
        ):
            raise ValueError("Importance must be a number.")

        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("Importance must be between 0.0 and 1.0.")

        if isinstance(self.age, bool) or not isinstance(self.age, int):
            raise ValueError("Age must be an integer.")

        if self.age < 0:
            raise ValueError("Age cannot be negative.")

    @property
    def recency(self) -> float:
        return 1.0 / (1.0 + max(self.age, 0))

    @property
    def retention_score(self) -> float:
        return 0.7 * self.importance + 0.3 * self.recency


class MemoryManager:
    """Manages short-term and long-term memory collections."""

    def __init__(self):
        self.short_term: List[MemoryItem] = []
        self.long_term: List[MemoryItem] = []

    def add(self, item: MemoryItem) -> None:
        """Add a memory to short-term storage."""

        if not isinstance(item, MemoryItem):
            raise TypeError("item must be a MemoryItem instance.")

        if any(existing.id == item.id for existing in self.short_term):
            raise ValueError(f"Duplicate memory ID: {item.id}")

        self.short_term.append(item)

    def retrieve(self, query: str, top_k: int = 3) -> List[MemoryItem]:
        """
        Retrieve relevant short-term memories.

        Ranking:
        1. Highest keyword overlap.
        2. Highest retention score.
        3. Alphabetical memory ID for deterministic ties.
        """

        if not isinstance(query, str):
            raise TypeError("query must be a string.")

        if isinstance(top_k, bool) or not isinstance(top_k, int):
            raise ValueError("top_k must be an integer.")

        if top_k <= 0:
            return []

        query_words = set(re.findall(r"\b\w+\b", query.lower()))

        if not query_words:
            return []

        ranked = []

        for item in self.short_term:
            memory_words = set(
                re.findall(r"\b\w+\b", item.text.lower())
            )

            overlap = len(query_words & memory_words)

            if overlap > 0:
                ranked.append(
                    (
                        overlap,
                        item.retention_score,
                        item.id,
                        item
                    )
                )

        ranked.sort(
            key=lambda result: (
                -result[0],
                -result[1],
                result[2]
            )
        )

        return [result[3] for result in ranked[:top_k]]

    
    
    def prune(self, capacity: int, min_importance: float = 0.0):
        """
        Prune short-term memory using retention score,
        minimum importance, and duplicate detection.
        """

        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise ValueError("capacity must be a non-negative integer.")

        if capacity < 0:
            raise ValueError("capacity must be non-negative.")

        if isinstance(min_importance, bool) or not isinstance(
            min_importance, (int, float)
        ):
            raise ValueError("min_importance must be a number.")

        if not 0.0 <= min_importance <= 1.0:
            raise ValueError("min_importance must be between 0 and 1.")

        ranked = sorted(
            self.short_term,
            key=lambda item: (-item.retention_score, item.id)
        )

        kept = []
        removed = []
        seen_text = set()

        for item in ranked:
            normalized_text = " ".join(item.text.lower().split())

            if item.importance < min_importance:
                removed.append(item)
                continue

            if normalized_text in seen_text:
                removed.append(item)
                continue

            if len(kept) < capacity:
                kept.append(item)
                seen_text.add(normalized_text)
            else:
                removed.append(item)

        self.short_term = kept

        return kept, removed


    
    def move_kept_to_long_term(self) -> None:
        """
        Preserve active short-term memories in long-term storage.

        Existing long-term IDs are not duplicated.
        """
        existing_ids = {
            item.id for item in self.long_term
        }

        for item in self.short_term:
            if item.id not in existing_ids:
                self.long_term.append(item)
                existing_ids.add(item.id)

    def summarize(self) -> str:
        """
        Generate a compact representation of active short-term memory.

        Original memory records remain unchanged.
        """
        if not self.short_term:
            return "No active memory."

        return " | ".join(
            f"[{item.id}]: {item.text}"
            for item in self.short_term
        )


    def inspect_retention(self) -> None:
        """Display importance, recency, and retention score."""

        print("\nMEMORY RETENTION INSPECTION")
        print("-" * 65)

        for item in sorted(
            self.short_term,
            key=lambda x: (-x.retention_score, x.id)
        ):
            print(
                f"ID={item.id} | "
                f"Importance={item.importance:.2f} | "
                f"Recency={item.recency:.2f} | "
                f"Score={item.retention_score:.4f}"
            )

    
def build_context(items: List[MemoryItem]) -> str:
    """Build a readable context from memory records."""

    if not isinstance(items, list):
        raise TypeError("items must be a list.")

    if not all(isinstance(item, MemoryItem) for item in items):
        raise TypeError("All items must be MemoryItem instances.")

    if not items:
        return "No active memory."

    return "\n".join(
        f"- {item.text}"
        for item in items
    )


if __name__ == "__main__":
    manager = MemoryManager()

    items = [
        MemoryItem("m1", "User prefers concise explanations", 0.90, 1),
        MemoryItem("m2", "Project requires Python implementation", 0.95, 0),
        MemoryItem("m3", "Old discussion about unrelated travel", 0.30, 8),
        MemoryItem("m4", "Pruning should preserve relevant context", 0.88, 2),
        MemoryItem("m5", "Temporary note with low importance", 0.20, 4),
    ]

    for item in items:
        manager.add(item)

    print("TOPIC 16 - EXERCISE 5")
    print("=" * 65)

    print("\nBEFORE PRUNING")
    print("Short-term count:", len(manager.short_term))

    kept, removed = manager.prune(
        capacity=3,
        min_importance=0.25
    )

    print("\nRETAINED IDs:", [item.id for item in kept])
    print("REMOVED IDs:", [item.id for item in removed])

    manager.move_kept_to_long_term()

    print("\nLONG-TERM MEMORY")
    print("Long-term count:", len(manager.long_term))
    print("Long-term IDs:", [item.id for item in manager.long_term])

    print("\nSHORT-TERM SUMMARY")
    print(manager.summarize())

    print("\nFINAL WORKING CONTEXT")
    print(build_context(manager.short_term))

    print("\nFINAL STATISTICS")
    print("Short-term memories:", len(manager.short_term))
    print("Long-term memories:", len(manager.long_term))
    print("Removed memories:", len(removed))
