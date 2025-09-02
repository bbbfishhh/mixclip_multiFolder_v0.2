import gradio as gr
import main
from typing import List, Dict, Any
import os

MAX_MIDDLE_FOLDERS = 5

def process_videos(*args):
    """
    从 Gradio 界面收集输入，格式化为参数字典，然后调用后端处理函数。
    """
    # 正确地从扁平化的 args 元组中解析参数
    # 前5个是全局/hook/code参数
    enable_hook = args[0]
    hook_path = args[1]
    enable_code = args[2]
    code_path = args[3]
    num_videos = args[4]

    # 接下来是 middle 的参数，按 MAX_MIDDLE_FOLDERS (5) 个一组进行切片
    offset = 5
    middle_visibilities = args[offset : offset + MAX_MIDDLE_FOLDERS]
    offset += MAX_MIDDLE_FOLDERS
    middle_paths = args[offset : offset + MAX_MIDDLE_FOLDERS]
    offset += MAX_MIDDLE_FOLDERS
    middle_intervals = args[offset : offset + MAX_MIDDLE_FOLDERS]
    offset += MAX_MIDDLE_FOLDERS
    middle_counts = args[offset : offset + MAX_MIDDLE_FOLDERS]

    # 构建参数字典
    params: Dict[str, Any] = {
        "global": {"num_videos": int(num_videos)},
        "hook": {"enabled": enable_hook, "path": hook_path if hook_path else None},
        "code": {"enabled": enable_code, "path": code_path if code_path else None},
        "middles": []
    }

    # 验证并填充 middle 部分
    for i in range(MAX_MIDDLE_FOLDERS):
        if middle_visibilities[i]:
            # 从 Textbox 获取路径字符串并去除首尾空格
            folder_path = middle_paths[i].strip() if middle_paths[i] else ""
            
            if not folder_path:
                return f"[错误] Middle 文件夹 #{i+1} 的路径不能为空。"
            
            params["middles"].append({
                "path": folder_path,
                "intervals": float(middle_intervals[i]),
                "count": int(middle_counts[i])
            })
    
    if not params["middles"]:
        return "[错误] 至少需要一个 Middle 文件夹配置。"

    # 调用后端处理逻辑
    try:
        gr.Info("任务已开始，正在后台处理视频...")
        result_message = main.run_processing(params)
        return f"[成功] {result_message}"
    except Exception as e:
        return f"[发生严重错误] {e}"


# --- Gradio 界面构建 ---
with gr.Blocks(theme=gr.themes.Soft(), title="自动化视频混剪工具") as app:
    gr.Markdown("# 自动化视频混剪工具 v2.0")
    gr.Markdown("请按以下步骤配置参数，然后点击“生成视频”按钮。")

    with gr.Row():
        with gr.Column(scale=2):
            # 全局设置
            with gr.Group():
                gr.Markdown("## 1. 全局设置")
                num_videos_input = gr.Number(label="要生成的视频总数", value=10, minimum=1, step=1)
            
            # Hook 和 Code 启用开关
            with gr.Group():
                gr.Markdown("## 2. 开头 (Hook) & 结尾 (Code) 设置")
                with gr.Row():
                    enable_hook_checkbox = gr.Checkbox(label="启用 Hook 视频 (开头)", value=True)
                    enable_code_checkbox = gr.Checkbox(label="启用 Code 视频 (结尾)", value=True)
            
            # Hook 配置 (文件选择)
            with gr.Group(visible=True) as hook_box:
                gr.Markdown("### Hook 视频文件")
                hook_file_input = gr.File(label="选择 Hook 视频文件", file_count="single", type="filepath")
            
            # Code 配置 (文件选择)
            with gr.Group(visible=True) as code_box:
                gr.Markdown("### Code 视频文件")
                code_file_input = gr.File(label="选择 Code 视频文件", file_count="single", type="filepath")

            # Middle 配置 (路径输入)
            with gr.Group():
                gr.Markdown("## 3. 中间 (Middle) 素材设置")
                gr.Markdown("请直接粘贴素材文件夹的**绝对路径**。")
                
                middle_boxes = []
                middle_visibilities_state = []
                middle_path_inputs = []
                middle_interval_inputs = []
                middle_count_inputs = []

                for i in range(MAX_MIDDLE_FOLDERS):
                    is_visible = (i == 0)
                    with gr.Group(visible=is_visible) as middle_box:
                        gr.Markdown(f"#### Middle 文件夹 #{i+1}")
                        # 将 gr.File 更改为 gr.Textbox
                        path = gr.Textbox(label="素材文件夹路径", placeholder="例如: /Users/samsun/code/mixclip/test_media/middle1", scale=2)
                        with gr.Row():
                            intervals = gr.Number(label="截取秒数", value=2.0, minimum=0.1, scale=1)
                            count = gr.Number(label="片段数", value=1, minimum=1, step=1, scale=1)

                    middle_boxes.append(middle_box)
                    middle_visibilities_state.append(gr.State(is_visible))
                    middle_path_inputs.append(path)
                    middle_interval_inputs.append(intervals)
                    middle_count_inputs.append(count)

                with gr.Row():
                    add_button = gr.Button("➕ 添加一个 Middle 文件夹")
                    remove_button = gr.Button("➖ 移除最后一个 Middle 文件夹")
            
            # 生成按钮和输出
            with gr.Group():
                gr.Markdown("## 4. 开始生成")
                generate_button = gr.Button("🚀 生成视频", variant="primary", size="lg")
                output_textbox = gr.Textbox(label="处理结果", lines=3, interactive=False)

        # 侧边栏说明
        with gr.Column(scale=1):
            with gr.Group():
                gr.Markdown(
                    """
                    ### 使用说明
                    1.  **全局设置**: ...
                    2.  **Hook & Code**: ...
                    3.  **Middle 素材**:
                        -   **素材文件夹路径**: 将包含视频素材的文件夹的**绝对路径**粘贴到输入框中。
                        -   **截取秒数**: ...
                        -   **片段数**: ...
                    4.  **生成**: ...
                    """
                )

    # --- 事件处理逻辑 (无需更改) ---
    enable_hook_checkbox.change(lambda x: gr.update(visible=x), enable_hook_checkbox, hook_box)
    enable_code_checkbox.change(lambda x: gr.update(visible=x), enable_code_checkbox, code_box)

    def add_middle_folder(*visibilities):
        new_visibilities = list(visibilities)
        for i in range(len(new_visibilities)):
            if not new_visibilities[i]:
                new_visibilities[i] = True
                break
        updates = [gr.update(visible=v) for v in new_visibilities]
        return updates + new_visibilities
    
    add_button.click(
        add_middle_folder, 
        inputs=middle_visibilities_state, 
        outputs=middle_boxes + middle_visibilities_state
    )

    def remove_middle_folder(*visibilities):
        new_visibilities = list(visibilities)
        for i in range(len(new_visibilities) - 1, 0, -1):
            if new_visibilities[i]:
                new_visibilities[i] = False
                break
        updates = [gr.update(visible=v) for v in new_visibilities]
        return updates + new_visibilities

    remove_button.click(
        remove_middle_folder,
        inputs=middle_visibilities_state,
        outputs=middle_boxes + middle_visibilities_state
    )

    all_inputs = [
        enable_hook_checkbox, hook_file_input,
        enable_code_checkbox, code_file_input,
        num_videos_input,
    ] + middle_visibilities_state + middle_path_inputs + middle_interval_inputs + middle_count_inputs

    generate_button.click(
        fn=process_videos,
        inputs=all_inputs,
        outputs=output_textbox
    )

if __name__ == "__main__":
    app.launch()