import logging
import sys

# 获取一个 logger 实例
logger = logging.getLogger('MixClipLogger')

def setup_logger(log_file_path: str):
    """配置日志记录器"""
    # 设置日志级别
    logger.setLevel(logging.DEBUG)

    # 创建一个文件处理器，用于写入日志文件
    file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 创建一个流处理器，用于在控制台输出
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)

    # 定义日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # 添加处理器到 logger
    # 防止重复添加 handler
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)