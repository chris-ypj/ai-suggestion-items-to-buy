# author : chris-jyp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from router import airouter


def create_app() -> FastAPI:
    # create FastAPI app instance
    app = FastAPI(
        title="AI Suggestion",
        description="Generates AI suggestions based on the provided data of users consumed items",
        version="1.0.0"
    )

    # set CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # allow all origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # include routers
    app.include_router(airouter.router, prefix="/api")
    return app
# create FastAPI app instance
app = create_app()
@app.get("/health", summary="Health Check", description="Returns the health status of the service")
async def health_check():
    return {"status": "ok", "message": "Service is healthy"}
@app.get("/", summary="redirect to Health Check", description="Returns the health status of the service")
async def health_check():
    return {"status": "ok", "message": "Service is healthy"}