from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import chat, compress, config_api, files, sessions, tokens
from graph.agent import AgentManager
from scheduler import ScheduledTaskRunner
from tools.skills_scanner import scan_skills


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
agent_manager = AgentManager()
scan_skills(BASE_DIR)
agent_manager.initialize(BASE_DIR)
task_runner = ScheduledTaskRunner(agent_manager, agent_manager.task_store)


@asynccontextmanager
async def lifespan(app: FastAPI):
    agent_manager.memory_indexer.rebuild_index()
    await task_runner.start()
    yield
    await task_runner.stop()


app = FastAPI(title="Mini OpenClaw", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.build_router(agent_manager), prefix="/api")
app.include_router(sessions.build_router(agent_manager), prefix="/api")
app.include_router(files.build_router(BASE_DIR, agent_manager.memory_indexer), prefix="/api")
app.include_router(tokens.build_router(BASE_DIR, agent_manager.session_manager, agent_manager.config_store), prefix="/api")
app.include_router(compress.build_router(agent_manager), prefix="/api")
app.include_router(config_api.build_router(agent_manager.config_store), prefix="/api")


@app.get("/health")
async def health():
    return {"ok": True}
