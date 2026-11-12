
import unittest

from pruning_memory import MemoryItem, MemoryManager, build_context


class TestMemoryItem(unittest.TestCase):

    def test_memory_item_creation(self):
        item = MemoryItem("m1", "Important information", 0.9, 1)

        self.assertEqual(item.id, "m1")
        self.assertEqual(item.text, "Important information")
        self.assertEqual(item.importance, 0.9)
        self.assertEqual(item.age, 1)

    def test_recency_for_new_item(self):
        item = MemoryItem("m1", "New memory", 0.8, 0)

        self.assertEqual(item.recency, 1.0)

    def test_recency_for_older_item(self):
        item = MemoryItem("m1", "Old memory", 0.8, 4)

        self.assertEqual(item.recency, 0.2)

    def test_retention_score(self):
        item = MemoryItem("m1", "Important memory", 0.9, 1)

        expected = 0.7 * 0.9 + 0.3 * 0.5

        self.assertAlmostEqual(item.retention_score, expected)

    def test_empty_id_rejected(self):
        with self.assertRaises(ValueError):
            MemoryItem("", "Some memory", 0.8, 1)

    def test_empty_text_rejected(self):
        with self.assertRaises(ValueError):
            MemoryItem("m1", "  ", 0.8, 1)

    def test_invalid_importance_rejected(self):
        with self.assertRaises(ValueError):
            MemoryItem("m1", "Some memory", 1.5, 1)

    def test_negative_importance_rejected(self):
        with self.assertRaises(ValueError):
            MemoryItem("m1", "Some memory", -0.1, 1)

    def test_negative_age_rejected(self):
        with self.assertRaises(ValueError):
            MemoryItem("m1", "Some memory", 0.8, -1)

    def test_memory_item_is_immutable(self):
        item = MemoryItem("m1", "Some memory", 0.8, 1)

        with self.assertRaises(AttributeError):
            item.age = 5


class TestMemoryManager(unittest.TestCase):

    def setUp(self):
        self.manager = MemoryManager()

    def test_empty_manager(self):
        self.assertEqual(len(self.manager.short_term), 0)
        self.assertEqual(len(self.manager.long_term), 0)

    def test_add_memory(self):
        item = MemoryItem("m1", "Useful information", 0.9, 0)

        self.manager.add(item)

        self.assertEqual(len(self.manager.short_term), 1)
        self.assertEqual(self.manager.short_term[0], item)

    def test_add_multiple_memories(self):
        items = [
            MemoryItem("m1", "First memory", 0.9, 0),
            MemoryItem("m2", "Second memory", 0.7, 1),
            MemoryItem("m3", "Third memory", 0.5, 2),
        ]

        for item in items:
            self.manager.add(item)

        self.assertEqual(len(self.manager.short_term), 3)

    def test_invalid_item_rejected(self):
        with self.assertRaises(TypeError):
            self.manager.add("not a memory item")

    def test_duplicate_id_rejected(self):
        item1 = MemoryItem("m1", "First memory", 0.9, 0)
        item2 = MemoryItem("m1", "Second memory", 0.7, 1)

        self.manager.add(item1)

        with self.assertRaises(ValueError):
            self.manager.add(item2)


class TestMemoryRetrieval(unittest.TestCase):

    def setUp(self):
        self.manager = MemoryManager()

        self.items = [
            MemoryItem("m1", "Python programming project", 0.9, 0),
            MemoryItem("m2", "Python programming tutorial", 0.7, 2),
            MemoryItem("m3", "Travel planning information", 0.8, 1),
            MemoryItem("m4", "Python development guide", 0.95, 1),
            MemoryItem("m5", "Database management notes", 0.6, 4),
        ]

        for item in self.items:
            self.manager.add(item)

    def test_retrieve_matching_memory(self):
        results = self.manager.retrieve("Python programming")

        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].id, "m1")

    def test_retrieval_top_k_limit(self):
        results = self.manager.retrieve("Python", top_k=2)

        self.assertLessEqual(len(results), 2)

    def test_retrieval_returns_only_relevant_items(self):
        results = self.manager.retrieve("Python")

        self.assertTrue(
            all("python" in item.text.lower() for item in results)
        )

    def test_unrelated_query(self):
        results = self.manager.retrieve("football cricket")

        self.assertEqual(results, [])

    def test_empty_query(self):
        results = self.manager.retrieve("")

        self.assertEqual(results, [])

    def test_zero_top_k(self):
        results = self.manager.retrieve("Python", top_k=0)

        self.assertEqual(results, [])

    def test_negative_top_k(self):
        results = self.manager.retrieve("Python", top_k=-1)

        self.assertEqual(results, [])

    def test_invalid_query_type(self):
        with self.assertRaises(TypeError):
            self.manager.retrieve(123)

    def test_invalid_top_k_type(self):
        with self.assertRaises(ValueError):
            self.manager.retrieve("Python", top_k=1.5)

    def test_deterministic_retrieval(self):
        first = [
            item.id
            for item in self.manager.retrieve("Python", top_k=3)
        ]

        second = [
            item.id
            for item in self.manager.retrieve("Python", top_k=3)
        ]

        self.assertEqual(first, second)

    def test_retention_score_tie_breaking(self):
        manager = MemoryManager()

        manager.add(
            MemoryItem("m2", "Python guide", 0.8, 0)
        )
        manager.add(
            MemoryItem("m1", "Python guide", 0.8, 0)
        )

        results = manager.retrieve("Python")

        self.assertEqual(
            [item.id for item in results],
            ["m1", "m2"]
        )


class TestMemoryPruning(unittest.TestCase):

    def setUp(self):
        self.manager = MemoryManager()

        self.items = [
            MemoryItem("m1", "Important recent item", 0.9, 0),
            MemoryItem("m2", "Useful older item", 0.8, 1),
            MemoryItem("m3", "Old low value item", 0.2, 8),
            MemoryItem("m4", "Another useful item", 0.7, 2),
            MemoryItem("m5", "Temporary note", 0.1, 5),
        ]

        for item in self.items:
            self.manager.add(item)

    def test_prune_five_items_capacity_three(self):
        kept, removed = self.manager.prune(3)
        self.assertEqual(len(kept), 3)
        self.assertEqual(len(removed), 2)

    def test_prune_less_than_capacity(self):
        manager = MemoryManager()
        manager.add(MemoryItem("m1", "First memory", 0.9, 0))
        manager.add(MemoryItem("m2", "Second memory", 0.8, 1))

        kept, removed = manager.prune(3)
        self.assertEqual(len(kept), 2)
        self.assertEqual(len(removed), 0)

    def test_zero_capacity(self):
        kept, removed = self.manager.prune(0)
        self.assertEqual(len(kept), 0)
        self.assertEqual(len(removed), 5)

    def test_negative_capacity(self):
        with self.assertRaises(ValueError):
            self.manager.prune(-1)

    def test_deterministic_pruning(self):
        first_kept, first_removed = self.manager.prune(3)

        second_manager = MemoryManager()
        for item in self.items:
            second_manager.add(item)

        second_kept, second_removed = second_manager.prune(3)

        self.assertEqual(
            [item.id for item in first_kept],
            [item.id for item in second_kept]
        )
        self.assertEqual(
            [item.id for item in first_removed],
            [item.id for item in second_removed]
        )

    def test_tie_breaking_by_id(self):
        manager = MemoryManager()
        manager.add(MemoryItem("m2", "Same score", 0.8, 0))
        manager.add(MemoryItem("m1", "Same score", 0.8, 0))

        kept, removed = manager.prune(1)

        self.assertEqual([item.id for item in kept], ["m1"])
        self.assertEqual([item.id for item in removed], ["m2"])

    def test_boolean_capacity_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.prune(True)

    
class TestLongTermMemoryAndSummary(unittest.TestCase):

    def setUp(self):
        self.manager = MemoryManager()

        self.items = [
            MemoryItem("m1", "User prefers concise answers", 0.9, 0),
            MemoryItem("m2", "Project uses Python", 0.8, 1),
            MemoryItem("m3", "Deployment requires monitoring", 0.7, 2),
        ]

        for item in self.items:
            self.manager.add(item)

    def test_move_kept_to_long_term(self):
        self.manager.move_kept_to_long_term()

        self.assertEqual(len(self.manager.long_term), 3)

    def test_long_term_contains_original_items(self):
        self.manager.move_kept_to_long_term()

        self.assertEqual(
            [item.id for item in self.manager.long_term],
            ["m1", "m2", "m3"]
        )

    def test_long_term_does_not_duplicate_items(self):
        self.manager.move_kept_to_long_term()
        self.manager.move_kept_to_long_term()

        self.assertEqual(len(self.manager.long_term), 3)

    def test_short_term_is_preserved(self):
        self.manager.move_kept_to_long_term()

        self.assertEqual(len(self.manager.short_term), 3)

    def test_empty_long_term_transfer(self):
        manager = MemoryManager()

        manager.move_kept_to_long_term()

        self.assertEqual(manager.long_term, [])

    def test_summary_contains_memory_text(self):
        summary = self.manager.summarize()

        self.assertIn("User prefers concise answers", summary)
        self.assertIn("Project uses Python", summary)

    def test_empty_summary(self):
        manager = MemoryManager()

        self.assertEqual(
            manager.summarize(),
            "No active memory."
        )

    def test_summary_does_not_modify_source_records(self):
        original = list(self.manager.short_term)

        self.manager.summarize()

        self.assertEqual(self.manager.short_term, original)

    def test_build_context(self):
        context = build_context(self.items)

        self.assertIn("User prefers concise answers", context)
        self.assertIn("Project uses Python", context)
        self.assertIn("Deployment requires monitoring", context)

    def test_empty_context(self):
        self.assertEqual(build_context([]), "No active memory.")

    def test_invalid_context_input(self):
        with self.assertRaises(TypeError):
            build_context("not a list")

    def test_invalid_context_item(self):
        with self.assertRaises(TypeError):
            build_context(["not a memory item"])


class TestPruningImprovements(unittest.TestCase):

    def test_minimum_importance_filter(self):
        manager = MemoryManager()

        manager.add(MemoryItem("m1", "High value memory", 0.9, 0))
        manager.add(MemoryItem("m2", "Low value memory", 0.2, 0))

        kept, removed = manager.prune(
            capacity=5,
            min_importance=0.5
        )

        self.assertEqual([item.id for item in kept], ["m1"])
        self.assertEqual([item.id for item in removed], ["m2"])

    def test_duplicate_text_removed(self):
        manager = MemoryManager()

        manager.add(MemoryItem("m1", "Python is useful", 0.9, 0))
        manager.add(MemoryItem("m2", "Python is useful", 0.8, 0))

        kept, removed = manager.prune(5)

        self.assertEqual(len(kept), 1)
        self.assertEqual(len(removed), 1)

    def test_duplicate_detection_ignores_case(self):
        manager = MemoryManager()

        manager.add(MemoryItem("m1", "Python is useful", 0.9, 0))
        manager.add(MemoryItem("m2", "PYTHON IS USEFUL", 0.8, 0))

        kept, removed = manager.prune(5)

        self.assertEqual(len(kept), 1)
        self.assertEqual(len(removed), 1)

    def test_duplicate_detection_ignores_extra_spaces(self):
        manager = MemoryManager()

        manager.add(MemoryItem("m1", "Python is useful", 0.9, 0))
        manager.add(MemoryItem("m2", " Python   is useful ", 0.8, 0))

        kept, removed = manager.prune(5)

        self.assertEqual(len(kept), 1)
        self.assertEqual(len(removed), 1)

    def test_minimum_importance_validation(self):
        manager = MemoryManager()

        with self.assertRaises(ValueError):
            manager.prune(3, min_importance=1.5)

    def test_invalid_minimum_importance_type(self):
        manager = MemoryManager()

        with self.assertRaises(ValueError):
            manager.prune(3, min_importance="high")

    def test_improved_pruning_is_deterministic(self):
        items = [
            MemoryItem("m1", "Python guide", 0.9, 0),
            MemoryItem("m2", "Python guide", 0.8, 0),
            MemoryItem("m3", "Database guide", 0.7, 1),
        ]

        first = MemoryManager()
        second = MemoryManager()

        for item in items:
            first.add(item)
            second.add(item)

        first_kept, first_removed = first.prune(2, 0.5)
        second_kept, second_removed = second.prune(2, 0.5)

        self.assertEqual(
            [item.id for item in first_kept],
            [item.id for item in second_kept]
        )

        self.assertEqual(
            [item.id for item in first_removed],
            [item.id for item in second_removed]
        )

    def test_low_importance_memory_does_not_consume_capacity(self):
        manager = MemoryManager()

        manager.add(MemoryItem("m1", "Low importance", 0.1, 0))
        manager.add(MemoryItem("m2", "High importance", 0.9, 0))
        manager.add(MemoryItem("m3", "Medium importance", 0.7, 0))

        kept, removed = manager.prune(
            capacity=2,
            min_importance=0.5
        )

        self.assertEqual(len(kept), 2)
        self.assertEqual(len(removed), 1)



if __name__ == "__main__":
    unittest.main()
