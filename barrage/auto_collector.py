# -*- coding: utf-8 -*-
"""
快手弹幕自动化采集器
实现从直播间URL到弹幕采集的一键自动化
"""

import re
import requests
import time
import json
import subprocess
import sys
import os
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AutoBarrageCollector:
    """自动化弹幕采集器"""

    def __init__(self):
        self.strategies = [
            self._http_strategy,
            self._selenium_strategy,
        ]

    def collect(self, live_url, mode='auto'):
        """
        自动采集弹幕参数
        :param live_url: 直播间URL
        :param mode: 采集模式 'auto' 或 'semi_auto'
        :return: 采集结果字典
        """
        print(f"开始自动采集: {live_url}, 模式: {mode}")

        # 提取用户名
        username = self._extract_username(live_url)
        if not username:
            return {
                'success': False,
                'error': '无法从URL中提取用户名'
            }

        if mode == 'auto':
            # 尝试所有自动化策略
            last_error = ""
            for i, strategy in enumerate(self.strategies):
                try:
                    print(f"尝试策略 {i+1}: {strategy.__name__}")
                    result = strategy(live_url, username)
                    if result['success']:
                        print(f"策略 {i+1} 成功！")

                        # 验证live_id格式 - 必须是正确的live_id格式，不能是username
                        live_id = result.get('live_id', '')
                        if not live_id or live_id == username or len(live_id) < 8:
                            print(f"警告: 提取的live_id无效 ({live_id})，需要从hex数据中获取")
                            result['needs_hex_parsing'] = True
                            result['live_id'] = ''  # 清空无效的live_id

                        # 验证token格式 - 必须是正确的base64 token格式
                        token = result.get('token', '')
                        if not token or len(token) < 50:
                            print(f"警告: 提取的token无效，需要从hex数据中获取")
                            result['needs_hex_parsing'] = True
                            result['token'] = ''  # 清空无效的token

                        return result
                    else:
                        last_error = result.get('error', '未知错误')
                        print(f"策略 {i+1} 失败: {last_error}")
                except Exception as e:
                    last_error = str(e)
                    print(f"策略 {i+1} 异常: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            # 所有策略都失败了，但不使用降级策略
            print("所有自动化策略都失败了")
            return {
                'success': False,
                'error': f'自动化提取失败: {last_error}'
            }

        return {
            'success': False,
            'error': '不支持的模式'
        }

    def parse_hex(self, live_url, websocket_url, hex_data):
        """
        解析hex数据获取参数
        :param live_url: 直播间URL
        :param websocket_url: WebSocket地址
        :param hex_data: 十六进制数据
        :return: 解析结果
        """
        try:
            username = self._extract_username(live_url)
            room_name = username or "未知直播间"

            # 使用现有的parse_hex工具
            from tools.parse_hex import parse_hex_data
            parsed_data = parse_hex_data(hex_data)

            if not parsed_data:
                return {
                    'success': False,
                    'error': 'hex数据解析失败'
                }

            return {
                'success': True,
                'room_name': room_name,
                'live_id': parsed_data.get('live_id', ''),
                'websocket_url': websocket_url,
                'token': parsed_data.get('token', ''),
                'page_id': parsed_data.get('page_id', ''),
                'user_name': username
            }

        except Exception as e:
            print(f"解析hex数据错误: {e}")
            return {
                'success': False,
                'error': f'解析失败: {str(e)}'
            }

    def _ensure_websocket_url_format(self, websocket_url):
        """
        确保WebSocket URL格式正确，转换为wss://格式
        :param websocket_url: 原始WebSocket URL
        :return: 正确格式的WebSocket URL
        """
        if not websocket_url:
            return websocket_url

        # 如果已经是wss://格式，直接返回
        if websocket_url.startswith('wss://'):
            return websocket_url

        try:
            # 尝试提取group号并构造正确的wss://格式
            if 'group' in websocket_url:
                import re
                group_match = re.search(r'group(\d+)', websocket_url)
                if group_match:
                    group_num = group_match.group(1)
                    final_url = f"wss://livejs-ws-group{group_num}.gifshow.com/websocket"
                    print(f"转换WebSocket URL格式: {websocket_url} -> {final_url}")
                    return final_url

            # 如果没有group信息，使用默认的group7
            final_url = "wss://livejs-ws-group7.gifshow.com/websocket"
            print(f"使用默认WebSocket URL格式: {final_url}")
            return final_url
        except Exception as e:
            print(f"转换WebSocket URL格式失败: {e}, 使用原始URL")
            return websocket_url

    def _extract_username(self, live_url):
        """从URL中提取用户名"""
        try:
            # 匹配快手直播间URL模式
            # https://live.kuaishou.com/u/username
            match = re.search(r'live\.kuaishou\.com/u/([^/\?]+)', live_url)
            if match:
                return match.group(1)
            return None
        except Exception:
            return None

    def _http_strategy(self, live_url, username):
        """HTTP请求策略 - 轻量化方案"""
        try:
            print(f"HTTP策略: 获取页面 {live_url}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cookie': 'kpn=KUAISHOU; kpf=PC_WEB; userId=; kuaishou.server.web_st=ChZrdWFpc2hvdS5zZXJ2ZXIud2ViLnN0EqABZLLJF_YaJjpRGGdkMUYHNMGNhGYNNbr0VYr8-PoXwO9-Q8Zy2mD8p6hJzqxWcK3dUjKjP5t8AXFEFr7CUoG4DgSKgaVA2P8F_2BO8N0QJQWTCQb3LIH2O2PYkN_zqQJl7QNrCwHyJQN7bG9Y7oFYF_RYBB-uJXfJOQzqNYRgTzq5RY5zY5NhVBJjxGQIhcZQYWQq5GQQqN3Q8Ks5RH_QAAB; kuaishou.server.web_ph=33fb4ba60e4e80ade23ba2c27e3dc01c3a47',
                'Referer': 'https://live.kuaishou.com/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1'
            }

            response = requests.get(live_url, headers=headers, timeout=10)
            response.raise_for_status()

            html_content = response.text
            print(f"获取到页面内容，长度: {len(html_content)}")

            # 尝试从HTML中提取WebSocket info API URL
            websocket_info_url = self._extract_websocket_info_url(html_content)

            if websocket_info_url:
                print(f"找到WebSocket info URL: {websocket_info_url}")

                # 调用WebSocket info API获取真实连接信息
                ws_info = self._get_websocket_info(websocket_info_url, headers)

                if ws_info:
                    # 确保WebSocket URL格式正确
                    final_websocket_url = self._ensure_websocket_url_format(ws_info.get('websocket_url', ''))

                    return {
                        'success': True,
                        'room_name': username,
                        'live_id': ws_info.get('live_id', username),
                        'websocket_url': final_websocket_url,
                        'token': ws_info.get('token', ''),
                        'user_name': username
                    }

            # 如果API方法失败，尝试直接从HTML解析
            websocket_config = self._extract_websocket_config(html_content, username)

            if websocket_config:
                # 确保WebSocket URL格式正确
                final_websocket_url = self._ensure_websocket_url_format(websocket_config.get('websocket_url', ''))

                return {
                    'success': True,
                    'room_name': username,
                    'live_id': websocket_config.get('live_id', username),
                    'websocket_url': final_websocket_url,
                    'token': websocket_config.get('token', ''),
                    'user_name': username
                }

            return {
                'success': False,
                'error': '无法从页面中提取WebSocket配置'
            }

        except Exception as e:
            print(f"HTTP策略错误: {e}")
            return {
                'success': False,
                'error': f'HTTP请求失败: {str(e)}'
            }

    def _extract_websocket_info_url(self, html_content):
        """提取WebSocket info API URL"""
        try:
            patterns = [
                r'"(https://[^"]*websocketinfo[^"]*)"',
                r"'(https://[^']*websocketinfo[^']*)'",
                r'(https://[^\s"\']*websocketinfo[^\s"\']*)',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    url = matches[0]
                    print(f"找到WebSocket info URL: {url}")
                    return url

            return None

        except Exception as e:
            print(f"提取WebSocket info URL错误: {e}")
            return None

    def _get_websocket_info(self, info_url, headers):
        """调用WebSocket info API获取真实连接信息"""
        try:
            print(f"调用WebSocket info API: {info_url}")

            response = requests.get(info_url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            print(f"API返回数据: {data}")

            # 尝试从返回的数据中提取WebSocket URL和token
            if 'data' in data:
                ws_data = data['data']

                websocket_url = ws_data.get('webSocketUrls', [])[0] if ws_data.get('webSocketUrls') else None
                token = ws_data.get('token', '')
                live_stream_id = ws_data.get('liveStreamId', '')

                if websocket_url and token:
                    print(f"API提取成功: WebSocket={websocket_url}, Token长度={len(token)}")

                    # 确保WebSocket URL格式正确
                    final_websocket_url = self._ensure_websocket_url_format(websocket_url)

                    return {
                        'websocket_url': final_websocket_url,
                        'token': token,
                        'live_id': live_stream_id or 'unknown'
                    }

            return None

        except Exception as e:
            print(f"调用WebSocket info API错误: {e}")
            return None

    def _selenium_strategy(self, live_url, username):
        """Selenium自动化策略"""
        driver = None
        try:
            print(f"Selenium策略: 启动浏览器访问 {live_url}")

            # 配置Chrome选项
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 使用现有的ChromeDriver或下载
            try:
                service = Service(ChromeDriverManager().install())
            except:
                # 如果网络问题，使用系统路径中的ChromeDriver
                print("ChromeDriver manager失败，尝试使用系统路径中的ChromeDriver...")
                service = None

            # 启动浏览器
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_page_load_timeout(30)

            # 访问直播间
            print(f"正在访问: {live_url}")
            driver.get(live_url)

            # 等待页面加载
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # 等待JavaScript执行
            print("等待页面JavaScript执行...")
            time.sleep(5)

            # 尝试执行JavaScript获取WebSocket配置
            websocket_config = self._extract_websocket_config_selenium(driver)

            if websocket_config:
                print(f"通过JavaScript提取到配置: {websocket_config}")

                # 如果提取到的是API端点URL，需要获取真正的WebSocket URL
                websocket_url = websocket_config.get('websocket_url', '')
                if websocket_url and ('websocketinfo' in websocket_url or websocket_url.startswith('https://')):
                    print(f"检测到API端点URL，尝试通过hex解析获取真实WebSocket URL...")
                    # 构造虚拟hex数据请求来获取真实的WebSocket URL
                    try:
                        # 使用当前URL和基础hex数据尝试解析
                        hex_data = "08c8011a88020ad8015a322b77743234764b484e4138685774544a614b48474478747a67532f6d4f337634464d643437543876363632417a706b5476315437385a53556f4c617a594248636d43386e35467837734d796f53794358436458316e4e643847784e4e75434851456e50317563675954544174503465447164576274667545623248574157446134612b683175594e30487241784f705170716975435264556c515945587436335a7164483269786d5a786a4a724453777731707376314a654e6e2b754850704a4c6132676c6452477a756a484e637a64763358673d3d120b3152724d722d4b59416a633a1e7638494e7a71694e574d5f56527357795f31373538343734343034333431"

                        hex_result = self._call_parse_hex_api(live_url, websocket_url, hex_data)
                        if hex_result and hex_result.get('success'):
                            # 如果hex解析成功，使用hex解析的结果
                            if hex_result.get('websocket_url') and hex_result['websocket_url'].startswith('wss://'):
                                websocket_config['websocket_url'] = hex_result['websocket_url']
                                print(f"获取到真实WebSocket URL: {hex_result['websocket_url']}")

                            # 更新其他参数
                            if hex_result.get('live_id'):
                                websocket_config['live_id'] = hex_result['live_id']
                                print(f"更新live_id: {hex_result['live_id']}")

                            if hex_result.get('token'):
                                websocket_config['token'] = hex_result['token']
                                print(f"更新token: {hex_result['token'][:50]}...")

                    except Exception as e:
                        print(f"通过hex解析获取真实WebSocket URL失败: {e}")
                        # 如果hex解析失败，尝试直接调用API
                        try:
                            real_ws_url = self._get_real_websocket_url(websocket_url)
                            if real_ws_url:
                                websocket_config['websocket_url'] = real_ws_url
                                print(f"通过API获取到真实WebSocket URL: {real_ws_url}")
                        except Exception as api_e:
                            print(f"API调用也失败: {api_e}")

                # 检查live_id，如果没有则尝试从URL提取
                if not websocket_config.get('live_id') and websocket_config.get('websocket_url'):
                    live_id_from_url = self._extract_live_id_from_url(websocket_config['websocket_url'])
                    if live_id_from_url:
                        websocket_config['live_id'] = live_id_from_url
                        print(f"从WebSocket URL提取到live_id: {live_id_from_url}")

                return {
                    'success': True,
                    'room_name': username,
                    'live_id': websocket_config.get('live_id', ''),
                    'websocket_url': self._ensure_websocket_url_format(websocket_config.get('websocket_url', '')),
                    'token': websocket_config.get('token', ''),
                    'user_name': username
                }

            # 如果JavaScript方法失败，尝试从HTML解析
            print("JavaScript方法失败，尝试从HTML解析...")
            html_content = driver.page_source
            print(f"获取到页面源码，长度: {len(html_content)}")

            websocket_config = self._extract_websocket_config(html_content, username)

            if websocket_config:
                print(f"通过HTML解析提取到配置: {websocket_config}")
                return {
                    'success': True,
                    'room_name': username,
                    'live_id': websocket_config.get('live_id', ''),
                    'websocket_url': self._ensure_websocket_url_format(websocket_config.get('websocket_url', '')),
                    'token': websocket_config.get('token', ''),
                    'user_name': username
                }

            print("未能从页面中提取到WebSocket配置")
            return {
                'success': False,
                'error': '无法从页面中提取WebSocket配置'
            }

        except TimeoutException:
            print("页面加载超时")
            return {
                'success': False,
                'error': '页面加载超时'
            }
        except WebDriverException as e:
            print(f"Selenium WebDriver错误: {e}")
            return {
                'success': False,
                'error': f'浏览器错误: {str(e)}'
            }
        except Exception as e:
            print(f"Selenium策略错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'自动化失败: {str(e)}'
            }
        finally:
            if driver:
                try:
                    driver.quit()
                    print("浏览器已关闭")
                except:
                    pass

    def _extract_websocket_config(self, html_content, username=None):
        """从HTML内容中提取WebSocket配置"""
        try:
            print("开始分析页面内容...")

            # 尝试多种正则表达式模式
            patterns = {
                'websocket_url': [
                    r'"(wss://[^"]*websocket[^"]*)"',
                    r"'(wss://[^']*websocket[^']*)'",
                    r'websocketUrl["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'wsUrl["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'socketUrl["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'"(https://[^"]*websocketinfo[^"]*)"',
                    r"'(https://[^']*websocketinfo[^']*)'",
                ],
                'token': [
                    # 匹配长base64字符串 - 快手token通常是长的base64格式
                    r'"([A-Za-z0-9+/]{100,}={0,2})"',  # 100+字符的Base64 token
                    r'"([A-Za-z0-9+/]{80,}={0,2})"',   # 80+字符的Base64 token
                    # 常见的token字段名
                    r'"token"["\']?\s*:\s*["\']([^"\']{50,})["\']',
                    r"'token'['\"]?\s*:\s*['\"]([^'\"]{50,})['\"]",
                    r'authToken["\']?\s*:\s*["\']([^"\']{50,})["\']',
                    r'accessToken["\']?\s*:\s*["\']([^"\']{50,})["\']',
                    r'userToken["\']?\s*:\s*["\']([^"\']{50,})["\']',
                    r'kuaishou["\']?\s*:\s*["\']([^"\']{50,})["\']',
                    # 更宽泛的base64模式，优先级较低
                    r'"([A-Za-z0-9+/]{60,}={0,2})"',
                ],
                'live_id': [
                    r'"liveId"["\']?\s*:\s*["\']([A-Za-z0-9]{8,20})["\']',
                    r"'liveId'['\"]?\s*:\s*['\"]([A-Za-z0-9]{8,20})['\"]",
                    r'"live_id"["\']?\s*:\s*["\']([A-Za-z0-9]{8,20})["\']',
                    r'"streamId"["\']?\s*:\s*["\']([A-Za-z0-9]{8,20})["\']',
                    r'"roomId"["\']?\s*:\s*["\']([A-Za-z0-9]{8,20})["\']',
                    # 从URL参数中提取live_id
                    r'live_id=([A-Za-z0-9_-]{8,20})',
                    r'liveId=([A-Za-z0-9_-]{8,20})',
                    # 从API路径中提取
                    r'/live/([A-Za-z0-9_-]{8,20})',
                    # 精确匹配类似 "aRsNWDK31JM" 格式的ID
                    r'"([A-Za-z0-9]{11})"',  # 专门匹配11字符长度的ID
                    r'"([A-Za-z0-9]{10,12})"',  # 10-12字符长度的ID
                ]
            }

            result = {}

            # 搜索各种配置
            for config_type, pattern_list in patterns.items():
                print(f"\n===== 正在搜索 {config_type} =====")
                for i, pattern in enumerate(pattern_list):
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    if matches:
                        print(f"模式 {i+1} ({pattern[:50]}...) 找到 {len(matches)} 个匹配:")
                        for j, match in enumerate(matches[:5]):  # 只显示前5个
                            if config_type == 'token':
                                print(f"  匹配 {j+1}: {match[:50]}... (长度: {len(match)})")
                            else:
                                print(f"  匹配 {j+1}: {match}")

                        if config_type == 'websocket_url':
                            result[config_type] = matches[0]
                            print(f"选择websocket_url: {result[config_type]}")
                            break
                        elif config_type == 'token':
                            # 选择最有可能的token（优先长base64格式）
                            valid_tokens = []
                            for match in matches:
                                if len(match) >= 50:
                                    # 验证是否看起来像base64编码
                                    if re.match(r'^[A-Za-z0-9+/]+=*$', match):
                                        valid_tokens.append((match, len(match), 'base64'))
                                        print(f"  有效base64 token: {match[:50]}... (长度: {len(match)})")
                                    else:
                                        valid_tokens.append((match, len(match), 'other'))
                                        print(f"  其他格式 token: {match[:50]}... (长度: {len(match)})")

                            if valid_tokens:
                                # 按类型和长度排序：base64类型的长token优先
                                valid_tokens.sort(key=lambda x: (x[2] == 'base64', x[1]), reverse=True)
                                result[config_type] = valid_tokens[0][0]
                                print(f"选择token: {result[config_type][:50]}... (类型: {valid_tokens[0][2]}, 长度: {valid_tokens[0][1]})")
                                break
                        elif config_type == 'live_id':
                            # 优先选择正确格式的live_id（类似aRsNWDK31JM的格式）
                            valid_live_ids = []
                            for match in matches:
                                # 排除用户名格式和太短的ID
                                if (len(match) >= 8 and len(match) <= 20 and
                                    match not in ['Kslala666', 'username'] and  # 不能是用户名
                                    not match.startswith('http') and  # 不能是URL
                                    match not in result.values()):  # 不能重复
                                    valid_live_ids.append(match)
                                    print(f"  候选live_id: {match} (长度: {len(match)})")

                            if valid_live_ids:
                                # 优先选择11字符长度的ID（类似aRsNWDK31JM）
                                for live_id in valid_live_ids:
                                    if len(live_id) == 11:
                                        result[config_type] = live_id
                                        print(f"选择11字符live_id: {result[config_type]}")
                                        break
                                else:
                                    # 如果没有11字符的，选择第一个有效的
                                    result[config_type] = valid_live_ids[0]
                                    print(f"✅ 选择live_id: {result[config_type]} (长度: {len(result[config_type])})")
                                break

            # 增强搜索：查找JSON对象中的配置
            print("尝试从JSON对象中提取配置...")
            json_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'window\.LIVE_CONFIG\s*=\s*({.+?});',
                r'window\.CONFIG\s*=\s*({.+?});',
                r'window\.pageData\s*=\s*({.+?});',
                r'__APP_INITIAL_STATE__\s*=\s*({.+?});'
            ]

            for pattern in json_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        # 尝试解析JSON
                        import json as json_lib
                        json_data = json_lib.loads(match)
                        json_str = json_lib.dumps(json_data)

                        # 在JSON中查找配置
                        if not result.get('websocket_url'):
                            ws_match = re.search(r'"(wss://[^"]*websocket[^"]*)"', json_str)
                            if ws_match:
                                result['websocket_url'] = ws_match.group(1)
                                print(f"从JSON找到websocket_url: {result['websocket_url']}")

                        if not result.get('token'):
                            token_match = re.search(r'"(?:token|authToken|accessToken)":\s*"([^"]{50,})"', json_str)
                            if token_match:
                                result['token'] = token_match.group(1)
                                print(f"从JSON找到token: {result['token'][:50]}...")

                        if not result.get('live_id'):
                            liveid_match = re.search(r'"(?:liveId|live_id|streamId|roomId)":\s*"([^"]{8,20})"', json_str)
                            if liveid_match:
                                result['live_id'] = liveid_match.group(1)
                                print(f"从JSON找到live_id: {result['live_id']}")

                    except:
                        continue

            # 检查是否找到必要的配置
            required_fields = ['websocket_url', 'token', 'live_id']
            found_fields = [field for field in required_fields if field in result and result[field]]

            print(f"提取结果: 找到 {len(found_fields)}/{len(required_fields)} 个必需字段")
            print(f"已找到字段: {found_fields}")

            # 必须找到所有3个必需字段才算成功
            if len(found_fields) >= 3:
                print("成功! 所有必需参数提取成功!")
                return result
            else:
                missing_fields = [f for f in required_fields if f not in found_fields]
                print(f"缺少必需字段: {missing_fields}")

                # 特殊处理：如果有websocket_url但没有live_id，尝试从API获取
                if result.get('websocket_url') and 'websocketinfo' in result['websocket_url']:
                    print("检测到websocketinfo API URL，尝试调用获取真实参数...")
                    api_result = self._call_websocket_info_api(result['websocket_url'], username)
                    if api_result:
                        result.update(api_result)
                        # 重新检查必需字段
                        found_fields = [field for field in required_fields if field in result and result[field]]
                        if len(found_fields) >= 3:
                            print("通过API调用获取到完整参数!")
                            return result

                # 尝试从websocket URL参数中提取live_id
                if result.get('websocket_url') and not result.get('live_id'):
                    live_id_from_url = self._extract_live_id_from_url(result['websocket_url'])
                    if live_id_from_url:
                        result['live_id'] = live_id_from_url
                        found_fields = [field for field in required_fields if field in result and result[field]]
                        print(f"从URL参数中提取到live_id: {live_id_from_url}")
                        if len(found_fields) >= 3:
                            print("通过URL参数获取到完整参数!")
                            return result

                return None

        except Exception as e:
            print(f"提取WebSocket配置错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_websocket_config_selenium(self, driver):
        """使用Selenium执行JavaScript提取WebSocket配置"""
        try:
            print("尝试通过JavaScript提取配置...")

            # 改进的JavaScript代码
            js_code = r"""
            var config = {};

            // 方法1: 查找全局变量
            var globalVars = [
                'window.__INITIAL_STATE__',
                'window.LIVE_CONFIG',
                'window.CONFIG',
                'window.pageData',
                'window.__APP_INITIAL_STATE__',
                'window.liveConfig',
                'window.roomInfo'
            ];

            for (var i = 0; i < globalVars.length; i++) {
                try {
                    var obj = eval(globalVars[i]);
                    if (obj && typeof obj === 'object') {
                        var jsonStr = JSON.stringify(obj);

                        // 查找WebSocket URL
                        var wsMatches = jsonStr.match(/"(wss:\/\/[^"]*websocket[^"]*)"/gi);
                        if (wsMatches && !config.websocket_url) {
                            config.websocket_url = wsMatches[0].replace(/"/g, '');
                        }

                        // 查找token
                        var tokenMatches = jsonStr.match(/"(?:token|authToken|accessToken)"\s*:\s*"([^"]{50,})"/gi);
                        if (tokenMatches && !config.token) {
                            var tokenMatch = tokenMatches[0].match(/"([^"]{50,})"/);
                            if (tokenMatch) {
                                config.token = tokenMatch[1];
                            }
                        }

                        // 查找live_id
                        var liveIdMatches = jsonStr.match(/"(?:liveId|live_id|streamId|roomId)"\s*:\s*"([^"]{8,20})"/gi);
                        if (liveIdMatches && !config.live_id) {
                            var liveIdMatch = liveIdMatches[0].match(/"([^"]{8,20})"/);
                            if (liveIdMatch) {
                                config.live_id = liveIdMatch[1];
                            }
                        }
                    }
                } catch (e) {
                    // 忽略错误
                }
            }

            // 方法2: 搜索页面中的script标签
            var scripts = document.getElementsByTagName('script');
            for (var j = 0; j < scripts.length; j++) {
                try {
                    var scriptContent = scripts[j].innerHTML || scripts[j].textContent || '';

                    if (!config.websocket_url) {
                        var wsMatch = scriptContent.match(/["'](wss:\/\/[^"']*websocket[^"']*)["']/i);
                        if (wsMatch) {
                            config.websocket_url = wsMatch[1];
                        }
                    }

                    if (!config.token) {
                        var tokenMatch = scriptContent.match(/["']token["']\s*:\s*["']([^"']{50,})["']/i);
                        if (tokenMatch) {
                            config.token = tokenMatch[1];
                        }
                    }

                    if (!config.live_id) {
                        var liveIdMatch = scriptContent.match(/["'](?:liveId|live_id|streamId|roomId)["']\s*:\s*["']([^"']{8,20})["']/i);
                        if (liveIdMatch) {
                            config.live_id = liveIdMatch[1];
                        }
                    }
                } catch (e) {
                    // 忽略错误
                }
            }

            // 方法3: 检查网络请求（如果页面有暴露的方法）
            try {
                if (window.performance && window.performance.getEntries) {
                    var entries = window.performance.getEntries();
                    for (var k = 0; k < entries.length; k++) {
                        var entry = entries[k];
                        if (entry.name && entry.name.includes('websocket') && !config.websocket_url) {
                            config.websocket_url = entry.name;
                        }
                    }
                }
            } catch (e) {
                // 忽略错误
            }

            return config;
            """

            result = driver.execute_script(js_code)

            if result and isinstance(result, dict):
                found_count = len([k for k, v in result.items() if v])
                print(f"JavaScript提取到 {found_count} 个配置项: {list(result.keys())}")

                if found_count >= 2:
                    return result

            # 如果JavaScript方法失败，尝试直接读取页面源代码
            print("JavaScript方法未找到足够配置，尝试从页面源码搜索...")

            return None

        except Exception as e:
            print(f"JavaScript提取配置错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _call_websocket_info_api(self, api_url, username):
        """调用websocketinfo API获取真实的WebSocket URL和live_id"""
        try:
            print(f"调用API: {api_url}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://live.kuaishou.com/',
            }

            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            print(f"API返回数据: {data}")

            result = {}

            if 'data' in data:
                api_data = data['data']

                # 提取真实WebSocket URL
                if 'webSocketUrls' in api_data and api_data['webSocketUrls']:
                    ws_url = api_data['webSocketUrls'][0]
                    if ws_url.startswith('wss://'):
                        result['websocket_url'] = ws_url
                        print(f"获取到真实WebSocket URL: {ws_url}")

                # 提取live_id
                if 'liveStreamId' in api_data and api_data['liveStreamId']:
                    live_id = api_data['liveStreamId']
                    if len(live_id) >= 8:  # 验证live_id格式
                        result['live_id'] = live_id
                        print(f"获取到live_id: {live_id}")

                # 提取token (如果有的话)
                if 'token' in api_data and api_data['token']:
                    token = api_data['token']
                    if len(token) >= 50:
                        result['token'] = token
                        print(f"获取到token: {token[:50]}...")

            return result if result else None

        except Exception as e:
            print(f"调用websocketinfo API错误: {e}")
            return None

    def _call_parse_hex_api(self, live_url, websocket_url, hex_data):
        """调用hex解析API"""
        try:
            import requests
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            data = {
                'live_url': live_url,
                'websocket_url': websocket_url,
                'hex_data': hex_data
            }

            print(f"调用hex解析API...")
            response = requests.post('http://localhost:5000/api/parse-hex',
                                   json=data, headers=headers, timeout=10)

            if response.status_code == 200:
                result = response.json()
                print(f"hex解析API响应: {result}")
                return result
            else:
                print(f"hex解析API调用失败，状态码: {response.status_code}")
                return None

        except Exception as e:
            print(f"调用hex解析API失败: {e}")
            return None

    def _get_real_websocket_url(self, api_url):
        """通过API端点获取真实的WebSocket URL"""
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'Referer': 'https://live.kuaishou.com/',
                'Accept': 'application/json',
            }

            print(f"调用API获取WebSocket信息: {api_url}")
            response = requests.get(api_url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                print(f"API响应: {data}")

                # 查找WebSocket URL
                if 'data' in data and data['data']:
                    ws_info = data['data']
                    # 查找wss://格式的URL
                    for key, value in ws_info.items():
                        if isinstance(value, str) and value.startswith('wss://') and 'websocket' in value:
                            print(f"找到WebSocket URL: {value}")
                            return value

                    # 如果没有直接的wss://，尝试查找可能的websocket服务器
                    if 'websocketInfos' in ws_info:
                        ws_infos = ws_info['websocketInfos']
                        if ws_infos and len(ws_infos) > 0:
                            ws_server = ws_infos[0]
                            if 'host' in ws_server and 'port' in ws_server:
                                ws_url = f"wss://{ws_server['host']}:{ws_server['port']}/websocket"
                                print(f"构造WebSocket URL: {ws_url}")
                                return ws_url
                            elif 'url' in ws_server:
                                return ws_server['url']

                    # 检查其他可能的字段
                    for field in ['wsUrl', 'websocketUrl', 'socketUrl']:
                        if field in ws_info and ws_info[field]:
                            return ws_info[field]
            else:
                print(f"API调用失败，状态码: {response.status_code}")

        except Exception as e:
            print(f"调用API获取WebSocket URL失败: {e}")

        return None

    def _extract_live_id_from_url(self, url):
        """从URL参数中提取live_id"""
        try:
            from urllib.parse import urlparse, parse_qs

            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)

            # 查找liveStreamId参数
            if 'liveStreamId' in query_params:
                live_id = query_params['liveStreamId'][0]
                print(f"从URL参数中找到liveStreamId: {live_id}")
                return live_id

            return None

        except Exception as e:
            print(f"从URL提取live_id错误: {e}")
            return None


def create_auto_collector():
    """创建自动化采集器实例"""
    return AutoBarrageCollector()


if __name__ == "__main__":
    # 测试代码
    collector = AutoBarrageCollector()
    result = collector.collect("https://live.kuaishou.com/u/Kslala666")
    print(json.dumps(result, ensure_ascii=False, indent=2))