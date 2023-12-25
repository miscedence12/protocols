import json


SUNLINK_HEADER_ONE = 0x42
SUNLINK_HEADER_TWO = 0x53
SUNLINK_HEADER_THR = 0x03

robot_id=1

def checkCrc(data, size):
    #初始化了用于CRC的生成多项式和初始值。
    gen = 0xA001  #十进制为40961
    crc = 0xFFFF  #十进制为65535

    if data == None:
        return crc
    
    for i in range(size):
        #将数据与 CRC 寄存器进行按位异或操作，相同为 0，不同为 1
        crc ^=  data[i]
        #每次循环都会检查 crc 的最低位是否为 1，
        #如果是，则执行右移一位和与生成多项式异或的操作，否则执行简单的右移一位操作
        for k in range(8):
            if (crc & 0x01) == 0x01:
                crc = crc >> 1
                crc = crc ^ gen
            else:
                crc = crc >> 1
    return crc

def intToChar(data):
    return data.to_bytes(length=1, byteorder='little').decode('UTF-8')

def wrapper(msg_id, json_msg):  #数据包构建函数
   
    # 转化成string
    msg = json.dumps(json_msg)

    buf = bytearray()
    buf.append(SUNLINK_HEADER_ONE)
    buf.append(SUNLINK_HEADER_TWO)
    buf.append(SUNLINK_HEADER_THR)
    
    # 2 --> size
    str_len = len(msg) #28
    msg_len = str_len + 2 + 4 + 4

    # 记录消息长度（2字节）
    buf.append((msg_len & 0x00FF)) #十进制38等于十六进制26，26的ASCII码为&，所以这里的&是为了标识消息长度
    buf.append((msg_len >> 8))  #右移8位

    # 记录消息ID（2字节）
    buf.append((msg_id & 0x00FF)) #十进制3152&0x00FF=0101 0000 =十进制80 80的ASCII码为P
    buf.append((msg_id >> 8)) #右移8位得到1100 ，十六进制为C
    
    # 记录robotID（4字节）
    buf.append((robot_id & 0xFF))
    buf.append((robot_id >> 8) & 0xFF)
    buf.append((robot_id >> 16) & 0xFF)
    buf.append((robot_id >> 24) & 0xFF)
    

    # 序列化字符串尺寸
    buf.append((str_len & 0x00FF))  #28->1c 10进制转16进制
    buf.append((str_len >> 8))

    # 拷贝数据
    for item in msg:
        buf.append(int.from_bytes(item.encode('UTF-8'), byteorder='little'))

    # CRC校验
    msg_crc = checkCrc(buf, len(buf))
    buf.append(msg_crc & 0xFF)
    buf.append(msg_crc >> 8)
    return buf

# 从字节流中将数据转换成对应的消息内容（转换成‘列表’）
class ParseMsg:
    buf = None

    def __init__(self):
        self.buf = []

    def pushData(self, data): #将字节数据添加到缓冲区
        for item in data:
            self.buf.append(item)

    def parseMsg(self):  #解析缓冲区中的数据，检查帧头、消息长度、CRC校验等，并提取出消息ID和JSON消息内容。
        msg = []
        if len(self.buf) < 7:
            return False, -1, json.loads('{}')
        
        # print(self.buf)

        # 判断消息头是否正确
        if not self.msgHeader(self.buf):
            return False, -1, json.loads('{}')

        # print('Msg Header Ok')
        # 获取消息长度
        print(self.buf[4] << 8)
        msg_len = (self.buf[4] << 8)  + self.buf[3] - 4

        # print('Msg Len: ', msg_len)
        # 判断消息接受是否完整
        if len(self.buf) < msg_len + 9:
            return False, -1, json.loads('{}')

        # 进行数据校验
        msg_crc = (self.buf[msg_len + 8] << 8) + self.buf[msg_len + 7] 
        new_crc = checkCrc(self.buf, msg_len + 7)
        # print('old crc:', hex(msg_crc), 'new_crc:', hex(new_crc))
        if new_crc != msg_crc:
            self.popByte(0, msg_len + 9)
            return False, -1, json.loads('{}')
        # print('Old: ', msg_crc, ', New: ', new_crc)
        
        # 获取消息id
        msg_id = self.buf[5] + (self.buf[6] << 8)
        str_size = self.buf[11] + (self.buf[12] << 8)
        # print('MsgID: ', msg_id, 'StrSize: ', str_size)

        # 删除头部数据
        self.popByte(0, 13)

        # 获取消息
        for i in range(0, str_size):
            msg.append(intToChar(self.buf[i]))
        
        # 删除消息(2 --> crc)
        self.popByte(0, str_size + 2)

        try:
            # print(msg) 
            json_data = json.loads(''.join(msg))
        except:
            print('unicode decode error')
            return False, msg_id, json.loads('{}')

        return True, msg_id, json_data

    # 校验消息头
    def msgHeader(self, data):
        if data == None:
            return False
        
        header1 = data[0]
        header2 = data[1]
        header3 = data[2]

        if header1 != SUNLINK_HEADER_ONE:
            print('header1: ', header1)
            return False

        if header2 != SUNLINK_HEADER_TWO:
            print('header2: ', header2)
            return False

        if header3 != SUNLINK_HEADER_THR:
            print('header3: ', header3)
            return False

        return True
    
    #从缓冲区中移除指定长度的字节数据。
    def popByte(self, start, len): 
        for i in range(start, start + len):
            self.buf.pop(start)

if  __name__=="__main__":
    msg = {'robot_id': 1, 'client': 0x03}
    buf=wrapper(3152,msg)
    print(f"buf:{buf},len:{len(buf)}")

    buf_parse=ParseMsg()
    buf_parse.pushData(buf)
    ret, msg_id, msg=buf_parse.parseMsg()
    print(f"ret:{ret},msg_id:{msg_id},msg:{msg}")
  
    