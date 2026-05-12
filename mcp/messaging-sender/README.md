# Feishu + Discord + Dot. Sender MCP

统一的消息发送 MCP，支持飞书、Discord、Dot. 墨水屏设备。凭证外置，源码不含敏感信息。

## 快速开始

### 1. 克隆后配置凭证

```bash
cp config.json.example config.json
# 编辑 config.json，填入真实凭证
```

### 2. 配置示例（config.json）

```json
{
  "feishu": {
    "app_id": "cli_xxxx",
    "app_secret": "xxxx"
  },
  "discord": {
    "bot_token": "Bot xxxx"
  },
  "dot": {
    "api_key": "dot_app_xxxx",
    "device_id": "XXXXXXXXXXXX"
  }
}
```

> **Dot. 凭证获取方式：**
> - `api_key`：Dot. App → More → API Keys → Create API Key
> - `device_id`：Dot. App → Device → Device Serial Number

### 3. 注册到 OpenClaw

在 `openclaw.json` 的 `mcp.servers` 中添加：

```json
"messaging-sender": {
  "command": "python3",
  "args": ["/path/to/messaging-sender/server.py"]
}
```

## 工具

### 飞书

| 工具 | 说明 |
|------|------|
| `send_feishu_text` | 发送纯文本（最常用） |
| `send_to_feishu` | 通用接口，支持 text/post/interactive |

### Discord

| 工具 | 说明 |
|------|------|
| `send_discord_text` | 发送纯文本 |
| `send_to_discord` | 通用接口，支持文本或 embed JSON |

### Dot. 墨水屏

| 工具 | 说明 |
|------|------|
| `send_dot_text` | 在设备上显示文字（标题 + 正文 + 签名），支持 icon 字段传入任意图片自动处理 |
| `send_dot_image` | 在设备上显示 PNG 图片（支持本地路径或 base64） |
| `render_eink_template` | 用 JSON 模板渲染 1-bit 墨水屏图片，返回 base64 PNG（不发送，可调试） |
| `send_eink_template` | 渲染模板并直接发送到 Dot. 设备（一键完成） |

## 调用示例

### 飞书

```
tool: messaging-sender
name: send_feishu_text
arguments: {"text": "Hello!", "receive_id": "ou_xxx"}
```

### Discord

```
tool: messaging-sender
name: send_discord_text
arguments: {"text": "Hello!", "channel_id": "123456789"}
```

### Dot.

#### send_dot_text - icon 字段说明

**icon 字段只接受 base64 PNG**。

使用方式：先从 iconfont 渲染出 PNG，拿到 base64 再传入。

渲染脚本参考 `knowledge/icon-to-base64.py`，已预渲染的 icon 位于 `/Users/hm/openclaw-config/asset/font/icons/`。

```json
tool: messaging-sender
name: send_dot_text
arguments: {"title": "提醒", "message": "该喝水了", "signature": "AI助手", "icon": "<base64 PNG>"}
```

#### send_dot_image

```
tool: messaging-sender
name: send_dot_image
arguments: {"image_path": "/path/to/chart.png"}
```

## 模板渲染（render_eink_template / send_eink_template）

为 296×152 / 1-bit 墨水屏设计的模板化渲染器。把布局和数据分离，
让 AI 用 JSON 模板自由排版文字 + 图标 + 图片 + 二维码。

### 依赖

```bash
pip install -r requirements.txt
```

`Pillow` 必装；`qrcode` 仅在需要二维码元素时使用。

### 模板格式

最小示例：

```json
{
  "meta": { "width": 296, "height": 152, "background": "white" },
  "elements": [
    { "type": "text", "x": 8, "y": 8, "content": "Hello ${name}", "size": 16 },
    { "type": "line", "x1": 0, "y1": 32, "x2": 296, "y2": 32, "width": 2 },
    { "type": "qrcode", "x": 200, "y": 50, "size": 80, "content": "${url}" }
  ]
}
```

### 元素类型

| type | 关键字段 | 说明 |
|---|---|---|
| `text` | content / size / fonts / max_width / line_height / align / color | 支持 `${var}` 插值、自动换行、对齐 |
| `icon` | name / size / color | 优先按 iconfont.json 的 `font_class` 查字符；找不到则查 `icons/{size}/{name}.bmp` |
| `image` | src / width / height / dither | 支持本地路径或 `data:` URI；自动 Floyd-Steinberg dither 到 1-bit |
| `line` | x1, y1, x2, y2 / width / color | 直线 |
| `rect` | width / height / fill / stroke / stroke_width | 矩形 |
| `qrcode` | content / size / border | 自动生成二维码（需 `qrcode` 库） |
| `container` | layout (vbox/hbox/absolute) / gap / padding / children | 自动布局容器 |

### 字体策略

- 模板中可用 `fonts: ["source-han-bold", "ark-pixel-12"]` 指定字体优先级
- 始终在末尾追加系统字体（macOS PingFang）作为终极兜底，**永不出豆腐**
- 推荐字体（放到 `fonts/` 目录）：
  - `unifont.otf` — 通用兜底，[下载](https://unifoundry.com/unifont/)
  - `ark-pixel-12px-monospaced-zh_cn.otf` — 12px 中文像素字体
  - `SourceHanSansSC-Bold.otf` — 大字号标题

### 变量插值

模板中的 `${var}` 或 `${nested.path}` 占位符会被 `data` 字段替换：

```json
{ "type": "text", "content": "${user.name} 的待办" }
```

### 调用示例

只渲染（用于调试）：

```
tool: messaging-sender
name: render_eink_template
arguments: {
  "template": "schedule",
  "data": {"title": "今日待办", "date": "2026-05-11", "time": "14:00", "location": "会议室 A", "desc": "项目周会", "updated_at": "14:30"},
  "save_path": "/tmp/preview.png",
  "return_base64": false
}
```

渲染并直接发送到 Dot.：

```
tool: messaging-sender
name: send_eink_template
arguments: {
  "template": "weather",
  "data": {"city": "上海", "temp": "23", "condition": "多云", "humidity": "65", "wind": "东南风 3 级", "updated": "14:00"}
}
```

`template` 字段支持三种传入方式：
1. **模板名** — 自动从 `templates/{name}.json` 加载（如 `"schedule"`）
2. **绝对路径** — 任意 JSON 模板文件
3. **JSON 对象 / 字符串** — 直接传入完整模板

### 内置模板

`templates/` 目录提供 4 个开箱即用模板：

| 模板名 | 用途 | 必需变量 |
|---|---|---|
| `schedule` | 日程卡片 | title, date, time, location, desc, updated_at |
| `todo` | 待办列表 | count, item1-4, footer |
| `weather` | 天气面板 | city, temp, condition, humidity, wind, updated |
| `qrcard` | 二维码卡片 | title, subtitle, url, footer |

### 像素级最佳实践（墨水屏专用）

- 边缘留 6–8px padding（屏厂 ITO 边缘易显示不全）
- 行距至少 1.4 × 字号
- 分隔线最小 2px
- 所有坐标用整数（小数会破坏 hinting）
- ≤14px 文字优先用点阵字体（如 ark-pixel）
- 大字号用 Bold 字重（125 PPI 下 Regular 太细）
