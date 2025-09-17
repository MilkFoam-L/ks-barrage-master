# 快手弹幕爬取系统 - 网页版

这是一个基于Flask的网页界面系统，用于管理快手弹幕爬取任务。

## 功能特性

🚀 **房间管理**
- 添加、编辑、删除直播房间
- 为每个房间配置独立的Live ID、WebSocket地址和Token
- 房间状态实时监控（运行中/已停止/错误）

💬 **实时弹幕**
- 实时显示弹幕内容
- 支持多房间弹幕同时显示
- 可按房间过滤弹幕
- 自动滚动功能

📊 **数据管理**
- 弹幕历史记录存储
- 统计信息实时更新
- 数据库自动管理

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动网页服务
```bash
python app.py
```

### 3. 访问网页界面
打开浏览器访问：http://localhost:5000

## 使用说明

### 添加房间
1. 在"房间管理"区域填写房间信息：
   - **房间名称**: 自定义名称，用于标识房间
   - **房间ID**: 快手直播间的Live ID（如：_0xmxugsdno）
   - **WebSocket地址**: 快手弹幕WebSocket服务地址
   - **Token**: 用户认证Token
2. 点击"添加房间"按钮

### 管理房间
- **启动**: 开始抓取该房间的弹幕
- **停止**: 停止弹幕抓取
- **查看**: 切换到该房间的弹幕视图
- **删除**: 删除房间及其所有弹幕记录

### 查看弹幕
- 默认显示所有房间的弹幕
- 使用下拉菜单过滤特定房间的弹幕
- 自动滚动功能保持最新弹幕在视图中

## 配置说明

### Token获取方法
1. 登录快手网页版
2. 打开直播间
3. 使用浏览器开发者工具抓取WebSocket连接中的Token

### WebSocket地址
常见的快手弹幕WebSocket地址格式：
- `wss://livejs-ws-group10.gifshow.com/websocket`
- `wss://live-ws-pg-group11.kuaishou.com/websocket`

不同直播间可能使用不同的WebSocket服务器群组。

### Live ID
在直播间URL中可以找到Live ID，通常格式如：`_0xmxugsdno`

## 数据库

系统使用SQLite数据库存储数据，数据库文件：`barrage.db`

### 数据表结构

**rooms表**（房间信息）
- id: 房间ID
- room_name: 房间名称
- live_id: 快手Live ID
- websocket_url: WebSocket地址
- token: 认证Token
- status: 房间状态
- created_at: 创建时间
- updated_at: 更新时间

**barrages表**（弹幕记录）
- id: 弹幕ID
- room_id: 所属房间ID
- user_name: 用户名
- content: 弹幕内容
- timestamp: 时间戳
- raw_data: 原始数据（JSON格式）

## 技术栈

- **后端**: Flask + Flask-SocketIO
- **前端**: HTML + CSS + JavaScript
- **数据库**: SQLite
- **WebSocket**: Socket.IO
- **弹幕协议**: Protocol Buffers

## API接口

### 房间管理
- `GET /api/rooms` - 获取所有房间
- `POST /api/rooms` - 添加房间
- `PUT /api/rooms/<id>` - 更新房间
- `DELETE /api/rooms/<id>` - 删除房间

### 弹幕操作
- `POST /api/rooms/<id>/start` - 启动房间弹幕抓取
- `POST /api/rooms/<id>/stop` - 停止房间弹幕抓取
- `GET /api/rooms/<id>/barrages` - 获取房间弹幕历史
- `GET /api/barrages` - 获取所有弹幕

### WebSocket事件
- `new_barrage` - 新弹幕推送事件

## 注意事项

1. **Token有效期**: 快手的Token有一定有效期，失效后需要重新获取
2. **WebSocket地址**: 不同直播间可能需要不同的WebSocket服务器地址
3. **并发限制**: 建议不要同时运行过多房间，避免被限制访问
4. **网络稳定性**: 弹幕抓取依赖网络连接，网络不稳定可能导致连接断开

## 故障排除

### 弹幕无法抓取
1. 检查Token是否有效
2. 确认WebSocket地址是否正确
3. 验证Live ID是否正确
4. 检查网络连接

### 页面显示异常
1. 清除浏览器缓存
2. 检查JavaScript控制台错误
3. 确认Flask服务正常运行

### 数据库错误
1. 检查磁盘空间
2. 确认数据库文件权限
3. 重启Flask服务

## 更新日志

### v1.0.0
- 首次发布
- 基本的房间管理功能
- 实时弹幕显示
- SQLite数据库支持

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规。
