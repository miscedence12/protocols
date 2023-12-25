import huidiao.session
import time
import threading

class Gesture:
    client = None
    handler = None

    def __init__(self, ip, port):
        self.client = huidiao.session.Session((ip, port), 'huidiao/logging.conf')
        self.client.registerHandler(self.handlerMsg)

        # 启动心跳包程序
        tryThread = threading.Thread(target=self.heartBeat)
        tryThread.start()

    # 与主控相连的心跳包
    def heartBeat(self):
        # 发送给主控的心跳包数据
        msg = {'robot_id': 1, 'client': 0x03}

        # 按照1HZ周期发送心跳包
        print('Start Heart Beat')
        while not self.client.isExit():
            if not self.client.isConnect():
                time.sleep(1)
                continue

            self.client.sendMsg(3152, msg)
            time.sleep(1)
        print('Exit heart Beat')

    # 接受主控消息
    def handlerMsg(self, msg_id, json_msg):
        if self.handler != None:
            self.handler(msg_id, json_msg)
        
        '''
        if msg_id == 3100:
            # 在此处添加消息处理逻辑
            # xxxxx(具体逻辑由手势识别程序实现)
            print('Start Gesture Cmd', json_msg['start'])
        else:
            print(msg)
            return
        '''

    def registerHandler(self, handlerMsg):
        self.handler = handlerMsg
        
        # session一定要退出
        # client.exit()

    def sendMsg(self, msg_id, msg):
        self.client.sendMsg(msg_id, msg)

    def exit(self):
        self.client.exit()
