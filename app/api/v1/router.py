"""
API v1 router — aggregates all endpoint routers under /api/v1.

Each router is mounted at its own prefix so future endpoints can be
added or removed without touching this file.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import ai, analysis, auth, chat, dashboard, rag, report, reports, upload

api_router = APIRouter()

api_router.include_router(auth.router,      prefix="/auth",      tags=["Authentication"])
api_router.include_router(upload.router,    prefix="/upload",    tags=["Upload"])
api_router.include_router(report.router,    prefix="/report",    tags=["Report"])
api_router.include_router(analysis.router,  prefix="/analysis",  tags=["Analysis"])
api_router.include_router(chat.router,      prefix="/chat",      tags=["Chat"])
api_router.include_router(ai.router,        prefix="/ai",        tags=["AI (Gemini)"])
api_router.include_router(rag.router,       prefix="/rag",       tags=["RAG"])
api_router.include_router(reports.router,   prefix="/reports",   tags=["Report Management"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
