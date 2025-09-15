# Local LLM Setup Guide

This guide explains how to run the project with a local LLM (e.g., Llama 7B) instead of OpenAI.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Model Configuration

Configure the model in `config.py`:

```python
# Default model (small & fast)
LLM_MODEL_NAME = "microsoft/DialoGPT-medium"

# For Llama 7B (larger, better quality)
# LLM_MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"
```

### 3. Test the Application

```bash
python test_local_llm.py
```

### 4. Run the App

```bash
streamlit run app/ui/streamlit_app.py
```

## 📋 Supported Models

### Small Models (Fast, low RAM)
- `microsoft/DialoGPT-small` (varsayılan fallback)
- `microsoft/DialoGPT-medium`

### Llama Models (Better performance, more RAM)
- `meta-llama/Llama-2-7b-chat-hf` (önerilen)
- `meta-llama/Llama-2-7b-hf`

## ⚙️ Configuration Options

In `config.py` you may set:

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

### Minimum
- **RAM**: 8GB (for DialoGPT)
- **Disk**: 2GB free
- **Python**: 3.8+

### Recommended (Llama 7B)
- **RAM**: 16GB+
- **GPU**: NVIDIA GPU (8GB+ VRAM)
- **Disk**: 10GB+

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

| Model | Boyut | RAM | Hız | Kalite |
|-------|-------|-----|-----|--------|
| DialoGPT-small | ~300MB | 2GB | Çok Hızlı | Orta |
| DialoGPT-medium | ~1.5GB | 4GB | Hızlı | İyi |
| Llama-2-7b | ~13GB | 16GB | Yavaş | Çok İyi |

## 🔄 Switching from OpenAI

Project can run fully local:
- ✅ No OpenAI API key
- ✅ No internet required
- ✅ Data stays on device
- ✅ No API cost

## 📝 Notes

- First run downloads the model (requires internet)
- Models are cached for faster subsequent runs
- Uses GPU automatically if available
- Works on CPU too (slower)
