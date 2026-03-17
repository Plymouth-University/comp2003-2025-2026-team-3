# Project Organization Review

This document provides a review of the current project folder structure and proposes recommendations for future organization.

## Current High-Level Structure

The project is organized into three main top-level directories:

```
.
├── backend/       # FastAPI application and services
├── docs/          # Project documentation
└── frontend/      # Vanilla TypeScript SPA
```

This separation is clean and follows standard practice for a full-stack application with decoupled front and back ends.

---

## Backend Structure (`backend/`)

The backend code is well-organized with a clear separation of concerns.

```
backend/
├── alembic/              # Database migration scripts
├── app/                  # Main application source code
│   ├── routers/          # API endpoint definitions
│   ├── schemas/          # Pydantic data models
│   ├── services/         # Business logic (AI, Profile Service)
│   ├── repositories/     # Database interaction layer
│   ├── models/           # SQLAlchemy ORM models
│   ├── providers/        # External service connectors (e.g., mock Autotask)
│   ├── auth.py           # Authentication logic
│   ├── config.py         # Application configuration
│   ├── database.py       # Database session management
│   └── main.py           # FastAPI app entry point
├── data/                 # Data files for AI processing
├── scripts/              # Standalone operational scripts
└── tests/                # Tests
```

### Review & Recommendations

-   **`app/services/ai_categoriser.py`**: This file appears to be a legacy or redundant entry. The core AI logic resides within the `app/services/ai/` directory.
    -   **Recommendation**: **Delete** `app/services/ai_categoriser.py`.
-   **`data/Unprocessed Tickets/`**: This directory seems to be unused, as scripts now reference `data/tickets.json` directly.
    -   **Recommendation**: **Delete** the `data/Unprocessed Tickets/` directory to avoid confusion.
-   **Overall**: The backend structure is robust and scalable. The use of repositories, services, and schemas promotes maintainability.

---

## Frontend Structure (`frontend/`)

The frontend follows a feature-oriented structure, which is a modern approach for SPAs.

```
frontend/
├── src/
│   ├── app/              # Main application controller (App.ts)
│   ├── assets/           # Static assets (images, icons)
│   ├── components/       # Reusable UI components (TicketCard, etc.)
│   ├── pages/            # Top-level screen components
│   ├── shared/           # Cross-cutting concerns (auth, types, utils)
│   └── styles/           # Global styles
├── index.html            # Main HTML entry point
├── tailwind.config.js    # Tailwind CSS configuration
└── tsconfig.json         # TypeScript configuration
```

### Review & Recommendations

-   **`src/app/App.ts`**: The main application file is nested one level deeper than necessary.
    -   **Recommendation**: Move `src/app/App.ts` to `src/App.ts` and delete the `src/app` directory. Update the import in `src/main.ts`.
-   **`assets/` vs. `public/`**: The name `assets` is clear, but `public` is a more common convention for static files that are copied directly to the build output.
    -   **Recommendation (Minor)**: Consider renaming `assets` to `public` in the future for better alignment with industry conventions.
-   **Overall**: The frontend structure is clean and easy to navigate. The separation of pages, components, and shared logic is effective.

---

## Documentation Structure (`docs/`)

The documentation is comprehensive but could benefit from better organization.

### Recommendation

A flatter, more organized structure based on topic would be more intuitive. This involves renaming and moving files to create logical groups.

**Proposed New Structure (To Be Implemented):**

-   **`docs/README.md`**: A central index file.
-   **Architecture:**
    -   `SYSTEM_ARCHITECTURE.md`
    -   `FRONTEND_ARCHITECTURE.md`
    -   `AI_SYSTEM_ARCHITECTURE.md`
    -   `LOGGING_ARCHITECTURE.md`
-   **Services & Integrations:**
    -   `PROFILE_SERVICE_GUIDE.md`
    -   `ENTRA_ID_INTEGRATION.md`
-   **Developer Guides:**
    -   `LOCAL_DEVELOPMENT_GUIDE.md`
    -   `API_REFERENCE.md`
    -   `AI_OPERATIONS_GUIDE.md`
-   **Code-Level Docs:**
    -   `FRONTEND_APP_CONTROLLER.md`
    -   `FRONTEND_DOM_UTILS.md`
    -   `FRONTEND_TAILWIND_CONFIG.md`
-   **Project Safety:**
    -   `PROJECT_SAFETY_GUIDE.md`

This refactoring will make the documentation easier to navigate and maintain.
