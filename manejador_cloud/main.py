from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from routers import cloud_accounts, resources, metrics, health, projects
from middleware.rate_limit import RateLimitMiddleware
from cache import redis_client

# Basic logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(title="Manejador Cloud API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(RateLimitMiddleware, redis_client=redis_client)
app.include_router(projects.router)         
app.include_router(cloud_accounts.router)  
app.include_router(resources.router)
app.include_router(metrics.router)
app.include_router(health.router)
