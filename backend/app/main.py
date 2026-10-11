from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy import text
from app.config import settings
from app.database.connection import engine
from app.routes.api import router
from app.routes.reports import router as reports_router

DISCLAIMER='CareTrack is an educational demonstration project using fictional data. It is not intended for real clinical use.'
app=FastAPI(title='CareTrack API',description=DISCLAIMER,version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_methods=['GET','POST','PUT','DELETE','OPTIONS'],allow_headers=['Authorization','Content-Type'])
app.include_router(router)
app.include_router(reports_router)

@app.exception_handler(IntegrityError)
async def integrity_error(request:Request,exc:IntegrityError):
    code=exc.orig.args[0] if exc.orig.args else None
    message={1062:'A record with these unique details already exists',1451:'This record is referenced by history and cannot be deleted',1452:'A referenced record does not exist',3819:'A database constraint rejected these values',1048:'A required value is missing'}.get(code,'These values conflict with database integrity rules')
    return JSONResponse(status_code=409,content={'detail':message})

@app.exception_handler(DBAPIError)
async def database_error(request:Request,exc:DBAPIError):
    code=exc.orig.args[0] if exc.orig.args else None
    if code==1644: return JSONResponse(status_code=409,content={'detail':str(exc.orig.args[1])})
    if code in (1205,1213): return JSONResponse(status_code=409,content={'detail':'Another operation changed these records. Please retry'})
    return JSONResponse(status_code=503,content={'detail':'The database is unavailable. Please try again shortly'})

@app.get('/api/health',tags=['System'])
def health():
    with engine.connect() as conn: conn.execute(text('SELECT 1'))
    return {'status':'ok','database':'mysql','disclaimer':DISCLAIMER}
