"""
AI模型缓存管理器
用于缓存已初始化的AI模型，避免重复加载，提高处理速度
"""

import time
from typing import Dict, Any, Optional
import threading

class AIModelCache:
    """AI模型缓存管理器"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._cache_timeout = 1800  # 30分钟缓存超时
    
    def get_model(self, model_key: str) -> Optional[Any]:
        """获取缓存的模型"""
        with self._lock:
            if model_key in self._cache:
                cache_entry = self._cache[model_key]
                # 检查缓存是否过期
                if time.time() - cache_entry['timestamp'] < self._cache_timeout:
                    print(f"🚀 使用缓存的{model_key}模型")
                    return cache_entry['model']
                else:
                    # 缓存过期，删除
                    del self._cache[model_key]
                    print(f"⏰ {model_key}模型缓存已过期")
            return None
    
    def set_model(self, model_key: str, model: Any):
        """缓存模型"""
        with self._lock:
            self._cache[model_key] = {
                'model': model,
                'timestamp': time.time()
            }
            print(f"💾 缓存{model_key}模型")
    
    def clear_cache(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            print("🗑️ 清空AI模型缓存")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        with self._lock:
            info = {
                'cached_models': list(self._cache.keys()),
                'cache_count': len(self._cache),
                'cache_timeout': self._cache_timeout
            }
            return info

# 全局缓存实例
_global_cache: Optional[AIModelCache] = None

def get_ai_model_cache() -> AIModelCache:
    """获取全局AI模型缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = AIModelCache()
    return _global_cache

def clear_ai_model_cache():
    """清空全局AI模型缓存"""
    global _global_cache
    if _global_cache:
        _global_cache.clear_cache()

# 便捷函数
def get_cached_model(model_key: str) -> Optional[Any]:
    """获取缓存的模型"""
    cache = get_ai_model_cache()
    return cache.get_model(model_key)

def cache_model(model_key: str, model: Any):
    """缓存模型"""
    cache = get_ai_model_cache()
    cache.set_model(model_key, model)

def get_cache_info() -> Dict[str, Any]:
    """获取缓存信息"""
    cache = get_ai_model_cache()
    return cache.get_cache_info()

if __name__ == "__main__":
    # 测试缓存功能
    print("🧪 测试AI模型缓存...")
    
    # 模拟模型
    class MockModel:
        def __init__(self, name):
            self.name = name
            print(f"🔧 初始化模型: {name}")
    
    # 测试缓存
    cache = get_ai_model_cache()
    
    # 第一次获取（应该返回None）
    model1 = cache.get_model('test_model')
    print(f"第一次获取: {model1}")
    
    # 缓存模型
    mock_model = MockModel('TestModel')
    cache.set_model('test_model', mock_model)
    
    # 第二次获取（应该返回缓存的模型）
    model2 = cache.get_model('test_model')
    print(f"第二次获取: {model2.name if model2 else None}")
    
    # 获取缓存信息
    info = cache.get_cache_info()
    print(f"缓存信息: {info}")
    
    print("✅ AI模型缓存测试完成")
