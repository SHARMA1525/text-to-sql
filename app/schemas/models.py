from pydantic import BaseModel, Field
from typing import List, Optional

class RetrieveRequest(BaseModel):
    question: str = Field(
        ..., 
        min_length=1, 
        max_length=500, 
        description="The natural language question to find relevant database tables for."
    )

class RetrieveResponse(BaseModel):
    retrieved_tables: List[str] = Field(..., description="List of top table names matching the question.")
    scores: List[float] = Field(..., description="Similarity scores corresponding to the retrieved tables.")

class GenerateSQLRequest(BaseModel):
    question: str = Field(
        ..., 
        min_length=1, 
        max_length=500, 
        description="The natural language question to translate into SQL."
    )
    use_retrieved_context: bool = Field(
        default=True, 
        description="If True, performs semantic table retrieval. Otherwise, uses all tables."
    )

class GenerateSQLResponse(BaseModel):
    sql: str = Field(..., description="The generated SQLite SQL query.")
    retrieved_tables: List[str] = Field(..., description="The tables selected for prompt context.")
    is_valid_syntax: bool = Field(..., description="Whether the SQL is syntactically safe (SELECT only).")
    confidence: float = Field(..., description="Estimated confidence score for the generated query.")

class ExecuteQueryRequest(BaseModel):
    sql: str = Field(..., description="The SELECT SQL query to execute.")

class ExecuteQueryResponse(BaseModel):
    columns: List[str] = Field(default=[], description="List of column names returned by the query.")
    rows: List[List] = Field(default=[], description="Query rows returned by the database.")
    row_count: int = Field(default=0, description="Total number of records returned.")
    error: Optional[str] = Field(default=None, description="Database error message if execution failed.")

class BenchmarkResponse(BaseModel):
    retrieval_recall_at_5: float = Field(..., description="Recall at 5 for table retrieval.")
    sql_generation_success_rate: float = Field(..., description="Successful execution rate of generated SQL.")
    parsing_success_rate: float = Field(..., description="Safety and parse validation success rate.")
    average_latency_ms: float = Field(..., description="Average complete generation pipeline latency in milliseconds.")
    details: Optional[List[dict]] = Field(default=None, description="Optional per-question run breakdown.")
