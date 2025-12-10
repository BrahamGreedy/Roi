import tkinter as tk
import socket
import threading
import json
from client_config import *

class AgentClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Tank Agent")
        
        self.order_frame = tk.Frame(master, bg="#222", pady=15)
        self.order_frame.pack(fill=tk.X)
        self.order_label = tk.Label(self.order_frame, text="ЖДУ ПРИКАЗ", font=("Impact", 18), fg="#00ff00", bg="#222")
        self.order_label.pack()

        self.log_text = tk.Text(master, height=8, width=40, state='disabled', bg="#f0f0f0")
        self.log_text.pack(padx=5, pady=5)

        # Пульт управления (Танковая схема)
        ctrl_frame = tk.Frame(master)
        ctrl_frame.pack(pady=15)
        
        btn_cfg = {'width': 8, 'height': 2, 'font': ('Arial', 10, 'bold')}
        
        # Расположение кнопок
        #       [ ВПЕРЕД ]
        # [ЛЕВО] [ НАЗАД  ] [ПРАВО]
        
        btn_fwd = tk.Button(ctrl_frame, text="ВПЕРЕД", command=lambda: self.send_action("forward"), **btn_cfg)
        btn_fwd.grid(row=0, column=1)
        
        btn_left = tk.Button(ctrl_frame, text="ПОВ. ЛЕВО", command=lambda: self.send_action("turn_left"), **btn_cfg)
        btn_left.grid(row=1, column=0)
        
        btn_bwd = tk.Button(ctrl_frame, text="НАЗАД", command=lambda: self.send_action("backward"), **btn_cfg)
        btn_bwd.grid(row=1, column=1)
        
        btn_right = tk.Button(ctrl_frame, text="ПОВ. ПРАВО", command=lambda: self.send_action("turn_right"), **btn_cfg)
        btn_right.grid(row=1, column=2)

        self.sock = None
        threading.Thread(target=self.network_loop, daemon=True).start()

    def log(self, text):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def set_order_text(self, text, color="#00ff00"):
        self.order_label.config(text=text, fg=color)

    def network_loop(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            self.log("Связь с Хостом установлена.")
            
            buffer = ""
            while True:
                data = self.sock.recv(1024)
                if not data: break
                buffer += data.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line: self.process_server_msg(json.loads(line))
        except Exception as e:
            self.log(f"Сбой сети: {e}")
            self.set_order_text("DISCONNECTED", "red")

    def process_server_msg(self, msg):
        mtype = msg.get("type")
        
        if mtype == "init":
            self.log(f"Система инициализирована. ID: {msg['id']}")
            
        elif mtype == "order":
            cmd = msg['cmd']
            self.set_order_text(f"ПРИКАЗ: {cmd}", "cyan")
            self.log(f">> Получен приказ: {cmd}")

        elif mtype == "feedback":
            status = msg['status']
            text = msg['msg']
            if status == "success":
                self.log(f"[OK] {text}")
                self.set_order_text("ОЖИДАНИЕ...", "gray")
            else:
                self.log(f"[ОШИБКА] {text}")
                self.set_order_text("ПРОВАЛ ОПЕРАЦИИ", "red")

    def send_action(self, action_code):
        if not self.sock: return
        req = {"type": "action_attempt", "action": action_code}
        try:
            self.sock.send(json.dumps(req).encode() + b'\n')
        except:
            self.log("Ошибка передачи пакета")

if __name__ == "__main__":
    root = tk.Tk()
    app = AgentClient(root)
    root.mainloop()