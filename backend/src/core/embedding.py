from typing import List
import os
import requests

EMBEDDING_MODEL = "ollama"
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")  # 或 "mxbai-embed-large"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# Batch size for /api/embed; override with env EMBEDDING_BATCH_SIZE (see config/settings.py)
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "16"))

def embed_text(text: str) -> List[float]:
    """Single-text embed; for many chunks use embed_texts() to avoid N requests."""
    if EMBEDDING_MODEL == "ollama":
        return _embed_text_ollama(text)
    else:
        raise Exception(f"不支持的嵌入模型: {EMBEDDING_MODEL}")


def embed_texts(texts: List[str], batch_size: int = None) -> List[List[float]]:
    """
    Batch embed many texts with fewer HTTP requests.
    Ollama /api/embed accepts input as array of strings; we send batches of batch_size.
    """
    if not texts:
        return []
    batch_size = batch_size or EMBEDDING_BATCH_SIZE
    if EMBEDDING_MODEL == "ollama":
        return _embed_batch_ollama(texts, batch_size)
    else:
        return [_embed_text_ollama(t) for t in texts]

def _embed_text_ollama(text: str) -> List[float]:
    """
    使用 Ollama 本地模型进行文本嵌入
    支持新版 /api/embed 和旧版 /api/embeddings 两种 API
    """
    last_error = None
    
    # 先尝试新版 API (/api/embed)
    try:
        url = f"{OLLAMA_BASE_URL}/api/embed"
        payload = {
            "model": OLLAMA_EMBED_MODEL,
            "input": text,
        }
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        # 新版 API 返回 embeddings: [[...]]，单条输入取 [0]
        vectors = result.get("embeddings")
        if vectors and isinstance(vectors, list) and len(vectors) > 0:
            return vectors[0]
    except requests.exceptions.HTTPError as e:
        # 获取详细错误信息
        error_detail = ""
        if e.response is not None:
            try:
                error_detail = e.response.text[:500]
            except:
                pass
        last_error = f"/api/embed failed: {e.response.status_code if e.response else 'unknown'} - {error_detail}"
        # 如果是 404 或 400，尝试旧版 API
        if e.response is not None and e.response.status_code in (400, 404):
            pass  # 继续尝试旧版 API
        elif e.response is not None and e.response.status_code == 500:
            pass  # 可能是模型问题，尝试旧版 API
        else:
            raise Exception(f"Ollama embedding 请求失败: {str(e)} | {error_detail}")
    except requests.exceptions.RequestException as e:
        last_error = f"/api/embed failed: {str(e)}"
    
    # 回退到旧版 API (/api/embeddings)
    try:
        url = f"{OLLAMA_BASE_URL}/api/embeddings"
        payload = {
            "model": OLLAMA_EMBED_MODEL,
            "prompt": text,
        }
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        # 旧版 API 返回 embedding: [...]
        embedding = result.get("embedding")
        if embedding and isinstance(embedding, list):
            return embedding
        raise Exception(f"Ollama 返回格式异常: {result}")
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        if e.response is not None:
            try:
                error_detail = e.response.text[:500]
            except:
                pass
        raise Exception(
            f"Ollama embedding 请求失败: {str(e)} | 详情: {error_detail}\n"
            f"请确保已安装模型: ollama pull {OLLAMA_EMBED_MODEL}"
        )
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ollama embedding 请求失败: {str(e)}")


def _embed_batch_ollama(texts: List[str], batch_size: int) -> List[List[float]]:
    """
    Call Ollama /api/embed with input as list of strings (batch). Reduces N requests to ceil(N/batch_size).
    Falls back to sequential single-text if batch API fails (e.g. old Ollama).
    """
    out: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            url = f"{OLLAMA_BASE_URL}/api/embed"
            payload = {"model": OLLAMA_EMBED_MODEL, "input": batch}
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            vectors = result.get("embeddings")
            if vectors and isinstance(vectors, list) and len(vectors) == len(batch):
                out.extend(vectors)
            else:
                for t in batch:
                    out.append(_embed_text_ollama(t))
        except Exception:
            for t in batch:
                out.append(_embed_text_ollama(t))
    return out