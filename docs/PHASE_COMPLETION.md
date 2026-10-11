# Phase completion

The user authorized all phases without further approval. Each phase has concrete implementation artifacts and checks.

| Phase | Delivered artifacts | Verification |
|---|---|---|
| 1 — Architecture | ERD, complete attribute/key dictionary, cardinality/participation, FD/3NF derivation, Mermaid/draw.io/DBML | 20 tables, 160 attributes and 21 FKs structurally reviewed |
| 2 — Schema | Numbered database/schema SQL, explicit ORM models, InnoDB constraints/indexes | Installed on MySQL 8.4.11; direct constraint tests |
| 3 — Seed | Deterministic Python generator and standalone verified SQL snapshot | Every requested minimum met; clean-schema SQL import passes |
| 4 — Backend | FastAPI configuration, SQLAlchemy sessions/models, Pydantic, hashing/JWT/errors/CORS | Auth/RBAC/error tests and interactive OpenAPI |
| 5 — Patient/case APIs | CRUD, draft bundle, case history/timeline, transactional submission | API integration plus full browser case workflow |
| 6 — Remaining APIs | Visits/sections, appointments, diagnoses, fictional prescriptions, follow-ups, catalogs, doctors/users, analytics | Integration tests, concurrent schedule test and browser booking workflow |
| 7 — Frontend | Responsive role workspace and all requested pages | Strict TypeScript build; desktop/tablet visual QA |
| 8 — Connection | React fetch → Vite proxy → FastAPI → SQLAlchemy → PyMySQL → MySQL | Browser registration/submission and fresh API reads; health query |
| 9 — Advanced DBMS | Four views/functions, business/cache procedures, meaningful triggers, 57 DQL queries and SQL labs | Actual MySQL lab execution; cache refresh and view API reads |
| 10 — Testing | Eight integration tests, three browser workflows, SQL verifier and clean seed restore | Passing results detailed in TESTING.md |
| 11 — Documentation | Setup/run guide, implementation/API, SQL lab, testing, three-person presentation/viva guide | All files present, startup and source package prepared |

The reporting cache is intentionally a materialized-view equivalent, not a native MySQL materialized view. Future-scope items remain proposals and are listed as such in the presentation guide.
