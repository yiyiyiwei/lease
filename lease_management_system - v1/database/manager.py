"""
数据库管理模块
"""
import sqlite3
import hashlib
import datetime
from typing import List, Dict, Any, Optional, Union
from contextlib import contextmanager

from config.settings import config
from utils.logging import get_logger
from models.entities import User

logger = get_logger("DatabaseManager")


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.db_name = config.database.db_name
        self._connection = None
        self._cursor = None
        self.init_database()
     
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"数据库操作错误: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """初始化数据库表结构"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建用户表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL CHECK(role IN ('admin', 'operator', 'viewer')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建合同表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS contracts (
                        contract_id TEXT PRIMARY KEY,
                        customer_name TEXT NOT NULL,
                        room_number TEXT NOT NULL,
                        area REAL DEFAULT 0,
                        total_rent REAL DEFAULT 0,
                        initial_total_rent REAL DEFAULT 0,
                        payment_name TEXT NOT NULL,
                        eas_code TEXT NOT NULL,
                        tax_rate REAL DEFAULT 0.05,
                        need_adjust_income INTEGER DEFAULT 0,
                        deposit_amount REAL DEFAULT 0,
                        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        initial_stamp_duty REAL DEFAULT 0,
                        created_by TEXT NOT NULL,
                        is_effective INTEGER NOT NULL DEFAULT 0,
                        effective_date DATE,
                        contract_type TEXT NOT NULL CHECK(contract_type IN ('新增', '续租', '变更')),
                        original_contract_id TEXT,
                        FOREIGN KEY (original_contract_id) REFERENCES contracts(contract_id) ON DELETE SET NULL
                    )
                ''')
                
                # 创建租金期表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rent_periods (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contract_id TEXT NOT NULL,
                        start_date DATE NOT NULL,
                        end_date DATE NOT NULL,
                        monthly_rent REAL NOT NULL,
                        FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE
                    )
                ''')
                
                # 创建免租期表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS free_periods (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contract_id TEXT NOT NULL,
                        start_date DATE NOT NULL,
                        end_date DATE NOT NULL,
                        FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE
                    )
                ''')
                
                # 创建收款记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS payment_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contract_id TEXT NOT NULL,
                        date DATE NOT NULL,
                        amount REAL NOT NULL,
                        payment_type TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT NOT NULL,
                        FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE
                    )
                ''')
                
                # 创建押金记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS deposit_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contract_id TEXT NOT NULL,
                        date DATE NOT NULL,
                        amount REAL NOT NULL,
                        record_type TEXT NOT NULL CHECK(record_type IN ('收取', '退还')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT NOT NULL,
                        remark TEXT DEFAULT "",
                        FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE
                    )
                ''')
                
                # 创建开票记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS invoice_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contract_id TEXT NOT NULL,
                        date DATE NOT NULL,
                        amount REAL NOT NULL,
                        tax_amount REAL DEFAULT 0,
                        invoice_number TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT NOT NULL,
                        FOREIGN KEY (contract_id) REFERENCES contracts(contract_id) ON DELETE CASCADE
                    )
                ''')
                
                # 创建操作日志表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS operation_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user TEXT NOT NULL,
                        operation_type TEXT NOT NULL,
                        target_type TEXT NOT NULL,
                        target_id TEXT NOT NULL,
                        details TEXT,
                        operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 添加初始管理员用户
                cursor.execute("SELECT * FROM users WHERE username = 'admin'")
                if not cursor.fetchone():
                    admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
                    cursor.execute('''
                        INSERT INTO users (username, password_hash, role)
                        VALUES ('admin', ?, 'admin')
                    ''', (admin_hash,))
                    logger.info("初始管理员用户创建成功")
                
                conn.commit()
                logger.info("数据库表结构初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise
    
    def verify_user(self, username: str, password: str) -> Optional[User]:
        """验证用户登录"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT username, role, created_at FROM users
                    WHERE username = ? AND password_hash = ?
                ''', (username, password_hash))
                
                row = cursor.fetchone()
                if row:
                    return User(
                        username=row["username"],
                        role=row["role"],
                        created_at=datetime.datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
                    )
                return None
        except Exception as e:
            logger.error(f"用户验证失败: {str(e)}")
            return None
    
    def execute_query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                result = cursor.fetchall()
                return [dict(row) for row in result] if result else []
        except Exception as e:
            logger.error(f"查询执行失败: SQL={sql}, 参数={params}, 错误={str(e)}")
            return []
    
    def execute_command(self, sql: str, params: tuple = ()) -> bool:
        """执行命令（INSERT, UPDATE, DELETE）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"命令执行失败: SQL={sql}, 参数={params}, 错误={str(e)}")
            return False

    # 新增：执行INSERT并返回自增ID
    def execute_return_id(self, sql: str, params: tuple = ()) -> Optional[int]:
        """执行插入语句并返回新记录的ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                return cursor.lastrowid  # 返回自增ID
        except Exception as e:
            logger.error(f"插入并返回ID失败: SQL={sql}, 参数={params}, 错误={str(e)}")
            return None  # 失败时返回None

    
    def execute_command_with_id(self, sql: str, params: tuple = ()) -> Optional[int]:
        """执行命令并返回最后插入的ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                last_id = cursor.lastrowid
                conn.commit()
                return last_id
        except Exception as e:
            logger.error(f"命令执行失败: SQL={sql}, 参数={params}, 错误={str(e)}")
            return None
    
    def execute_batch(self, sql: str, params_list: List[tuple]) -> bool:
        """批量执行命令"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(sql, params_list)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"批量执行失败: SQL={sql}, 错误={str(e)}")
            return False
    
    def log_operation(self, user: str, operation_type: str, target_type: str, 
                     target_id: str, details: str = None):
        """记录操作日志"""
        self.execute_command('''
            INSERT INTO operation_logs (user, operation_type, target_type, target_id, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (user, operation_type, target_type, target_id, details))
