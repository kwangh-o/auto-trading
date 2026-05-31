from fastapi import FastAPI

from api.routers import symbols

app = FastAPI(title="Auto Trade API")

app.include_router(symbols.router)
