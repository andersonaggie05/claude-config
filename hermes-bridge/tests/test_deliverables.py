"""Tests for agent deliverable storage and retrieval."""

from __future__ import annotations

import sqlite3

import pytest

from hermes_bridge.deliverables import save_deliverable, search_deliverables


class TestSaveDeliverable:
    """Tests for save_deliverable."""

    def test_basic_save(self, db_conn: sqlite3.Connection) -> None:
        did = save_deliverable(
            db_conn,
            session_id="sess-001",
            agent_role="software-architect",
            project="appendix-k",
            deliverable_type="architecture",
            title="Approval workflow design",
            content="The approval workflow uses a state machine...",
        )
        assert did > 0

        row = db_conn.execute("SELECT * FROM deliverables WHERE id = ?", (did,)).fetchone()
        assert row["agent_role"] == "software-architect"
        assert row["project"] == "appendix-k"
        assert row["status"] == "active"

    def test_save_with_consumers_and_pipeline(self, db_conn: sqlite3.Connection) -> None:
        did = save_deliverable(
            db_conn,
            session_id="sess-001",
            agent_role="sprint-prioritizer",
            project="appendix-k",
            deliverable_type="sprint-plan",
            title="Sprint 12 plan",
            content="Priority items: approval workflow, data retention...",
            downstream_consumers=["software-architect", "reality-checker"],
            pipeline_id="pipeline-001",
        )

        row = db_conn.execute("SELECT * FROM deliverables WHERE id = ?", (did,)).fetchone()
        assert row["pipeline_id"] == "pipeline-001"
        assert '"software-architect"' in row["downstream_consumers"]

    def test_supersede_on_save(self, db_conn: sqlite3.Connection) -> None:
        """New deliverable with same key supersedes the old one."""
        did1 = save_deliverable(
            db_conn,
            session_id="sess-001",
            agent_role="software-architect",
            project="appendix-k",
            deliverable_type="architecture",
            title="Design v1",
            content="First version of the design.",
        )
        did2 = save_deliverable(
            db_conn,
            session_id="sess-002",
            agent_role="software-architect",
            project="appendix-k",
            deliverable_type="architecture",
            title="Design v2",
            content="Revised design with trade-off analysis.",
        )

        old = db_conn.execute("SELECT status FROM deliverables WHERE id = ?", (did1,)).fetchone()
        new = db_conn.execute("SELECT status FROM deliverables WHERE id = ?", (did2,)).fetchone()
        assert old["status"] == "superseded"
        assert new["status"] == "active"

    def test_supersede_only_same_key(self, db_conn: sqlite3.Connection) -> None:
        """Deliverables with different types are not superseded."""
        did1 = save_deliverable(
            db_conn,
            session_id="sess-001",
            agent_role="software-architect",
            project="appendix-k",
            deliverable_type="architecture",
            title="Architecture doc",
            content="Architecture content.",
        )
        save_deliverable(
            db_conn,
            session_id="sess-001",
            agent_role="software-architect",
            project="appendix-k",
            deliverable_type="review",
            title="Review doc",
            content="Review content.",
        )

        old = db_conn.execute("SELECT status FROM deliverables WHERE id = ?", (did1,)).fetchone()
        assert old["status"] == "active"  # NOT superseded


class TestSearchDeliverables:
    """Tests for search_deliverables."""

    @pytest.fixture(autouse=True)
    def _seed_deliverables(self, db_conn: sqlite3.Connection) -> None:
        """Seed test deliverables."""
        self.conn = db_conn
        save_deliverable(
            db_conn,
            session_id="sess-001",
            agent_role="software-architect",
            project="appendix-k",
            deliverable_type="architecture",
            title="Approval workflow design",
            content="State machine for training record approvals.",
            downstream_consumers=["code-reviewer", "reality-checker"],
            pipeline_id="pipe-001",
        )
        save_deliverable(
            db_conn,
            session_id="sess-001",
            agent_role="reality-checker",
            project="appendix-k",
            deliverable_type="assessment",
            title="Approval workflow assessment",
            content="NEEDS WORK: 3 test failures found.",
            pipeline_id="pipe-001",
        )
        save_deliverable(
            db_conn,
            session_id="sess-002",
            agent_role="compliance-auditor",
            project="qaqc",
            deliverable_type="assessment",
            title="QAQC audit readiness",
            content="75% ready. Gap in record retention.",
        )

    def test_search_by_project(self) -> None:
        results = search_deliverables(self.conn, project="appendix-k")
        assert len(results) == 2
        assert all(r["project"] == "appendix-k" for r in results)

    def test_search_by_agent_role(self) -> None:
        results = search_deliverables(self.conn, agent_role="reality-checker")
        assert len(results) == 1
        assert results[0]["title"] == "Approval workflow assessment"

    def test_search_by_pipeline_id(self) -> None:
        results = search_deliverables(self.conn, pipeline_id="pipe-001")
        assert len(results) == 2

    def test_search_by_consumer(self) -> None:
        results = search_deliverables(self.conn, for_consumer="reality-checker")
        assert len(results) == 1
        assert results[0]["agent_role"] == "software-architect"

    def test_fts_search(self) -> None:
        results = search_deliverables(self.conn, query="state machine")
        assert len(results) == 1
        assert results[0]["agent_role"] == "software-architect"

    def test_fts_search_across_title_and_content(self) -> None:
        results = search_deliverables(self.conn, query="audit readiness")
        assert len(results) == 1
        assert results[0]["project"] == "qaqc"

    def test_excludes_superseded_by_default(self) -> None:
        # Save a new architecture doc, superseding the old one
        save_deliverable(
            self.conn,
            session_id="sess-003",
            agent_role="software-architect",
            project="appendix-k",
            deliverable_type="architecture",
            title="Approval workflow design v2",
            content="Revised state machine with rollback.",
        )

        results = search_deliverables(self.conn, project="appendix-k")
        titles = [r["title"] for r in results]
        assert "Approval workflow design v2" in titles
        assert "Approval workflow design" not in titles

    def test_includes_superseded_when_requested(self) -> None:
        save_deliverable(
            self.conn,
            session_id="sess-003",
            agent_role="software-architect",
            project="appendix-k",
            deliverable_type="architecture",
            title="Design v2",
            content="Revised.",
        )

        results = search_deliverables(self.conn, project="appendix-k", include_archived=True)
        assert len(results) >= 3  # Original + superseded + assessment

    def test_limit(self) -> None:
        results = search_deliverables(self.conn, limit=1)
        assert len(results) == 1

    def test_no_filters_returns_all_active(self) -> None:
        results = search_deliverables(self.conn)
        assert len(results) == 3

    def test_combined_filters(self) -> None:
        results = search_deliverables(
            self.conn, project="appendix-k", agent_role="software-architect"
        )
        assert len(results) == 1
        assert results[0]["deliverable_type"] == "architecture"
