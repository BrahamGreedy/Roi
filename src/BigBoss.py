from Supervisor import Supervisor
import socket
import threading
from config import HOST, PORT

from utils import *

''' это идеи про данные робота
про движение робота:
1) есть просто некий флаг для каждого робота, который отвечает за движение и если изменения координат не совпадает с флагом значит ошибка
2) считает движение только по изменениям координат
'''
'''
что может робот передать биг боссу
1) Заряд
2) Мощность мотора
3) Есть ли препятствие спереди
'''

class BigBoss():
    def __init__(self):
        self.supervisor = Supervisor()

        self.agents = {}
        
        self.create_socket()

    def get_field_size(self):
        self.field_size = self.supervisor.get_field_size()

    def get_robot_data(self):
        self.robot_data = self.supervisor.get_robot_data()
    
    def get_breakstone_mask(self):
        self.breakstone_mask = self.supervisor.get_breakstone_mask()

    def create_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(4)
        threading.Thread(target=self.accept_clients, daemon=True).start()

    def accept_clients(self):
        while True:
            conn, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()
    
    def handle_client(self, conn):
        pass

    def get_command(self):
        pass

    def send_command(self):
        pass

    def get_agent_positions(self):
        pass

    def create_logic(self):
        pass