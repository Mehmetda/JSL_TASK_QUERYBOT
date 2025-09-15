# LLM Switching Guide

This guide explains the LLM selection options in the Streamlit UI.

## 🤖 LLM Options

### 1. 🔄 Auto Mode (Recommended)
- How it works: Uses OpenAI if internet is available, otherwise Local LLM
- Advantages: Automatic switching, best overall performance
- Usage: Default choice

### 2. 🔑 OpenAI Only
- How it works: Uses only OpenAI API
- Advantages: Highest quality, fast
- Requirements: Internet + OpenAI API key

### 3. 🏠 Local Only
- How it works: Uses only Local LLM
- Advantages: Works offline, data stays local
- Requirements: Sufficient RAM (8GB+)

## 🎯 Usage Scenarios

### Scenario 1: Normal Use
```
Choice: Auto Mode
State: Internet available + OpenAI key present
Result: Uses OpenAI
```

### Scenario 2: Internet Outage
```
Choice: Auto Mode
State: No internet
Result: Uses Local LLM
```

### Scenario 3: No OpenAI Key
```
Choice: Auto Mode
State: Internet available but no OpenAI key
Result: Uses Local LLM
```

### Scenario 4: Fully Offline
```
Choice: Local Only
State: No internet
Result: Uses Local LLM
```

## 🔧 Configuration

### OpenAI API Key
```bash
# Create .env
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### Local LLM Model (Ollama)
```env
# .env (recommended)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=tinyllama   # default in this project
# Alternatives (if pulled): gemma3:4b, llama3:8b, etc.
```

```python
# config.py reads from environment
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama")
```

## 📊 Status Indicators

### Sidebar shows:
- 🌐 **Internet**: Connectivity status
- 🔑 **OpenAI**: API availability
- 🎯 **Currently using**: Active LLM

### Metadata includes:
- **Selected Mode**: User-selected mode
- **Effective Mode**: Actually used mode
- **Token Usage**: LLM usage stats

## 🚀 Setup

```bash
# 1. Install packages
pip install -r requirements.txt

# 2. Download spaCy models
python -m spacy download xx_ent_wiki_sm
python -m spacy download en_core_web_sm

# 3. Test
python test_local_llm.py

# 4. Run UI
streamlit run app/ui/streamlit_app.py
```

## 🐛 Troubleshooting

### OpenAI Unavailable
- ✅ Check internet connectivity
- ✅ Check your OpenAI API key
- ✅ Use Auto mode (falls back to Local)

### Local LLM Not Loading
- ✅ Ensure sufficient RAM (8GB+)
- ✅ Use a smaller model (DialoGPT-small)
- ✅ Disable GPU usage (USE_GPU=False in config.py)

### Performance Issues
- ✅ Use a smaller model for Local mode
- ✅ Use GPU if available
- ✅ Prefer Auto mode for best balance

## 💡 Tips

1. First run: Start with Auto mode
2. Offline: Use Local Only mode
3. Best quality: Use OpenAI Only
4. Security: Use Local Only
5. Performance: Use Auto mode

## 📈 Performance Comparison

| Mode | Speed | Quality | Security | Cost |
|------|-------|---------|----------|------|
| Auto | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| OpenAI | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| Local | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
