# DISHA System Architecture Overview

DISHA operates on a multi-tiered architecture:
1. Client: Next.js 14 web app and Rust CLI.
2. API Gateway & Logic: Modular FastAPI backend with domain-driven boundaries.
3. Event Processing & Async Tasks: Background worker with transactional outbox.
4. Persistence: PostgreSQL with Row-Level Security (RLS) for strict multi-campus isolation.
5. Trust Layer: On-chain immutable hash anchoring.
