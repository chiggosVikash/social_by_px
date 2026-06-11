# Social by PX

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**Social by PX** is an open-source, multi-agent AI content generation platform. It automatically discovers trending news, verifies article quality, generates social-media carousel content, renders branded carousel images, and publishes approved content to social media platforms (Instagram, Facebook). 

It combines LangGraph AI agents, workflow orchestration (RQ), automated image generation, and social publishing while maintaining human approval before publication.

## Key Features

- **Autonomous Research**: Scours the web for trending topics using Tavily API and LangGraph agents.
- **Content Verification**: AI-driven verification of article quality before generating content.
- **Automated Carousel Generation**: Converts news into multi-slide text & image prompts.
- **Human-in-the-Loop**: A clean Next.js UI to review, approve, or reject AI-generated content before publishing.
- **Multi-Platform Publishing**: Strategy-pattern based integrations for Instagram Carousels and Facebook Posts via the Meta Graph API.
- **Monorepo Architecture**: Clean separation between a fast, SOLID-compliant FastAPI backend and a responsive Next.js frontend.

---

## Tech Stack

### Backend (`apps/api`)
- **Language**: Python 3.12+
- **Framework**: FastAPI
- **AI Orchestration**: LangGraph, LangChain
- **Database**: PostgreSQL (via SQLAlchemy Async)
- **Background Jobs**: Redis Queue (RQ)
- **Security**: Cryptography (Fernet) for OAuth token encryption
- **Package Manager**: `uv`

### Frontend (`apps/web`)
- **Framework**: Next.js 14+ (App Router, React Server Components)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Package Manager**: `pnpm`

---

## Prerequisites

Before starting, ensure you have the following installed on your machine:
- [Node.js](https://nodejs.org/en/) (v20 or higher)
- [pnpm](https://pnpm.io/) (v9 or higher)
- [Python](https://www.python.org/) (v3.12 or higher)
- [uv](https://github.com/astral-sh/uv) (Extremely fast Python package installer)
- [PostgreSQL](https://www.postgresql.org/) (v15 or higher)
- [Redis](https://redis.io/) (For background workers)

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/social_by_px.git
cd social_by_px
```

### 2. Backend Setup (`apps/api`)

Navigate to the API directory:
```bash
cd apps/api
```

Install dependencies using `uv`:
```bash
uv sync
```

Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` to include your API keys (OpenAI, Tavily, Postgres URL, Redis URL, encryption keys).

Run the backend server:
```bash
uv run uvicorn src.main:app --reload --port 8000
```

Start the RQ worker (in a separate terminal):
```bash
cd apps/api
uv run rq worker
```

### 3. Frontend Setup (`apps/web`)

Navigate to the web directory:
```bash
cd apps/web
```

Install dependencies:
```bash
pnpm install
```

Start the development server:
```bash
pnpm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to access the dashboard.

---

## Architecture Overview

This project uses a standard monorepo structure.

```
social_by_px/
├── apps/
│   ├── api/                  # FastAPI Backend
│   │   ├── src/
│   │   │   ├── agents/       # LangGraph Agents & Nodes
│   │   │   ├── api/          # FastAPI Routers
│   │   │   ├── core/         # Config & Security
│   │   │   ├── db/           # Database Session
│   │   │   ├── models/       # SQLAlchemy Models
│   │   │   ├── repositories/ # Repository Pattern (Data Access)
│   │   │   ├── schemas/      # Pydantic Models
│   │   │   └── services/     # Publishers & Renderers (Strategy Pattern)
│   │   └── pyproject.toml    # Python dependencies
│   └── web/                  # Next.js Frontend
│       ├── src/
│       │   ├── app/          # App Router Pages
│       │   ├── components/   # React Components
│       │   └── lib/          # Utilities
│       └── package.json      # Node dependencies
└── README.md
```

### AI Workflow (LangGraph)
1. **Research Agent**: Uses Tavily API to find news related to project keywords.
2. **Verification Agent**: Evaluates article relevance and quality.
3. **Query Refinement Agent**: Enhances search terms if verification fails.
4. **Content Generation Agent**: Converts verified articles into slides and image prompts.
5. **Slide Verification Agent**: Validates slide lengths and format.
6. **Publishing Agent**: Interfaces with Meta Graph API via the backend Publisher Strategy.

---

## Environment Variables

### Backend (`apps/api/.env`)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Async Postgres connection string (e.g. `postgresql+asyncpg://user:pass@localhost:5432/socialbypx`) |
| `REDIS_URL` | Redis URL for background jobs (e.g. `redis://localhost:6379/0`) |
| `OPENAI_API_KEY` | Your OpenAI API key for LLM agents |
| `TAVILY_API_KEY` | Your Tavily API key for web search |
| `ENCRYPTION_KEY` | 32-byte url-safe base64-encoded Fernet key (Generate via Python's `cryptography.fernet`) |

---

## Contributing

We welcome contributions from the community! Please read our [CONTRIBUTING.md](./CONTRIBUTING.md) for details on our code of conduct, development process, and how to submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
