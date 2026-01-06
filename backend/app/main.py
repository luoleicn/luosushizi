"""FastAPI app entrypoint."""


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_config_path, load_config
from app.api.router import router as api_router


def create_app() -> FastAPI:
    config_path = get_config_path()
    settings = load_config(config_path)

    app = FastAPI(title=settings.app.name)
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=(
            settings.cors.dev_origins
            if settings.cors.env == "dev"
            else settings.cors.prod_origins
        ),
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()
