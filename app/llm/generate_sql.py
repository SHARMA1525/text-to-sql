import os
import re
from groq import Groq
from app.utils.logger import log   # ← FIXED: was get_logger("llm")
from app.retrieval.retrieve_tables import retrieve_top_tables, get_global_schema
from app.validation.validate_sql import check_sql


def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        log.error("GROQ_API_KEY is not defined in environment variables.")
        raise ValueError("GROQ_API_KEY environment variable is missing. Please define it in your .env file.")
    return Groq(api_key=api_key)


def clean_sql(raw_sql: str) -> str:
    cleaned = raw_sql.strip()

    if "```" in cleaned:
        match = re.search(r"```(?:sql)?\n(.*?)\n```", cleaned, re.DOTALL | re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()
        else:
            cleaned = cleaned.replace("```sql", "").replace("```", "").strip()

    cleaned = cleaned.strip("`").strip()
    cleaned = cleaned.rstrip(";").strip()

    return cleaned


def build_prompt(question: str, retrieved_tables: list, schema_data: dict) -> str:
    schema_context = []

    for table_name in retrieved_tables:
        if table_name in schema_data:
            table_info = schema_data[table_name]
            cols = table_info["columns"]

            columns_str = "\n".join(
                [f"    - {col_name}: {col_desc}" for col_name, col_desc in cols.items()]
            )

            schema_context.append(
                f"Table: {table_name}\n"
                f"Description: {table_info['description']}\n"
                f"Columns:\n{columns_str}"
            )

    joined_schemas = "\n\n".join(schema_context)

    table_list = ", ".join(retrieved_tables)

    prompt = f"""You are a helpful database expert assistant.
Your task is to translate the user's natural language question into a single valid SQLite SQL query.

Available tables (you MUST use ALL relevant tables from this list): {table_list}

Database schema:
{joined_schemas}

Instructions:
1. ONLY return the raw SQL query — no explanations, no markdown, no extra text.
2. The query MUST be a safe, read-only SELECT statement.
3. You MUST join tables using the foreign key relationships shown in the schema.
4. If the question involves counting or grouping, use GROUP BY with aggregate functions.
5. If the question says "excluding" or "except", use WHERE with a filter condition.
6. Use only standard SQLite syntax — no PostgreSQL-specific functions.
7. Use DISTINCT when a student or record could appear multiple times due to joins.

User Question: {question}
SQL Query:"""

    return prompt


def get_sql(question: str, use_retrieved_context: bool = True) -> dict:
    log.info(f"Generating SQL for: '{question}' | use_context={use_retrieved_context}")

    schema_data = get_global_schema()

    if use_retrieved_context:
        retrieval_res = retrieve_top_tables(question, top_k=5)
        retrieved_tables = retrieval_res["retrieved_tables"]
        scores = retrieval_res["scores"]
        base_confidence = round(float(sum(scores) / len(scores)), 2) if scores else 0.85
    else:
        retrieved_tables = list(schema_data.keys())
        base_confidence = 0.80

    prompt = build_prompt(question, retrieved_tables, schema_data)
    log.info(f"Prompt built. Length: {len(prompt)} chars")

    try:
        client = get_groq_client()
        log.info("Calling Groq llama-3.3-70b-versatile...")

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,   
            max_tokens=512,     
        )

        raw_response = response.choices[0].message.content
        log.info(f"Raw LLM response: {raw_response}")

        sql_query = clean_sql(raw_response)
        log.info(f"Cleaned SQL: {sql_query}")

        validation_res = check_sql(sql_query)
        is_valid = validation_res["is_valid"]
        parsing_errors = validation_res.get("error", None)

        confidence = round(base_confidence, 2) if is_valid else 0.0

        return {
            "sql": sql_query,
            "retrieved_tables": retrieved_tables,
            "is_valid_syntax": is_valid,
            "parsing_errors": parsing_errors,       
            "confidence": confidence,
            "prompt_used": prompt,             
        }

    except Exception as e:
        log.error(f"LLM call failed: {str(e)}")
        return {
            "sql": "",
            "retrieved_tables": retrieved_tables,
            "is_valid_syntax": False,
            "parsing_errors": str(e),              
            "confidence": 0.0,
            "prompt_used": prompt,                 
            "error": str(e),
        }