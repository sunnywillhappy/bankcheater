# Camera to Gemini Demo

一个最小可运行示例：
1. 调用电脑摄像头实时读取画面。
2. 每隔固定时间抓取一帧。
3. 通过 Gemini API 把图片发送给 AI。
4. 在终端输出 AI 返回的分析结果。

## 1) 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows（PowerShell）可用：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) 配置 Gemini API Key（4 选 1）

### 方式 A：命令行直接传

```bash
python camera_ai.py --api-key "AIza..."
```

### 方式 B：环境变量

Linux / macOS:

```bash
export GEMINI_API_KEY="AIza..."
```

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="AIza..."
```

### 方式 C：在项目根目录放 `.env`

创建 `.env` 文件并写入：

```env
GEMINI_API_KEY=AIza...
```

### 方式 D：启动后按提示输入

如果没配置 A/B/C，脚本会自动提示你输入 key（输入不回显）。

## 3) 运行（Windows 建议用 `python` 启动）

```bash
python camera_ai.py
```

可选参数：

```bash
python camera_ai.py \
  --model gemini-1.5-flash \
  --prompt "请识别画面中的人物动作，并用中文给出建议" \
  --camera-index 0 \
  --interval 2
```

按 `q` 退出。

## 常见问题

- 报错 `未找到 Gemini API Key`：请按“配置 Gemini API Key”里的任一方式设置，或启动后手动输入。
- 摄像头打不开：尝试 `--camera-index 1` 或检查系统隐私权限中是否允许 Python 访问摄像头。
