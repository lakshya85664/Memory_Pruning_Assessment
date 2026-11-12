# Topic 16 — Memory Pruning Assessment

## Project overview
This project implements a deterministic memory-pruning system in Python. It models memory records, calculates retention scores from importance and recency, retrieves relevant memories, enforces configurable short-term memory capacity, transfers retained records into long-term storage, and builds a compact working context.

## Exercises completed
1. **Build the memory model:** `MemoryItem` stores an ID, text, importance, and age. It exposes `recency` and `retention_score` properties. `MemoryManager` maintains short-term and long-term collections.
2. **Retrieval and retention scoring:** keyword-overlap retrieval ranks matching memories by overlap, then retention score, then ID for deterministic tie-breaking. Retention is `0.7 * importance + 0.3 * recency`.
3. **Implement pruning:** `prune(capacity)` ranks records by retention score, retains records up to capacity, and returns retained and removed collections separately.
4. **Long-term memory and summarization:** retained records can be preserved in long-term storage. The manager generates a compact summary, and `build_context()` creates a readable context.
5. **Test, inspect, and improve:** the improved policy supports a minimum-importance threshold and normalized duplicate-text detection. Tests cover validation, edge cases, ranking, capacity, and deterministic behavior.

## Retention formulas
```text
recency = 1 / (1 + max(age, 0))
retention_score = 0.7 * importance + 0.3 * recency
```

## Project structure
```text
Memory_Pruning_Assessment/
├── pruning_memory.py
├── test_pruning_memory.py
├── README.md
├── requirements.txt
└── .gitignore
```

## Requirements
- Python 3.10 or newer recommended.
- No third-party dependencies; `unittest` is included with Python.

## Setup — Windows Command Prompt
```bat
cd /d E:\Tayana_Projects\Memory_Engineering\Memory_Pruning_Assessment
.venv\Scripts\activate
python -m pip install -r requirements.txt
```
If the virtual environment does not exist, create it first:
```bat
python -m venv .venv
.venv\Scripts\activate
```

## Run the demonstration
```bat
python pruning_memory.py
```

## Run tests
```bat
python -m unittest -v test_pruning_memory.py
python -m unittest discover -v
```
**Verified result: 53 tests passed.** Both test commands completed successfully with `OK`.

## Improvements implemented
- Minimum-importance threshold: records below the configured threshold are removed before capacity is allocated.
- Duplicate detection: text is normalized by lowercasing and collapsing whitespace before duplicate comparison.
- Deterministic pruning: records are ordered by descending retention score, with memory ID as a stable tie-breaker.
- Input validation for capacity and importance threshold.

## Implementation notes and limitations
- Retrieval uses lexical keyword overlap, not semantic embeddings.
- Memory collections are in-memory and are not persisted across process restarts.
- The summary is a compact concatenation of retained memory text, not an LLM-generated abstractive summary.
- Production use would require persistence, semantic retrieval, privacy controls, and operational monitoring.

## Reflection (approximately 300 words)
This assessment helped me understand that memory management in an AI agent is not only about storing information, but also about deciding what information remains useful over time. In the first exercise, I created a structured memory model with an identifier, text, importance, and age. Calculating recency and retention scores made it clear how older memories can gradually become less valuable while important information can still remain relevant.

The retrieval exercise introduced a simple way to find memories using keyword overlap. I added ranking based on relevance and retention score, along with deterministic tie-breaking so repeated queries return consistent results. The pruning exercise connected these scores to a practical capacity limit. Instead of keeping every record, the manager retains the highest-scoring memories and returns removed records separately. Testing zero capacity, insufficient capacity, and tied scores helped verify that the behavior is predictable.

The long-term memory exercise showed how retained information can be preserved separately from short-term memory. I also implemented a compact summary and a working-context builder, which demonstrate how selected memories can be supplied to a later reasoning step without including every stored record.

For the final improvement, I added a minimum-importance threshold and duplicate detection. The threshold prevents low-importance records from occupying available capacity, while normalized duplicate detection avoids storing the same text multiple times merely because capitalization or spacing differs. These improvements made the pruning policy more practical and were covered by additional unit tests.

The final test suite completed with 53 passing tests, and the demonstration showed three retained memories, two removed memories, and three records preserved in long-term storage. The project uses simple lexical retrieval and in-memory storage, so a production system would need persistent storage, semantic search, and stronger privacy and monitoring controls. Overall, this project strengthened my understanding of memory lifecycle design, deterministic ranking, and test-driven implementation.
