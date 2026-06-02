"""StewardPath adaptive concierge-intake package.

Pure-Python (no FastAPI/Pydantic) so the deterministic intake logic stays
importable and testable offline. FastAPI routes in ``app.main`` orchestrate
these modules; they never own business logic themselves.
"""
