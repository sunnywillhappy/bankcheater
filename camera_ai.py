import argparse
import getpass
import os
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
from google import genai
from google.genai import types


@dataclass
class CameraAIConfig:
    model: str
    prompt: str
    camera_index: int
    interval: float
    show_window: bool
    api_key: str
    strict_model: bool


def load_api_key(from_cli: str | None) -> str:
    if from_cli:
        return from_cli.strip()

    env_key = os.getenv('GEMINI_API_KEY', '').strip()
    if env_key:
        return env_key

    env_file = Path('.env')
    if env_file.exists():
        for raw_line in env_file.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            if key.strip() == 'GEMINI_API_KEY':
                return value.strip().strip('"').strip("'")

    manual_key = getpass.getpass('未检测到 Gemini API Key，请直接输入（输入不回显）: ').strip()
    if manual_key:
        return manual_key

    raise EnvironmentError(
        '未找到 Gemini API Key。请任选其一：\n'
        '1) 命令行参数：python camera_ai.py --api-key "AIza..."\n'
        '2) 环境变量（Windows PowerShell）：$env:GEMINI_API_KEY="AIza..."\n'
        '3) 在脚本同目录创建 .env 文件并写入：GEMINI_API_KEY=AIza...\n'
        '4) 启动后按提示手动输入 API Key'
    )


def validate_api_key_format(api_key: str) -> None:
    if not api_key.startswith('AIza'):
        raise ValueError(
            'Gemini API Key 格式看起来不对（通常以 "AIza" 开头）。\n'
            '请确认你粘贴的是 Google AI Studio 的 API Key，而不是其他平台的密钥。'
        )


def list_generate_content_models(client: genai.Client) -> list[str]:
    models = []
    for m in client.models.list():
        supported = getattr(m, 'supported_actions', None) or []
        name = getattr(m, 'name', '')
        if not name:
            continue
        if 'generateContent' in supported:
            models.append(name.replace('models/', ''))
    return models


def pick_fallback_model(available_models: list[str]) -> str | None:
    if not available_models:
        return None
    for name in available_models:
        if 'flash' in name:
            return name
    return available_models[0]


def preflight_check(client: genai.Client, model: str, strict_model: bool) -> str:
    try:
        client.models.generate_content(
            model=model,
            contents='Reply with OK only.',
        )
        return model
    except Exception as exc:
        msg = str(exc)
        if '404' in msg and 'not found' in msg.lower():
            available_models = list_generate_content_models(client)
            if strict_model:
                raise RuntimeError(
                    '指定模型不可用（404 NOT_FOUND）。\n'
                    f'你传入: {model}\n'
                    f'当前可用于 generateContent 的模型: {available_models[:10]}'
                ) from exc

            fallback = pick_fallback_model(available_models)
            if fallback:
                print(f'⚠️ 指定模型 {model} 不可用，自动切换到: {fallback}')
                return fallback

            raise RuntimeError(
                '指定模型不可用（404 NOT_FOUND），且无法获取可用模型列表。\n'
                '请检查网络是否可访问 Gemini API，或稍后重试。'
            ) from exc

        if '400' in msg:
            raise RuntimeError(
                'Gemini 返回 400 Bad Request。常见原因：\n'
                '1) API Key 无效/粘贴错误（请重新生成并粘贴）\n'
                '2) 使用了不可用模型名（可尝试 --model gemini-2.0-flash）\n'
                '3) 网络环境拦截了 Google 接口，返回 HTML 错误页\n'
                f'原始错误: {msg}'
            ) from exc
        if '401' in msg or '403' in msg:
            raise RuntimeError(
                'Gemini 鉴权失败（401/403）。请检查 API Key 是否正确、是否有权限。\n'
                f'原始错误: {msg}'
            ) from exc
        raise RuntimeError(f'Gemini 预检查失败: {msg}') from exc


def encode_frame_to_jpeg_bytes(frame) -> bytes:
    ok, buffer = cv2.imencode('.jpg', frame)
    if not ok:
        raise RuntimeError('无法将摄像头画面编码为 JPG')
    return buffer.tobytes()


def analyze_frame(client: genai.Client, model: str, frame, prompt: str) -> str:
    image_bytes = encode_frame_to_jpeg_bytes(frame)
    response = client.models.generate_content(
        model=model,
        contents=[
            prompt,
            types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'),
        ],
    )
    return (response.text or '').strip()


def run(config: CameraAIConfig) -> None:
    validate_api_key_format(config.api_key)

    client = genai.Client(api_key=config.api_key)
    active_model = preflight_check(client, config.model, config.strict_model)

    cap = cv2.VideoCapture(config.camera_index)
    if not cap.isOpened():
        raise RuntimeError(f'无法打开摄像头 index={config.camera_index}')

    last_sent = 0.0

    print('Gemini 连接检查通过。')
    print(f'当前模型: {active_model}')
    print('摄像头已开启。按 q 退出。')
    print(f'每 {config.interval} 秒发送一帧给 Gemini 分析...')

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print('读取摄像头画面失败，跳过本帧。')
                continue

            if config.show_window:
                cv2.imshow('Camera Preview (press q to quit)', frame)

            now = time.time()
            if now - last_sent >= config.interval:
                last_sent = now
                try:
                    result = analyze_frame(client, active_model, frame, config.prompt)
                    print('-' * 60)
                    print(f'[{time.strftime("%H:%M:%S")}] Gemini 分析结果：')
                    print(result or '(空结果)')
                except Exception as exc:
                    print(f'调用 Gemini 接口失败: {exc}')

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


def parse_args() -> CameraAIConfig:
    parser = argparse.ArgumentParser(
        description='调用电脑摄像头并将画面通过 Gemini API 发给 AI 分析。'
    )
    parser.add_argument(
        '--model',
        default='gemini-2.0-flash',
        help='用于图像分析的 Gemini 模型名 (默认: gemini-2.0-flash)',
    )
    parser.add_argument(
        '--prompt',
        default='请描述这张图片中发生了什么，并指出可能的风险或异常。',
        help='发送给 AI 的提示词',
    )
    parser.add_argument(
        '--camera-index',
        type=int,
        default=0,
        help='摄像头编号 (默认: 0)',
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=3.0,
        help='每隔多少秒发送一帧到 AI (默认: 3 秒)',
    )
    parser.add_argument(
        '--no-window',
        action='store_true',
        help='不显示本地摄像头预览窗口',
    )
    parser.add_argument(
        '--api-key',
        default=None,
        help='可直接传入 Gemini API Key；未传时自动尝试环境变量、.env 或启动时输入',
    )
    parser.add_argument(
        '--strict-model',
        action='store_true',
        help='模型不可用时不自动回退，直接报错退出',
    )

    args = parser.parse_args()
    return CameraAIConfig(
        model=args.model,
        prompt=args.prompt,
        camera_index=args.camera_index,
        interval=max(0.5, args.interval),
        show_window=not args.no_window,
        api_key=load_api_key(args.api_key),
        strict_model=args.strict_model,
    )


if __name__ == '__main__':
    run(parse_args())
