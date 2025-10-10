"""
AImodelcachemanager
用于cache已initialize的AImodel，避免duplicateload，提高processspeed
"""

import time
from typing import Dict, Any, Optional
import threading

class AIModelCache:
    """AImodelcache管理器"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._cache_timeout = 1800  # 30分钟cache超时
    
    def get_model(self, model_key: str) -> Optional[Any]:
        """获取cache的model"""
        with self._lock:
            if model_key in self._cache:
                cache_entry = self._cache[model_key]
                # checkcache是否过期
                if time.time() - cache_entry['timestamp'] < self._cache_timeout:
                    print(f"🚀 使用cache的{model_key}model")
                    return cache_entry['model']
                else:
                    # cache过期，delete
                    del self._cache[model_key]
                    print(f"⏰ {model_key}modelcache已过期")
            return None
    
    def set_model(self, model_key: str, model: Any):
        """cachemodel"""
        with self._lock:
            self._cache[model_key] = {
                'model': model,
                'timestamp': time.time()
            }
            print(f"💾 cache{model_key}model")
    
    def clear_cache(self):
        """清空cache"""
        with self._lock:
            self._cache.clear()
            print("🗑️ 清空AImodelcache")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取cacheinformation"""
        with self._lock:
            info = {
                'cached_models': list(self._cache.keys()),
                'cache_count': len(self._cache),
                'cache_timeout': self._cache_timeout
            }
            return info

# 全局cacheinstance
_global_cache: Optional[AIModelCache] = None

def get_ai_model_cache() -> AIModelCache:
    """获取全局AImodelcacheinstance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = AIModelCache()
    return _global_cache

def clear_ai_model_cache():
    """清空全局AImodelcache"""
    global _global_cache
    if _global_cache:
        _global_cache.clear_cache()

# 便捷function
def get_cached_model(model_key: str) -> Optional[Any]:
    """获取cache的model"""
    cache = get_ai_model_cache()
    return cache.get_model(model_key)

def cache_model(model_key: str, model: Any):
    """cachemodel"""
    cache = get_ai_model_cache()
    cache.set_model(model_key, model)

def get_cache_info() -> Dict[str, Any]:
    """获取cacheinformation"""
    cache = get_ai_model_cache()
    return cache.get_cache_info()

if __name__ == "__main__":
    # testcachefunction
    print("🧪 测试AImodelcache...")
    
    # 模拟model
    class MockModel:
        def __init__(self, name):
            self.name = name
            print(f"🔧 initializemodel: {name}")
    
    # testcache
    cache = get_ai_model_cache()
    
    # 第一次get（应该returnNone）
    model1 = cache.get_model('test_model')
    print(f"第一次获取: {model1}")
    
    # cachemodel
    mock_model = MockModel('TestModel')
    cache.set_model('test_model', mock_model)
    
    # 第二次get（应该returncache的model）
    model2 = cache.get_model('test_model')
    print(f"第二次获取: {model2.name if model2 else None}")
    
    # getcacheinformation
    info = cache.get_cache_info()
    print(f"cacheinformation: {info}")
    
    print("✅ AImodelcache测试完成")
