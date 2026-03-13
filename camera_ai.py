import argparse
import base64
import os
import time
from dataclasses import dataclass

import cv2
from openai import OpenAI


@dataclass
class CameraAIConfig:
    model: str
    prompt: str
    camera_index: int
    interval: float
    show_window: bool


def encode_frame_to_data_url(frame) -> str:
    ok, buffer = cv2.imencode('.jpg', frame)
    if not ok:
        raise RuntimeError('无法将摄像头画面编码为 JPG')
    b64 = base64.b64encode(buffer).decode('utf-8')
    return f'data:image/jpeg;base64,{b64}'


def analyze_frame(client: OpenAI, frame, model: str, prompt: str) -> str:
    image_data_url = encode_frame_to_data_url(frame)
    response = client.responses.create(
        model=model,
        input=[
            {
                'role': 'user',
                'content': [
                    {'type': 'input_text', 'text': prompt},
                    {'type': 'input_image', 'image_url': image_data_url},
                ],
            }
        ],
    )
    return response.output_text.strip()


def run(config: CameraAIConfig) -> None:
    if not os.getenv('OPENAI_API_KEY'):
        raise EnvironmentError('请先设置 OPENAI_API_KEY 环境变量')

    cap = cv2.VideoCapture(config.camera_index)
    if not cap.isOpened():
        raise RuntimeError(f'无法打开摄像头 index={config.camera_index}')

    client = OpenAI()
    last_sent = 0.0

    print('摄像头已开启。按 q 退出。')
    print(f'每 {config.interval} 秒发送一帧给 AI 分析...')

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
                    result = analyze_frame(client, frame, config.model, config.prompt)
                    print('-' * 60)
                    print(f'[{time.strftime("%H:%M:%S")}] AI 分析结果：')
                    print(result or '(空结果)')
                except Exception as exc:
                    print(f'调用 AI 接口失败: {exc}')

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


def parse_args() -> CameraAIConfig:
    parser = argparse.ArgumentParser(
        description='调用电脑摄像头并将画面通过 API 发给 AI 分析。'
    )
    parser.add_argument(
        '--model',
        default='gpt-4.1-mini',
        help='用于图像分析的模型名 (默认: gpt-4.1-mini)',
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

    args = parser.parse_args()
    return CameraAIConfig(
        model=args.model,
        prompt=args.prompt,
        camera_index=args.camera_index,
        interval=max(0.5, args.interval),
        show_window=not args.no_window,
    )


if __name__ == '__main__':
    run(parse_args())
