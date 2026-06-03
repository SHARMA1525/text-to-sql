import time
from app.utils.logger import get_logger
from app.retrieval.retrieve_tables import retrieve_top_tables
from app.llm.generate_sql import get_sql
from app.database.run_query import run_sql

logger = get_logger("benchmark")

BENCHMARK_QUESTIONS = [
    {
        "question": "Which departments have more than 100 students?",
        "ground_truth": ["departments", "students"]
    },
    {
        "question": "List all students enrolled in the Computer Science department.",
        "ground_truth": ["students", "departments"]
    },
    {
        "question": "What is the average grade of students in course 101?",
        "ground_truth": ["enrollments"]
    },
    {
        "question": "Show all professors working in the Science building.",
        "ground_truth": ["professors", "departments"]
    },
    {
        "question": "Find the total number of students in the university.",
        "ground_truth": ["students"]
    },
    {
        "question": "Which classrooms have a capacity greater than 50?",
        "ground_truth": ["classrooms"]
    },
    {
        "question": "List courses offered by the Mathematics department.",
        "ground_truth": ["courses", "departments"]
    },
    {
        "question": "Get the email address of professor John Doe.",
        "ground_truth": ["professors"]
    },
    {
        "question": "Who is the manager of the Biology department?",
        "ground_truth": ["departments"]
    },
    {
        "question": "List the names of all students who enrolled in Fall 2023.",
        "ground_truth": ["students"]
    },
    {
        "question": "What is the highest capacity room in building A?",
        "ground_truth": ["classrooms"]
    },
    {
        "question": "Find all students who got an A grade.",
        "ground_truth": ["enrollments", "students"]
    },
    {
        "question": "List the total credits of all courses.",
        "ground_truth": ["courses"]
    },
    {
        "question": "Which courses have 4 credits?",
        "ground_truth": ["courses"]
    },
    {
        "question": "Get the name and room capacity of all classrooms in the Engineering building.",
        "ground_truth": ["classrooms"]
    },
    {
        "question": "How many professors are in the History department?",
        "ground_truth": ["professors", "departments"]
    },
    {
        "question": "List student names and their course titles.",
        "ground_truth": ["students", "enrollments", "courses"]
    },
    {
        "question": "Find the building where student Alice's department is located.",
        "ground_truth": ["students", "departments"]
    },
    {
        "question": "Show all enrollment details for student ID 5.",
        "ground_truth": ["enrollments"]
    },
    {
        "question": "Which courses are offered in the building 'Main Hall'?",
        "ground_truth": ["courses", "departments"]
    }
]

def run_benchmark() -> dict:
    logger.info("Starting Text-to-SQL pipeline benchmark...")
    
    total_recall = 0.0
    parsing_successes = 0
    generation_successes = 0
    total_latency_ms = 0.0
    details = []
    
    for idx, item in enumerate(BENCHMARK_QUESTIONS):
        question = item["question"]
        gt_tables = item["ground_truth"]
        
        logger.info(f"Running benchmark item {idx+1}/20: '{question}'")
        
        start_time = time.time()
        
        retrieval_res = retrieve_top_tables(question, top_k=5)
        retrieved_set = set(retrieval_res["retrieved_tables"])
        gt_set = set(gt_tables)
        
        intersection = gt_set.intersection(retrieved_set)
        recall_at_5 = len(intersection) / len(gt_set)
        total_recall += recall_at_5
        
        generation_res = get_sql(question, use_retrieved_context=True)
        generated_sql = generation_res["sql"]
        is_valid_syntax = generation_res["is_valid_syntax"]
        
        if is_valid_syntax:
            parsing_successes += 1
            
        execution_success = False
        execution_error = None
        
        if generated_sql and is_valid_syntax:
            db_res = run_sql(generated_sql)
            if db_res["error"] is None:
                execution_success = True
                generation_successes += 1
            else:
                execution_error = db_res["error"]
        else:
            execution_error = "SQL generation or syntax parsing failed"
            
        latency_ms = (time.time() - start_time) * 1000
        total_latency_ms += latency_ms
        
        details.append({
            "question": question,
            "ground_truth_tables": gt_tables,
            "retrieved_tables": list(retrieval_res["retrieved_tables"]),
            "retrieval_recall_at_5": round(recall_at_5, 2),
            "generated_sql": generated_sql,
            "parsing_success": is_valid_syntax,
            "execution_success": execution_success,
            "execution_error": execution_error,
            "latency_ms": round(latency_ms, 2)
        })
        
    num_queries = len(BENCHMARK_QUESTIONS)
    
    metrics = {
        "retrieval_recall_at_5": round(total_recall / num_queries, 4),
        "parsing_success_rate": round(parsing_successes / num_queries, 4),
        "sql_generation_success_rate": round(generation_successes / num_queries, 4),
        "average_latency_ms": round(total_latency_ms / num_queries, 2),
        "details": details
    }
    
    logger.info("Benchmark complete. Aggregated metrics:")
    logger.info(f" -> Recall@5: {metrics['retrieval_recall_at_5']}")
    logger.info(f" -> Parsing Success Rate: {metrics['parsing_success_rate']}")
    logger.info(f" -> SQL Gen Success Rate: {metrics['sql_generation_success_rate']}")
    logger.info(f" -> Avg Latency: {metrics['average_latency_ms']} ms")
    
    return metrics

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    from app.retrieval.retrieve_tables import initialize_retrieval_system
    from app.database.run_query import init_database
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.abspath(os.path.join(current_dir, "..", "schemas", "schema.json"))
    db_path = os.path.abspath(os.path.join(current_dir, "..", "..", "data.db"))
    
    init_database(db_path)
    initialize_retrieval_system(schema_path)
    run_benchmark()
