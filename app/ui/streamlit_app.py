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
from app.main import run_query_pipeline

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
            
    except Exception as e:
        st.markdown("### Error")
        st.error(f"An error occurred: {str(e)}")
