#!/usr/bin/env python3
"""
数据库适配器 - 为核算模块提供兼容接口
"""
import sqlite3
from database.manager import DatabaseManager
from utils.logging import get_logger

logger = get_logger("DatabaseAdapter")

class DatabaseAdapter:
    """
    数据库适配器类
    将现代的DatabaseManager接口适配为核算模块期望的旧式接口
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.conn = None
        self.cursor = None
        self._is_connected = False
    
    def connect(self):
        """建立数据库连接"""
        try:
            # 创建一个持久连接
            self.conn = sqlite3.connect(self.db_manager.db_name)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            self._is_connected = True
            logger.info("数据库适配器连接建立")
        except Exception as e:
            logger.error(f"数据库适配器连接失败: {e}")
            raise
    
    def disconnect(self):
        """断开数据库连接"""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            if self.conn:
                self.conn.close()
                self.conn = None
            self._is_connected = False
            logger.info("数据库适配器连接断开")
        except Exception as e:
            logger.error(f"数据库适配器断开失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
    
    def execute_query(self, sql: str, params: tuple = ()):
        """执行查询（兼容方法）"""
        return self.db_manager.execute_query(sql, params)
    
    def execute_command(self, sql: str, params: tuple = ()):
        """执行命令（兼容方法）"""
        return self.db_manager.execute_command(sql, params)

def create_compatible_db(db_manager: DatabaseManager):
    """
    创建兼容的数据库对象
    用于核算模块
    """
    return DatabaseAdapter(db_manager)

# 测试函数
def test_adapter():
    """测试适配器功能"""
    try:
        print("测试数据库适配器...")
        
        # 创建原始数据库管理器
        db_manager = DatabaseManager()
        print("✓ DatabaseManager创建成功")
        
        # 创建适配器
        adapter = create_compatible_db(db_manager)
        print("✓ 适配器创建成功")
        
        # 测试连接
        adapter.connect()
        print("✓ 适配器连接成功")
        
        # 测试查询
        adapter.cursor.execute("SELECT COUNT(*) FROM users")
        count = adapter.cursor.fetchone()[0]
        print(f"✓ 查询测试成功，用户数: {count}")
        
        # 测试上下文管理器模式
        with create_compatible_db(db_manager) as db:
            db.cursor.execute("SELECT COUNT(*) FROM contracts")
            contract_count = db.cursor.fetchone()[0]
            print(f"✓ 上下文管理器测试成功，合同数: {contract_count}")
        
        # 断开连接
        adapter.disconnect()
        print("✓ 适配器断开成功")
        
        print("✓ 所有测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_adapter()
