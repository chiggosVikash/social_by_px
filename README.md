# Social by PX

**Social by PX** is an open-source, multi-agent AI content generation platform. It automatically discovers trending news, verifies article quality, generates social-media carousel content, renders branded carousel images, and publishes approved content to social media platforms (Instagram, Facebook).

It combines LangGraph AI agents, workflow orchestration (RQ), automated image generation, and social publishing while maintaining human approval before publication.

## Key Features

- **Autonomous Research**: Scours the web for trending topics using Tavily API and LangGraph agents.
- **Content Verification**: AI-driven verification of article quality before generating content.
- **Automated Carousel Generation**: Converts news into multi-slide text & image prompts.
- **Human-in-the-Loop**: A clean Next.js UI to review, approve, or reject AI-generated content before publishing.
- **Multi-Platform Publishing**: Strategy-pattern based integrations for Instagram Carousels and Facebook Posts via the Meta Graph API.
- **Monorepo Architecture**: Clean separation between a fast, SOLID-compliant FastAPI backend and a responsive Next.js frontend.
- **Style Presets & Visual Types**: Each project picks one of 6 visual styles; slides are routed to cheap PIL gradients, uploaded templates, or premium DALL-E art based on what they need.

## Tech Stack

- **Backend**: Python 3.12+, FastAPI
- **Frontend**: Next.js 14+ (App Router), React, Tailwind CSS, shadcn/ui, Zustand, Axios
- **AI Orchestration**: LangGraph, LangChain, OpenAI
- **Database**: PostgreSQL (via SQLAlchemy Async, Alembic)
- **Background Jobs**: Redis Queue (RQ)
- **Security**: Cryptography (Fernet) for token encryption
- **Package Managers**: `uv` (Python), `pnpm` (Node)

## Image Generation System

The platform now generates premium-quality carousel visuals with a Gen Z aesthetic:

### Key Improvements
- **Style Presets**: Each project chooses a visual style (6 options) that locks the color palette and aesthetic vocabulary
- **Structured Prompts**: LLM generates creative direction briefs, not generic "abstract background" prompts
- **Text-Accurate Generation**: DALL-E designs compositions with intentional text zones; PIL renders the actual text
- **Cost-Effective**: Only 1-2 DALL-E calls per carousel (vs 5 before), saving 60-80%

### Visual Types Per Slide
- **Hook slide**: Full AI-generated art (highest visual impact)
- **Context/Insight**: Template or gradient (cost-effective, text-focused)
- **Proof/CTA**: Always gradient + typography (maximum text clarity)

### Default Styles
- **General Soft**: Neutral cream & charcoal, versatile for all industries
- **Tech Editorial**: Muted earth tones, Substack + Linear aesthetic
- **Health Warm**: Warm cream with botanicals, Kinfolk + Goop style
- **Finance Paper**: Cream paper, Bloomberg + Economist aesthetic
- **Education Warm**: Academic, Are.na + Kinfeel aesthetic  
- **Marketing Bold**: High contrast, Apple keynote + Dribbble style

## Prerequisites

Before starting, ensure you have the following installed on your machine:
- Node.js 20 or higher
- pnpm 9 or higher
- Python 3.11 or higher
- uv (Extremely fast Python package installer)
- PostgreSQL 15 or higher (or Docker)
- Redis (For background workers)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/social_by_px.git
cd social_by_px
```

### 2. Environment Setup

Copy the example environment file in the root directory:

```bash
cp .env.example .env
```

Configure the following key variables in your `.env` file:

| Variable | Description | Example |
| -------- | ----------- | ------- |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://postgres:pass@localhost:5432/social_by_px` |
| `SYNC_DATABASE_URL` | Sync PostgreSQL connection string | `postgresql://postgres:pass@localhost:5432/social_by_px` |
| `REDIS_URL` | Redis connection for background tasks | `redis://localhost:6379/0` |
| `OPENAI_API_KEY` | OpenAI API key for LLM agents | `sk-...` |
| `TAVILY_API_KEY` | Tavily API key for web search | `tvly-...` |
| `NEXT_PUBLIC_API_URL` | Frontend connection to backend API | `http://localhost:8000` |

### 3. Backend Setup (`apps/api`)

Navigate to the API directory:

```bash
cd apps/api
```

Install Python dependencies using `uv`:

```bash
uv sync
```

Run database migrations to set up your schema:

```bash
uv run alembic upgrade head
```

Start the development server:

```bash
uv run uvicorn main:app --app-dir src --reload --port 8000
```

Start the RQ worker (in a separate terminal) for background jobs:

```bash
cd apps/api
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES PYTHONPATH=src uv run rq worker workflow default
```

### 4. Frontend Setup (`apps/web`)

Navigate to the web directory:

```bash
cd apps/web
```

Install JavaScript dependencies:

```bash
pnpm install
```

Start the development server:

```bash
pnpm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Architecture

### Directory Structure

```
social_by_px/
├── apps/
│   ├── api/                  # FastAPI Backend
│   │   ├── alembic/          # Database migrations
│   │   ├── src/
│   │   │   ├── agents/       # LangGraph Agents & Nodes
│   │   │   ├── api/          # FastAPI Routers
│   │   │   ├── core/         # Config & Security
│   │   │   ├── db/           # Database Session
│   │   │   ├── models/       # SQLAlchemy Models
│   │   │   ├── repositories/ # Repository Pattern (Data Access)
│   │   │   ├── schemas/      # Pydantic Models
│   │   │   ├── services/     # Publishers & Renderers
│   │   │   └── workers/      # RQ worker tasks
│   │   └── pyproject.toml    # Python dependencies
│   └── web/                  # Next.js Frontend
│       ├── public/           # Static assets
│       ├── src/
│       │   ├── app/          # App Router Pages & Layouts
│       │   ├── components/   # React Components (shadcn/ui)
│       │   ├── store/        # Zustand state management
│       │   └── lib/          # Utilities
│       └── package.json      # Node dependencies
└── .env.example              # Example environment variables
```

### Request Lifecycle & Data Flow

1. **Frontend Request**: The Next.js frontend uses Axios (or React Server Components) to request data from the FastAPI backend.
2. **Backend Routing**: FastAPI routes the request to the appropriate endpoint in `src/api/`.
3. **Business Logic & Agents**: If the request involves content generation, LangGraph agents in `src/agents/` are triggered or background jobs are queued via RQ.
4. **Data Access**: Controllers interact with `src/repositories/` which perform database operations using SQLAlchemy.
5. **Publishing**: Approved content is passed to `src/services/` where strategy-pattern publishers interact with external APIs (e.g., Meta Graph API).

### AI Workflow (LangGraph)

1. **Research Agent**: Uses Tavily API to find news related to project keywords.
2. **Verification Agent**: Evaluates article relevance and quality.
3. **Query Refinement Agent**: Enhances search terms if verification fails.
4. **Content Generation Agent**: Converts verified articles into slides and image prompts.
5. **Slide Verification Agent**: Validates slide lengths and format.
6. **Publishing Agent**: Interfaces with Meta Graph API via the backend Publisher Strategy.

## Environment Variables

### Complete Reference

| Variable | Description |
| -------- | ----------- |
| `DATABASE_URL` | Async Postgres connection string. |
| `SYNC_DATABASE_URL` | Sync Postgres connection string used by Alembic migrations. |
| `REDIS_URL` | Redis URL for background jobs (RQ). |
| `OPENAI_API_KEY` | Your OpenAI API key for LLM agents. |
| `TAVILY_API_KEY` | Your Tavily API key for web search. |
| `META_APP_ID` | Meta App ID for publishing to Facebook/Instagram. |
| `META_APP_SECRET` | Meta App Secret. |
| `CLOUDFLARE_R2_ACCESS_KEY_ID` | Cloudflare R2 access key for media storage. |
| `CLOUDFLARE_R2_SECRET_ACCESS_KEY` | Cloudflare R2 secret key. |
| `CLOUDFLARE_R2_ENDPOINT_URL` | Cloudflare R2 endpoint URL. |
| `CLOUDFLARE_R2_BUCKET_NAME` | Cloudflare R2 bucket name. |
| `NEXT_PUBLIC_API_URL` | Base URL for the frontend to call the backend API. |

## Available Scripts

### Backend (`apps/api`)

| Command | Description |
| ------- | ----------- |
| `uv run uvicorn src.main:app --reload` | Start the FastAPI development server. |
| `uv run rq worker` | Start the Redis Queue background worker. |
| `uv run alembic upgrade head` | Run all pending database migrations. |
| `uv run alembic revision --autogenerate` | Generate a new migration based on model changes. |

### Frontend (`apps/web`)

| Command | Description |
| ------- | ----------- |
| `pnpm dev` | Start the Next.js development server. |
| `pnpm build` | Build the Next.js app for production. |
| `pnpm start` | Start the production Next.js server. |
| `pnpm lint` | Run ESLint. |

## Deployment

Since this project is a monorepo, deployment is typically split between the frontend and the backend.

### Frontend (Next.js)

The `apps/web` directory is optimized for Vercel deployment:
1. Connect your repository to Vercel.
2. Set the Root Directory to `apps/web`.
3. Vercel will automatically detect the Next.js framework.
4. Add the necessary Environment Variables (e.g., `NEXT_PUBLIC_API_URL`).

### Backend (FastAPI)

The `apps/api` directory can be deployed using Docker, Render, or Railway.

**Docker (Example)**

Build and run:

```bash
cd apps/api
# Ensure you have a Dockerfile here
docker build -t socialbypx-api .

docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e REDIS_URL=redis://... \
  -e OPENAI_API_KEY=... \
  socialbypx-api
```

## Troubleshooting

### Database Connection Issues

**Error:** `could not connect to server: Connection refused`

**Solution:**
1. Verify PostgreSQL is running.
2. Check your `.env` to ensure `DATABASE_URL` and `SYNC_DATABASE_URL` point to the right port and include the correct credentials.
3. Ensure the database `social_by_px` has been created.

### Missing Module Errors in Python

**Error:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
Ensure you are running commands from within the `apps/api` directory.
Run `uv sync` to ensure all dependencies are installed.

### Background Jobs Not Processing

**Error:** Content generation gets stuck or doesn't trigger.

**Solution:**
Ensure the RQ worker is running in a separate terminal:
```bash
cd apps/api
uv run rq worker
```
Also, ensure your local Redis server is active and accessible at the URL provided in `.env`.
