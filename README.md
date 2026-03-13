# Camera to AI Demo

一个最小可运行示例：
1. 调用电脑摄像头实时读取画面。
2. 每隔固定时间抓取一帧。
3. 通过 OpenAI API 把图片发送给 AI。
4. 在终端输出 AI 返回的分析结果。

## 1) 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) 设置 API Key

```bash
export OPENAI_API_KEY="你的key"
```

## 3) 运行

```bash
python camera_ai.py
```

可选参数：

```bash
python camera_ai.py \
  --model gpt-4.1-mini \
  --prompt "请识别画面中的人物动作，并用中文给出建议" \
  --camera-index 0 \
  --interval 2
```

按 `q` 退出。

## 说明

- 本项目默认使用 `OpenAI Responses API` 的图像输入能力。
- 如果你需要“把摄像头能力封装成 HTTP 服务”（例如前端上传截图到后端再请求 AI），可在此脚本基础上再加 FastAPI。当前版本先给你一个最直接可运行的端到端脚本。
