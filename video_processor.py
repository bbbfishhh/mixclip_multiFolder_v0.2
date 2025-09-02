import os
import subprocess
import random
import time
import shutil
from typing import List, Dict, Any, Tuple, Union

# 导入日志记录器
from logger import logger

def get_video_duration(video_path: str) -> float:
    """使用 ffprobe 获取视频的时长（秒）"""
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return float(result.stdout)
    except (subprocess.CalledProcessError, ValueError) as e:
        logger.warning(f"无法获取视频 {os.path.basename(video_path)} 的时长，已跳过。错误: {e}")
        return 0.0


def create_clip_pools(middle_configs: List[Dict[str, Any]]) -> (List[List[Tuple[str, float]]], List[int]):
    """
    为每个 middle 文件夹创建并处理片段池 (重构版)。
    """
    logger.info("--- (重构版) 开始创建素材片段池 ---")
    clip_pools = []
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv')

    # 遍历每个 middle 文件夹的配置
    for i, config in enumerate(middle_configs):
        folder_path = config["path"]
        interval = config["intervals"]
        logger.info(f"正在处理 Middle 文件夹 #{i+1}: {folder_path}")

        if not os.path.isdir(folder_path):
            raise FileNotFoundError(f"错误：Middle 文件夹 '{folder_path}' 不存在。")

        current_pool = []
        video_files_in_folder = [f for f in os.listdir(folder_path) if f.lower().endswith(video_extensions)]
        
        logger.info(f"在 '{folder_path}' 中找到 {len(video_files_in_folder)} 个视频文件。")

        # 遍历文件夹中的每一个视频文件
        for filename in video_files_in_folder:
            video_path = os.path.join(folder_path, filename)
            video_duration = get_video_duration(video_path)
            
            clips_from_this_video = 0
            if video_duration >= interval:
                start_time = 0.0
                while start_time + interval <= video_duration:
                    current_pool.append((video_path, start_time))
                    start_time += interval
                    clips_from_this_video += 1
            
            if clips_from_this_video > 0:
                logger.debug(f"  - 从 '{filename}' 生成了 {clips_from_this_video} 个片段。")
            else:
                logger.debug(f"  - '{filename}' 时长不足，未生成片段。")
        
        if not current_pool:
            logger.warning(f"警告：Middle 文件夹 '{folder_path}' 中未找到足够时长的视频来创建任何片段。")
            # 即使池为空，也添加一个空池以保持索引对齐
            clip_pools.append([])
            continue

        random.shuffle(current_pool)
        clip_pools.append(current_pool)
        logger.info(f"Middle #{i+1} 片段池创建完成，共包含 {len(current_pool)} 个片段。")
        logger.debug(f"片段池 #{i+1} 内容 (前5个): {current_pool[:5]}")

    if not any(clip_pools):
        raise ValueError("错误：所有 Middle 文件夹都未能成功创建片段池，无法继续。")
        
    pointers = [0] * len(clip_pools)
    logger.info("--- 所有片段池创建完毕 ---")
    return clip_pools, pointers

def generate_final_edit_lists(params: Dict[str, Any], clip_pools: List[List[Tuple[str, float]]], pointers: List[int]) -> List[List[Union[str, Tuple[str, float, float]]]]:
    """
    根据参数、片段池和指针，生成所有最终视频的剪辑清单。
    """
    logger.info("--- 开始生成最终剪辑清单 ---")
    num_videos_to_generate = params["global"]["num_videos"]
    hook_info = params["hook"]
    middle_configs = params["middles"]
    code_info = params["code"]

    all_final_lists = []

    for i in range(num_videos_to_generate):
        final_video_sequence = []
        log_sequence_details = []

        # 1. 添加 Hook 视频
        if hook_info["enabled"]:
            final_video_sequence.append(hook_info["path"])
            log_sequence_details.append(f"Hook: {os.path.basename(hook_info['path'])}")

        # 2. 从每个 Middle 片段池中挑选片段
        for j, middle_config in enumerate(middle_configs):
            clips_to_take = middle_config["count"]
            current_pool = clip_pools[j]
            pool_size = len(current_pool)
            
            if pool_size == 0:
                logger.warning(f"Middle #{j+1} 片段池为空，跳过。")
                continue

            log_middle_details = []
            for _ in range(clips_to_take):
                current_pointer = pointers[j]
                selected_clip_index = current_pointer % pool_size
                video_path, start_time = current_pool[selected_clip_index]
                
                # 添加 (视频路径, 起始时间, 截取时长)
                final_video_sequence.append((video_path, start_time, middle_config["intervals"]))
                
                log_middle_details.append(f"片段{selected_clip_index}({os.path.basename(video_path)} @{start_time:.2f}s)")
                
                pointers[j] += 1
            
            log_sequence_details.append(f"Middle#{j+1}: " + ", ".join(log_middle_details) + f" (指针 -> {pointers[j]})")


        # 3. 添加 Code 视频
        if code_info["enabled"]:
            final_video_sequence.append(code_info["path"])
            log_sequence_details.append(f"Code: {os.path.basename(code_info['path'])}")
        
        all_final_lists.append(final_video_sequence)
        logger.info(f"视频 #{i+1} 剪辑清单生成: {' | '.join(log_sequence_details)}")

    logger.info("--- 所有剪辑清单生成完毕 ---")
    return all_final_lists

def render_video(edit_list: list, output_filepath: str, config):
    """
    根据单个剪辑清单，裁剪、标准化、拼接并生成最终视频。
    """
    output_folder = os.path.dirname(output_filepath)
    temp_dir = os.path.join(output_folder, f'temp_{os.path.basename(output_filepath)}')
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        temp_clip_paths = []
        concat_list_path = os.path.join(temp_dir, 'concat_list.txt')

        for i, clip_info in enumerate(edit_list):
            temp_clip_path = os.path.join(temp_dir, f'clip_{i:03d}.mp4')
            temp_clip_paths.append(temp_clip_path)

            if isinstance(clip_info, str): # Hook 或 Code 视频
                video_path = clip_info
                ffmpeg_command = [
                    'ffmpeg', '-y', '-i', video_path,
                    '-vf', f'scale={config.TARGET_WIDTH}:{config.TARGET_HEIGHT}:force_original_aspect_ratio=decrease,pad={config.TARGET_WIDTH}:{config.TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={config.TARGET_FPS}',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
                    '-an', temp_clip_path
                ]
            else: # Middle 视频片段
                video_path, start_time, duration = clip_info
                ffmpeg_command = [
                    'ffmpeg', '-y', '-ss', str(start_time), '-i', video_path,
                    '-t', str(duration),
                    '-vf', f'scale={config.TARGET_WIDTH}:{config.TARGET_HEIGHT}:force_original_aspect_ratio=decrease,pad={config.TARGET_WIDTH}:{config.TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={config.TARGET_FPS}',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
                    '-an', temp_clip_path
                ]
            
            subprocess.run(ffmpeg_command, check=True, capture_output=True)

        with open(concat_list_path, 'w') as f:
            for path in temp_clip_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")

        concat_command = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_list_path, '-c', 'copy', output_filepath
        ]
        subprocess.run(concat_command, check=True, capture_output=True)
        
        logger.info(f"成功渲染视频: {os.path.basename(output_filepath)}")

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)