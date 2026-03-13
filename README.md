# Camera to Gemini Demo (google.genai)

一个最小可运行示例：
1. 调用电脑摄像头实时读取画面。
2. 每隔固定时间抓取一帧。
3. 通过 Gemini API（google.genai SDK）把图片发送给 AI。
4. 在终端输出 AI 返回的分析结果。

## 1) 安装依赖（先升级 pip，避免编译报错）

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install --no-cache-dir -r requirements.txt
```

Windows（PowerShell）可用：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install --no-cache-dir -r requirements.txt
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
  --model gemini-2.0-flash \
  --prompt "请识别画面中的人物动作，并用中文给出建议" \
  --camera-index 0 \
  --interval 2
```

按 `q` 退出。

## 模型 404 的处理

- 如果你指定的模型不可用（例如你遇到的 `gemini-1.5-flash` 404），脚本会自动调用 `ListModels` 找可用模型并自动回退（优先 flash）。
- 你会在终端看到：`指定模型 xxx 不可用，自动切换到: yyy`。
- 如果你不想自动回退，增加参数：`--strict-model`。

## 常见问题

- 报错 `未找到 Gemini API Key`：请按“配置 Gemini API Key”里的任一方式设置，或启动后手动输入。
- 报错 `Gemini API Key 格式看起来不对`：你可能粘贴了非 Gemini Key。Gemini Key 通常以 `AIza` 开头。
- 报错 `Gemini 返回 400 Bad Request`：
  1) Key 无效或复制不完整；
  2) 模型名不可用（先试默认模型）；
  3) 网络把 Google 接口拦截成 HTML 错误页（`<html>...400...`）。
- 安装时报 `Failed building wheel for tiktoken`：
  1) 你当前项目不需要 `openai`/`tiktoken`，只需要 `google-genai` + `opencv-python`。先执行：
     - `python -m pip uninstall -y openai tiktoken`
  2) 再执行本 README 的“安装依赖（先升级 pip）”四条命令重新安装。
  3) 如果你是复用旧虚拟环境，建议删除 `.venv` 后重新创建，避免旧依赖残留。
