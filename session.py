import socket
import threading
import time
import logging

# 自定义python
import huidiao.sunlink

BUFFERSIZE = 1024

class Session:
    session = None
    address = None
    shutdown = True
    logger = None
    ended = False
    parsemsg = None
    handler = None

    def __init__(self, addr, log_conf):
        # 设置日志参数
        logging.basicConfig(level = logging.INFO,format = '[%(asctime)s][%(funcName)s][%(levelname)s]: %(message)s')
        self.logger = logging.getLogger('session')
        self.parsemsg = huidiao.sunlink.ParseMsg()

        # 设置TCP的客户端
        self.session = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

        # 设置socket超时（这里超时会报异常）
        self.session.settimeout(1)

        try:
            self.address = addr
            self.session.connect(addr)
        except:
            self.logger.warn('每2s尝试连接一次服务器')
            tryThread = threading.Thread(target=self.tryConnect)
            tryThread.start()
        else:
            self.logger.info('成功连接到服务器')
            recvThread = threading.Thread(target=self.recvMsg)
            recvThread.start()
            self.shutdown = False
    
    # 尝试连接到服务器
    def tryConnect(self):
        while not self.ended:
            try:
                self.session.connect(self.address)
            except:
                self.logger.warn('未发现服务器程序')
                time.sleep(2)
            else:
                break
        
        if not self.ended:
            self.logger.info('服务器连接成功')
            # 建立连接的标志
            self.shutdown = False

            # 启动接受数据线程
            recvThread = threading.Thread(target=self.recvMsg)
            recvThread.start()

    def isConnect(self):
        if self.shutdown:
            return False
        else:
            return True

    # 向服务器端发送数据
    def sendMsg(self, msg_id, msg):
        if msg == None:
            return False
        if self.shutdown:
            return False

        try:
            # 将json消息序列化
            inData = huidiao.sunlink.wrapper(msg_id, msg)

            # 发送消息
            self.session.send(inData)
        except UnboundLocalError:
            self.logger.error('socket is invalid')
            
        return True
    
    # 接收来自服务器的数据
    def recvMsg(self):
        while not self.ended:
            try:
                out_data = self.session.recv(BUFFERSIZE)
                if len(out_data) == 0:
                    # 连接断开标志
                    self.shutdown = True
                    self.logger.warn('服务器程序断开')
                    break
                
                # self.logger.info('返回数据信息：{!r}'.format(out_data))
            except UnboundLocalError:
                self.logger.error('socket is invalid')
            except IOError:
                # self.logger.error('socket timeout')
                continue

            self.parsemsg.pushData(out_data)
            ret, msg_id, msg = self.parsemsg.parseMsg()
            if not ret:
                continue

            if self.handler != None:
                self.handler(msg_id, msg)

        if not self.ended:
            self.logger.info('尝试连接到服务器')
            self.session = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            tryThread = threading.Thread(target=self.tryConnect)
            tryThread.start()

    def registerHandler(self, handler):
        self.handler = handler

    def exit(self):
        try:
            self.ended = True
            # 好像使用shutdown还需要判断是否连接成功
            if not self.shutdown:
                # 0: rd, 1: wr, 2: rd_wr
                self.session.shutdown(2)
                
            self.shutdown = True
            # 关闭连接
            self.session.close()

            self.logger.info('Session Exit!!!')
        except UnboundLocalError:
            self.logger.error('socket is invalid')

    def isExit(self):
        return self.ended


        
    

