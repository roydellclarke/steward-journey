"""Test package bootstrap.

Force LLM augmentation off for the whole suite before any test imports
``app.main`` (which reads ``.env`` at import time). Without this, a local
``.env`` that enables augmentation makes API tests fire real Kimi/DeepSeek
requests: slow, flaky, and network-dependent. Tests that need the LLM path
build their own settings and monkeypatch the transport (see test_llm_merge).

``setdefault`` keeps an explicit shell override in charge, and because
``Settings.from_env`` also uses ``setdefault`` when loading ``.env``, this
value wins over the file.
"""

import os

os.environ.setdefault("STEWARDPATH_USE_LLM", "false")
