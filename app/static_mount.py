from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

def mount_static(app: FastAPI):
    app.mount("/ui", StaticFiles(directory="web", html=True), name="ui")
