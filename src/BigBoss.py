from Supervisor import Supervisor
import socket
import threading
from config import HOST, PORT
from utils import *

class BigBoss():
    def __init__(self):
        self.agents = {} # Словарь {id_robota: socket_connection}
        self.server_socket = None
        self.create_socket()

    def set_field_size(self, field_size):
        self.field_size = field_size

    def set_robot_data(self, robot_data):
        self.robot_data = robot_data
    
    def set_breakstone_mask(self, breakstone_mask):
        self.breakstone_mask = breakstone_mask

    def create_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Разрешаем повторное использование порта, чтобы не ждать таймаута после перезапуска
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(4)
        print(f"Server started on {HOST}:{PORT}")
        threading.Thread(target=self.accept_clients, daemon=True).start()

    def accept_clients(self):
        while True:
            conn, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()
    
    def handle_client(self, conn):
        """
        Обработка подключения клиента.
        Ожидаем первое сообщение вида {"type": "register", "id": 1}
        """
        try:
            msg = recv_message(conn)
            if msg and msg.get('type') == 'register':
                agent_id = msg.get('id')
                self.agents[agent_id] = conn
                print(f"[BigBoss] Agent {agent_id} connected via {conn.getpeername()}")
            else:
                print(f"[BigBoss] Unknown client connection attempt")
                conn.close()
        except Exception as e:
            print(f"[BigBoss] Error handling client: {e}")

    def send_target_to_agent(self, agent_id, target_x, target_y):
        """
        Отправка двух чисел (координат) выбранному агенту.
        """
        if agent_id in self.agents:
            conn = self.agents[agent_id]
            # Формируем сообщение. Структура может быть любой, 
            # но сделаем так, как просили: отправка координат.
            payload = {
                "type": "move_to",
                "target": (int(target_x), int(target_y))
            }
            try:
                send_message(conn, payload)
                print(f"[BigBoss] Sent target ({target_x}, {target_y}) to Agent {agent_id}")
                return True
            except Exception as e:
                print(f"[BigBoss] Failed to send to {agent_id}: {e}")
                del self.agents[agent_id] # Удаляем мертвое соединение
                return False
        else:
            print(f"[BigBoss] Agent {agent_id} not connected")
            return False

    def get_connected_agents(self):
        return list(self.agents.keys())
    
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