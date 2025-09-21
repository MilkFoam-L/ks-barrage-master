# -*- coding: utf-8 -*-
"""
测试自动化功能
"""

import requests
import json
import time
import threading
from app import app, socketio, init_db

def test_auto_extract():
    """测试自动提取功能"""
    test_url = "https://live.kuaishou.com/u/Kslala666"

    print(f"测试自动提取: {test_url}")

    try:
        response = requests.post('http://localhost:5000/api/auto-extract',
                               json={'live_url': test_url, 'mode': 'auto'},
                               timeout=30)

        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 自动提取成功!")
                print(f"房间名称: {result.get('room_name')}")
                print(f"直播ID: {result.get('live_id')}")
                print(f"WebSocket URL: {result.get('websocket_url', '')[:50]}...")
                print(f"Token: {result.get('token', '')[:30]}...")
            else:
                print(f"❌ 自动提取失败: {result.get('error')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")

def test_parse_hex():
    """测试hex解析功能"""
    test_url = "https://live.kuaishou.com/u/Kslala666"
    test_websocket = "wss://livejs-ws-group10.gifshow.com/websocket"
    test_hex = "08c8011a88020ad8015a322b77743234764b484e4138685774544a614b48474478747a67532f6d4f337634464d643437543876363632417a706b5476315437385a53556f4c617a594248636d43386e35467837734d796f53794358436458316e4e643847784e4e75434851456e50317563675954544174503465447164576274667545623248574157446134612b683175594e30487241784f705170716975435264556c515945587436335a7164483269786d5a786a4a724453777731707376314a654e6e2b75485044537056626e54763241726b533051755778716938513d3d120b746276794339394270416f3a1e78445638377546387846374e6f5a31795f31373538323739363633343936"

    print(f"测试hex解析")

    try:
        response = requests.post('http://localhost:5000/api/parse-hex',
                               json={
                                   'live_url': test_url,
                                   'websocket_url': test_websocket,
                                   'hex_data': test_hex
                               },
                               timeout=10)

        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ hex解析成功!")
                print(f"房间名称: {result.get('room_name')}")
                print(f"直播ID: {result.get('live_id')}")
                print(f"Token: {result.get('token', '')[:30]}...")
            else:
                print(f"❌ hex解析失败: {result.get('error')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")

def start_server():
    """启动服务器"""
    print("正在启动测试服务器...")
    init_db()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    # 启动服务器
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(3)

    print("\n" + "="*50)
    print("开始测试自动化功能")
    print("="*50)

    # 测试hex解析功能（这个比较简单，先测试）
    print("\n1. 测试hex解析功能")
    print("-" * 30)
    test_parse_hex()

    # 测试自动提取功能（可能需要浏览器环境）
    print("\n2. 测试自动提取功能")
    print("-" * 30)
    test_auto_extract()

    print("\n" + "="*50)
    print("测试完成，服务器继续运行...")
    print("你可以访问 http://localhost:5000 查看网页界面")
    print("="*50)

    # 保持程序运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n程序退出")