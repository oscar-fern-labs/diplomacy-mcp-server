from fastapi import FastAPI
from .server import router
from .db import close_pool
from .static_mount import mount_static

app = FastAPI(title="Diplomacy MCP Server")
app.include_router(router)
mount_static(app)

@app.on_event("shutdown")
async def shutdown():
    await close_pool()
