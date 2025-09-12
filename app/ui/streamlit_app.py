"""
Streamlit UI for Medical QueryBot
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import datetime
from app.main import run_query_pipeline
from app.llm.llm_manager import get_llm_manager
from app.utils import check_internet_connection, check_openai_availability
from app.history.query_history import get_history_manager
from app.models.query_models import QueryRequest

st.set_page_config(page_title="Medical QueryBot", layout="wide")

# Sidebar
with st.sidebar:
    # John Snow LABS Logo - Enhanced
    try:
        # Use absolute path and better image display
        logo_path = os.path.join(project_root, "app", "assets", "images.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=200, use_container_width=False)
        else:
            # Fallback with styled text
            st.markdown("""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       border-radius: 10px; margin-bottom: 20px;">
                <h2 style="color: white; margin: 0; font-family: 'Arial', sans-serif; font-weight: bold;">
                    🧬 John Snow LABS
                </h2>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        # Enhanced fallback
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0; font-family: 'Arial', sans-serif; font-weight: bold;">
                🧬 John Snow LABS
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    # LLM Selection Section
    st.markdown("---")
    st.markdown("### 🤖 LLM Selection")
    
    # Initialize LLM manager
    if 'llm_manager' not in st.session_state:
        st.session_state.llm_manager = get_llm_manager()
    
    llm_manager = st.session_state.llm_manager
    
    # Check connectivity
    internet_available = check_internet_connection()
    openai_available = check_openai_availability() if internet_available else False
    local_available = llm_manager.local_client is not None

    # If internet is down, make sure we don't stick to OpenAI-only mode
    try:
        if not internet_available and llm_manager.get_current_mode() == "openai":
            llm_manager.set_mode("local")
    except Exception:
        pass
    
    # Display connectivity status
    col1, col2 = st.columns(2)
    with col1:
        if internet_available:
            st.success("🌐 Internet: Connected")
        else:
            st.error("🌐 Internet: Disconnected")
    
    with col2:
        if openai_available:
            st.success("🔑 OpenAI: Available")
        else:
            st.error("🔑 OpenAI: Unavailable")
    
    # LLM Mode Selection
    available_modes = llm_manager.get_available_modes()
    
    if "auto" in available_modes:
        mode_options = ["auto", "openai", "local"]
        mode_labels = {
            "auto": "🔄 Auto (Internet → Local)",
            "openai": "🔑 OpenAI Only",
            "local": "🏠 Local Only"
        }
    else:
        mode_options = available_modes
        mode_labels = {
            "openai": "🔑 OpenAI",
            "local": "🏠 Local"
        }
    
    selected_mode = st.radio(
        "Choose LLM Mode:",
        options=mode_options,
        format_func=lambda x: mode_labels.get(x, x),
        index=0 if "auto" in mode_options else 0
    )
    
    # Update LLM mode
    if selected_mode != llm_manager.get_current_mode():
        llm_manager.set_mode(selected_mode)
        st.rerun()
    
    # Optional manual refresh for status (helps reflect network toggles)
    st.button("Refresh status", key="refresh_status")

    # Display current effective mode
    effective_mode = llm_manager.get_effective_mode()
    if effective_mode == "openai":
        st.info("🎯 Currently using: OpenAI")
    elif effective_mode == "local":
        st.info("🎯 Currently using: Local LLM")
    
    # (Removed LLM Status Details expander per request)
    
    # (Moved Query History & Statistics below main submit area)

# Main content
st.markdown("<h1 style='text-align:center;margin-top:0;'>Medical QueryBot</h1>", unsafe_allow_html=True)

# Query section
st.markdown("### Ask a Question")
question = st.text_input(label="Question", placeholder="Please enter your medical question", label_visibility="collapsed")

if st.button("Submit", type="primary") and question.strip():
    try:
        result = run_query_pipeline(question)
        
        # Display complete JSON response
        st.markdown("### JSON Response")
        st.json(result)
        
        # Download Response (JSON)
        st.markdown("### Download Response")
        try:
            import json as _json
            json_bytes = _json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button(
                label="Download JSON",
                data=json_bytes,
                file_name=f"query_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        except Exception as e:
            st.warning(f"Could not create JSON: {e}")
        
        # Optional: Display individual components for better readability
        with st.expander("📋 Individual Components"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**SQL Query:**")
                st.code(result["sql"], language="sql")
            
            with col2:
                st.markdown("**Answer:**")
                if result["answer"]:
                    st.success(result["answer"])
                else:
                    st.warning("No answer generated")
        
        # Enhanced metadata display
        with st.expander("📊 Detailed Metadata"):
            meta = result["meta"]
            
            # Query Information
            st.markdown("### 🔍 Query Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Query Type", meta.get("database", {}).get("query_type", "N/A"))
            with col2:
                st.metric("Complexity", meta.get("database", {}).get("complexity", "N/A"))
            with col3:
                st.metric("Tables Used", len(meta.get("database", {}).get("tables_used", [])))
            # Relevant schema snippet
            relevant = meta.get("database", {}).get("relevant_schema")
            if relevant:
                st.markdown("### 🔎 Relevant Schema (Auto‑selected)")
                st.code(relevant)
            
            # Results Information
            st.markdown("### 📈 Results Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows Returned", meta.get("results", {}).get("row_count", 0))
            with col2:
                st.metric("Columns Returned", meta.get("results", {}).get("columns_returned", 0))
            with col3:
                perf = meta.get("performance", {})
                st.metric("Exec Time (ms)", perf.get("execution_ms", "N/A"))
                st.caption(f"Data Size: {perf.get('data_size_estimate', 'N/A')}")

            # LLM Information
            st.markdown("### 🤖 LLM Information")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Selected Mode", llm_manager.get_current_mode().title())
            with col2:
                st.metric("Effective Mode", llm_manager.get_effective_mode().title())
            
            # Tokens (if available)
            tokens = meta.get("performance", {}).get("tokens", {})
            if tokens:
                st.markdown("### 🧮 Token Usage")
                tc1, tc2, tc3 = st.columns(3)
                with tc1:
                    st.metric("SQL Gen Tokens", tokens.get("sql_generation", 0))
                with tc2:
                    st.metric("Answer Tokens", tokens.get("answer_summarization", 0))
                with tc3:
                    total = int(tokens.get("sql_generation", 0)) + int(tokens.get("answer_summarization", 0))
                    st.metric("Total Tokens", total)
            
            # Validation Status
            st.markdown("### ✅ Validation Status")
            validation = meta.get("validation", {})
            if validation.get("is_valid", False):
                st.success(f"✅ SQL Safety: {validation.get('sql_safety', 'N/A')}")
            else:
                st.error(f"❌ SQL Safety: {validation.get('sql_safety', 'N/A')}")
                if validation.get("error"):
                    st.error(f"Error: {validation['error']}")
            if validation.get("retried"):
                st.info("🔁 Sorgu ilk denemede geçmedi, hata bağlamıyla otomatik yeniden denendi.")
            
            # Tables Used
            tables = meta.get("database", {}).get("tables_used", [])
            if tables:
                st.markdown("### 🗄️ Tables Used")
                st.write(", ".join(tables))
            
            
            # Full metadata (collapsible)
            with st.expander("🔧 Raw Metadata"):
                st.json(meta)
        
        # Query History Section (moved below results)
        st.markdown("---")
        st.markdown("### 📚 Query History")
        
        history_manager = get_history_manager()
        
        # History controls
        col1, col2 = st.columns(2)
        with col1:
            show_history = st.checkbox("Show Query History", value=False)
        with col2:
            history_limit = st.selectbox("History Limit", [10, 25, 50, 100], index=1)
        
        if show_history:
            # Get query history
            history_entries = history_manager.get_query_history(limit=history_limit)
            
            if history_entries:
                st.markdown(f"**Last {len(history_entries)} queries:**")
                
                for i, entry in enumerate(history_entries):
                    with st.expander(f"Query {entry.id} - {entry.question[:50]}..."):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown(f"**Question:** {entry.question}")
                            st.markdown(f"**SQL:** `{entry.sql}`")
                        
                        with col2:
                            st.markdown(f"**Answer:** {entry.answer}")
                            st.markdown(f"**Success:** {'✅' if entry.success else '❌'}")
                        
                        with col3:
                            st.markdown(f"**Time:** {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S') if entry.timestamp else 'N/A'}")
                            st.markdown(f"**Execution:** {entry.execution_time_ms}ms")
                            st.markdown(f"**Rows:** {entry.rows_returned}")
                            st.markdown(f"**LLM:** {entry.llm_mode}")
                        
                        if entry.error:
                            st.error(f"**Error:** {entry.error}")
            else:
                st.info("No query history found")
        
        # Query Statistics (moved below results)
        with st.expander("📈 Query Statistics"):
            stats = history_manager.get_query_stats(days=30)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Queries", stats["total_queries"])
            
            with col2:
                st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
            
            with col3:
                st.metric("Avg Execution Time", f"{stats['avg_execution_time_ms']:.1f}ms")
            
            with col4:
                st.metric("Total Tokens", f"{stats['total_tokens_used']:,}")
            
            # LLM Mode Distribution
            if stats["llm_mode_stats"]:
                st.markdown("**LLM Mode Distribution:**")
                for mode, count in stats["llm_mode_stats"].items():
                    st.write(f"- {mode}: {count} queries")
            
            # Daily Stats Chart
            if stats["daily_stats"]:
                st.markdown("**Daily Query Count:**")
                import pandas as pd
                daily_df = pd.DataFrame(list(stats["daily_stats"].items()), columns=["Date", "Queries"])
                daily_df["Date"] = pd.to_datetime(daily_df["Date"])
                st.line_chart(daily_df.set_index("Date"))
            
            # Export History
            st.markdown("**Export History:**")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Export JSON"):
                    try:
                        json_export = history_manager.export_history(format="json")
                        st.download_button(
                            label="Download JSON",
                            data=json_export,
                            file_name=f"query_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    except Exception as e:
                        st.error(f"Export failed: {e}")
            
            with col2:
                if st.button("📊 Export CSV"):
                    try:
                        csv_export = history_manager.export_history(format="csv")
                        st.download_button(
                            label="Download CSV",
                            data=csv_export,
                            file_name=f"query_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    except Exception as e:
                        st.error(f"Export failed: {e}")
            
    except Exception as e:
        st.markdown("### Error")
        st.error(f"An error occurred: {str(e)}")
