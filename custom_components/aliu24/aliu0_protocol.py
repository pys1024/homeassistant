import RPi.GPIO as gpio
from nrf24 import NRF24
import time


class Aliu0_protocol:
    '''自定义通信协议V1.0说明
    通信协议结构：
    通信指令(1字节)+操作数据(1字节)+设备编号(1字节)+发送方地址(5字节)+附加数据(24字节)
    发送方地址能让接收方知道指令由谁发起，附加数据根据指令利用，一般不用
    '''
    # 主机与子机通信指令
    DEVICE_STATE  = 0XA6        #返回设备当前的状态，没有操作数据
    DEVICE_TYPE   = 0XAF	#返回当前设备的类型，没有操作数据
    SET_STATE     = 0XB9	#设置设备的状态
    LOCK_STATE    = 0X86	#锁定设备的状态
    REQUEST_STATE = 0X83	#请求设备的状态
    REQUEST_TYPE  = 0X3A	#请求设备的类型
    # 设备状态
    DISCONNECTED  = 0XF9        #represent device disconnected
    STATE_ON      = 0X03	#开启状态
    STATE_OFF     = 0X34	#关闭状态
    STATE_0       = 0X73	#状态0
    STATE_1       = 0X74	#状态1
    STATE_2       = 0X75	#状态2
    STATE_3       = 0X76	#状态3
    STATE_4       = 0X77	#状态4
    STATE_5       = 0X78	#状态5
    # 设备种类
    TYPE_SWITCH   = 0XC3	#设备控制开关类型，开关两种状态
    TYPE_SENSOR   = 0XD8	#传感器类型，开关两种状态
    TYPE_TEMP     = 0X3D	#温度传感器类型，返回温度数值
    TYPE_TIME     = 0X5B	#计时器类型，返回时间信息
    TYPE_LIGHT    = 0X9F	#光强传感器类型，返回光照强度
    TYPE_DISTANCE = 0X1C	#距离传感器类型，返回距离数值
    # 其他
    NOTHING       = 0X64	#无

    def __init__(self, bus, ce, irq, host_addr, slave_base):
        """Initialize"""
        self._host_addr = host_addr
        self._slave_addr = [0x00] + slave_base
        self._tx_pack = [0]*32
        self._tx_pack[0] = self.SET_STATE
        self._tx_pack[1] = self.STATE_ON
        self._tx_pack[3:8] = self._host_addr

        self._rx_pack = [0]

        self._radio = NRF24()
        self._radio.begin(0, bus, ce, irq)

        self._radio.setRetries(15,15)

        self._radio.setPayloadSize(32)
        self._radio.setChannel(0x40)
        self._radio.setDataRate(NRF24.BR_2MBPS)

        #radio.setPALevel(NRF24.PA_MAX)
        #radio.setAutoAck(0)
        #radio.setAutoAckPipe(0, True)
        #radio.setAutoAckPipe(1, True)
        #radio.setCRCLength(NRF24.CRC_16)

        self._radio.openWritingPipe(self._slave_addr)
        self._radio.openReadingPipe(1, self._host_addr)

        #self._radio.startListening()
        #self._radio.stopListening()

        # radio.printDetails()
    def _send_pack(self,retry):
        count = 0
        while count <= retry:
            count += 1
            sta = self._radio.write(self._tx_pack)
            if sta == 1:
                return True
        return False

    def set_on(self, addr, id):
        self._tx_pack[0] = self.SET_STATE
        self._tx_pack[1] = self.STATE_ON
        self._tx_pack[2] = id
        self._slave_addr[0] = addr

        self._radio.openWritingPipe(self._slave_addr)
        self._radio.stopListening()

        sta = self._send_pack(5)
        self._radio.startListening ()
        return sta

    def set_off(self, addr, id):
        self._tx_pack[0] = self.SET_STATE
        self._tx_pack[1] = self.STATE_OFF
        self._tx_pack[2] = id
        self._slave_addr[0] = addr

        self._radio.openWritingPipe(self._slave_addr)
        self._radio.stopListening()

        sta = self._send_pack(5)
        self._radio.startListening ()
        return sta

    def lock_on(self, addr, id):
        self._tx_pack[0] = self.LOCK_STATE
        self._tx_pack[1] = self.STATE_ON
        self._tx_pack[2] = id
        self._slave_addr[0] = addr

        self._radio.openWritingPipe(self._slave_addr)
        self._radio.stopListening()

        sta = self._send_pack(5)
        self._radio.startListening ()
        return sta

    def lock_off(self, addr, id):
        self._tx_pack[0] = self.LOCK_STATE
        self._tx_pack[1] = self.STATE_OFF
        self._tx_pack[2] = id
        self._slave_addr[0] = addr

        self._radio.openWritingPipe(self._slave_addr)
        self._radio.stopListening()

        sta = self._send_pack(5)
        self._radio.startListening ()
        return sta

    def request(self, addr, id):
        self._tx_pack[0] = self.REQUEST_STATE
        self._tx_pack[1] = self.DEVICE_STATE
        self._tx_pack[2] = id
        self._slave_addr[0] = addr

        self._radio.openWritingPipe(self._slave_addr)
        self._radio.stopListening()

        sta = self._send_pack(5)
        self._radio.startListening ()
        return sta

    def get_data (self):
        pipe = [0]        
        data = [False, 0x00, 0, False] # status, device_addr, device_id, device_state
        if self._radio.available (pipe, False, 1):
            self._radio.read (self._rx_pack)
            if self._rx_pack [0] == self.DEVICE_STATE:
                data [0] = True
                data [1] = self._rx_pack [3]
                data [2] = self._rx_pack [2]
                data [3] = self._rx_pack [1] == self.STATE_ON
        return data

    def __del__ (self):
        self._radio.end()
