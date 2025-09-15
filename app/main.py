"""
Main pipeline for QueryBot
"""
import re
import logging
import time
from app.agents.sql_agent import generate_sql_with_agent
from app.tools.sql_executor import execute_sql
from app.tools.answer_summarizer import summarize_results, LAST_SUMMARY_USAGE
from app.services.provider import get_provider
from app.tools.sql_validator import validate_sql
from app.agents.system_prompt import get_relevant_schema_snippets
from app.llm.llm_manager import get_llm_manager
from app.security import TableAllowlistManager
from app.models.query_models import QueryResponse, QueryRequest, QueryMetadata, ValidationInfo, DatabaseInfo, PerformanceInfo, LLMInfo, SecurityInfo, QueryType, ComplexityLevel, ValidationStatus, LLMMode
from app.utils.logger import get_structured_logger, log_query_pipeline_start, log_query_pipeline_end
from app.utils.tracing import get_trace_manager, with_trace, add_trace_metadata
from app.history.query_history import save_query_to_history


# Basic logging configuration
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

# Get structured logger
structured_logger = get_structured_logger()

# Initialize LLM on module load
logger.info("Initializing LLM manager...")
try:
    llm_manager = get_llm_manager()
    logger.info("LLM manager initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize LLM manager: {e}")
    logger.info("Continuing with fallback model...")


def _normalize_sql_table_names(sql: str) -> str:
    """Case-insensitive normalization of common table-name typos/aliases."""
    if not sql:
        return sql
    import re
    mappings = {
        "json_admissionss": "json_admissions",
        "json_admission": "json_admissions",
        "json_patient": "json_patients",
        "json_provider": "json_providers",
        "json_transfer": "json_transfers",
        "json_careunit": "json_careunits",
        "json_labs": "json_lab",
        "json_diagnosis": "json_diagnoses",
        "json_insurances": "json_insurance",
        # generic aliases
        "admissions": "json_admissions",
        "patients": "json_patients",
        "providers": "json_providers",
        "transfers": "json_transfers",
        "careunits": "json_careunits",
        "diagnoses": "json_diagnoses",
        "insurance": "json_insurance",
        "lab": "json_lab",
    }
    normalized = sql
    for wrong, right in mappings.items():
        pattern = r"\b" + re.escape(wrong) + r"\b"
        normalized = re.sub(pattern, right, normalized, flags=re.IGNORECASE)
    return normalized

def extract_tables_from_sql(sql: str) -> list:
    """Extract table names from SQL query"""
    if not sql:
        return []
    
    # Simple regex to find table names after FROM and JOIN
    tables = re.findall(r'(?:FROM|JOIN)\s+(\w+)', sql.upper())
    return list(set(tables))  # Remove duplicates


def classify_query_type(sql: str) -> str:
    """Classify the type of SQL query"""
    if not sql:
        return "UNKNOWN"
    
    sql_upper = sql.upper().strip()
    
    if sql_upper.startswith('SELECT COUNT'):
        return "COUNT_QUERY"
    elif sql_upper.startswith('SELECT') and 'GROUP BY' in sql_upper:
        return "GROUP_BY_QUERY"
    elif sql_upper.startswith('SELECT') and 'ORDER BY' in sql_upper:
        return "ORDERED_QUERY"
    elif sql_upper.startswith('SELECT') and 'JOIN' in sql_upper:
        return "JOIN_QUERY"
    elif sql_upper.startswith('SELECT'):
        return "SELECT_QUERY"
    else:
        return "OTHER"


def assess_query_complexity(sql: str) -> str:
    """Assess the complexity of the SQL query"""
    if not sql:
        return "UNKNOWN"
    
    sql_upper = sql.upper()
    complexity_score = 0
    
    # Count complexity indicators
    if 'JOIN' in sql_upper:
        complexity_score += 2
    if 'GROUP BY' in sql_upper:
        complexity_score += 1
    if 'ORDER BY' in sql_upper:
        complexity_score += 1
    if 'HAVING' in sql_upper:
        complexity_score += 1
    if 'WHERE' in sql_upper:
        complexity_score += 1
    if 'COUNT' in sql_upper:
        complexity_score += 1
    
    if complexity_score <= 1:
        return "SIMPLE"
    elif complexity_score <= 3:
        return "MEDIUM"
    else:
        return "COMPLEX"


def run_query_pipeline(question: str, request: QueryRequest = None) -> QueryResponse:
    """Run the complete query pipeline with enhanced security and type safety"""
    
    # Start structured logging and tracing
    trace_id = log_query_pipeline_start(question, getattr(request, 'user_id', None) if request else None)
    start_time = time.perf_counter()
    
    # Start trace
    trace_manager = get_trace_manager()
    trace_id = trace_manager.start_trace(
        trace_id=trace_id,
        user_id=getattr(request, 'user_id', None) if request else None,
        request_id=getattr(request, 'request_id', None) if request else None,
        metadata={"question": question, "component": "query_pipeline"}
    )
    
    # Initialize request if not provided
    if request is None:
        request = QueryRequest(question=question)
    
    provider = get_provider()
    # Initialize security manager
    security_manager = provider.get_security_manager()
    
    # Check for data modification intent FIRST
    modification_intent = [
        'sil', 'silmek', 'silme', 'güncelle', 'güncellemek', 'ekle', 'eklemek',
        'değiştir', 'değiştirmek', 'kaldır', 'kaldırmak', 'temizle', 'temizlemek'
    ]
    
    question_lower = question.lower()
    for intent in modification_intent:
        if intent in question_lower:
            logger.warning(f"Data modification intent '{intent}' detected, blocking operation")
            structured_logger.log_security_event(trace_id, "data_modification_blocked", {
                "intent": intent,
                "question": question
            })
            
            execution_time_ms = int((time.perf_counter() - start_time) * 1000)
            log_query_pipeline_end(trace_id, False, execution_time_ms, 0, "Data modification blocked")
            
            blocked_response = QueryResponse(
                sql="SELECT 'DATA MODIFICATION NOT ALLOWED' AS message",
                answer="This operation is not allowed. You can only perform data reading operations.",
                meta=QueryMetadata(
                    results={},
                    validation=ValidationInfo(
                        is_valid=True,
                        error=None,
                        sql_safety=ValidationStatus.BLOCKED_DATA_MODIFICATION,
                        retried=False
                    ),
                    database=DatabaseInfo(
                        query_type=QueryType.OTHER,
                        complexity=ComplexityLevel.SIMPLE
                    ),
                    performance=PerformanceInfo(
                        rows_returned=0,
                        columns_returned=0,
                        data_size_estimate="0 characters",
                        execution_ms=execution_time_ms
                    ),
                    security=security_manager.get_security_info()
                ),
                success=False,
                error="Data modification blocked",
                trace_id=trace_id
            )
            return blocked_response.model_dump()
    
    # Get database connection
    conn = provider.get_connection()
    
    try:
        # Generate SQL using new agent system
        logger.info("Generating SQL for question using SQL Agent")
        sql_start_time = time.perf_counter()
        
        # Use new SQL agent
        sql_response = generate_sql_with_agent(
            question=question,
            language="en",
            max_tokens=300,
            temperature=0.1,
            user_id=request.user_id if request else None,
            session_id=request.session_id if request else None
        )
        
        sql_generation_time = int((time.perf_counter() - sql_start_time) * 1000)
        
        # Extract SQL and usage from agent response
        if sql_response.success:
            sql = sql_response.result.get("sql", "")
            sql_usage = sql_response.result.get("usage", {})
        else:
            sql = ""
            sql_usage = {}
            logger.error(f"SQL generation failed: {sql_response.error}")
        
        # Normalize SQL immediately after generation (defensive)
        sql = _normalize_sql_table_names(sql)

        # Log SQL generation
        structured_logger.log_sql_generation(
            trace_id, question, sql, "local", 
            sql_usage.get("total_tokens", 0), sql_generation_time
        )

        # Hard guard: Only SELECT statements are allowed
        if not sql.strip().lower().startswith("select"):
            logger.warning("Non-SELECT SQL detected; blocking operation")
            execution_time_ms = int((time.perf_counter() - start_time) * 1000)
            blocked_response = QueryResponse(
                sql=sql,
                answer="Access denied: Only SELECT queries are allowed.",
                meta=QueryMetadata(
                    results={},
                    validation=ValidationInfo(
                        is_valid=False,
                        error="Only SELECT queries are allowed.",
                        sql_safety=ValidationStatus.FAILED,
                        retried=False
                    ),
                    database=DatabaseInfo(
                        query_type=QueryType.OTHER,
                        complexity=ComplexityLevel.SIMPLE
                    ),
                    performance=PerformanceInfo(
                        rows_returned=0,
                        columns_returned=0,
                        data_size_estimate="0 characters",
                        execution_ms=0
                    ),
                    security=security_manager.get_security_info()
                ),
                success=False,
                error="Only SELECT queries are allowed."
            )
            return blocked_response.model_dump()
        
        # Final defensive normalization for common table typos before validation
        typo_normalizations = {
            "json_admissionss": "json_admissions",
            "json_admission": "json_admissions",
            "json_patientss": "json_patients",
            "json_patient": "json_patients",
            "json_provider": "json_providers",
            "json_transfer": "json_transfers",
            "json_careunit": "json_careunits",
            "json_labs": "json_lab",
            "json_diagnosis": "json_diagnoses",
            "json_insurances": "json_insurance",
            # common column typos
            "json_insurance": "insurance",
        }
        for wrong, right in typo_normalizations.items():
            sql = sql.replace(wrong, right)

        # Validate SQL against allowlist
        logger.info("Validating SQL against allowlist")
        is_valid, error_message, security_info = security_manager.validate_query(sql)
        
        if not is_valid:
            logger.warning(f"SQL query blocked by allowlist: {error_message}")
            blocked_by_allowlist = QueryResponse(
                sql=sql,
                answer=f"Access denied: {error_message}",
                meta=QueryMetadata(
                    results={},
                    validation=ValidationInfo(
                        is_valid=False,
                        error=error_message,
                        sql_safety=ValidationStatus.FAILED,
                        retried=False
                    ),
                    database=DatabaseInfo(
                        query_type=QueryType.OTHER,
                        complexity=ComplexityLevel.SIMPLE
                    ),
                    performance=PerformanceInfo(
                        rows_returned=0,
                        columns_returned=0,
                        data_size_estimate="0 characters",
                        execution_ms=0
                    ),
                    security=security_info
                ),
                success=False,
                error=error_message
            )
            return blocked_by_allowlist.model_dump()
        
        # Validate SQL syntax
        logger.info("Validating generated SQL syntax")
        validation_result = validate_sql(conn, sql)
        retried = False
        if not validation_result["is_valid"]:
            # One-time retry with guidance appended to the question
            logger.warning("SQL validation failed, attempting one-time retry with guidance")
            retry_question = (
                question
                + "\nNote: Generate a single SELECT statement, do not use semicolons, use appropriate column and table names from the current schema."
                + f"\nValidator error: {validation_result.get('error', '')}"
            )
            retry_response = generate_sql_with_agent(
                question=retry_question,
                language="en",
                max_tokens=300,
                temperature=0.1,
                user_id=request.user_id if request else None,
                session_id=request.session_id if request else None
            )
            if retry_response.success:
                sql = _normalize_sql_table_names(retry_response.result.get("sql", ""))
            else:
                sql = ""
            validation_result = validate_sql(conn, sql)
            retried = True
            if not validation_result["is_valid"]:
                logger.error("Retry validation also failed")
                failed_validation_response = QueryResponse(
                    sql=sql,
                    answer="",
                    meta=QueryMetadata(
                        results={},
                        validation=ValidationInfo(
                            is_valid=False,
                            error=validation_result.get("error"),
                            sql_safety=ValidationStatus.FAILED,
                            retried=retried
                        ),
                        database=DatabaseInfo(
                            query_type=QueryType.OTHER,
                            complexity=ComplexityLevel.SIMPLE
                        ),
                        performance=PerformanceInfo(
                            rows_returned=0,
                            columns_returned=0,
                            data_size_estimate="0 characters",
                            execution_ms=0
                        ),
                        security=security_info
                    ),
                    success=False,
                    error="SQL validation failed"
                )
                return failed_validation_response.model_dump()
        
        # Execute SQL with timing (normalize one last time before exec)
        sql = _normalize_sql_table_names(sql)
        logger.info("Executing SQL")
        t0 = time.perf_counter()
        rows, meta = execute_sql(conn, sql)
        exec_ms = int((time.perf_counter() - t0) * 1000)
        
        # Log SQL execution
        structured_logger.log_sql_execution(trace_id, sql, exec_ms, len(rows))
        
        # Summarize results
        logger.info("Summarizing results")
        summary_start_time = time.perf_counter()
        answer = summarize_results(question, rows)
        summary_time = int((time.perf_counter() - summary_start_time) * 1000)
        
        # Log answer summarization
        structured_logger.log_answer_summarization(
            trace_id, question, len(rows), 
            LAST_SUMMARY_USAGE.get("total_tokens", 0), summary_time
        )
        
        # Prepare enhanced metadata (prefer provider for metadata-filtered retrieval in future)
        relevant_schema = provider.get_relevant_schema(conn, question, top_k=3)
        
        # Create response
        response = QueryResponse(
            sql=sql,
            answer=answer,
            meta=QueryMetadata(
                results={
                    "row_count": len(rows),
                    "columns": meta.get("columns", [])
                },
                validation=ValidationInfo(
                    is_valid=validation_result["is_valid"],
                    error=validation_result.get("error"),
                    sql_safety=ValidationStatus.PASSED if validation_result["is_valid"] else ValidationStatus.FAILED,
                    retried=retried
                ),
                database=DatabaseInfo(
                    tables_used=extract_tables_from_sql(sql),
                    query_type=QueryType(classify_query_type(sql)),
                    complexity=ComplexityLevel(assess_query_complexity(sql)),
                    relevant_schema=relevant_schema
                ),
                performance=PerformanceInfo(
                    rows_returned=len(rows),
                    columns_returned=len(meta.get("columns", [])),
                    data_size_estimate=f"{len(str(rows))} characters",
                    execution_ms=exec_ms,
                    tokens={
                        "sql_generation": sql_usage.get("total_tokens", 0),
                        "answer_summarization": LAST_SUMMARY_USAGE.get("total_tokens", 0)
                    }
                ),
                security=security_info,
                trace_id=request.trace_id
            ),
            success=True
        )
        
        # Log successful completion
        execution_time_ms = int((time.perf_counter() - start_time) * 1000)
        log_query_pipeline_end(trace_id, True, execution_time_ms, len(rows))
        
        # End trace
        trace_summary = trace_manager.end_trace(trace_id)
        if trace_summary:
            add_trace_metadata("final_execution_time_ms", execution_time_ms)
            add_trace_metadata("final_rows_returned", len(rows))
            add_trace_metadata("success", True)
        
        # Save to query history
        try:
            save_query_to_history(response, request)
        except Exception as e:
            logger.warning(f"Failed to save query to history: {e}")
        
        logger.info("Pipeline completed successfully")
        return response.model_dump()
        
    except Exception as e:
        logger.exception("Pipeline failed with an unhandled exception")
        structured_logger.log_error(trace_id, e, {"question": question})
        
        execution_time_ms = int((time.perf_counter() - start_time) * 1000)
        log_query_pipeline_end(trace_id, False, execution_time_ms, 0, str(e))
        
        # End trace with error
        trace_summary = trace_manager.end_trace(trace_id)
        if trace_summary:
            add_trace_metadata("final_execution_time_ms", execution_time_ms)
            add_trace_metadata("final_rows_returned", 0)
            add_trace_metadata("success", False)
            add_trace_metadata("error", str(e))
        
        error_response = QueryResponse(
            sql="",
            answer=f"An error occurred: {str(e)}",
            meta=QueryMetadata(
                results={},
                validation=ValidationInfo(
                    is_valid=False,
                    error=str(e),
                    sql_safety=ValidationStatus.FAILED,
                    retried=False
                ),
                database=DatabaseInfo(
                    query_type=QueryType.OTHER,
                    complexity=ComplexityLevel.SIMPLE
                ),
                performance=PerformanceInfo(
                    rows_returned=0,
                    columns_returned=0,
                    data_size_estimate="0 characters",
                    execution_ms=execution_time_ms
                ),
                security=security_manager.get_security_info()
            ),
            success=False,
            error=str(e),
            trace_id=trace_id
        )
        return error_response.model_dump()
    finally:
        conn.close()
