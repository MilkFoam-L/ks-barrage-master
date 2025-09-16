# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个快手直播弹幕采集系统，通过WebSocket连接快手直播间获取实时弹幕数据。系统使用Protocol Buffers进行数据序列化，支持单个直播间和批量处理多个直播间。

## 常用命令

### 安装依赖
```bash
pip3 install -r requirements.txt
```

### 运行单个直播间弹幕采集
```bash
python -m barrage.ks_barrage
```

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