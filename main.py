import pathlib
from datetime import datetime, timezone
import passlib
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient
from bson import Decimal128
from contextlib import asynccontextmanager
from config import MONGO_DB

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
    app.mongodb_client = AsyncIOMotorClient(MONGO_DB)
    app.mongodb = app.mongodb_client["cc-iot"]
    yield

    # Disconnect from Atlas at application shutdown
    app.mongodb_client.close()


app = FastAPI(lifespan=lifespan)  # TODO (openapi_url=None) or (docs_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    data = await app.mongodb["data"].find().to_list(length=None)
    context = dict(request=request, data=data)
    response = templates.TemplateResponse("index.html", context)
    return response


@app.post("/add-data", response_class=JSONResponse)
async def add_data(request: Request):
    app_interface = await app.mongodb["app"].find_one()

    if app_interface.get("api_shutdown_at") and app_interface.get("api_shutdown_at") < datetime.now(timezone.utc):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "API is shutdown"})

    try:
        data = await request.json()
        # Insert the data into the 'data' collection
        await request.app.mongodb["data"].insert_one(data)
        # Return a success response
        return JSONResponse(status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(e)})


# @app.post("/add-data", response_class=JSONResponse)
# async def add_data(request: Request):
#     data = await request.json()
#     # Add a timestamp to the data
#     data_with_timestamp = {
#         "temperature": data.get("temperature"),
#         "humidity": data.get("humidity"),
#         "timestamp": datetime.now(timezone.utc)
#     }
#     # Insert the data into the 'data' collection
#     result = await request.app.mongodb["data"].insert_one(data_with_timestamp)
#     # Return a success response with the inserted ID
#     return JSONResponse(status_code=status.HTTP_200_OK, content={"inserted_id": str(result.inserted_id)})


@app.get("/get-data", response_class=JSONResponse)
async def get_data(request: Request):
    app_interface = await app.mongodb["app"].find_one()

    if app_interface is None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "App interface not found"})

    data = await app.mongodb["data"].find_one()

    return JSONResponse(status_code=status.HTTP_200_OK, content={"app": app_interface, "data": data})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
