"""
日志管理工具模块
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from config.settings import config


class LoggerManager:
    """日志管理器"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str = "LeaseManagement") -> logging.Logger:
        """获取或创建日志器"""
        if name not in cls._loggers:
            cls._loggers[name] = cls._create_logger(name)
        return cls._loggers[name]
    
    @classmethod
    def _create_logger(cls, name: str) -> logging.Logger:
        """创建日志器"""
        logger = logging.getLogger(name)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
            
        logger.setLevel(logging.INFO)
        
        # 创建日志目录
        os.makedirs(config.logging.log_dir, exist_ok=True)
        
        # 创建文件处理器
        handler = RotatingFileHandler(
            config.logging.log_path,
            maxBytes=config.logging.max_bytes,
            backupCount=config.logging.backup_count,
            encoding=config.logging.encoding
        )
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # 添加处理器到日志器
        logger.addHandler(handler)
        
        return logger


# 便捷函数
def get_logger(name: str = "LeaseManagement") -> logging.Logger:
    """获取日志器的便捷函数"""
    return LoggerManager.get_logger(name)


# 全局日志器实例
logger = get_logger()
