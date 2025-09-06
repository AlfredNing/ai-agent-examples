from loguru import logger
import sys


# 日志格式
logger_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}"

# 移除默认的日志配置
logger.remove()

# 定义统一格式
logger.add(sys.stdout, level="DEBUG", format=logger_format, colorize=True)
logger.add(sys.stderr, level="ERROR", format=logger_format, colorize=True)

# 日志文件
logger.add("logs/app.log", rotation="1 MB", level="DEBUG", format=logger_format, )

LOG = logger

__all__ = ["LOG"]
