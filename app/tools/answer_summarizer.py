"""
Answer summarization module using LLM
"""
import os
import json
from typing import List, Tuple, Any
from app.llm.llm_manager import get_llm_manager

# Use LLM manager for flexible LLM selection
llm_manager = get_llm_manager()

# Expose last usage for metrics
LAST_SUMMARY_USAGE = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def format_data_for_llm(rows: List[Tuple[Any, ...]]) -> str:
    """Format SQL results for LLM processing"""
    if not rows:
        return "No data found."
    
    # Convert rows to readable format
    formatted_data = []
    for i, row in enumerate(rows[:10]):  # Limit to first 10 rows
        if len(row) == 1 and isinstance(row[0], str):
            try:
                # Try to parse JSON data
                data = json.loads(row[0])
                formatted_data.append(f"Record {i+1}: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                formatted_data.append(f"Record {i+1}: {row[0]}")
        else:
            formatted_data.append(f"Record {i+1}: {row}")
    
    return "\n\n".join(formatted_data)


def summarize_results_with_llm(question: str, rows: List[Tuple[Any, ...]]) -> str:
    """Use LLM to generate meaningful answer from SQL results"""
    if not rows:
        return "No data found in the database for this question."
    
    try:
        # Format data for LLM
        formatted_data = format_data_for_llm(rows)
        
        # Create prompt for LLM with better formatting
        prompt = f"""You are a medical database expert. Provide a clear and meaningful English answer based on the database results for the user's question.

User Question: {question}

Database Results:
{formatted_data}

Total {len(rows)} records found.

Please provide the answer in this format:
1. **Main Answer**: Direct answer to the user's question
2. **Details**: Important numerical data and statistics
3. **Summary**: General assessment

Answer:"""

        # Call LLM
        response = llm_manager.generate_response(
            messages=[
                {"role": "system", "content": "You are a medical database expert. You analyze database results and provide meaningful answers to users in English."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        # capture usage
        try:
            usage = response.get("usage", {})
            if usage:
                LAST_SUMMARY_USAGE.update({
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                })
        except Exception:
            pass

        content = response.get("content", "").strip()
        
        # If content is empty, provide a fallback answer
        if not content:
            return f"Found {len(rows)} records in the database. Could not get detailed analysis from LLM."
        
        return content
        
    except Exception as e:
        print(f"LLM Error in summarization: {e}")
        return f"Found {len(rows)} records in the database. (LLM error: {str(e)})"


def summarize_results(question: str, rows: List[Tuple[Any, ...]]) -> str:
    """Main function to summarize results using LLM"""
    return summarize_results_with_llm(question, rows)
