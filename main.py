from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import init_db
from routes import auth, documents, process, ppt, youtube, profile

app = FastAPI(title="LearnFlux API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()

# ── Routers ───────────────────────────────────────────────
app.include_router(auth.router,       prefix="/auth",      tags=["Auth"])
app.include_router(documents.router,  prefix="/documents", tags=["Documents"])
app.include_router(process.router,    prefix="/documents", tags=["AI Process"])
app.include_router(ppt.router,        prefix="/ppt",       tags=["PPT"])
app.include_router(youtube.router,    prefix="/youtube",   tags=["YouTube"])
app.include_router(profile.router,    prefix="",           tags=["Profile"])

@app.get("/")
async def root():
    return {"message": "LearnFlux API is running!"}