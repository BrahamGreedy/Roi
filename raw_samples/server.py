import tkinter as tk
import socket
import threading
import json
import random
import queue
from config import *

class GameServer:
    def __init__(self, master):
        self.master = master
        self.master.title("Host (Tank Controls)")
        
        # Данные: {id: {conn, x, y, color, direction, last_order}}
        self.clients = {} 
        self.client_id_counter = 0
        self.walls = set()
        self.finish_point = (GRID_W - 2, GRID_H - 2)
        self.selected_agent_id = None
        self.msg_queue = queue.Queue()

        self.generate_map()
        self.setup_gui()
        self.start_server()

    def generate_map(self):
        # ТОЛЬКО ВНЕШНИЕ СТЕНЫ
        self.walls.clear()
        for x in range(GRID_W):
            self.walls.add((x, 0))
            self.walls.add((x, GRID_H-1))
        for y in range(GRID_H):
            self.walls.add((0, y))
            self.walls.add((GRID_W-1, y))
        
        if self.finish_point in self.walls: self.walls.remove(self.finish_point)

    def setup_gui(self):
        self.canvas = tk.Canvas(self.master, width=GRID_W*CELL_SIZE, height=GRID_H*CELL_SIZE, bg='white')
        self.canvas.pack(side=tk.LEFT)
        
        panel = tk.Frame(self.master)
        panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        tk.Label(panel, text="ЛОГ КОМАНДИРА").pack()
        self.log_list = tk.Listbox(panel, height=20, width=30)
        self.log_list.pack()
        
        tk.Label(panel, text="Стрелки Вверх/Вниз: Движение").pack(pady=(10,0))
        tk.Label(panel, text="Стрелки Влево/Вправо: Поворот").pack()
        
        self.status_label = tk.Label(panel, text="...", fg="blue", font=("Arial", 10, "bold"))
        self.status_label.pack(pady=10)

        self.master.bind("<KeyPress>", self.on_key_press)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.process_queue()
        self.draw_grid()

    def log(self, msg):
        self.msg_queue.put(('log', msg))

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)
        threading.Thread(target=self.accept_clients, daemon=True).start()

    def accept_clients(self):
        while True:
            conn, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

    def handle_client(self, conn):
        c_id = self.client_id_counter
        self.client_id_counter += 1
        
        # Спавн подальше от стен
        sx, sy = random.randint(2, GRID_W-3), random.randint(2, GRID_H-3)
        start_dir = random.choice([DIR_N, DIR_E, DIR_S, DIR_W])
        color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        
        self.clients[c_id] = {
            'id': c_id, 
            'x': sx, 'y': sy, 
            'direction': start_dir,
            'color': color, 
            'conn': conn, 
            'last_order': None
        }
        self.msg_queue.put(('refresh', None))
        self.log(f"Агент {c_id} готов.")

        try:
            conn.send(json.dumps({"type": "init", "id": c_id}).encode() + b'\n')
            while True:
                data = conn.recv(1024)
                if not data: break
                lines = data.decode().strip().split('\n')
                for line in lines:
                    if not line: continue
                    try:
                        msg = json.loads(line)
                        if msg['type'] == 'action_attempt':
                            self.validate_and_action(c_id, msg['action'])
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"Err {c_id}: {e}")
        finally:
            if c_id in self.clients: del self.clients[c_id]
            self.msg_queue.put(('refresh', None))
            conn.close()

    def send_order(self, client_id, action_code):
        if client_id not in self.clients: return
        agent = self.clients[client_id]
        
        # action_code: "forward", "backward", "turn_left", "turn_right"
        cmd_ru = {
            "forward": "ВПЕРЕД",
            "backward": "НАЗАД",
            "turn_left": "ПОВОРОТ ЛЕВ.",
            "turn_right": "ПОВОРОТ ПРАВ."
        }

        agent['last_order'] = action_code
        msg = {"type": "order", "cmd": cmd_ru[action_code]}
        
        try:
            agent['conn'].send(json.dumps(msg).encode() + b'\n')
            self.log(f"Приказ {client_id}: {cmd_ru[action_code]}")
        except:
            pass

    def validate_and_action(self, client_id, action):
        agent = self.clients[client_id]
        expected = agent['last_order']
        
        # 1. Проверка дисциплины
        if expected is None or action != expected:
            resp = {"type": "feedback", "status": "error", "msg": "НЕВЕРНАЯ КОМАНДА! Нарушение приказа!"}
            agent['conn'].send(json.dumps(resp).encode() + b'\n')
            self.log(f"Агент {client_id} ошибся.")
            return

        # 2. Логика выполнения
        current_dir = agent['direction']
        cx, cy = agent['x'], agent['y']
        
        if action == "turn_left":
            agent['direction'] = (current_dir - 1) % 4
            self.send_success(agent)
            
        elif action == "turn_right":
            agent['direction'] = (current_dir + 1) % 4
            self.send_success(agent)
            
        elif action in ["forward", "backward"]:
            dx, dy = OFFSETS[current_dir]
            if action == "backward":
                dx, dy = -dx, -dy
            
            new_x, new_y = cx + dx, cy + dy
            
            # Коллизии
            if (new_x, new_y) in self.walls:
                self.send_fail(agent, "Стена!")
                return
            
            for oid, other in self.clients.items():
                if oid != client_id and other['x'] == new_x and other['y'] == new_y:
                    self.send_fail(agent, "Авария!")
                    return
            
            agent['x'], agent['y'] = new_x, new_y
            self.send_success(agent)
            
            if (new_x, new_y) == self.finish_point:
                self.log(f"АГЕНТ {client_id} ПОБЕДИЛ!")

    def send_success(self, agent):
        agent['last_order'] = None
        resp = {"type": "feedback", "status": "success", "msg": "Выполнено."}
        agent['conn'].send(json.dumps(resp).encode() + b'\n')
        self.msg_queue.put(('refresh', None))

    def send_fail(self, agent, reason):
        resp = {"type": "feedback", "status": "error", "msg": f"ОШИБКА: {reason}"}
        agent['conn'].send(json.dumps(resp).encode() + b'\n')

    def on_key_press(self, event):
        if self.selected_agent_id is None: return
        
        # Схема управления "Танк"
        if event.keysym == 'Up': self.send_order(self.selected_agent_id, "forward")
        elif event.keysym == 'Down': self.send_order(self.selected_agent_id, "backward")
        elif event.keysym == 'Left': self.send_order(self.selected_agent_id, "turn_left")
        elif event.keysym == 'Right': self.send_order(self.selected_agent_id, "turn_right")

    def on_canvas_click(self, event):
        cx = event.x // CELL_SIZE
        cy = event.y // CELL_SIZE
        for cid, data in self.clients.items():
            if data['x'] == cx and data['y'] == cy:
                self.selected_agent_id = cid
                self.status_label.config(text=f"Выбран агент: {cid}", fg=data['color'])
                self.draw_grid()
                return

    def process_queue(self):
        try:
            while True:
                cmd, data = self.msg_queue.get_nowait()
                if cmd == 'refresh': self.draw_grid()
                elif cmd == 'log':
                    self.log_list.insert(0, data)
        except queue.Empty:
            pass
        self.master.after(100, self.process_queue)

    def draw_grid(self):
        self.canvas.delete("all")
        # Стены (только рамка теперь)
        for wx, wy in self.walls:
            self.canvas.create_rectangle(wx*CELL_SIZE, wy*CELL_SIZE, (wx+1)*CELL_SIZE, (wy+1)*CELL_SIZE, fill="#444", outline="#444")
            
        # Финиш
        fx, fy = self.finish_point
        self.canvas.create_rectangle(fx*CELL_SIZE, fy*CELL_SIZE, (fx+1)*CELL_SIZE, (fy+1)*CELL_SIZE, fill="gold")

        # Агенты (ТРЕУГОЛЬНИКИ)
        for cid, data in self.clients.items():
            cx, cy = data['x'], data['y']
            direction = data['direction']
            
            # Координаты центра клетки в пикселях
            px = cx * CELL_SIZE + CELL_SIZE/2
            py = cy * CELL_SIZE + CELL_SIZE/2
            r = CELL_SIZE / 2 - 2 # Радиус (отступ)
            
            # Вершины треугольника в зависимости от направления
            if direction == DIR_N:
                points = [px, py-r,  px-r, py+r,  px+r, py+r] # Острие вверх
            elif direction == DIR_E:
                points = [px+r, py,  px-r, py-r,  px-r, py+r] # Острие вправо
            elif direction == DIR_S:
                points = [px, py+r,  px-r, py-r,  px+r, py-r] # Острие вниз
            elif direction == DIR_W:
                points = [px-r, py,  px+r, py-r,  px+r, py+r] # Острие влево
            
            outline = "red" if cid == self.selected_agent_id else "black"
            width = 3 if cid == self.selected_agent_id else 1
            
            self.canvas.create_polygon(points, fill=data['color'], outline=outline, width=width)
            
            # ID в центре
            self.canvas.create_text(px, py, text=str(cid), fill="white" if data['color']!='#ffffff' else 'black', font=("Arial", 8, "bold"))

if __name__ == "__main__":
    root = tk.Tk()
    app = GameServer(root)
    root.mainloop()