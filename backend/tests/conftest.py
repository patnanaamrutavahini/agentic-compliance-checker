"""Hermetic test configuration: no model downloads, no external services."""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="compliance_tests_")
os.environ.setdefault("EMBEDDING_BACKEND", "none")
os.environ.setdefault("VECTOR_BACKEND", "memory")
os.environ.setdefault("USE_IN_MEMORY_REDIS", "true")
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_tmp}/test.db")
os.environ.setdefault("UPLOAD_DIR", os.path.join(_tmp, "uploads"))
os.environ.setdefault("REPORTS_DIR", os.path.join(_tmp, "reports"))
