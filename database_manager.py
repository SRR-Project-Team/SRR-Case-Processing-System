#!/usr/bin/env python3
"""
数据库管理工具

本工具提供SRR案件数据库的完整管理功能，包括：
- 数据库统计和监控
- 案件数据查询和搜索
- 数据导入导出
- 数据库维护和清理

主要功能：
1. 显示数据库统计信息（案件数量、文件类型分布等）
2. 列出和搜索案件数据
3. 导出案件数据为JSON格式
4. 删除指定案件或清理数据库
5. 提供交互式命令行界面

使用方式：
- python database_manager.py stats    # 显示统计信息
- python database_manager.py list 10  # 列出最近10个案件
- python database_manager.py search "关键词"  # 搜索案件
- python database_manager.py export backup.json  # 导出数据
- python database_manager.py delete 123  # 删除案件ID 123

作者: Project3 Team
版本: 2.0
"""
import sys
import os
import json
from datetime import datetime

# 添加项目路径以导入数据库模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import get_db_manager

class DatabaseManager:
    """
    数据库管理工具类
    
    提供SRR案件数据库的完整管理功能，包括统计、查询、导出等操作。
    
    Attributes:
        db: 数据库管理器实例
    """
    
    def __init__(self):
        """
        初始化数据库管理器
        
        获取数据库管理器实例，用于后续的数据库操作。
        """
        self.db = get_db_manager()
    
    def show_stats(self):
        """显示统计信息"""
        print("📊 数据库统计信息")
        print("=" * 50)
        
        stats = self.db.get_stats()
        print(f"总案件数: {stats['total_cases']}")
        print(f"TXT案件: {stats['txt_cases']}")
        print(f"TMO案件: {stats['tmo_cases']}")
        print(f"RCC案件: {stats['rcc_cases']}")
        print()
    
    def list_cases(self, limit=10):
        """列出案件"""
        print(f"📋 最近 {limit} 个案件")
        print("=" * 50)
        
        cases = self.db.get_cases(limit=limit)
        if not cases:
            print("暂无案件数据")
            return
        
        for i, case in enumerate(cases, 1):
            print(f"{i}. ID: {case['id']}")
            print(f"   文件: {case['original_filename']} ({case['file_type']})")
            print(f"   来电人: {case['E_caller_name']}")
            print(f"   斜坡号: {case['G_slope_no']}")
            print(f"   位置: {case['H_location']}")
            print(f"   创建时间: {case['created_at']}")
            print()
    
    def search_cases(self, keyword):
        """搜索案件"""
        print(f"🔍 搜索关键词: '{keyword}'")
        print("=" * 50)
        
        cases = self.db.search_cases(keyword)
        if not cases:
            print("未找到匹配的案件")
            return
        
        print(f"找到 {len(cases)} 个匹配案件:")
        for i, case in enumerate(cases, 1):
            print(f"{i}. ID: {case['id']} - {case['E_caller_name']} - {case['G_slope_no']}")
        print()
    
    def get_case_details(self, case_id):
        """获取案件详情"""
        print(f"📄 案件详情 (ID: {case_id})")
        print("=" * 50)
        
        case = self.db.get_case(case_id)
        if not case:
            print("案件不存在")
            return
        
        # 显示A-Q字段
        fields = [
            ('A_date_received', '接收日期'),
            ('B_source', '来源'),
            ('C_case_number', '案件号'),
            ('D_type', '类型'),
            ('E_caller_name', '来电人'),
            ('F_contact_no', '联系电话'),
            ('G_slope_no', '斜坡号'),
            ('H_location', '位置'),
            ('I_nature_of_request', '请求性质'),
            ('J_subject_matter', '事项主题'),
            ('K_10day_rule_due_date', '10天规则截止'),
            ('L_icc_interim_due', 'ICC临时回复'),
            ('M_icc_final_due', 'ICC最终回复'),
            ('N_works_completion_due', '工程完成'),
            ('O1_fax_to_contractor', '传真给承包商'),
            ('O2_email_send_time', '邮件发送时间'),
            ('P_fax_pages', '传真页数'),
            ('Q_case_details', '案件详情')
        ]
        
        for field, label in fields:
            value = case.get(field, '')
            if value:
                print(f"{label}: {value}")
        
        print(f"\n原始文件: {case['original_filename']}")
        print(f"文件类型: {case['file_type']}")
        print(f"创建时间: {case['created_at']}")
        print()
    
    def export_cases(self, filename=None):
        """导出案件数据"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cases_export_{timestamp}.json"
        
        print(f"📤 导出案件数据到: {filename}")
        
        cases = self.db.get_cases(limit=1000)  # 导出所有案件
        
        export_data = {
            'export_time': datetime.now().isoformat(),
            'total_cases': len(cases),
            'cases': cases
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 导出完成，共 {len(cases)} 个案件")
        print()
    
    def interactive_menu(self):
        """交互式菜单"""
        while True:
            print("🗄️ 数据库管理工具")
            print("=" * 30)
            print("1. 显示统计信息")
            print("2. 列出案件")
            print("3. 搜索案件")
            print("4. 查看案件详情")
            print("5. 导出案件数据")
            print("0. 退出")
            print()
            
            choice = input("请选择操作 (0-5): ").strip()
            
            if choice == '0':
                print("👋 再见！")
                break
            elif choice == '1':
                self.show_stats()
            elif choice == '2':
                limit = input("显示数量 (默认10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                self.list_cases(limit)
            elif choice == '3':
                keyword = input("搜索关键词: ").strip()
                if keyword:
                    self.search_cases(keyword)
            elif choice == ' ':
                case_id = input("案件ID: ").strip()
                if case_id.isdigit():
                    self.get_case_details(int(case_id))
            elif choice == '5':
                filename = input("导出文件名 (回车使用默认): ").strip()
                self.export_cases(filename if filename else None)
            else:
                print("❌ 无效选择，请重试")
            
            input("\n按回车键继续...")
            print("\n" + "="*50 + "\n")

def main():
    """主函数"""
    manager = DatabaseManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'stats':
            manager.show_stats()
        elif command == 'list':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            manager.list_cases(limit)
        elif command == 'search':
            keyword = sys.argv[2] if len(sys.argv) > 2 else ''
            manager.search_cases(keyword)
        elif command == 'details':
            case_id = int(sys.argv[2]) if len(sys.argv) > 2 else 0
            manager.get_case_details(case_id)
        elif command == 'export':
            filename = sys.argv[2] if len(sys.argv) > 2 else None
            manager.export_cases(filename)
        else:
            print("❌ 未知命令")
            print("可用命令: stats, list, search, details, export")
    else:
        # 交互式模式
        manager.interactive_menu()

if __name__ == "__main__":
    main()
