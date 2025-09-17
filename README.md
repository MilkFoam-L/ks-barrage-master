# 快手直播弹幕采集系统

这是一个快手直播弹幕采集系统，通过WebSocket连接快手直播间获取实时弹幕数据。系统提供Web界面管理多个直播间，并支持实时弹幕显示和数据存储。

## ✨ 特性

- 🎯 **多房间管理**: 支持同时管理和监控多个快手直播间
- 🚀 **实时弹幕**: WebSocket实时推送弹幕到前端界面
- 💾 **数据存储**: SQLite数据库存储弹幕历史记录
- 🎨 **现代化UI**: 美观的Web界面，支持实时状态反馈
- 📊 **系统监控**: 实时显示系统状态和连接信息
- 🔄 **批量处理**: 支持RabbitMQ批量处理多个直播间

## 🏗️ 项目结构

```
ks-barrage-master/
├── app.py                 # Flask主应用
├── requirements.txt       # 项目依赖
├── config.py             # RabbitMQ配置
├── barrage/              # 弹幕采集核心模块
│   ├── ks_barrage.py     # 主要的弹幕采集器
│   ├── ks_barrage_batch.py # 批量处理
│   └── process.py        # 处理工具类
├── proto/                # Protocol Buffers定义
│   ├── ks_barrage.proto  # 弹幕数据结构定义
│   ├── ks_barrage_pb2.py # 编译后的protobuf文件
│   └── compile.sh        # 编译脚本
├── templates/            # HTML模板
│   └── index.html        # 主页面
├── celery_ks/           # Celery配置(可选)
├── tools/               # 工具脚本
│   └── parse_hex.py     # 十六进制数据解析工具
└── docs/                # 文档目录
```

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 编译Protocol Buffers

```bash
cd proto
sh compile.sh
```

或手动编译：
```bash
python -m grpc_tools.protoc -I . --python_out=. proto/ks_barrage.proto
```

### 运行Web应用

```bash
python app.py
```

应用将在 http://localhost:5000 启动

### 单个直播间测试

```bash
python -m barrage.ks_barrage
```

### 批量处理(需要RabbitMQ)

```bash
python -m barrage.ks_barrage_batch
```

## 📝 使用说明

1. **添加房间**: 在Web界面中填入直播间信息（房间名、live_id、WebSocket URL、token）
2. **启动采集**: 点击房间卡片的"启动"按钮开始弹幕采集
3. **查看弹幕**: 点击"查看"按钮切换到对应房间的实时弹幕
4. **停止采集**: 点击"停止"按钮停止弹幕采集
5. **系统监控**: 查看系统状态卡片获取实时系统信息

## ⚙️ 配置说明

### 认证配置
- 需要登录快手账号获取token进行弹幕采集
- WebSocket URL格式：`wss://livejs-ws-group*.gifshow.com/websocket`
- 连接参数包括：token、live_id、page_id

### 数据库
- 使用SQLite数据库存储房间信息和弹幕记录
- 数据库文件：`barrage.db`（已添加到.gitignore）

### RabbitMQ配置（可选）
在 `config.py` 中配置RabbitMQ连接信息用于批量处理。

## 🛠️ 开发指南

### 核心架构

1. **WebSocket连接**: 通过websocket-client-py3连接快手直播间
2. **Protocol Buffers**: 使用protobuf进行数据序列化/反序列化
3. **Flask + SocketIO**: Web框架和实时通信
4. **多线程处理**: 每个直播间在独立线程中处理

### 扩展开发

- 修改 `barrage/ks_barrage.py` 中的 `parse_barrage` 方法来自定义弹幕处理逻辑
- 使用 `protobuf_inspector` 工具分析新的数据包结构
- 在 `app.py` 中的 `BarrageHandler` 类中添加自定义处理逻辑

## 📋 注意事项

- Token可能有时效性，需要定期更新
- 不同直播间可能对应不同的WebSocket服务器组
- Windows环境下注意Unicode编码问题
- 系统需要稳定的网络连接

## 🤝 贡献

欢迎提交Issues和Pull Requests来改进项目。

## 📄 许可证

本项目仅供学习和研究使用。