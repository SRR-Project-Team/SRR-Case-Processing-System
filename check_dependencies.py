#!/usr/bin/env python3
"""
依赖检查脚本 - 自动检查代码中使用的第三方库是否都在 requirements.txt 中

用法：
    python check_dependencies.py
"""
import re
import os
from pathlib import Path
from typing import Set, Dict

# 标准库（不需要安装）
STDLIB_MODULES = {
    'os', 'sys', 're', 'json', 'pickle', 'datetime', 'time', 'pathlib', 'typing',
    'collections', 'itertools', 'functools', 'operator', 'warnings', 'logging',
    'tempfile', 'subprocess', 'threading', 'signal', 'sqlite3', 'difflib',
    'importlib', 'traceback', 'asyncio', 'io', 'abc', 'contextlib', 'copy',
    'enum', 'hashlib', 'random', 'shutil', 'stat', 'string', 'struct', 'textwrap',
    'unicodedata', 'urllib', 'uuid', 'weakref', 'builtins', 'codecs', 'decimal'
}

# 模块导入名到包名的映射（有些包导入名和包名不同）
MODULE_TO_PACKAGE = {
    'PIL': 'Pillow',
    'cv2': 'opencv-python',
    'sklearn': 'scikit-learn',
    'fitz': 'PyMuPDF',
    'yaml': 'PyYAML',
    'docx': 'python-docx',
}

def find_python_files(root_dir: Path) -> list:
    """查找所有 Python 文件"""
    python_files = []
    for ext in ['**/*.py']:
        python_files.extend(root_dir.glob(ext))
    return python_files

def extract_imports(file_path: Path, project_root: Path) -> Set[str]:
    """从 Python 文件中提取所有导入的模块名"""
    imports = set()
    
    # 项目内部模块名（不需要安装）
    project_modules = {'src', 'core', 'ai', 'utils', 'database', 'services', 'api', 'config'}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 匹配 import 语句: import module 或 from module import ...
        # 只匹配顶级模块名（不是相对导入）
        for line in content.split('\n'):
            line = line.strip()
            
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue
            
            # 跳过相对导入（from . import 或 from .. import）
            if re.match(r'^from\s+\.+', line):
                continue
            
            # 匹配绝对导入
            if line.startswith('import '):
                match = re.match(r'^import\s+([a-zA-Z0-9_]+)', line)
                if match:
                    module = match.group(1)
                    if module not in project_modules:
                        imports.add(module)
            elif line.startswith('from '):
                match = re.match(r'^from\s+([a-zA-Z0-9_]+)', line)
                if match:
                    module = match.group(1)
                    # 排除相对导入和项目内部模块
                    if module not in project_modules and not module.startswith('.'):
                        imports.add(module)
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}")
    
    return imports

def parse_requirements(requirements_file: Path) -> Set[str]:
    """解析 requirements.txt 文件，提取所有包名"""
    packages = set()
    
    if not requirements_file.exists():
        return packages
    
    with open(requirements_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue
            
            # 移除可选依赖标记，如 uvicorn[standard] -> uvicorn
            if '[' in line:
                line = line[:line.index('[')]
            
            # 解析包名（移除版本号、注释等）
            # 格式: package==1.0.0 或 package>=1.0.0 等
            parts = re.split(r'[>=<!=;]', line)
            if parts:
                package_name = parts[0].strip()
                # 保存原始大小写
                packages.add(package_name)
                # 同时添加小写版本用于匹配
                packages.add(package_name.lower())
                # 处理下划线/连字符转换
                packages.add(package_name.replace('_', '-'))
                packages.add(package_name.replace('_', '-').lower())
    
    return packages

def normalize_package_name(module_name: str) -> str:
    """将模块名转换为可能的包名（有些包名和导入名不同）"""
    mapping = {
        'sklearn': 'scikit-learn',
        'PIL': 'Pillow',
        'cv2': 'opencv-python',
        'yaml': 'PyYAML',
        'fitz': 'PyMuPDF',
    }
    return mapping.get(module_name, module_name.lower())

def check_dependencies():
    """主检查函数"""
    project_root = Path(__file__).parent
    src_dir = project_root / 'src'
    requirements_file = project_root / 'config' / 'requirements.txt'
    
    print("🔍 检查项目依赖...")
    print("=" * 60)
    
    # 获取所有 Python 文件
    python_files = find_python_files(src_dir)
    print(f"📁 找到 {len(python_files)} 个 Python 文件")
    
    # 提取所有导入的模块
    all_imports = set()
    for py_file in python_files:
        imports = extract_imports(py_file, project_root)
        all_imports.update(imports)
    
    # 过滤掉标准库
    third_party_imports = all_imports - STDLIB_MODULES
    
    print(f"\n📦 发现的第三方模块: {len(third_party_imports)} 个")
    if third_party_imports:
        print(f"   模块列表: {', '.join(sorted(third_party_imports))}")
    
    # 解析 requirements.txt
    required_packages = parse_requirements(requirements_file)
    print(f"\n📋 requirements.txt 中的包: {len(required_packages)} 个")
    
    # 检查缺失的依赖
    missing = []
    for module in sorted(third_party_imports):
        # 获取包名（可能是映射后的）
        package_name = MODULE_TO_PACKAGE.get(module, normalize_package_name(module))
        
        # 检查是否在 requirements.txt 中
        module_in_req = module.lower() in required_packages or module in required_packages
        package_in_req = package_name.lower() in required_packages or package_name in required_packages
        
        # 检查映射关系（如 PIL -> Pillow, fitz -> PyMuPDF）
        mapped_package = MODULE_TO_PACKAGE.get(module)
        mapped_in_req = mapped_package and (mapped_package.lower() in required_packages or mapped_package in required_packages)
        
        if not module_in_req and not package_in_req and not mapped_in_req:
            missing.append((module, package_name))
    
    # 过滤掉项目内部模块的误报（如果以常见项目模块名开头）
    missing = [m for m in missing if not any(
        m[0].startswith(proj_mod) for proj_mod in ['ai_', 'nlp_']
    )]
    
    print("\n" + "=" * 60)
    if missing:
        print("❌ 发现缺失的依赖:")
        for module, package in missing:
            print(f"   - {module} (可能需要安装: {package})")
        print("\n💡 建议：将这些依赖添加到 config/requirements.txt")
        return False
    else:
        print("✅ 所有依赖都已包含在 requirements.txt 中！")
        return True

if __name__ == '__main__':
    success = check_dependencies()
    exit(0 if success else 1)

