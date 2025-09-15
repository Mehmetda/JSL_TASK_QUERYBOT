# Local LLM Setup Guide

This guide explains how to run the project with a local Llama 7B model instead of OpenAI.

## 🚀 Quick Start

### 1. Install Required Packages

```bash
pip install -r requirements.txt
```

### 2. Model Configuration

Configure model settings in `config.py`:

```python
# Default model (small and fast)
LLM_MODEL_NAME = "microsoft/DialoGPT-medium"

# For Llama 7B (larger, better quality)
# LLM_MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"
```

### 3. Test the Application

```bash
python test_local_llm.py
```

### 4. Run the Application

```bash
streamlit run app/ui/streamlit_app.py
```

## 📋 Supported Models

### Small Models (Fast, low RAM)
- `microsoft/DialoGPT-small` (varsayılan fallback)
- `microsoft/DialoGPT-medium`

### Llama Models (Better quality, higher RAM)
- `meta-llama/Llama-2-7b-chat-hf` (önerilen)
- `meta-llama/Llama-2-7b-hf`

## ⚙️ Configuration Options

You can adjust the following settings in `config.py`:

```python
# LLM Model
LLM_MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"

# Embedding Model (for semantic search)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# GPU usage
USE_GPU = True  # use GPU if available

# Database path
DATABASE_PATH = "app/db/demo.sqlite"
```

## 🔧 System Requirements

### Minimum Requirements
- **RAM**: 8GB (DialoGPT için)
- **Disk**: 2GB boş alan
- **Python**: 3.8+

### Recommended (for Llama 7B)
- **RAM**: 16GB+
- **GPU**: NVIDIA GPU (8GB+ VRAM)
- **Disk**: 10GB+ boş alan

## 🐛 Troubleshooting

### Model Load Error
```bash
# Clear cache
rm -rf ~/.cache/huggingface/

# Retry
python test_local_llm.py
```

### GPU Usage
```python
# Disable GPU in config.py
USE_GPU = False
```

### Out of Memory
Use a smaller model:
```python
LLM_MODEL_NAME = "microsoft/DialoGPT-small"
```

## 📊 Performance Comparison

| Model | Size | RAM | Speed | Quality |
|-------|------|-----|-------|---------|
| DialoGPT-small | ~300MB | 2GB | Very Fast | Medium |
| DialoGPT-medium | ~1.5GB | 4GB | Fast | Good |
| Llama-2-7b | ~13GB | 16GB | Slow | Very Good |

## 🔄 Switching from OpenAI

The project can operate fully locally:
- ✅ No OpenAI API key required
- ✅ No internet required
- ✅ Data security (local processing)
- ✅ Zero usage cost

## 📝 Notes

- The model will be downloaded on first run (requires internet)
- Models are cached for faster subsequent runs
- GPU is used automatically if available
- CPU-only works but will be slower
