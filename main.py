import pathlib
from datetime import datetime, timezone
import passlib
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient
from bson import Decimal128
from contextlib import asynccontextmanager
# from config import MONGO_DB

import uvicorn
from bson import ObjectId
from fastapi import FastAPI, Request, Depends, status, Response, Cookie, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import BackgroundTasks


BASE_DIR = pathlib.Path(__file__).resolve().parent  # app
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    pass
    # # Connect to Atlas at application startup
    # app.mongodb_client = AsyncIOMotorClient(MONGO_DB)
    # app.mongodb = app.mongodb_client['ai_links']
    yield

    pass
    # # Disconnect from Atlas at application shutdown
    # app.mongodb_client.close()


app = FastAPI(lifespan=lifespan)  # TODO (openapi_url=None) or (docs_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    context = dict(request=request, data="Hello, World! 123")
    response = templates.TemplateResponse("index.html", context)

    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
