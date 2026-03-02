# coding: utf-8
"""
日志输出与格式化模块

功能说明：
- ColoredFormatter: 自定义日志格式化器，为不同级别的日志添加彩色输出
  DEBUG (青色) | INFO (绿色) | WARNING (黄色) | ERROR (红色) | CRITICAL (紫色)
  
- setup_logger(name, level): 创建并配置一个日志记录器
  同时输出到控制台（彩色）和 logs/app.log 文件（纯文本，按天滚动）
  日志文件保留最近 7 天

使用示例：
    from law_ai.logger import setup_logger
    import logging
    
    app_logger = setup_logger("App", level=logging.INFO)
    app_logger.info("✓ 服务启动")
    app_logger.warning("⚠ 检测到异常")
    app_logger.error("✗ 错误信息")
"""
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

# ── 日志目录 ─────────────────────────────────────────────────────────────────
_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, "app.log")


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器（用于控制台）"""
    
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
        record.levelname = f"{color}[{log_level}]{self.RESET}"
        formatter = logging.Formatter('%(levelname)s [%(name)s] %(message)s')
        return formatter.format(record)


class PlainFormatter(logging.Formatter):
    """纯文本日志格式化器（用于文件）"""
    
    def format(self, record):
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return formatter.format(record)


def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """设置日志记录器，同时输出到控制台和 logs/app.log"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # ── 控制台处理器（彩色）──────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)
    
    # ── 文件处理器（按天滚动，保留 7 天）────────────────────
    file_handler = TimedRotatingFileHandler(
        _LOG_FILE,
        when='midnight',     # 每天零点滚动
        interval=1,
        backupCount=7,       # 保留最近 7 天
        encoding='utf-8'
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(level)
    file_handler.setFormatter(PlainFormatter())
    logger.addHandler(file_handler)
    
    logger.propagate = False
    return logger


# 创建全局日志记录器
retriever_logger = setup_logger("Retriever")
chain_logger = setup_logger("Chain")
app_logger = setup_logger("App")
