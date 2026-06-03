import sqlparse
from app.utils.logger import get_logger

logger = get_logger("validation")

def is_safe(sql: str) -> bool:
    if not sql or not sql.strip():
        logger.warning("Empty SQL query provided for safety validation.")
        return False
    
    cleaned_sql = sql.strip().rstrip(";").strip()
    
    try:
        parsed_statements = sqlparse.parse(cleaned_sql)
        if not parsed_statements:
            logger.warning("Failed to parse SQL statement.")
            return False
        
        forbidden_keywords = {
            "DROP", "DELETE", "UPDATE", "INSERT", 
            "ALTER", "TRUNCATE", "CREATE", "REPLACE"
        }
        
        for stmt in parsed_statements:
            stmt_type = stmt.get_type()
            if stmt_type != "SELECT":
                logger.warning(f"Rejected unsafe statement type: {stmt_type}")
                return False
                
            for token in stmt.flatten():
                if (token.ttype in sqlparse.tokens.Keyword or 
                    token.ttype in sqlparse.tokens.DML or 
                    token.ttype in sqlparse.tokens.DDL):
                    
                    value_upper = token.value.upper()
                    if value_upper in forbidden_keywords:
                        logger.warning(f"Rejected statement due to forbidden keyword: {value_upper}")
                        return False
                        
        return True
        
    except Exception as e:
        logger.error(f"Error occurred during sqlparse safety checking: {str(e)}")
        return False

def check_sql(sql: str) -> dict:
    logger.info(f"Checking query safety: '{sql}'")
    
    is_valid = is_safe(sql)
    
    if is_valid:
        logger.info("SQL validation passed.")
        return {
            "is_valid": True,
            "error": None
        }
    else:
        logger.warning("SQL validation failed.")
        return {
            "is_valid": False,
            "error": "SQL validation failed: Only SELECT statements are allowed. Modifiers like DROP, DELETE, UPDATE, INSERT, ALTER, or TRUNCATE are prohibited."
        }
