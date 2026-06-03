import os
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.utils.logger import get_logger
from app.database.run_query import init_database
from app.retrieval.retrieve_tables import initialize_retrieval_system
from app.api.routes import router as api_router

load_dotenv()

logger = get_logger("main")

app = FastAPI(
    title="Enterprise Text-to-SQL FastAPI Service",
    description="A beginner-friendly Enterprise Text-to-SQL API using FastAPI, SQLite, SentenceTransformers, and Groq.",
    version="1.0.0",
    docs_url="/docs",     
    redoc_url="/redoc"    
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

app.include_router(api_router)

@app.on_event("startup")
def startup_event():
    logger.info("Starting up Text-to-SQL service...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(current_dir, "schemas", "schema.json")
    db_path = os.path.abspath(os.path.join(current_dir, "..", "data.db"))
    
    logger.info(f"Resolved absolute paths:\n - Schema: {schema_path}\n - Database: {db_path}")
    
    try:
        init_database(db_path)
    except Exception as e:
        logger.error(f"Failed to seed SQLite database: {str(e)}")
        raise e
        
    try:
        initialize_retrieval_system(schema_path)
    except Exception as e:
        logger.error(f"Failed to build FAISS retrieval index: {str(e)}")
        raise e
        
    logger.info("FastAPI service startup check completed successfully.")

@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system error on request {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred in the service. Please check application logs for details."
        }
    )

@app.get("/", status_code=status.HTTP_200_OK, summary="Service Health and Welcome")
def root_endpoint():
    return {
        "status": "online",
        "service": "Enterprise Text-to-SQL FastAPI Service",
        "documentation": "/docs"
    }
