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
    app_interface = await app.mongodb["app"].find_one()
    api_is_active = app_interface.get("api_is_active")

    data = await app.mongodb["data"].find().to_list(length=None)
    context = dict(request=request,  data=data, api_is_active=api_is_active)
    response = templates.TemplateResponse("index.html", context)
    return response


@app.post("/add-data", response_class=JSONResponse)
async def add_data(request: Request):
    app_interface = await app.mongodb["app"].find_one()

    api_is_active = app_interface.get("api_is_active")
    if not api_is_active:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "API is not active"})

    try:
        data = await request.json()
        temperature = data.get("temperature")
        humidity = data.get("humidity")

        if not temperature or not humidity:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "Temperature and humidity are required"})

        # Insert the data into the 'data' collection
        await request.app.mongodb["data"].insert_one(
            dict(
                temperature=temperature, 
                humidity=humidity, 
                timestamp=datetime.now(timezone.utc)
            )
        )
        # Return a success response
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Data added successfully"})
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(e)})


@app.post("/update-app-interface", response_class=JSONResponse)
async def update_app_interface(request: Request):
    json_data = await request.json()
    api_is_active = json_data.get("api_is_active")

    app_interface = await app.mongodb["app"].find_one()
    await app.mongodb["app"].update_one({"_id": app_interface["_id"]}, {"$set": {"api_is_active": api_is_active}})

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "App interface updated successfully"})


@app.get("/get-data", response_class=JSONResponse)
async def get_data(request: Request):
    app_interface = await app.mongodb["app"].find_one()
    if app_interface is None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "App interface not found"})

    data = await app.mongodb["data"].find().to_list(length=None)
    return JSONResponse(status_code=status.HTTP_200_OK, content={"data": data})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
