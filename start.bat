@echo off
chcp 65001 > nul

echo.
echo ============================================
echo   正在准备启动 MixClip 视频混剪工具...
echo ============================================
echo.

echo [步骤 1/2] 正在检查并安装所需组件...
pip install -r requirements.txt

echo.
echo [步骤 2/2] 正在启动程序...
echo 请稍等片刻，浏览器会自动打开操作页面。
echo.
echo 注意：使用期间请不要关闭此窗口！
echo.

python app.py

pause