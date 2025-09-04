# === 模拟 Gradio 前端输入 ===
# 用户可以直接在这里修改参数，模拟前端操作

# 注意：请确保所有 path 都是真实有效的路径，否则程序会出错。
# Windows 示例: "C:/Users/YourUser/Desktop/MyVideos"
# Mac/Linux 示例: "/Users/youruser/videos"

PARAMS = {
    "global": {
        "num_videos": 1  # 要生成的视频总数
    },
    "hook": {
        "enabled": True,             # 是否启用 Hook
        "path": "/Users/samsun/code/mixclip/test_media/hook/hook.mp4" # Hook 视频路径
    },
    "middles": [
        # 可以有 1 到 5 个 Middle 设置, 最多为 5 个
        {
            "path": "/Users/samsun/code/mixclip/test_media/middle1", # Middle 1 文件夹路径
            "intervals": 2.0,                # Middle 1 视频截取时长
            "count": 10                       # 每个最终视频使用多少个 Middle 1 片段
        },
        {
            "path": "/Users/samsun/code/mixclip/test_media/middle2",
            "intervals": 3.0,
            "count": 3
        }
    ],
    "code": {
        "enabled": True,              # 是否启用 Code
        "path": "/Users/samsun/code/mixclip/test_media/code/code.mp4"   # Code 视频路径
    }
}


# === 全局视频规格设置 ===
# 这些参数通常保持不变，不通过前端传递

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30