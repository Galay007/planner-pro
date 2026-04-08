from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import (SQLAlchemyError, IntegrityError, OperationalError, 
    ProgrammingError, DataError, InternalError)
import logging
from typing import Any

logger = logging.getLogger(__name__)

def register_db_exception_handlers(app: FastAPI):

    @app.exception_handler(SQLAlchemyError)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"SQLAlchemyError error: {exc}", exc_info=True)
        
        # if isinstance(exc, IntegrityError):
        #     status_code = status.HTTP_409_CONFLICT
        # elif isinstance(exc, DataError):
        #     status_code = status.HTTP_422_UNPROCESSABLE_ENTITY  
        # elif isinstance(exc, OperationalError):
        #     status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        # elif isinstance(exc, (ProgrammingError, InternalError)):
        #     status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        # else:
        #     status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # raise HTTPException(
        #     status_code=status_code,
        #     detail=f"{exc}"
        # )
    
    @app.exception_handler(ValueError)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.warning(f"Validation error: {exc}", exc_info=True)
        
        # error_str = str(exc).lower()
        
        # if any(x in error_str for x in ['invalid literal', 'could not convert', 'int()', 'float()']):
        #     status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        #     detail = "Неверный формат числа"
        # elif any(x in error_str for x in ['email', 'invalid email', '@']):
        #     status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        #     detail = "Неверный email"
        # elif 'uuid' in error_str or 'guid' in error_str:
        #     status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        #     detail = "Неверный UUID"
        # elif any(x in error_str for x in ['date', 'time', 'datetime']):
        #     status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        #     detail = "Неверный формат даты"
        # elif len(error_str) > 100:
        #     status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        #     detail = "Ошибка валидации данных"
        # else:
        #     status_code = status.HTTP_400_BAD_REQUEST
        # detail = f"Неверные параметры: {exc}"
        # raise HTTPException(
        #     status_code=status_code, 
        #     detail=detail
        # )

    @app.exception_handler(IntegrityError)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.warning(f"Integrity violation: {exc.orig}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"{exc.orig}"
        )

