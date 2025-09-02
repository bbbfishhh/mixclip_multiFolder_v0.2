import os
import datetime
import sys
import time

# 导入配置和核心功能
import config
import video_processor
from logger import setup_logger, logger

def run_processing(params: dict) -> str:
    """
    接收参数并执行视频混剪的核心逻辑。
    返回输出文件夹的路径。
    """
    try:
        # --- 准备工作 ---
        num_videos = params["global"]["num_videos"]

        # 创建输出目录和日志
        date_str = datetime.date.today().strftime('%Y-%m-%d')
        timestamp_str = datetime.datetime.now().strftime('%H%M%S')

        output_folder_name = f"{date_str}-total{num_videos}"
        output_dir = os.path.join('output', output_folder_name)
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置日志
        log_filename = f"mix-log-{date_str}-{timestamp_str}.txt"
        log_file = os.path.join(output_dir, log_filename)
        setup_logger(log_file)
        
        logger.info(f"所有输出视频和日志将保存在: {os.path.abspath(output_dir)}")
        
        # --- 阶段一：分析与创建片段池 ---
        clip_pools, pointers = video_processor.create_clip_pools(params["middles"])
        
        # --- 阶段二：生成剪辑清单 ---
        all_edit_lists = video_processor.generate_final_edit_lists(params, clip_pools, pointers)
        
        # --- 阶段三：渲染 ---
        logger.info("\n--- 开始批量渲染视频 ---")
        total_videos = len(all_edit_lists)
        for i, edit_list in enumerate(all_edit_lists):
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"mixclip_v1_{timestamp}_{i+1:03d}.mp4"
            output_filepath = os.path.join(output_dir, output_filename)
            
            logger.info(f"--> 正在生成第 {i + 1}/{total_videos} 个视频: {output_filename}")
            video_processor.render_video(edit_list, output_filepath, config)
        
        logger.info("\n--- 所有任务已完成！---")
        success_message = f"成功生成 {total_videos} 个视频，保存在: {os.path.abspath(output_dir)}"
        logger.info(success_message)
        return success_message

    except (ValueError, FileNotFoundError) as e:
        logger.error(f"发生错误: {e}", exc_info=True)
        raise e  # 重新抛出异常，以便上层（如Gradio）可以捕获
    except Exception as e:
        logger.error(f"发生未知错误: {e}", exc_info=True)
        raise e


def main():
    """
    主函数，用于直接运行脚本，从 config.py 加载配置。
    """
    print("--- 自动化视频混剪工具 (v2.0) - 命令行模式 ---")
    try:
        run_processing(config.PARAMS)
    except (ValueError, FileNotFoundError) as e:
        print(f"\n错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生未知错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()