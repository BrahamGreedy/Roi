import tkinter as tk
import random
import numpy as np
import cv2
from PIL import Image, ImageTk

from Supervisor import Supervisor
from BigBoss import BigBoss


from config import GRID_W, CELL_SIZE, GRID_H

class AFC_Chipok:
    def __init__(self, master):
        self.master = master
        title = random.choice(['Тут могла быть ваша реклама', 'Окно управления системы роя роботов'])
        self.master.title(title)

        self.flag_krest = 0 # 0 - нет крестика, 1 - куча (красный), 2 - зона (синий)
        self.krest_coord = (None, None)

        self.bb = BigBoss()
        self.supervisor = Supervisor('imgs', 8, 5, 0)

        self.setup_gui()
        self.bb.set_robot_data(self.supervisor.get_robot_data())

    def setup_gui(self):
        img = cv2.cvtColor(cv2.imread('C:\\Users\\Braham\\Desktop\\roi\\22.jpeg'), cv2.COLOR_BGR2RGB)
        #cv2 img
        h, w = img.shape[:2]
        koeff_y = (GRID_H*CELL_SIZE)/h
        koeff_x = (GRID_W*CELL_SIZE)/w

        koeff = min(koeff_y, koeff_x)
        img = cv2.resize(img, None, fx=koeff, fy=koeff, interpolation=cv2.INTER_LINEAR)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)

        self.canvas = tk.Canvas(self.master, width=GRID_W*CELL_SIZE, height=GRID_H*CELL_SIZE, bg='white')
        self.canvas.imgtk = imgtk
        self.canvas.create_image(0, 0, anchor="nw", image=imgtk)

        self.canvas.pack(side=tk.LEFT)

        panel = tk.Frame(self.master)
        panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        tk.Label(panel, text="ЛОГ КРУТОГО").pack()

        self.log_list = tk.Listbox(panel, height=20, width=30)
        self.log_list.pack()

        tk.Label(panel, text="Сначала всегда нажимаем на поле").pack(pady=(10,0))
        tk.Label(panel, text="ЛКМ+E: разместить кучу").pack()
        tk.Label(panel, text="ЛКМ+Q: первая точка области для выгрузки").pack()
        tk.Label(panel, text="далее ПКМ: вторая точка области для выгрузки").pack()

        self.status_label = tk.Label(panel, text="...", fg="blue", font=("Arial", 10, "bold"))
        self.status_label.pack(pady=10)

        self.master.bind("<KeyPress>", self.on_key_press)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def on_key_press(self, event):
        if self.krest_coord[0] is None: return
        
        # Схема управления "Танк"
        if event.keysym == 'e': 
            self.flag_krest = 1 #self.send_order(self.selected_agent_id, "forward")
            # что-то для создания точки кучи
        elif event.keysym == 'q': 
            self.flag_krest = 2 #self.send_order(self.selected_agent_id, "backward")

    def on_canvas_click(self, event):
        if self.flag_krest == 2:
            # установка второй точки и зоны выгрузки
            pass
        cx = event.x // CELL_SIZE
        cy = event.y // CELL_SIZE

        self.krest_coord = (cx, cy)

    def set_unload_zone(self):
        pass

    def set_breakstone_heap(self):
        pass
    

if __name__ == "__main__":
    root = tk.Tk()

    app = AFC_Chipok(root)

    root.mainloop()