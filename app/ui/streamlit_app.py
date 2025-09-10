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
    # John Snow LABS Logo
    try:
        st.image("app/assets/images.png", width=150)
    except:
        st.markdown("### 🏥 John Snow LABS")
    
    st.markdown("### Choose LLM Type")
    llm_type = st.selectbox("LLM Type", ["gpt-4o", "gpt-4", "gpt-3.5-turbo"], index=0, label_visibility="collapsed")
    
    st.markdown("### RAG Settings")
    st.markdown("**Select Top K values**")
    top_k = st.slider("Top K", 1, 50, 5, label_visibility="collapsed")
    
    st.markdown("**Select Score Threshold**")
    score_threshold = st.slider("Score Threshold", 0.10, 1.00, 0.30, label_visibility="collapsed")

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
            
            # Results Information
            st.markdown("### 📈 Results Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rows Returned", meta.get("results", {}).get("row_count", 0))
            with col2:
                st.metric("Columns Returned", meta.get("results", {}).get("columns_returned", 0))
            with col3:
                st.metric("Data Size", meta.get("performance", {}).get("data_size_estimate", "N/A"))
            
            # Validation Status
            st.markdown("### ✅ Validation Status")
            validation = meta.get("validation", {})
            if validation.get("is_valid", False):
                st.success(f"✅ SQL Safety: {validation.get('sql_safety', 'N/A')}")
            else:
                st.error(f"❌ SQL Safety: {validation.get('sql_safety', 'N/A')}")
                if validation.get("error"):
                    st.error(f"Error: {validation['error']}")
            
            # Tables Used
            tables = meta.get("database", {}).get("tables_used", [])
            if tables:
                st.markdown("### 🗄️ Tables Used")
                st.write(", ".join(tables))
            
            # Sample Data
            sample_data = meta.get("results", {}).get("sample_data", [])
            if sample_data:
                st.markdown("### 📋 Sample Data (First 3 rows)")
                st.write(sample_data)
            
            # Full metadata (collapsible)
            with st.expander("🔧 Raw Metadata"):
                st.json(meta)
            
    except Exception as e:
        st.markdown("### Error")
        st.error(f"An error occurred: {str(e)}")
