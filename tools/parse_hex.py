import binascii
import base64
import re
import os
import tempfile
from protobuf_inspector.types import StandardParser


def parse_hex_data(hex_data):
    """
    解析十六进制数据，提取live_id, token等参数
    :param hex_data: 十六进制字符串
    :return: 包含解析结果的字典
    """
    try:
        # 清理hex数据
        hex_data = hex_data.strip().replace(' ', '').replace('\n', '')

        # 转换为二进制数据
        data = binascii.unhexlify(hex_data)

        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(data)
        temp_file.close()

        try:
            # 使用protobuf_inspector解析
            parser = StandardParser()
            with open(temp_file.name, 'rb') as fh:
                output = parser.parse_message(fh, "message")

            print(f"解析输出: {output}")

            # 从解析结果中提取信息
            result = {}

            # 解析输出通常是字符串格式，需要进一步处理
            output_str = str(output)

            # 提取base64编码的token
            token_pattern = r'"([A-Za-z0-9+/]{50,}={0,2})"'
            token_matches = re.findall(token_pattern, output_str)

            if token_matches:
                # 通常第一个长的base64字符串是token
                result['token'] = token_matches[0]
                print(f"找到token: {result['token'][:50]}...")

            # 提取live_id (通常是较短的字符串)
            liveid_pattern = r'"([A-Za-z0-9]{8,20})"'
            liveid_matches = re.findall(liveid_pattern, output_str)

            if liveid_matches:
                # 过滤掉token，找到可能的live_id
                for match in liveid_matches:
                    if len(match) < 50 and match not in [result.get('token', '')]:
                        result['live_id'] = match
                        print(f"找到live_id: {result['live_id']}")
                        break

            # 提取page_id (通常包含下划线和时间戳)
            pageid_pattern = r'"([A-Za-z0-9_]+_\d{13})"'
            pageid_matches = re.findall(pageid_pattern, output_str)

            if pageid_matches:
                result['page_id'] = pageid_matches[0]
                print(f"找到page_id: {result['page_id']}")

            return result

        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file.name)
            except:
                pass

    except Exception as e:
        print(f"解析hex数据错误: {e}")
        return None


if __name__ == "__main__":
    # 测试数据
    hex_data = '08c8011a88020ad8015a322b77743234764b484e4138685774544a614b48474478747a67532f6d4f337634464d643437543876363632417a706b5476315437385a53556f4c617a594248636d43386e35467837734d796f53794358436458316e4e643847784e4e75434851456e50317563675954544174503465447164576274667545623248574157446134612b683175594e30487241784f705170716975435264556c515945587436335a7164483269786d5a786a4a724453777731707376314a654e6e2b754850704a4c6132676c6452477a756a484e637a64763358673d3d120b3152724d722d4b59416a633a1e7638494e7a71694e574d5f56527357795f31373538343734343034333431'

    result = parse_hex_data(hex_data)
    print(f"解析结果: {result}")

#  message:
#       1 <varint> = 200
#       3 <chunk> = message:
#           1 <chunk> =
#   "7oyhxmn8tCw/L1BR+YHhdzWqjJTKextEnZZxPStOVryFo+vGFTeinb7KGpfiQVedAE2ynrmJHed/
#   Aplj5TAPzKdyjcEy5ZXVFfxpd34DcF1XXFBm3fIbXMsbFpSDhqurNFkIbbLoCncmGKjMQd5vA+NOp
#   nhecvTzgNdVthrdUvSe6J/PVfujnbaL7Hu2sNqW+fcsuWi3vhZQOsqIq/pk1w=="
#           2 <chunk> = "aRsNWDK31JM"
#           7 <chunk> = "UCvbtPMrVUOBVmDu_1757955201599"