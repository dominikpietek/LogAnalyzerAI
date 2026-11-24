from typing import Annotated

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from stackscout.api.schemas import FileContent
from stackscout.domain.code_location import CodeLocation
from stackscout.domain.search import SearchResult
from stackscout.ports.workspace import Workspace


def create_app(workspace: Workspace) -> FastAPI:
    app = FastAPI(title="stackscout")

    @app.get("/files")
    def list_files(ext: Annotated[list[str] | None, Query()] = None) -> list[str]:
        extensions = frozenset(e.lower() for e in ext) if ext else None
        return [str(path) for path in workspace.list_files(extensions=extensions)]

    @app.get("/file", response_model=FileContent)
    def read_file(
        path: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> FileContent:
        location = CodeLocation(file_path=path, start_line=start_line, end_line=end_line)
        return FileContent(location=location, text=workspace.read_file(location))

    @app.get("/search", response_model=SearchResult)
    def search(
        q: str,
        regex: bool = False,
        max_results: int = Query(default=50, ge=1, le=500),
    ) -> SearchResult:
        return workspace.search(q, regex=regex, max_results=max_results)

    @app.exception_handler(Exception)
    async def workspace_error(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": type(exc).__name__, "detail": str(exc)},
        )

    @app.exception_handler(ValidationError)
    async def validation_error(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": "ValidationError", "detail": str(exc)},
        )

    return app
