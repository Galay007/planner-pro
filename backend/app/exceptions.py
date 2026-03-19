from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

logger = logging.getLogger(__name__)

def register_db_exception_handlers(app: FastAPI):

    @app.exception_handler(SQLAlchemyError)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Database error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"{exc}"
        )
    
    @app.exception_handler(ValueError)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.warning(f"Validation error for connection: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"{exc}"
        )

