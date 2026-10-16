"""
PII-Shield — Audit Database Connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SQLite async database connection and session factory.
"""

# TODO [Phase 3]: Implement database connection
#
# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# from backend.config import settings
#
# engine = create_async_engine(
#     settings.AUDIT_DB_URL.replace("sqlite:///", "sqlite+aiosqlite:///"),
#     echo=settings.DEBUG,
# )
#
# async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
#
#
# async def init_db():
#     """Create all tables."""
#     from backend.audit.models import Base
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#
#
# async def get_session() -> AsyncSession:
#     """Yield a database session."""
#     async with async_session() as session:
#         yield session
