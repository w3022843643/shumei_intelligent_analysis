"""E receiving acceptance on C 0.1.9, disposable SQLite and real public docs.

This script plays D's orchestration role only in an isolated acceptance store.
It never opens the team's MySQL database or changes D/C source repositories.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
C_ROOT = ROOT / "artifacts/c-0.1.9/data_foundation"
sys.path.insert(0, str(C_ROOT))
sys.path.insert(0, str(ROOT))


def main():
    from data_foundation import JobCreate, JobLease, LeaseLost, create_store
    from data_foundation.ingestion.real_dataset import import_real_dataset, validate_real_dataset

    from intelligent_analysis import ServiceBindings, answer_message, configure_services
    from intelligent_analysis.worker import process_knowledge_job, publish_knowledge_snapshot

    run_root = ROOT / "artifacts" / ("knowledge-acceptance-" + uuid4().hex[:8])
    run_root.mkdir(parents=True)
    manifest_path = C_ROOT / "real_data/2026-10-12-v2/manifest.json"
    validation = validate_real_dataset(manifest_path)
    database_url = "sqlite:///" + (run_root / "acceptance.db").as_posix()
    env = {**os.environ, "DATABASE_URL": database_url}
    subprocess.run([sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
                   cwd=C_ROOT, env=env, check=True, capture_output=True)
    store = create_store(database_url, data_root=run_root / "assets", allow_sqlite_for_tests=True)
    report = {"c_version": "0.1.9", "migration_head": "0006", "target": "isolated_sqlite",
              "business_database_verified": False, "dataset_validation": validation,
              "documents": [], "checks": {}}
    snapshot = {"documents": {}}
    index_path = run_root / "published-index.json"
    try:
        imported = import_real_dataset(store, manifest_path)
        report["import"] = {k: v for k, v in imported.items()
                            if k in {"dataset_id", "status", "database_dialect", "counts"}}
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for doc in manifest["documents"]:
            now = datetime.now(UTC)
            file_path = (manifest_path.parent / doc["text_path"]).resolve()
            if not file_path.is_relative_to(manifest_path.parent.resolve()):
                raise ValueError("Document path escapes dataset")
            payload = {"document_id": doc["id"], "version": doc["document_version"],
                       "file_path": str(file_path), "metadata": doc}
            with store.write() as uow:
                job = uow.jobs.enqueue_or_get(JobCreate("knowledge_index", doc["id"], payload,
                                                       "E receiving acceptance"), now)
            with store.write() as uow:
                claimed = uow.jobs.claim_job("e-acceptance", datetime.now(UTC),
                                              job_type="knowledge_index", job_id=job["id"])
            lease = JobLease(**claimed["lease"])
            prepared = process_knowledge_job(payload)
            staged = store.persist_file(source_id=doc["source_id"],
                                        original_name=f"index-{doc['id']}.json",
                                        stream=io.BytesIO(prepared["artifact_bytes"]))
            with store.write() as uow:
                index = uow.knowledge.begin_index(document_id=doc["id"], version=payload["version"],
                    job_id=job["id"], parser_version="text-parser-0.5.0",
                    embedding_model_version="keyword-tfidf-0.5.0", lease=lease)
                result = uow.knowledge.write_chunks(index["id"], prepared["chunks"], lease)
                replay = uow.knowledge.write_chunks(index["id"], prepared["chunks"], lease)
                assert replay["inserted"] == 0
                uow.knowledge.activate_index(document_id=doc["id"], version=payload["version"],
                    artifact_path=staged["relative_path"], artifact_sha256=prepared["artifact_sha256"],
                    expected_chunk_count=prepared["chunk_count"], lease=lease)
                uow.jobs.complete_job(lease, {"document_id": doc["id"]}, datetime.now(UTC))
            with store.read() as uow:
                assert uow.jobs.get_job(job["id"])["status"] == "succeeded"
                assert uow.knowledge.get_chunks(doc["id"])["status"] == "ready"
            snapshot["documents"].update(prepared["snapshot"]["documents"])
            publish_knowledge_snapshot(snapshot, str(index_path))
            report["documents"].append({"document_id": doc["id"], "title": doc["title"],
                "status": "ready", "chunk_count": prepared["chunk_count"],
                "text_sha256": hashlib.sha256(file_path.read_bytes()).hexdigest(),
                "artifact_sha256": prepared["artifact_sha256"], "duplicate_chunks_skipped": replay["skipped"],
                "inserted": result["inserted"]})
        # Real C lease expiry/recovery regression in this isolated store.
        old = datetime.now(UTC) - timedelta(minutes=10)
        with store.write() as uow:
            recovery_job = uow.jobs.enqueue_or_get(JobCreate(
                "knowledge_index", "lease-recovery", {}, "E isolated recovery check"), old)
            claimed = uow.jobs.claim_job("old-worker", old, 120, job_id=recovery_job["id"])
        expired = JobLease(**claimed["lease"])
        with store.write() as uow:
            recovered = uow.jobs.recover_expired(datetime.now(UTC))
        assert recovered["requeued"] == 1
        rejected = False
        try:
            with store.write() as uow:
                uow.jobs.update_progress(expired, 1, 0, datetime.now(UTC))
        except LeaseLost:
            rejected = True
        assert rejected
        with store.write() as uow:
            claimed = uow.jobs.claim_job("new-worker", datetime.now(UTC),
                job_type="knowledge_index", job_id=recovery_job["id"])
            new_lease = JobLease(**claimed["lease"])
            uow.jobs.update_progress(new_lease, 1, 0, datetime.now(UTC))
            uow.jobs.complete_job(new_lease, {"check": "recovered"}, datetime.now(UTC))
        report["checks"].update(expired_lease_rejected=True, recovery_new_lease_completed=True)
        configure_services(ServiceBindings(knowledge_index_path=str(index_path)))
        questions = ["2025年春节黄山运营时间", "2026年五一出游提示", "2024年部分景点关闭公告"]
        answers = [answer_message(q) for q in questions]
        (run_root / "question-answers.json").write_text(
            json.dumps(dict(zip(questions, answers)), ensure_ascii=False, indent=2), encoding="utf-8")
        report["question_checks"] = [{"question": q, "status": a["status"],
            "citation_ids": [c["id"] for c in a["citations"]],
            "citations": a["citations"], "answer_preview": a["answer"][:200],
            "limitations": a["limitations"]}
            for q, a in zip(questions, answers)]
        report["checks"]["restart_load"] = subprocess.run(
            [sys.executable, "-c", ("from intelligent_analysis import load_knowledge_index,answer_message; "
             f"load_knowledge_index({str(index_path)!r}); "
             "assert answer_message('黄山')['citations']; print('passed')")],
            cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
        report["checks"]["all_16_indexed"] = len(snapshot["documents"]) == 16
        report["checks"]["citations_keep_c_ids"] = all(
            c["id"] in snapshot["documents"] for a in answers for c in a["citations"])
        report["status"] = "passed"
    finally:
        store.dispose()
    output = Path(os.environ.get("E_ACCEPTANCE_REPORT", ROOT / "docs/acceptance/C019-knowledge.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"status": report["status"], "documents": len(report["documents"]),
                      "report": str(output)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
