# coding: utf-8
"""
日志输出与格式化模块

功能说明：
- ColoredFormatter: 自定义日志格式化器，为不同级别的日志添加彩色输出
  DEBUG (青色) | INFO (绿色) | WARNING (黄色) | ERROR (红色) | CRITICAL (紫色)
  
- setup_logger(name, level): 创建并配置一个彩色日志记录器
  支持自定义日志名称和级别
  输出到控制台，防止重复添加处理器

使用示例：
    from law_ai.logger import setup_logger
    import logging
    
    # 创建不同的日志记录器
    app_logger = setup_logger("AppLogger", level=logging.INFO)
    chain_logger = setup_logger("ChainLogger", level=logging.DEBUG)
    
    # 输出不同级别的日志
    app_logger.debug("这是 DEBUG 信息 (不会显示，因为日志级别是 INFO)")
    app_logger.info("✓ 这是 INFO 信息 (绿色)")
    app_logger.warning("⚠ 这是 WARNING 信息 (黄色)")
    app_logger.error("✗ 这是 ERROR 信息 (红色)")
    
    chain_logger.debug("🔧 这是 DEBUG 信息 (青色，因为日志级别是 DEBUG)")
    
    # 输出示例（在终端中显示彩色）:
    # [INFO] [AppLogger] ✓ 这是 INFO 信息 (绿色)
    # [WARNING] [AppLogger] ⚠ 这是 WARNING 信息 (黄色)
    # [ERROR] [AppLogger] ✗ 这是 ERROR 信息 (红色)
    # [DEBUG] [ChainLogger] 🔧 这是 DEBUG 信息 (青色，因为日志级别是 DEBUG)
"""
import logging
import sys
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_level = record.levelname
        color = self.COLORS.get(log_level, '')
        
        # 添加时间戳和颜色
        record.levelname = f"{color}[{log_level}]{self.RESET}"
        
        formatter = logging.Formatter(
            '%(levelname)s [%(name)s] %(message)s'
        )
        return formatter.format(record)


def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 移除已有的处理器，避免重复
    logger.handlers = []
    
    # 添加控制台处理器
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    formatter = ColoredFormatter()
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger


# 创建全局日志记录器
retriever_logger = setup_logger("Retriever")
chain_logger = setup_logger("Chain")
app_logger = setup_logger("App")
