import tkinter as tk
import random
import cv2
from PIL import Image, ImageTk
import os

from Supervisor import Supervisor
from BigBoss import BigBoss
from config import GRID_W, CELL_SIZE, GRID_H, ID_CAMERA

class AFC_Chipok:
    def __init__(self, master):
        self.master = master
        title = random.choice(['Тут могла быть ваша реклама', 'Окно управления системы роя роботов'])
        self.master.title(title)

        self.flag_krest = 0 
        self.krest_coord = (None, None)
        self.selected_agent_var = tk.IntVar(value=-1)

        self.bb = BigBoss()
        
        # Укажите корректный абсолютный или относительный путь к папке imgs
        calibration_path = os.path.join(os.getcwd(), 'imgs') 
        # Если папка в другом месте, пропишите полный путь вручную, например:
        # calibration_path = r'C:\Users\Braham\Desktop\roi\imgs'
        
        print(f"Loading calibration from: {calibration_path}")
        self.supervisor = Supervisor(calibration_path, 8, 5, ID_CAMERA)

        self.setup_gui()
        
        # ЗАПУСК ГЛАВНОГО ЦИКЛА
        self.main_loop()

    def setup_gui(self):
        # Canvas
        self.canvas_width = GRID_W * CELL_SIZE
        self.canvas_height = GRID_H * CELL_SIZE
        self.canvas = tk.Canvas(self.master, width=self.canvas_width, height=self.canvas_height, bg='black')
        self.canvas.pack(side=tk.LEFT)

        # Panel
        panel = tk.Frame(self.master)
        panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, expand=True)

        tk.Label(panel, text="ЛОГ СИСТЕМЫ", font=("Arial", 10, "bold")).pack(pady=5)
        self.log_list = tk.Listbox(panel, height=15, width=40)
        self.log_list.pack()

        tk.Label(panel, text="Выбор агента:", font=("Arial", 10, "bold")).pack(pady=(10, 5))
        self.agents_frame = tk.Frame(panel)
        self.agents_frame.pack()
        tk.Button(panel, text="Обновить список агентов", command=self.refresh_agents_list).pack(pady=5)

        self.status_label = tk.Label(panel, text="...", fg="blue")
        self.status_label.pack(pady=10)

        self.master.bind("<KeyPress>", self.on_key_press)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def refresh_agents_list(self):
        for widget in self.agents_frame.winfo_children():
            widget.destroy()
        
        connected_ids = self.bb.get_connected_agents()
        if not connected_ids:
            tk.Label(self.agents_frame, text="Нет агентов").pack()
            return

        for agent_id in connected_ids:
            tk.Radiobutton(self.agents_frame, text=f"Agent {agent_id}", 
                           variable=self.selected_agent_var, value=agent_id).pack(anchor=tk.W)

    def main_loop(self):
        """
        Главный цикл программы:
        1. Supervisor получает кадр и данные.
        2. BigBoss получает данные от Supervisor.
        3. Интерфейс обновляется.
        """
        # --- 1. SUPERVISOR: Получение и обработка кадра ---
        ret, _ = self.supervisor.get_frame()
        if ret:
            # Детектим маркеры
            _, corners, ids = self.supervisor.aruco_markers_detect()
            # Получаем кроп поля
            crop_img = self.supervisor.get_field(corners, ids)
            
            # Собираем данные о роботах (координаты, углы)
            robot_data = self.supervisor.get_robot_data()

            # --- 2. BIG BOSS: Обработка данных ---
            # Передаем БигБоссу актуальные данные о поле
            self.bb.set_robot_data(robot_data)
            
            # (Опционально) Здесь можно вызвать метод логики ББ, если он есть
            # self.bb.calculate_next_moves() 

            # --- 3. INTERFACE: Отображение ---
            if crop_img is not None and crop_img.size > 0:
                self.update_canvas_image(crop_img)
            
            # (Опционально) Обновить лог, если робот прислал что-то новое
            # self.update_logs_from_bb()

        # Планируем следующий кадр через 30 мс
        self.master.after(30, self.main_loop)

    def update_canvas_image(self, cv_img):
        # Конвертация для Tkinter
        img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (self.canvas_width, self.canvas_height))
        img_pil = Image.fromarray(img_resized)
        imgtk = ImageTk.PhotoImage(image=img_pil)
        
        self.canvas.create_image(0, 0, anchor="nw", image=imgtk)
        self.canvas.imgtk = imgtk

    def on_canvas_click(self, event):
        agent_id = self.selected_agent_var.get()
        if agent_id == -1:
            self.status_label.config(text="Выберите агента!", fg="red")
            return

        grid_x = event.x // CELL_SIZE
        grid_y = event.y // CELL_SIZE
        
        if 0 <= grid_x < GRID_W and 0 <= grid_y < GRID_H:
            # Отправка команды через BigBoss
            if self.bb.send_target_to_agent(agent_id, grid_x, grid_y):
                self.log_list.insert(tk.END, f"To {agent_id}: Move ({grid_x}, {grid_y})")
                self.log_list.see(tk.END)
            else:
                self.status_label.config(text="Ошибка отправки", fg="red")

    def on_key_press(self, event):
        pass # Ваша логика кнопок

if __name__ == "__main__":
    root = tk.Tk()
    app = AFC_Chipok(root)
    root.mainloop()