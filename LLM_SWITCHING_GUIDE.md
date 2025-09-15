# LLM Switching Guide

This guide explains the LLM selection options in the Streamlit UI.

## 🤖 LLM Options

### 1. 🔄 Auto Mode (Recommended)
- **How it works**: Uses OpenAI if online, otherwise Local LLM
- **Pros**: Automatic fallback, best overall
- **Usage**: Default option

### 2. 🔑 OpenAI Only
- **How it works**: Uses only OpenAI API
- **Pros**: Best quality, fast
- **Requires**: Internet + OpenAI API key

### 3. 🏠 Local Only
- **How it works**: Uses only local LLM
- **Pros**: Works offline, data stays local
- **Requires**: Enough RAM (8GB+)

## 🎯 Scenarios

### Scenario 1: Normal Use
```
Choice: Auto Mode
Status: Internet + OpenAI key available
Result: Uses OpenAI
```

### Scenario 2: Internet Outage
```
Choice: Auto Mode
Status: Offline
Result: Uses Local LLM
```

### Scenario 3: No OpenAI Key
```
Choice: Auto Mode
Status: Internet but no OpenAI key
Result: Uses Local LLM
```

### Scenario 4: Work Offline
```
Choice: Local Only
Status: Offline
Result: Uses Local LLM
```

## 🔧 Configuration

### OpenAI API Key
```bash
# Create a .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### Local LLM Model
```python
# In config.py
LLM_MODEL_NAME = "microsoft/DialoGPT-medium"  # Small model
# LLM_MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"  # Large model
```

## 📊 Status Indicators

### In Sidebar:
- 🌐 **Internet**: Connectivity
- 🔑 **OpenAI**: API availability
- 🎯 **Currently using**: Active LLM

### In Metadata:
- **Selected Mode**: User selected mode
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

# 4. Run
streamlit run app/ui/streamlit_app.py
```

## 🐛 Troubleshooting

### OpenAI Unavailable
- ✅ Check internet connectivity
- ✅ Check OpenAI API key
- ✅ Use Auto mode (falls back to local)

### Local LLM Not Loading
- ✅ Ensure enough RAM (8GB+)
- ✅ Choose a smaller model (DialoGPT-small)
- ✅ Disable GPU (USE_GPU=False in config.py)

### Performance Issues
- ✅ Use a smaller model in Local mode
- ✅ Use GPU if available
- ✅ Prefer Auto mode for best overall

## 💡 Tips

1. **First time**: Start with Auto mode
2. **Offline**: Use Local Only
3. **Best quality**: Use OpenAI Only
4. **Security**: Use Local Only
5. **Performance**: Use Auto mode

## 📈 Performance Comparison

| Mode | Speed | Quality | Security | Cost |
|------|-------|---------|----------|------|
| Auto | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| OpenAI | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| Local | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
