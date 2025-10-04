#!/usr/bin/env python3
"""
SRR案件处理系统启动脚本

本脚本提供便捷的系统启动、管理和监控功能，支持：
- 自动检测和清理现有进程
- 一键启动前后端服务
- 实时日志监控
- 系统健康检查
- 智能进程管理

主要功能：
1. 依赖检查和环境验证
2. 进程冲突检测和清理
3. 前后端服务启动
4. 实时日志显示
5. 系统状态监控

使用方式：
- python start.py start        # 启动系统
- python start.py start --logs # 启动系统（实时日志）
- python start.py check        # 系统检查
- python start.py cleanup      # 清理进程
- python start.py help         # 帮助信息

作者: Project3 Team
版本: 2.0
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

class SRRSystemManager:
    """
    SRR系统管理器
    
    负责管理SRR案件处理系统的启动、停止和监控。
    支持智能进程管理、实时日志显示和系统健康检查。
    
    Attributes:
        project_root (Path): 项目根目录路径
        backend_process (subprocess.Popen): 后端进程对象
        frontend_process (subprocess.Popen): 前端进程对象
        running (bool): 系统运行状态
        show_logs (bool): 是否显示实时日志
        log_thread (threading.Thread): 后端日志监控线程
        frontend_log_thread (threading.Thread): 前端日志监控线程
    """
    
    def __init__(self, show_logs=False):
        """
        初始化系统管理器
        
        Args:
            show_logs (bool): 是否显示实时日志，默认为False
        """
        self.project_root = Path(__file__).parent
        self.backend_process = None
        self.frontend_process = None
        self.running = False
        self.show_logs = show_logs  # 日志显示选项
        self.log_thread = None      # 后端日志监控线程
        self.frontend_log_thread = None  # 前端日志监控线程
        
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        # Check Python dependencies
        try:
            import fastapi
            import uvicorn
            import easyocr
            import transformers
            print("✅ Python dependencies OK")
        except ImportError as e:
            print(f"❌ Missing Python dependency: {e}")
            print("Please run: pip install -r config/requirements.txt")
            return False
            
        # Check if Node.js is available
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js {result.stdout.strip()} OK")
            else:
                raise FileNotFoundError
        except FileNotFoundError:
            print("❌ Node.js not found")
            print("Please install Node.js 16+ from https://nodejs.org/")
            return False
            
        return True
    
    def check_data_files(self):
        """Check if required model files exist"""
        print("📊 Checking model files...")
        
        models_dir = self.project_root / "models"
        required_files = [
            "ai_models/training_data.pkl",
            "mapping_rules/slope_location_mapping.json",
            "config/srr_rules.json",
            "config/keyword_rules.json",
            "metadata.json"
        ]
        
        missing_files = []
        for file_name in required_files:
            file_path = models_dir / file_name
            if not file_path.exists():
                missing_files.append(file_name)
        
        if missing_files:
            print(f"❌ Missing model files: {', '.join(missing_files)}")
            print(f"Please ensure model files are in: {models_dir}")
            print("💡 Run data conversion script to generate model files")
            return False
        
        print("✅ All model files present")
        return True
    
    def check_existing_processes(self):
        """检查是否有已运行的SRR相关进程"""
        print("🔍 检查现有进程...")
        
        existing_processes = []
        
        try:
            # 检查Python后端进程
            result = subprocess.run(['pgrep', '-f', 'main.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        existing_processes.append(('Python Backend', pid, 'main.py'))
        except:
            pass
        
        try:
            # 检查React前端进程
            result = subprocess.run(['pgrep', '-f', 'react-scripts'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        existing_processes.append(('React Frontend', pid, 'react-scripts'))
        except:
            pass
        
        try:
            # 检查npm start进程
            result = subprocess.run(['pgrep', '-f', 'npm.*start'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        existing_processes.append(('NPM Start', pid, 'npm start'))
        except:
            pass
        
        return existing_processes
    
    def stop_existing_processes(self):
        """停止现有的SRR相关进程"""
        print("🛑 停止现有进程...")
        
        processes_stopped = 0
        
        # 停止Python进程
        try:
            result = subprocess.run(['pkill', '-f', 'main.py'], 
                                  capture_output=True)
            if result.returncode == 0:
                processes_stopped += 1
                print("   ✅ Python后端进程已停止")
        except:
            pass
        
        # 停止React进程
        try:
            result = subprocess.run(['pkill', '-f', 'react-scripts'], 
                                  capture_output=True)
            if result.returncode == 0:
                processes_stopped += 1
                print("   ✅ React前端进程已停止")
        except:
            pass
        
        # 停止npm进程
        try:
            result = subprocess.run(['pkill', '-f', 'npm.*start'], 
                                  capture_output=True)
            if result.returncode == 0:
                processes_stopped += 1
                print("   ✅ NPM进程已停止")
        except:
            pass
        
        # 清理端口占用
        try:
            # 清理8001端口
            result = subprocess.run(['lsof', '-ti:8001'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        subprocess.run(['kill', '-9', pid], capture_output=True)
                print("   ✅ 端口8001已清理")
        except:
            pass
        
        try:
            # 清理3000端口
            result = subprocess.run(['lsof', '-ti:3000'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        subprocess.run(['kill', '-9', pid], capture_output=True)
                print("   ✅ 端口3000已清理")
        except:
            pass
        
        if processes_stopped > 0:
            print("⏳ 等待进程完全结束...")
            time.sleep(3)
        
        return processes_stopped
    
    def verify_cleanup(self):
        """验证清理是否成功"""
        print("🔍 验证清理结果...")
        
        remaining = self.check_existing_processes()
        
        # 检查端口占用
        port_8001_free = True
        port_3000_free = True
        
        try:
            result = subprocess.run(['lsof', '-i:8001'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                port_8001_free = False
        except:
            pass
        
        try:
            result = subprocess.run(['lsof', '-i:3000'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                port_3000_free = False
        except:
            pass
        
        if len(remaining) == 0 and port_8001_free and port_3000_free:
            print("✅ 系统清理完成，可以启动新实例")
            return True
        else:
            if remaining:
                print(f"⚠️ 仍有 {len(remaining)} 个进程在运行")
            if not port_8001_free:
                print("⚠️ 端口8001仍被占用")
            if not port_3000_free:
                print("⚠️ 端口3000仍被占用")
            return False
    
    def start_backend(self):
        """Start the FastAPI backend server"""
        print("🚀 Starting backend server...")
        
        backend_dir = self.project_root / "src" / "api"
        if not backend_dir.exists():
            print(f"❌ Backend directory not found: {backend_dir}")
            return False
            
        try:
            os.chdir(backend_dir)
            
            if self.show_logs:
                # 显示日志模式：不使用PIPE，让日志直接输出
                self.backend_process = subprocess.Popen([
                    sys.executable, "main.py"
                ])
                print("📋 Backend logs will be displayed in real-time")
            else:
                # 静默模式：使用PIPE重定向日志
                self.backend_process = subprocess.Popen([
                    sys.executable, "main.py"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a moment to check if process started successfully
            time.sleep(3)
            if self.backend_process.poll() is None:
                print("✅ Backend server started on http://localhost:8001")
                
                if not self.show_logs:
                    # 启动日志监控线程
                    self.start_log_monitoring()
                
                return True
            else:
                stdout, stderr = self.backend_process.communicate()
                print(f"❌ Backend failed to start:")
                print(f"STDOUT: {stdout.decode()}")
                print(f"STDERR: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting backend: {e}")
            return False
        finally:
            os.chdir(self.project_root)
    
    def start_log_monitoring(self):
        """Start monitoring backend logs"""
        if self.show_logs or not self.backend_process:
            return
        
        def monitor_logs():
            """Monitor backend process logs"""
            try:
                while self.running and self.backend_process:
                    # 读取后端进程的输出
                    if self.backend_process.stdout:
                        line = self.backend_process.stdout.readline()
                        if line:
                            print(f"[BACKEND] {line.decode().strip()}")
                    
                    if self.backend_process.stderr:
                        line = self.backend_process.stderr.readline()
                        if line:
                            print(f"[BACKEND ERROR] {line.decode().strip()}")
                    
                    time.sleep(0.1)
            except Exception as e:
                print(f"Log monitoring error: {e}")
        
        self.log_thread = threading.Thread(target=monitor_logs, daemon=True)
        self.log_thread.start()
    
    def start_frontend_log_monitoring(self):
        """Start monitoring frontend logs"""
        if self.show_logs or not self.frontend_process:
            return
        
        def monitor_frontend_logs():
            """Monitor frontend process logs"""
            try:
                while self.running and self.frontend_process:
                    # 读取前端进程的输出
                    if self.frontend_process.stdout:
                        line = self.frontend_process.stdout.readline()
                        if line:
                            print(f"[FRONTEND] {line.decode().strip()}")
                    
                    if self.frontend_process.stderr:
                        line = self.frontend_process.stderr.readline()
                        if line:
                            print(f"[FRONTEND ERROR] {line.decode().strip()}")
                    
                    time.sleep(0.1)
            except Exception as e:
                print(f"Frontend log monitoring error: {e}")
        
        self.frontend_log_thread = threading.Thread(target=monitor_frontend_logs, daemon=True)
        self.frontend_log_thread.start()
    
    def start_frontend(self):
        """Start the React frontend server"""
        print("🌐 Starting frontend server...")
        
        frontend_dir = self.project_root / "frontend" / "srr-chatbot"
        if not frontend_dir.exists():
            print(f"❌ Frontend directory not found: {frontend_dir}")
            return False
        
        # Check if node_modules exists
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            print("📦 Installing frontend dependencies...")
            try:
                os.chdir(frontend_dir)
                result = subprocess.run(['npm', 'install'], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"❌ npm install failed: {result.stderr}")
                    return False
                print("✅ Frontend dependencies installed")
            except Exception as e:
                print(f"❌ Error installing dependencies: {e}")
                return False
            finally:
                os.chdir(self.project_root)
        
        try:
            os.chdir(frontend_dir)
            
            if self.show_logs:
                # 显示日志模式：不使用PIPE，让日志直接输出
                self.frontend_process = subprocess.Popen([
                    'npm', 'start'
                ])
                print("📋 Frontend logs will be displayed in real-time")
            else:
                # 静默模式：使用PIPE重定向日志
                self.frontend_process = subprocess.Popen([
                    'npm', 'start'
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for frontend to start
            print("⏳ Waiting for frontend to start...")
            time.sleep(10)
            
            if self.frontend_process.poll() is None:
                print("✅ Frontend server started on http://localhost:3000")
                
                if not self.show_logs:
                    # 启动前端日志监控线程
                    self.start_frontend_log_monitoring()
                
                return True
            else:
                stdout, stderr = self.frontend_process.communicate()
                print(f"❌ Frontend failed to start:")
                print(f"STDOUT: {stdout.decode()}")
                print(f"STDERR: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting frontend: {e}")
            return False
        finally:
            os.chdir(self.project_root)
    
    def stop_services(self):
        """Stop all running services"""
        print("\n🛑 Stopping services...")
        
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
                print("✅ Backend stopped")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                print("⚠️ Backend force killed")
        
        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
                print("✅ Frontend stopped")
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                print("⚠️ Frontend force killed")
        
        self.running = False
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n📡 Received signal {signum}")
        self.stop_services()
        sys.exit(0)
    
    def monitor_processes(self):
        """Monitor running processes"""
        while self.running:
            time.sleep(5)
            
            # Check backend
            if self.backend_process and self.backend_process.poll() is not None:
                print("❌ Backend process died unexpectedly")
                self.running = False
                break
            
            # Check frontend
            if self.frontend_process and self.frontend_process.poll() is not None:
                print("❌ Frontend process died unexpectedly")
                self.running = False
                break
    
    def start_system(self):
        """Start the complete SRR system"""
        print("🎯 SRR Case Processing System Startup")
        print("=" * 50)
        
        # Check for existing processes first
        existing_processes = self.check_existing_processes()
        if existing_processes:
            print(f"⚠️ 发现 {len(existing_processes)} 个已运行的进程:")
            for proc_type, pid, name in existing_processes:
                print(f"   - {proc_type} (PID: {pid}) - {name}")
            
            print("")
            print("🔄 正在清理现有进程以避免冲突...")
            
            # Stop existing processes
            stopped_count = self.stop_existing_processes()
            
            # Verify cleanup
            if not self.verify_cleanup():
                print("❌ 无法完全清理现有进程，启动可能会失败")
                print("建议手动检查并清理相关进程后再试")
                return False
            
            print("✅ 现有进程清理完成")
            print("")
        else:
            print("✅ 没有检测到现有进程")
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Check data files
        if not self.check_data_files():
            return False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start backend
        if not self.start_backend():
            return False
        
        # Start frontend
        if not self.start_frontend():
            self.stop_services()
            return False
        
        self.running = True
        
        print("\n🎉 SRR System started successfully!")
        print("=" * 50)
        print("📡 Backend API: http://localhost:8001")
        print("🌐 Frontend UI: http://localhost:3000")
        print("📚 API Docs: http://localhost:8001/docs")
        print("=" * 50)
        print("Press Ctrl+C to stop the system")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_processes)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        self.stop_services()
        return True

def main():
    """Main entry point"""
    # 检查是否有 --logs 参数
    show_logs = "--logs" in sys.argv
    manager = SRRSystemManager(show_logs=show_logs)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            # 启动系统
            success = manager.start_system()
            return 0 if success else 1
        
        elif command == "check":
            print("🔍 Running system checks...")
            deps_ok = manager.check_dependencies()
            data_ok = manager.check_data_files()
            
            if deps_ok and data_ok:
                print("✅ All checks passed! System ready to start.")
                return 0
            else:
                print("❌ System checks failed. Please fix issues above.")
                return 1
        
        elif command == "cleanup":
            print("🧹 SRR系统清理工具")
            existing = manager.check_existing_processes()
            if existing:
                print(f"发现 {len(existing)} 个运行中的进程:")
                for proc_type, pid, name in existing:
                    print(f"   - {proc_type} (PID: {pid}) - {name}")
                
                stopped = manager.stop_existing_processes()
                if manager.verify_cleanup():
                    print("✅ 系统清理完成")
                    return 0
                else:
                    print("❌ 清理不完整，可能需要手动处理")
                    return 1
            else:
                print("✅ 没有发现运行中的SRR进程")
                return 0
        
        elif command == "help":
            print("SRR System Manager")
            print("Usage:")
            print("  python start.py start        - Start the complete system")
            print("  python start.py start --logs - Start system with real-time logs")
            print("  python start.py check        - Run system checks only")
            print("  python start.py cleanup      - Clean up existing processes")
            print("  python start.py help         - Show this help message")
            print("")
            print("Examples:")
            print("  python start.py start --logs  # Start with real-time logs (recommended for development)")
            print("  python start.py start         # Start silently")
            print("")
            print("Log modes:")
            print("  --logs: Show real-time backend and frontend logs")
            print("  default: Show logs in background with [BACKEND]/[FRONTEND] prefixes")
            return 0
        
        else:
            print(f"Unknown command: {command}")
            print("Use 'python start.py help' for usage information")
            return 1
    
    # Default: start the system
    success = manager.start_system()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
