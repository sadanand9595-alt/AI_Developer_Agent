"""
HTTP API layer for AI Command Center.

This package is a thin transport boundary over the existing,
already-audited service layer (services/*.py). It owns:

- Request/response validation (pydantic schemas)
- Authentication (JWT bearer tokens)
- Authorization / ownership enforcement
- Translating service-layer ValueError/Result failures into
  consistent HTTP error responses

It intentionally contains no business logic of its own.
"""
