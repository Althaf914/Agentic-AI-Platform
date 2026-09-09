"""
Unit tests for SharedMemory — write, search, check_duplicate, get_timeline.
Tests use PostgreSQL rows only (ChromaDB operations gracefully fallback).
"""

import uuid
import asyncio
from datetime import datetime, timezone, timedelta

import pytest

from backend.models.memory import Memory
from backend.memory.shared_memory import SharedMemory


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestSharedMemoryWrite:
    def test_write_stores_in_postgres(self, test_db):
        """write() should create a Memory row in PostgreSQL."""
        memory = SharedMemory(test_db)

        memory_id = run_async(memory.write(
            entity_type="company",
            entity_id="co-123",
            summary="Stripe is a payments company",
            metadata={"domain": "stripe.com"},
        ))

        assert memory_id is not None

        # Verify row in DB
        row = test_db.query(Memory).filter(Memory.id == memory_id).first()
        assert row is not None
        assert row.entity_type == "company"
        assert row.entity_id == "co-123"
        assert row.summary == "Stripe is a payments company"
        assert row.metadata_json["domain"] == "stripe.com"

    def test_write_sets_last_seen(self, test_db):
        """write() should set last_seen to current time."""
        memory = SharedMemory(test_db)

        memory_id = run_async(memory.write(
            entity_type="contact",
            entity_id="ct-456",
            summary="Contact at Acme Corp",
            metadata={},
        ))

        row = test_db.query(Memory).filter(Memory.id == memory_id).first()
        assert row.last_seen is not None


class TestSharedMemorySearch:
    def test_search_returns_relevant_entry(self, test_db):
        """search() should find entries matching the query text."""
        memory = SharedMemory(test_db)

        # Write 3 different entries
        run_async(memory.write("company", "co-1", "Stripe is a payments company", {"domain": "stripe.com"}))
        run_async(memory.write("company", "co-2", "Datadog is a monitoring platform", {"domain": "datadog.com"}))
        run_async(memory.write("company", "co-3", "Figma is a design tool", {"domain": "figma.com"}))

        # Fallback search (ChromaDB won't be available in test)
        results = memory._fallback_search("payments", top_k=1)

        assert len(results) >= 1
        assert "payments" in results[0]["summary"].lower()


class TestSharedMemoryCheckDuplicate:
    def test_check_duplicate_true(self, test_db):
        """check_duplicate should return True when domain is in memory."""
        memory = SharedMemory(test_db)

        run_async(memory.write(
            entity_type="company",
            entity_id="co-stripe",
            summary="Stripe (stripe.com) was processed and approved",
            metadata={"domain": "stripe.com"},
        ))

        result = memory.check_duplicate("stripe.com")
        assert result is True

    def test_check_duplicate_false(self, test_db):
        """check_duplicate should return False for unknown domains."""
        memory = SharedMemory(test_db)

        result = memory.check_duplicate("newcompany.com")
        assert result is False


class TestSharedMemoryTimeline:
    def test_get_timeline_ordered(self, test_db):
        """get_timeline should return entries in ascending created_at order."""
        memory = SharedMemory(test_db)
        entity_id = "co-timeline-test"

        # Write 3 entries (they'll be in insertion order)
        run_async(memory.write("company", entity_id, "First discovery", {}))
        run_async(memory.write("company", entity_id, "Validation passed", {}))
        run_async(memory.write("company", entity_id, "Qualified and approved", {}))

        timeline = run_async(memory.get_timeline(entity_id))

        assert len(timeline) == 3
        assert timeline[0]["summary"] == "First discovery"
        assert timeline[1]["summary"] == "Validation passed"
        assert timeline[2]["summary"] == "Qualified and approved"

        # Verify ordering
        for i in range(len(timeline) - 1):
            assert timeline[i]["created_at"] <= timeline[i + 1]["created_at"]

    def test_get_timeline_empty(self, test_db):
        """get_timeline for non-existent entity should return empty list."""
        memory = SharedMemory(test_db)

        timeline = run_async(memory.get_timeline("non-existent-id"))
        assert timeline == []
