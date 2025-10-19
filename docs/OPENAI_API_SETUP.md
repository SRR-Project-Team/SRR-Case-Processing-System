# OpenAI API Setup Guide

## Overview

This guide explains how to configure and use OpenAI API for the SRR Case Processing System. The system now supports both OpenAI API and Volcengine (Doubao) API, with OpenAI as the default provider.

## Prerequisites

- Python 3.8 or higher
- OpenAI API key (get one from [OpenAI Platform](https://platform.openai.com/))

## Installation

### 1. Install OpenAI SDK

```bash
pip install openai==1.12.0
```

Or install all requirements:

```bash
pip install -r config/requirements.txt
```

## Configuration

### 1. Set Environment Variable

#### On macOS/Linux:

```bash
# Add to ~/.zshrc or ~/.bashrc
export OPENAI_API_KEY="your-openai-api-key-here"

# Reload shell configuration
source ~/.zshrc  # or source ~/.bashrc
```

#### On Windows:

```cmd
# Set environment variable
setx OPENAI_API_KEY "your-openai-api-key-here"
```

Or set it in PowerShell:

```powershell
$env:OPENAI_API_KEY="your-openai-api-key-here"
```

### 2. Verify Configuration

```bash
# Check if environment variable is set
echo $OPENAI_API_KEY  # macOS/Linux
echo %OPENAI_API_KEY%  # Windows CMD
```

## API Provider Selection

The system supports multiple LLM providers. You can switch between them using the `LLM_PROVIDER` environment variable.

### Using OpenAI API (Default)

```bash
export LLM_PROVIDER="openai"
export OPENAI_API_KEY="your-openai-api-key"
```

### Using Volcengine API (Currently Disabled)

```bash
export LLM_PROVIDER="volcengine"
export ARK_API_KEY="your-volcengine-api-key"
```

**Note**: Volcengine API is currently disabled but kept in the code for future use.

## Configuration Files

### config/settings.py

```python
# LLM API Configuration
# OpenAI API (currently in use)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Volcengine API (kept for future use, currently disabled)
ARK_API_KEY = os.getenv("ARK_API_KEY")

# Default to OpenAI API
LLM_API_KEY = OPENAI_API_KEY
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
```

## Usage

### 1. Initialize LLM Service

The service is automatically initialized when the application starts:

```python
from config.settings import LLM_API_KEY, LLM_PROVIDER
from src.services.llm_service import init_llm_service

init_llm_service(LLM_API_KEY, LLM_PROVIDER)
```

### 2. Generate Summary

```python
from src.services.llm_service import get_llm_service

llm_service = get_llm_service()
summary = llm_service.summarize_text(text, max_length=600)
```

## OpenAI Models

The system uses the following OpenAI models:

- **GPT-4o-mini**: Default model for cost efficiency
  - Fast response time
  - Lower cost per token
  - Good quality for summarization tasks

### Model Configuration

You can modify the model in `src/services/llm_service.py`:

```python
response = self.client.chat.completions.create(
    model="gpt-4o-mini",  # Change this to use different models
    messages=[{"role": "user", "content": message}],
    max_tokens=300,
    temperature=0.3
)
```

### Available Models

- `gpt-4o-mini` - Fast and cost-effective (recommended)
- `gpt-4o` - More capable but more expensive
- `gpt-4-turbo` - High quality but slower
- `gpt-3.5-turbo` - Legacy model

## API Parameters

### Temperature

Controls randomness in responses:
- `0.0` - Deterministic, focused
- `0.3` - Balanced (default)
- `1.0` - Creative, diverse

### Max Tokens

Limits response length:
- `300` - Short summary (default)
- `600` - Medium summary
- `1000` - Long summary

## Troubleshooting

### Issue: "API key not set"

**Solution**: Make sure the environment variable is set correctly:

```bash
# Check if variable is set
echo $OPENAI_API_KEY

# If empty, set it again
export OPENAI_API_KEY="your-api-key"
```

### Issue: "Module not found: openai"

**Solution**: Install the OpenAI SDK:

```bash
pip install openai==1.12.0
```

### Issue: "Rate limit exceeded"

**Solution**: 
- Check your OpenAI account usage limits
- Implement request throttling
- Consider upgrading your OpenAI plan

### Issue: "Invalid API key"

**Solution**:
- Verify your API key is correct
- Check if your OpenAI account is active
- Ensure you have sufficient credits

## Cost Optimization

### Tips to Reduce Costs

1. **Use GPT-4o-mini**: Much cheaper than GPT-4
2. **Limit text length**: Process only necessary content
3. **Cache results**: Store summaries to avoid regeneration
4. **Batch requests**: Process multiple files together

### Estimated Costs

- **GPT-4o-mini**: ~$0.0001 per summary
- **GPT-4o**: ~$0.001 per summary
- **GPT-4-turbo**: ~$0.002 per summary

## Monitoring

### Check API Usage

1. Log in to [OpenAI Platform](https://platform.openai.com/)
2. Go to "Usage" section
3. Monitor your API usage and costs

### Enable Logging

The system logs all API calls. Check logs for:

```python
✅ OpenAI LLM client initialized successfully
✅ OpenAI AI summary generated successfully
```

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for configuration
3. **Rotate API keys** regularly
4. **Monitor usage** for unusual activity
5. **Set usage limits** in OpenAI dashboard

## Fallback Behavior

If OpenAI API is unavailable or fails:

1. System logs warning message
2. Returns `None` for summary
3. Continues processing without AI summary
4. Uses fallback summarization methods

## Migration from Volcengine API

If you're migrating from Volcengine API:

1. Set `OPENAI_API_KEY` environment variable
2. Keep `LLM_PROVIDER="openai"` (default)
3. Restart the application
4. Volcengine code remains in the system for future use

## Support

For issues related to:

- **OpenAI API**: Contact [OpenAI Support](https://help.openai.com/)
- **System Integration**: Check project documentation
- **Configuration**: Review this guide

## Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [OpenAI Pricing](https://openai.com/pricing)
- [OpenAI Best Practices](https://platform.openai.com/docs/guides/production-best-practices)

---

**Last Updated**: 2025-10-19
**Version**: 1.0

