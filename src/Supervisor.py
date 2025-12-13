import cv2
import numpy as np
import os
import sys

class Supervisor():
    def __init__(self, path, row, column, camera_id, id_corners = [0, 1, 2, 3], id_agents=[4, 5, 6, 7]):
        self.mtx, self.dist = self._get_calibrate_vals(path, row, column)
        self.id_corners = id_corners
        self.id_agents = id_agents
        # ВАЖНО: Добавим try/except или проверку, чтобы не падать при инициализации
        try:
            self.cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW) # CAP_DSHOW иногда помогает на Windows
            if not self.cap.isOpened():
                raise Exception("Camera not found")
        except:
             self.cap = cv2.VideoCapture(camera_id)

        self.frame = None
        self.crop_field = None

        self.aruco_detections = {} #id: corners (4, 2)

        # Инициализирующий кадр
        self.get_frame()
        frame, corners, ids = self.aruco_markers_detect()
        self.get_field(corners, ids)

    def _get_calibrate_vals(self, path, row, column):
        # ... (код без изменений) ...
        objp = np.zeros((row*column,3), np.float32)
        objp[:,:2] = np.mgrid[0:row,0:column].T.reshape(-1,2)
        objpoints = [] 
        imgpoints = [] 
        
        # Проверка существования пути
        if not os.path.exists(path):
            print(f"Warning: Calibration path {path} not found.")
            # Возвращаем дефолтные значения (единичная матрица), чтобы не падать
            return np.eye(3), np.zeros(5)

        for img_name in os.listdir(path):
            img_path = os.path.join(path, img_name)
            img = cv2.imread(img_path)
            if img is None: continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            retval, corners = cv2.findChessboardCorners(gray, (row, column))
            if retval:
                objpoints.append(objp)
                imgpoints.append(corners)

        if not objpoints:
             return np.eye(3), np.zeros(5)

        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
        return mtx, dist

    def _normalize_camera(self, img, mtx, dist):
        if img is None: return None
        h,  w = img.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))
        dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
        x, y, w, h = roi
        dst = dst[y:y+h, x:x+w]
        return dst

    def get_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.frame = frame
        return ret, frame

    def aruco_markers_detect(self):
        if self.frame is None:
            return None, None, None

        self.frame = self._normalize_camera(self.frame, self.mtx, self.dist)
        
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        aruco_params = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

        corners, ids, rejected = detector.detectMarkers(self.frame)
        
        self.aruco_detections = {} # Очищаем старые детекции, чтобы не хранить "призраков"
        
        if ids is not None:
            ids = ids.flatten()
            for id_val, corner in zip(ids, corners):
                # corner имеет форму (1, 4, 2), берем [0] чтобы получить (4, 2)
                self.aruco_detections[id_val] = corner[0] 

        return self.frame, corners, ids

    def get_field(self, corners, ids):
        # Если угловые маркеры не найдены, возвращаем весь кадр или None
        if self.frame is None: return None
        
        # Логика поиска углов поля
        coords_m = []
        if ids is not None:
            # ids уже flatten в aruco_markers_detect, но проверим
            ids_flat = ids.flatten() if hasattr(ids, 'flatten') else []
            
            # Проходим по всем известным углам
            for corner_id in self.id_corners:
                if corner_id in self.aruco_detections:
                    c = self.aruco_detections[corner_id] # c shape is (4, 2)
                    x_min, x_max = c[:, 0].min(), c[:, 0].max()
                    y_min, y_max = c[:, 1].min(), c[:, 1].max()
                    center_x = int((x_max+x_min)/2)
                    center_y = int((y_max+y_min)/2)
                    coords_m.append((center_x, center_y, corner_id))
        
        self.crop_field = self.frame
        if len(coords_m) == 4:
            coords_m.sort(key=lambda x: x[2]) # Сортируем по ID (0,1,2,3 - TL, TR, BR, BL)
            # Упрощенный кроп: от min(y) до max(y)
            x0, y0 = coords_m[0][:2]
            x_end, y_end = coords_m[-1][:2] # берем последнего (ID 3)
            # Это очень грубый кроп, лучше использовать perspectiveTransform, но оставим как было у вас:
            self.crop_field = self.frame[coords_m[0][1]:coords_m[-1][1], coords_m[0][0]:coords_m[-1][0]]
            
        return self.crop_field

    def get_agents_rotate_angle(self, id):
        if id not in self.aruco_detections:
            return "UNKNOWN"
            
        # ИСПРАВЛЕНИЕ: corner берем напрямую, это массив (4, 2)
        corner = self.aruco_detections[id] 
        
        center_x = int(np.mean(corner[:, 0]))
        center_y = int(np.mean(corner[:, 1]))

        # Перед робота - середина между точками 0 и 1 (верхняя грань маркера)
        front_x = int((corner[0][0] + corner[1][0]) / 2)
        front_y = int((corner[0][1] + corner[1][1]) / 2)

        delta_x = front_x - center_x
        delta_y = front_y - center_y
        angle_rad = np.atan2(delta_y, delta_x)
        angle_deg = np.deg2rad(angle_rad) # Тут у вас ошибка в логике: atan2 возвращает радианы. deg2rad переводит градусы в радианы.
        # Нужно np.rad2deg(angle_rad)
        angle_deg_val = np.degrees(angle_rad)

        if -135 < angle_deg_val < -45:
            desc = "UP"
        elif -45 <= angle_deg_val <= 45:
            desc = "RIGHT"
        elif 45 < angle_deg_val < 135:
            desc = "DOWN"
        else:
            desc = "LEFT"
        return desc

    def get_robot_data(self):
        '''
        Исправленный метод сбора данных
        '''
        robot_data = {}
        for id in self.id_agents:
            if id not in self.aruco_detections.keys():
                continue
            
            # ИСПРАВЛЕНИЕ: Убрали [0], так как aruco_detections[id] уже нужной размерности
            corner = self.aruco_detections[id] 
            
            x_min, x_max = corner[:, 0].min(), corner[:, 0].max()
            y_min, y_max = corner[:, 1].min(), corner[:, 1].max()
            center_x = int((x_max+x_min)/2)
            center_y = int((y_max+y_min)/2)
            
            direction = self.get_agents_rotate_angle(id)
            
            robot_data[id] = {
                'center_coord': (center_x, center_y),
                'direction': direction
            }
        return robot_data