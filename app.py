# -*- coding: utf-8 -*-
import json
import sqlite3
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import sys
import os

# 添加项目路径到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from barrage.ks_barrage import KuaishouBarrage

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ks-barrage-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 数据库初始化
def init_db():
    """初始化数据库"""
    conn = sqlite3.connect('barrage.db')
    c = conn.cursor()
    
    # 创建房间表
    c.execute('''CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_name TEXT NOT NULL,
                    live_id TEXT NOT NULL,
                    websocket_url TEXT NOT NULL,
                    token TEXT NOT NULL,
                    status TEXT DEFAULT 'stopped',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')
    
    # 创建弹幕记录表
    c.execute('''CREATE TABLE IF NOT EXISTS barrages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id INTEGER,
                    user_name TEXT,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raw_data TEXT,
                    FOREIGN KEY (room_id) REFERENCES rooms (id)
                 )''')
    
    conn.commit()
    conn.close()

# 存储活跃的弹幕连接
active_connections = {}

class BarrageHandler(KuaishouBarrage):
    """自定义弹幕处理器，用于将弹幕数据保存到数据库并推送到前端"""
    
    def __init__(self, live_id, room_id, token, websocket_url):
        self.room_id = room_id
        self.websocket_url = websocket_url
        self._token = token
        super().__init__(live_id)
    
    @property
    def token(self):
        return self._token
    
    @property
    def url(self):
        return self.websocket_url
    
    def on_open(self, ws):
        """连接建立时触发"""
        print(f"✅ 房间 {self.room_id} WebSocket连接已建立")
        socketio.emit('room_status', {
            'room_id': self.room_id,
            'status': 'connected',
            'message': 'WebSocket连接已建立'
        })
        super().on_open(ws)
    
    def on_error(self, ws, error):
        """通信发生错误时触发"""
        print(f"❌ 房间 {self.room_id} WebSocket错误: {error}")
        socketio.emit('room_status', {
            'room_id': self.room_id,
            'status': 'error',
            'message': f'连接错误: {str(error)}'
        })
        super().on_error(ws, error)
        
    def on_close(self, ws, close_status_code, close_msg):
        """连接关闭时触发"""
        print(f"🔴 房间 {self.room_id} WebSocket连接已关闭，状态码: {close_status_code}, 消息: {close_msg}")
        socketio.emit('room_status', {
            'room_id': self.room_id,
            'status': 'disconnected',
            'message': f'连接已关闭 (状态码: {close_status_code})'
        })
        super().on_close(ws, close_status_code, close_msg)
    
    def on_message(self, ws, message):
        """重写消息处理方法"""
        try:
            # 检查消息类型
            if isinstance(message, str):
                print(f"房间 {self.room_id} 收到文本消息: {message}")
                # 处理JSON错误消息
                try:
                    import json as json_lib
                    msg_data = json_lib.loads(message)
                    if msg_data.get('type') == 'SC_ERROR':
                        error_code = msg_data.get('code')
                        print(f"房间 {self.room_id} 服务器错误: 代码{error_code}")
                        if error_code == 21:
                            print(f"房间 {self.room_id} Token认证失败")
                        socketio.emit('room_status', {
                            'room_id': self.room_id,
                            'status': 'error',
                            'message': f'服务器错误 (代码: {error_code})'
                        })
                except:
                    pass
                return
                
            # 处理二进制消息
            if isinstance(message, bytes):
                super().on_message(ws, message)
                
        except Exception as e:
            print(f"房间 {self.room_id} 消息处理错误: {e}")
    
    def parse_barrage(self, msg: bytes):
        """重写弹幕解析方法，保存到数据库并推送到前端"""
        try:
            from proto.ks_barrage_pb2 import Barrage
            from google.protobuf import json_format
            
            barrage = Barrage()
            barrage.ParseFromString(msg)
            data = json_format.MessageToDict(barrage, preserving_proto_field_name=True)
            
            print(f"房间 {self.room_id} 解析弹幕数据: {data}")
            
            # 根据实际数据结构提取弹幕信息
            if 'barrage_content' in data and 'barrage_message' in data['barrage_content']:
                for message in data['barrage_content']['barrage_message']:
                    user_name = ""
                    content = ""
                    
                    # 提取用户名
                    if 'audience' in message:
                        if 'name' in message['audience']:
                            user_name = message['audience']['name']
                        elif 'eid' in message['audience']:
                            user_name = message['audience']['eid']
                    
                    # 提取弹幕内容
                    if 'comment_content' in message:
                        content = message['comment_content']
                    
                    if user_name and content:
                        # 保存到数据库
                        self.save_barrage(user_name, content, json.dumps(data, ensure_ascii=False))
                        
                        # 推送到前端
                        socketio.emit('new_barrage', {
                            'room_id': self.room_id,
                            'user_name': user_name,
                            'content': content,
                            'timestamp': datetime.now().strftime('%H:%M:%S')
                        })
                        
                        print(f"房间 {self.room_id} 新弹幕: {user_name}: {content}")
                    
        except Exception as e:
            print(f"房间 {self.room_id} 解析弹幕错误: {e}")
            import traceback
            traceback.print_exc()
    
    def save_barrage(self, user_name, content, raw_data):
        """保存弹幕到数据库"""
        try:
            conn = sqlite3.connect('barrage.db')
            c = conn.cursor()
            c.execute('''INSERT INTO barrages (room_id, user_name, content, raw_data) 
                        VALUES (?, ?, ?, ?)''', 
                     (self.room_id, user_name, content, raw_data))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"保存弹幕错误: {e}")

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    """获取所有房间"""
    conn = sqlite3.connect('barrage.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM rooms ORDER BY created_at DESC')
    rooms = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(rooms)

@app.route('/api/rooms', methods=['POST'])
def add_room():
    """添加房间"""
    data = request.json
    conn = sqlite3.connect('barrage.db')
    c = conn.cursor()
    c.execute('''INSERT INTO rooms (room_name, live_id, websocket_url, token) 
                VALUES (?, ?, ?, ?)''', 
             (data['room_name'], data['live_id'], data['websocket_url'], data['token']))
    conn.commit()
    room_id = c.lastrowid
    conn.close()
    return jsonify({'id': room_id, 'message': '房间添加成功'})

@app.route('/api/rooms/<int:room_id>', methods=['PUT'])
def update_room(room_id):
    """更新房间信息"""
    data = request.json
    conn = sqlite3.connect('barrage.db')
    c = conn.cursor()
    c.execute('''UPDATE rooms SET room_name=?, live_id=?, websocket_url=?, token=?, updated_at=CURRENT_TIMESTAMP 
                WHERE id=?''', 
             (data['room_name'], data['live_id'], data['websocket_url'], data['token'], room_id))
    conn.commit()
    conn.close()
    return jsonify({'message': '房间更新成功'})

@app.route('/api/rooms/<int:room_id>', methods=['DELETE'])
def delete_room(room_id):
    """删除房间"""
    # 先停止弹幕抓取
    stop_barrage(room_id)
    
    conn = sqlite3.connect('barrage.db')
    c = conn.cursor()
    # 删除相关弹幕记录
    c.execute('DELETE FROM barrages WHERE room_id=?', (room_id,))
    # 删除房间
    c.execute('DELETE FROM rooms WHERE id=?', (room_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': '房间删除成功'})

@app.route('/api/rooms/<int:room_id>/start', methods=['POST'])
def start_room_barrage(room_id):
    """启动房间弹幕抓取"""
    if room_id in active_connections:
        return jsonify({'message': '房间弹幕抓取已在运行中'})
    
    conn = sqlite3.connect('barrage.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM rooms WHERE id=?', (room_id,))
    room = dict(c.fetchone())
    conn.close()
    
    if not room:
        return jsonify({'error': '房间不存在'}), 404
    
    def run_barrage():
        try:
            print(f"开始启动房间 {room_id} 的弹幕抓取")
            print(f"房间信息: live_id={room['live_id']}, websocket_url={room['websocket_url']}")

            handler = BarrageHandler(room['live_id'], room_id, room['token'], room['websocket_url'])
            active_connections[room_id] = handler

            print(f"BarrageHandler 创建成功，房间 {room_id}")

            # 更新房间状态
            conn = sqlite3.connect('barrage.db')
            c = conn.cursor()
            c.execute('UPDATE rooms SET status="running" WHERE id=?', (room_id,))
            conn.commit()
            conn.close()

            print(f"开始调用 handler.start_run() 房间 {room_id}")
            # 开始抓取
            handler.start_run()

        except Exception as e:
            print(f"启动弹幕抓取错误: {e}")
            import traceback
            traceback.print_exc()
            if room_id in active_connections:
                del active_connections[room_id]

            # 更新房间状态
            conn = sqlite3.connect('barrage.db')
            c = conn.cursor()
            c.execute('UPDATE rooms SET status="error" WHERE id=?', (room_id,))
            conn.commit()
            conn.close()
    
    thread = threading.Thread(target=run_barrage)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': '弹幕抓取已启动'})

@app.route('/api/rooms/<int:room_id>/stop', methods=['POST'])
def stop_room_barrage(room_id):
    """停止房间弹幕抓取"""
    return jsonify({'message': stop_barrage(room_id)})

def stop_barrage(room_id):
    """停止弹幕抓取的内部方法"""
    if room_id in active_connections:
        try:
            # 调用停止方法
            active_connections[room_id].stop()
            del active_connections[room_id]
        except Exception as e:
            print(f"停止弹幕抓取错误: {e}")
    
    # 更新房间状态
    conn = sqlite3.connect('barrage.db')
    c = conn.cursor()
    c.execute('UPDATE rooms SET status="stopped" WHERE id=?', (room_id,))
    conn.commit()
    conn.close()
    
    return '弹幕抓取已停止'

@app.route('/api/rooms/<int:room_id>/barrages')
def get_room_barrages(room_id):
    """获取房间弹幕历史"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    offset = (page - 1) * per_page
    
    conn = sqlite3.connect('barrage.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''SELECT * FROM barrages WHERE room_id=? 
                ORDER BY timestamp DESC LIMIT ? OFFSET ?''', 
             (room_id, per_page, offset))
    barrages = [dict(row) for row in c.fetchall()]
    
    # 获取总数
    c.execute('SELECT COUNT(*) as total FROM barrages WHERE room_id=?', (room_id,))
    total = c.fetchone()['total']
    
    conn.close()
    
    return jsonify({
        'barrages': barrages,
        'total': total,
        'page': page,
        'per_page': per_page
    })

@app.route('/api/barrages')
def get_all_barrages():
    """获取所有房间的弹幕"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    offset = (page - 1) * per_page
    
    conn = sqlite3.connect('barrage.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''SELECT b.*, r.room_name FROM barrages b 
                LEFT JOIN rooms r ON b.room_id = r.id
                ORDER BY b.timestamp DESC LIMIT ? OFFSET ?''', 
             (per_page, offset))
    barrages = [dict(row) for row in c.fetchall()]
    
    # 获取总数
    c.execute('SELECT COUNT(*) as total FROM barrages')
    total = c.fetchone()['total']
    
    conn.close()
    
    return jsonify({
        'barrages': barrages,
        'total': total,
        'page': page,
        'per_page': per_page
    })

if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
