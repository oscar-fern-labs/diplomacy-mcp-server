from fastapi import FastAPI
from .server import router
from .db import close_pool

app = FastAPI(title="Diplomacy MCP Server")
app.include_router(router)

@app.on_event("shutdown")
async def shutdown():
    await close_pool()
