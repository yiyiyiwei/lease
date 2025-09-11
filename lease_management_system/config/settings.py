"""
系统配置管理模块
"""
import os
from dataclasses import dataclass,field
from typing import List


@dataclass
class DatabaseConfig:
    """数据库配置"""
    db_name: str = "lease.db"
    backup_dir: str = "backups"
    max_backups: int = 30
    
    @property
    def db_path(self) -> str:
        return os.path.abspath(self.db_name)


@dataclass
class LoggingConfig:
    """日志配置"""
    log_dir: str = "logs"
    log_file: str = "lease_management.log"
    max_bytes: int = 1 * 1024 * 1024  # 1MB
    backup_count: int = 10
    encoding: str = 'utf-8'
    
    @property
    def log_path(self) -> str:
        return os.path.join(self.log_dir, self.log_file)


@dataclass
class UIConfig:
    """界面配置"""
    window_title: str = "租赁合同管理系统"
    window_geometry: str = "1200x800"
    font_family: str = "SimHei"
    font_size: int = 10


@dataclass
class BusinessConfig:
    """业务配置"""
    default_tax_rate: float = 0.05  # 默认税率5%
    stamp_duty_rate: float = 0.001  # 印花税率0.1%
    overdue_check_days: int = 30    # 逾期检查天数
    max_import_errors: int = 100    # 最大导入错误数


@dataclass
class SystemConfig:
    """系统总配置"""
    # 使用 default_factory 代替直接实例化
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    business: BusinessConfig = field(default_factory=BusinessConfig)
    
    def __post_init__(self):
        """初始化后创建必要的目录"""
        os.makedirs(self.logging.log_dir, exist_ok=True)
        os.makedirs(self.database.backup_dir, exist_ok=True)


# 全局配置实例
config = SystemConfig()
