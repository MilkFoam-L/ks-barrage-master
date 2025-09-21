# 快手直播弹幕采集系统

这是一个快手直播弹幕采集系统，通过WebSocket连接快手直播间获取实时弹幕数据。系统提供Web界面管理多个直播间，并支持实时弹幕显示和数据存储。

## 🌟 新功能亮点 (v2.0)

我们为快手弹幕采集系统添加了全新的自动化功能，让用户体验更加友好：

### ✨ 主要改进

1. **🎯 一键启动模式** - 只需输入直播间URL，自动获取所有参数
2. **🔧 半自动模式** - 智能引导用户手动获取参数
3. **⚙️ 手动模式** - 保持原有的高级用户功能
4. **🔄 智能降级** - 自动模式失败时自动切换到半自动模式

## ✨ 特性

- 🎯 **多房间管理**: 支持同时管理和监控多个快手直播间
- 🚀 **实时弹幕**: WebSocket实时推送弹幕到前端界面
- 🤖 **智能自动化**: 一键启动，自动获取直播间参数
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
│   ├── auto_collector.py # 🆕 自动化采集器核心类
│   ├── ks_barrage_batch.py # 批量处理
│   └── process.py        # 处理工具类
├── proto/                # Protocol Buffers定义
│   ├── ks_barrage.proto  # 弹幕数据结构定义
│   ├── ks_barrage_pb2.py # 编译后的protobuf文件
│   └── compile.sh        # 编译脚本
├── templates/            # HTML模板
│   └── index.html        # 🆕 更新的前端界面
├── celery_ks/           # Celery配置(可选)
├── tools/               # 工具脚本
│   └── parse_hex.py     # 🆕 改进的hex解析工具
└── docs/                # 文档目录
```

## 🚀 快速开始

### 1. 启动系统

```bash
cd /path/to/ks-barrage-master
pip install -r requirements.txt
python app.py
```

然后访问: http://localhost:5000

### 2. 🎯 智能模式（推荐新手）

1. 在智能模式区域输入直播间URL（例如：`https://live.kuaishou.com/u/Kslala666`）
2. 点击"🎯 一键启动"按钮
3. 系统会自动尝试获取所有必要参数并启动弹幕采集

### 3. 🔧 半自动模式

如果一键启动失败，系统会自动引导您进入半自动模式：

1. 点击"🔧 半自动模式"按钮
2. 按照弹出的详细指导操作：
   - 访问直播间URL
   - 打开浏览器开发者工具
   - 捕获WebSocket连接和hex数据
3. 将获取的信息填入表单
4. 点击"🚀 解析并启动"

### 4. ⚙️ 手动模式

高级用户可以切换到手动模式：

1. 点击"⚙️ 切换到手动模式"
2. 手动填写所有参数：
   - 房间名称
   - 房间ID
   - WebSocket地址
   - Token
3. 点击"添加房间"

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

## 🔧 API接口

系统提供了以下新的API接口：

### 1. 自动提取接口

```bash
POST /api/auto-extract
Content-Type: application/json

{
    "live_url": "https://live.kuaishou.com/u/Kslala666",
    "mode": "auto"
}
```

### 2. hex解析接口

```bash
POST /api/parse-hex
Content-Type: application/json

{
    "live_url": "https://live.kuaishou.com/u/Kslala666",
    "websocket_url": "wss://livejs-ws-group10.gifshow.com/websocket",
    "hex_data": "08c8011a88020ad8015a322b..."
}
```

## 🛠️ 技术架构

### 核心组件

1. **AutoBarrageCollector**: 自动化采集器核心类
2. **混合策略模式**: HTTP + Selenium多重策略
3. **智能降级机制**: 自动 → 半自动 → 手动
4. **实时WebSocket通信**: 前后端实时数据同步

### 🔧 半自动模式操作步骤

当您点击"半自动模式"时，系统会显示详细的操作指导：

1. **打开直播间**: 在新标签页访问目标直播间
2. **打开开发者工具**: 按F12或右键选择"检查"
3. **切换到Network面板**: 点击"Network"标签
4. **过滤WebSocket**: 在筛选框中输入"WS"或"websocket"
5. **刷新页面**: 按F5刷新直播间页面
6. **找到WebSocket连接**: 查找websocket连接
7. **查看消息**: 点击连接，切换到"Messages"标签
8. **复制hex数据**: 复制第一个发送消息的十六进制数据

### 单个直播间测试

```bash
python -m barrage.ks_barrage
```

### 批量处理(需要RabbitMQ)

```bash
python -m barrage.ks_barrage_batch
```

## 📊 系统状态监控

新的界面提供了实时的系统状态监控：

- **系统状态**: WebSocket连接状态
- **服务器状态**: 后端服务状态
- **活跃连接**: 当前运行的房间数量
- **系统运行时间**: 系统持续运行时间
- **操作日志**: 详细的系统操作记录

## 🎯 使用场景

### 场景1: 新手用户
- 使用智能模式的"一键启动"
- 如果失败，系统自动引导到半自动模式
- 按照详细指导完成设置

### 场景2: 经验用户
- 直接使用半自动模式
- 快速获取参数并启动

### 场景3: 高级用户
- 切换到手动模式
- 自定义所有参数
- 批量管理多个直播间

## 🔍 故障排除

### 常见问题

**Q: 一键启动总是失败？**
A: 可能是网络问题或反爬虫机制，请尝试半自动模式

**Q: 找不到WebSocket连接？**
A: 确保直播间正在播放，刷新页面后重新查找

**Q: hex数据解析失败？**
A: 确保复制的是完整的十六进制数据，不包含其他字符

**Q: 系统运行慢？**
A: 检查Chrome浏览器是否正确安装，确保网络连接稳定

### 日志查看

系统提供了详细的日志记录：
- 前端：查看系统操作日志面板
- 后端：查看控制台输出
- 调试：开启Flask debug模式

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

## 🎉 总结

新的自动化功能大大简化了快手弹幕采集的使用流程：

1. **用户友好**: 从复杂的手动配置到一键启动
2. **智能引导**: 失败时自动引导用户完成配置
3. **向后兼容**: 保持原有功能的完整性
4. **可扩展性**: 便于添加更多自动化策略

## ⚡ 性能优化

1. **智能缓存**: 已解析的直播间参数缓存
2. **并发处理**: 多直播间并发采集
3. **资源管理**: 自动清理临时文件和浏览器进程
4. **错误恢复**: 智能重试和降级机制

## 📋 注意事项

- Token可能有时效性，需要定期更新
- 不同直播间可能对应不同的WebSocket服务器组
- Windows环境下注意Unicode编码问题
- 系统需要稳定的网络连接

## 🤝 贡献

欢迎提交Issues和Pull Requests来改进项目。

## 📄 许可证

本项目仅供学习和研究使用。

---

**📧 技术支持**: 如有问题请查看系统日志或联系开发团队
**🔄 版本**: v2.0 - 自动化增强版
**📅 更新日期**: 2025年9月