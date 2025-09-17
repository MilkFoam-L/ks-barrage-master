import binascii
from protobuf_inspector.types import StandardParser

hex_data = '08c8011a88020ad8014b75434b684e6d312f694b4a5156436175484956353458304659554c714c345872524536566b5374565862376e727075457651664f6b494471747350696b576530306c6c64775166716436644c77324b594f3136726f426f756161596648636e514a657253334747306a776c7748774253344f56382f4a4b69373173486f65594a6b3339544970776d675664344f5a48537076706e535a736436643750502b6a564464516d66767a425471733245735377564335354a4f61786e494a495976584b6678326c563868574f394254444a437457455666773d3d120b643768315950497a3354673a1e596d445f587a674d354e6a73383869595f31373538313238383834303630'

# 转换为二进制数据
data = binascii.unhexlify(hex_data)

# 写入二进制文件
with open('my-protobuf', 'wb') as w:
    w.write(data)

# 使用protobuf_inspector解析
parser = StandardParser()
with open('my-protobuf', 'rb') as fh:
    output = parser.parse_message(fh, "message")

print(output)

#  message:
#       1 <varint> = 200
#       3 <chunk> = message:
#           1 <chunk> =
#   "7oyhxmn8tCw/L1BR+YHhdzWqjJTKextEnZZxPStOVryFo+vGFTeinb7KGpfiQVedAE2ynrmJHed/
#   Aplj5TAPzKdyjcEy5ZXVFfxpd34DcF1XXFBm3fIbXMsbFpSDhqurNFkIbbLoCncmGKjMQd5vA+NOp
#   nhecvTzgNdVthrdUvSe6J/PVfujnbaL7Hu2sNqW+fcsuWi3vhZQOsqIq/pk1w=="
#           2 <chunk> = "aRsNWDK31JM"
#           7 <chunk> = "UCvbtPMrVUOBVmDu_1757955201599"