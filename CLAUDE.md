# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个快手直播弹幕采集系统，通过WebSocket连接快手直播间获取实时弹幕数据。系统使用Protocol Buffers进行数据序列化，支持单个直播间和批量处理多个直播间。

## 常用命令

### 安装依赖
```bash
pip3 install -r requirements.txt
```

### 运行弹幕采集

#### 🆕 方法一：自动化解析（推荐）
使用手动获取的hex数据自动解析参数：

```bash
# 交互式输入模式（推荐新手使用）
python -m barrage.manual_hex_barrage --interactive

# 命令行直接输入hex数据
python -m barrage.manual_hex_barrage --hex "你的hex数据" --websocket-url "WebSocket地址"

# 仅解析参数，不启动采集
python -m barrage.manual_hex_barrage --hex "你的hex数据" --parse-only
```

**获取hex数据的步骤：**
1. 访问直播间：https://live.kuaishou.com/u/Kslala666
2. 按F12打开开发者工具，切换到Network面板
3. 过滤"websocket"或"WS"连接
4. 找到WebSocket连接，切换到Messages标签
5. 复制第一个发送消息的hex数据

#### 方法二：传统手动模式
```bash
python -m barrage.ks_barrage --live-id "直播间ID"
```

#### 方法三：URL模式（实验性，可能被反爬虫阻止）
```bash
python -m barrage.ks_barrage --url "https://live.kuaishou.com/u/用户名" --show-browser
```

### 🔧 获取hex数据详细指导

```bash
# 显示详细的获取指导
python -m barrage.manual_hex_barrage --help-guide
```

### 示例hex数据格式
```
08c8011a88020ad8015a322b77743234764b484e4138685774544a614b48474478747a67532f6d4f337634464d643437543876363632417a706b5476315437385a53556f4c617a594248636d43386e35467837734d796f53794358436458796863574143384a4c366a6537456a39523945575a46506c6a552b644144574173614378764f6b583751374a7268504943442f65746c46466d644e4e5731537a4c32776d712f54554273336f4d5759444645536b586e665676774b4a4d3764313249713971635336383370686d79446d512f2f346f37622b3932795859556f37413d3d120b4539636452656d477a4f493a1e61346277484567585342673066764e735f31373538313936363034373334
```

## 🚀 快速开始（推荐）

### 🎯 一键启动 - 智能模式
```bash
python -m barrage.ultimate "https://live.kuaishou.com/u/Kslala666"
```
**智能模式会自动选择最佳方法，无需任何配置！**

### 📋 所有可用模式

#### 1. 🧠 智能模式（推荐）
自动尝试各种方法，直到成功：
```bash
python -m barrage.ultimate "直播间URL"
```

#### 2. 🤖 完全自动化模式
尝试完全自动获取参数：
```bash
python -m barrage.ultimate "直播间URL" --auto --show-browser
```

#### 3. 🔧 半自动化模式
引导用户手动获取hex数据：
```bash
python -m barrage.ultimate "直播间URL" --semi-auto
```

#### 4. ✋ 手动模式
用户提供所有参数：
```bash
python -m barrage.ultimate --manual
```

#### 5. 🎮 交互式模式
交互式选择模式：
```bash
python -m barrage.ultimate --interactive
```

### 🔧 获取hex数据详细指导

```bash
# 显示详细的获取指导
python -m barrage.manual_hex_barrage --help-guide
```

## 📊 使用示例

### 最简单的使用方式
```bash
# 一键启动，程序会自动处理所有事情
python -m barrage.ultimate "https://live.kuaishou.com/u/Kslala666"
```

### 如果自动化失败，使用半自动模式
```bash
# 程序会引导您手动获取必要的数据
python -m barrage.ultimate "https://live.kuaishou.com/u/Kslala666" --semi-auto
```

### 传统方式（兼容性）
```bash
# 传统手动hex输入
python -m barrage.manual_hex_barrage --interactive

# 传统live_id模式
python -m barrage.ks_barrage --live-id "直播间ID"
```

## 🎬 工作流程

1. **智能模式首先尝试完全自动化**
   - 自动打开浏览器访问直播间
   - 自动捕获WebSocket连接和参数
   - 如果成功，直接开始采集弹幕

2. **如果自动化失败，切换到半自动化**
   - 显示详细的手动获取指导
   - 用户按指导获取hex数据
   - 程序自动解析并开始采集

3. **最后备选：完全手动模式**
   - 用户手动提供所有参数
   - 程序直接开始采集

## 💡 常见问题

**Q: 遇到验证码怎么办？**
A: 如果自动化遇到验证码，程序会自动切换到半自动化模式

**Q: 哪种模式最推荐？**
A: 智能模式，它会自动选择最适合的方法

**Q: 如何调试问题？**
A: 使用 `--show-browser` 参数查看浏览器状态

**Q: 程序一直卡住不动？**
A: 按Ctrl+C中断，然后尝试半自动化模式

### 批量处理多个直播间
需要先配置RabbitMQ，然后：
```bash
python -m barrage.ks_barrage_batch
```

### 编译Protocol Buffers
```bash
sh proto/compile.sh
```
或手动编译：
```bash
python -m grpc_tools.protoc -I . --python_out=. proto/ks_barrage.proto
```

### 使用protobuf-inspector分析数据包
```bash
protobuf_inspector < my-protobuf
```

## 核心架构

### 数据流架构
1. **WebSocket连接**: 通过websocket-client-py3连接快手直播间WebSocket服务器
2. **Protocol Buffers**: 使用protobuf进行数据序列化/反序列化
3. **消息队列**: 通过RabbitMQ实现多直播间任务分发
4. **多线程处理**: 每个直播间在独立线程中处理弹幕数据

### 关键组件

#### 弹幕处理核心 (`barrage/ks_barrage.py`)
- `KuaishouBarrage`类：主要的弹幕采集器
- 处理WebSocket连接生命周期（连接、消息接收、错误处理、关闭）
- 实现心跳机制维持连接（每20秒发送一次）
- 根据弹幕类型使用不同的protobuf结构解析数据

#### Protocol Buffers定义 (`proto/ks_barrage.proto`)
- `Request`: WebSocket连接请求数据结构
- `Barrage`: 弹幕数据主结构
- `BarrageContent`: 弹幕内容（观众数、点赞数、消息列表）
- `BarrageMessage`: 单条弹幕消息
- `HeartbeatClient`: 客户端心跳包
- `BarrageType`: 弹幕类型枚举（心跳、连接成功、弹幕、观众排行等）

#### 批量处理系统
- `barrage/ks_barrage_batch.py`: 从RabbitMQ队列获取任务并创建处理线程
- `barrage/process.py`: 提供后台线程/进程执行工具类
- `config.py`: RabbitMQ连接配置

### 认证和连接
- 需要登录账号获取token才能采集弹幕
- WebSocket URL格式：`wss://livejs-ws-group*.gifshow.com/websocket`
- 连接参数包括：token、live_id、page_id
- page_id生成算法基于固定字符集和时间戳

### 数据解析流程
1. 接收WebSocket二进制消息
2. 使用`ResponseCommon`解析消息头确定弹幕类型
3. 根据类型选择对应的protobuf结构体解析
4. 将protobuf消息转换为JSON格式输出

## 开发注意事项

- 修改`barrage/ks_barrage.py`中的live_id来采集不同直播间
- token可能有时效性，需要定期更新
- 不同直播间可能对应不同的WebSocket服务器组
- 使用`protobuf_inspector`工具分析未知数据包结构
- 系统需要RabbitMQ支持批量处理功能

## 文件结构要点

- `proto/`: Protocol Buffers定义和编译脚本
- `barrage/`: 核心弹幕采集逻辑
- `celery_ks/`: Celery任务队列配置（可选）
- `config.py`: RabbitMQ配置
- `parse_hex.py`: 十六进制数据解析工具