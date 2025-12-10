import cv2
import numpy as np
import os
import sys

class Supervisor():
    def __init__(self, path, row, column, id_corners = [0, 1, 2, 3]):
        self.mtx, self.dist = self._get_calibrate_vals(path, row, column)
        # self._normalize_camera(path, mtx, dist)
        self.id_corners = id_corners
        
    def _normalize_camera(self, img, mtx, dist):
        # img = cv2.imread(os.path.join(path, os.listdir(path)[0]))
        h,  w = img.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))

        dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
        
        x, y, w, h = roi
        dst = dst[y:y+h, x:x+w]
        return dst
        # cv2.imshow('orig', img)
        # cv2.imshow('norm', dst)
        # cv2.waitKey(0)

    def aruco_markers_detect(self, frame):
        '''
        детекция aruco маркеров используя opencv
        '''
        frame = self._normalize_camera(frame, self.mtx, self.dist)
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        aruco_params = cv2.aruco.DetectorParameters()

        detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

        corners, ids, rejected = detector.detectMarkers(frame)
        
        # if ids is not None:
        #     # Рисуем рамку и ID
        #     cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            
        #     # Дополнительно: выводим координаты центра первого найденного маркера
        #     for i in range(len(ids)):
        #         c = corners[i][0]
        #         center_x = int(c[:, 0].mean())
        #         center_y = int(c[:, 1].mean())
                
        #         # Рисуем точку в центре
        #         cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                
        #         # Пишем координаты рядом
        #         cv2.putText(frame, f"ID:{ids[i][0]}", (center_x + 10, center_y), 
        #                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
        #         # print(f"Обнаружен маркер ID: {ids[i][0]} | Центр: ({center_x}, {center_y})")

        # # Показываем результат
        # cv2.imshow("ArUco Detector", frame)

        return frame, corners, ids

    def get_agents_rotate_angle(self):
        pass

    def get_field(self, frame, corners, ids):
        '''
        тут будем получать кроп фрейма
        '''
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
        ids = ids.reshape(-1)

        coords_m = []

        if ids.shape[0]==4:
            for i, corner in enumerate(corners):
                corner = corner[0]
                if ids[i] not in self.id_corners:
                    continue
                # print(corner)
                x_min, x_max = corner[:, 0].min(), corner[:, 0].max()
                y_min, y_max = corner[:, 1].min(), corner[:, 1].max()
                center_x = int((x_max+x_min)/2)#int(corner[:, 0].mean())
                center_y = int((y_max+y_min)/2)#int(corner[:, 1].mean())
                coords_m.append((center_x, center_y, ids[i]))
            
            if len(coords_m)==4:
                coords_m.sort(key=lambda x: x[2])
                # print(coords_m)
                # for i in range(4):
                #     cv2.circle(frame, (coords_m[i][0], coords_m[i][1]), 5, (0, 0, 255), -1)
                # cv2.circle(frame, (coords_m[-1][0], coords_m[-1][1]), 5, (0, 0, 255), -1)
                # cv2.rectangle(frame, (coords_m[0][0], coords_m[0][1]), (coords_m[-1][0], coords_m[-1][1]), (255,0,0), -1)
                frame = frame[coords_m[0][1]:coords_m[-1][1], coords_m[0][0]:coords_m[-1][0]]

        # cv2.imshow("Field", frame)

        return frame

    def get_frame(self):
        pass

    def _get_calibrate_vals(self, path, row, column):
        objp = np.zeros((row*column,3), np.float32)
        objp[:,:2] = np.mgrid[0:row,0:column].T.reshape(-1,2)
        objpoints = [] # 3d point in real world space
        imgpoints = [] # 2d points in image plane.
        
        for img_name in os.listdir(path):
            img_path = os.path.join(path, img_name)

            img = cv2.imread(img_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            retval, corners = cv2.findChessboardCorners(gray, (row, column))

            objpoints.append(objp)
            #в случае не понравится точность, то добавим cornersSubPix
            imgpoints.append(corners)

        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

        return mtx, dist
    
    def get_field_size(self):
        return self.crop.shape[:2]
    
    def get_robot_data(self):
        '''
        Docstring for get_robot_data
        
        направления, координаты, id (id aruco маркера), состояние робота (двигается ли)
        '''
        pass

    def get_breakstone(self):
        pass
    

obj = Supervisor('imgs', 8, 5)


cap = cv2.VideoCapture(0)
    
# Увеличим разрешение для лучшего распознавания (опционально)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    print("Ошибка: Камера не найдена!")
    sys.exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame, corners, ids = obj.aruco_markers_detect(frame)
    
    if len(corners)>0:
        # print(corners)
        # print(ids)
        frame = obj.get_field(frame, corners, ids)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
