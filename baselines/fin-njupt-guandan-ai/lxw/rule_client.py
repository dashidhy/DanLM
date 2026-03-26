# -*- coding: utf-8 -*-
# @Time       : 2020/10/1 16:30
# @Author     : Duofeng Wu
# @File       : client.py
# @Description:


import json
from ws4py.client.threadedclient import WebSocketClient
from state import State
from lxw.action import Action


class ExampleClient(WebSocketClient):

    def __init__(self, url):
        super().__init__(url)
        self.state = State()
        self.action = Action()
        self.position = None

    def opened(self):
        pass

    def closed(self, code, reason=None):
        print("Closed down", code, reason)

    def received_message(self, message):
        message = json.loads(str(message))                                    # 先序列化收到的消息，转为Python中的字典
        result = self.state.parse(message)  # 调用状态对象来解析状态
        stage = result[0]
        m_type = result[1]
        if m_type == 'notify':
            if stage == 'beginning':
                self.position = result[3]
        if "actionList" in message:                                           # 需要做出动作选择时调用动作对象进行解析
            public = message['publicInfo']
            rest_card = []
            for i in range(4):
                rest_card.append(public[i]['rest'])
            act_index = self.action.parse(message,self.position,rest_card)
            self.send(json.dumps({"actIndex": act_index}))


if __name__ == '__main__':
    try:
        ws = ExampleClient('ws://127.0.0.1:23456/game/client1')
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
