from fastapi import APIRouter, HTTPException, status
from app.utils.logger import log   # ← FIXED: was get_logger("routes"), log is the exported object
from app.schemas.models import (
    RetrieveRequest, RetrieveResponse,
    GenerateSQLRequest, GenerateSQLResponse,
    ExecuteQueryRequest, ExecuteQueryResponse,
    BenchmarkResponse
)
from app.retrieval.retrieve_tables import retrieve_top_tables
from app.llm.generate_sql import get_sql
from app.validation.validate_sql import check_sql
from app.database.run_query import run_sql
from app.benchmark.benchmark import run_benchmark

router = APIRouter()


@router.post(
    "/retrieve",
    response_model=RetrieveResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve relevant database tables",
    description="Uses SentenceTransformers + FAISS to find the top 5 most relevant tables for a question."
)
def retrieve_tables_endpoint(payload: RetrieveRequest):
    log.info(f"/retrieve called | question='{payload.question}'")
    try:
        results = retrieve_top_tables(payload.question, top_k=5)
        return results
    except Exception as e:
        log.error(f"/retrieve failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Table retrieval failed: {str(e)}"
        )


@router.post(
    "/generate-sql",
    response_model=GenerateSQLResponse,
    status_code=status.HTTP_200_OK,
    summary="Translate a natural language question into SQL",
    description="Retrieves relevant schemas and prompts Groq Llama 3.3 to produce a validated SELECT query."
)
def generate_sql_endpoint(payload: GenerateSQLRequest):
    log.info(f"/generate-sql called | question='{payload.question}'")
    try:
        results = get_sql(payload.question, use_retrieved_context=payload.use_retrieved_context)

        if "error" in results:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"LLM generation failed: {results['error']}"
            )

        return results

    except HTTPException as he:
        raise he
    except Exception as e:
        log.error(f"/generate-sql failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SQL generation failed: {str(e)}"
        )


@router.post(
    "/execute",
    response_model=ExecuteQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a SELECT query on the database",
    description="Validates the query with sqlparse then runs it against the SQLite college database."
)
def execute_query_endpoint(payload: ExecuteQueryRequest):
    log.info(f"/execute called | sql='{payload.sql}'")

    validation = check_sql(payload.sql)
    if not validation["is_valid"]:
        log.warning(f"Unsafe SQL rejected: {validation['error']}")
        return ExecuteQueryResponse(
            columns=[],
            rows=[],
            row_count=0,
            error=validation["error"]
        )

    try:
        db_results = run_sql(payload.sql)
        return ExecuteQueryResponse(
            columns=db_results["columns"],
            rows=db_results["rows"],
            row_count=db_results["row_count"],
            error=db_results["error"]
        )
    except Exception as e:
        log.error(f"/execute crashed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database execution failed: {str(e)}"
        )


@router.post(
    "/benchmark",
    response_model=BenchmarkResponse,
    status_code=status.HTTP_200_OK,
    summary="Run the evaluation benchmark",
    description="Runs 20 sample questions through the full pipeline and reports recall, accuracy, and latency metrics."
)
def benchmark_endpoint():
    log.info("/benchmark called")
    try:
        results = run_benchmark()
        return results
    except Exception as e:
        log.error(f"/benchmark failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmark execution failed: {str(e)}"
        )