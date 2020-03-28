#!/usr/bin/python3
import pyrealsense2 as rs
import numpy as np
import cv2

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QFileDialog

from MainWindow import Ui_MainWindow


class ControlWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(ControlWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Ship Self Drive")
        self.setStyleSheet(open("style.qss", "r").read())

        self.set_action()
        self.set_menu()
        self.init_status()
        self.set_button_signal()
        self.init_camera()
        self.start_capture()


    def set_action(self):
        """
          set mainWindow all action
        """
        self.quitAction = QtWidgets.QAction("&Exit", self)
        self.quitAction.setShortcut("Ctrl+Q")
        self.quitAction.setStatusTip('Close The App')
        self.quitAction.triggered.connect(self.closeApplication)

    def set_menu(self):
        """
          set mainWindow all menu
        """
        self.mainMenu = self.menuBar()
        self.fileMenu = self.mainMenu.addMenu('&File')
        self.fileMenu.addAction(self.quitAction)

    def init_status(self):
        self.save_status = False
        self.saved_frame = 0
        self.distance = 0

    def put_text(self):
        self.label_color_1.setText("保存帧数：{}".format(self.saved_frame))
        # self.label_color_2.setText("保存帧数：{}".format(self.saved_frame))
        # self.label_color_3.setText("保存帧数：{}".format(self.saved_frame))
        # self.label_depth_1.setText("前方有障碍物(m)：{}".format(self.distance))
        # self.label_depth_2.setText("{}".format()

    def set_button_signal(self):
        """
          Set some button on right tool widget
        """
        self.button_save_picture.clicked.connect(self.start_save_picture)
        self.button_add_label.clicked.connect(self.add_label_button)

    def init_camera(self):
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        self.pipeline.start(config)

    def next_frame_slot(self):
        """
          Stream the video to QLabel.
        """
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            pass

        # Convert images to numpy arrays
        self.depth_image = np.asanyarray(depth_frame.get_data())
        self.color_image = np.asanyarray(color_frame.get_data())
        self.color_RGB_image = cv2.cvtColor(self.color_image,
                                               cv2.COLOR_BGR2RGB)

        # The video stream is resized
        # before entering the small label on the left.
        self.depth_resize_image = cv2.resize(self.depth_image,
                                             (128, 96),
                                             interpolation=cv2.INTER_LINEAR)
        #depth label
        self.depth_colormap = cv2.applyColorMap(
            cv2.convertScaleAbs(self.depth_resize_image, alpha=0.03),
            cv2.COLORMAP_JET)

        self.image_down = QImage(self.depth_colormap,
                                 self.depth_colormap.shape[1],
                                 self.depth_colormap.shape[0],
                                 QImage.Format_RGB888)

        pix_down = QPixmap.fromImage(self.image_down)
        self.label_down.setPixmap(pix_down)
        self.label_down.setCursor(Qt.CrossCursor)

        # color label
        self.color_resize_image = cv2.resize(self.color_RGB_image,
                                                  (480, 360),
                                                  interpolation=cv2.INTER_LINEAR)
        self.put_text()
        # self.start_avoidance()
        self.measuring_depth()

        self.image_up = QImage(self.color_resize_image,
                                   self.color_resize_image.shape[1],
                                   self.color_resize_image.shape[0],
                                   QImage.Format_RGB888)

        pix_up = QPixmap.fromImage(self.image_up)
        self.label_up.setPixmap(pix_up)
        self.label_up.setCursor(Qt.CrossCursor)



    def start_capture(self):
        """
          Define QTime and drive QLabel update
        """
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.next_frame_slot)
        self.timer.start(10)

    def start_save_picture(self):
        if self.save_status == False:
            self.saved_frame = 0
            self.images = QFileDialog.getExistingDirectory(self, "选取文件夹",
                                                          "../../../")
            self.button_save_picture.setText('Stop save')

            self.saver = QtCore.QTimer()
            self.saver.timeout.connect(self.save)
            self.saver.start(1000)
            self.save_status = True

        elif self.save_status == True:
            self.stop_save()
            self.button_save_picture.setText('Save')
            self.save_status = False

    def save(self):
        cv2.imwrite('{}/{:>05}.jpg'.format(self.images, self.saved_frame),
                    self.color_image)
        self.saved_frame += 1

    def stop_save(self):
        self.saver.stop()

    def start_avoidance(self):
        self.avoidance = QtCore.QTimer()
        self.avoidance.timeout.connect(self.measuring_depth)
        self.avoidance.start(10)

    # def measuring_depth(self):
    #     x = int(128 / 3)
    #     y = int(96 / 3)
    #     safe_distance = 0.5
    #
    #     self.distance_1 = self.depth_resize_image[x][y] / 1000
    #     self.distance_2 = self.depth_resize_image[x*2][y] / 1000
    #     self.distance_3 = self.depth_resize_image[x][y*2] / 1000
    #     self.distance_4 = self.depth_resize_image[x*2][y*2] / 1000
    #
    #     if self.distance_1 < safe_distance \
    #         or self.distance_2 < safe_distance \
    #         or self.distance_3 < safe_distance \
    #         or self.distance_4 < safe_distance:
    #         self.label_depth_2.setText("前方有障碍物")
    #     else:
    #         self.label_depth_2.setText("前方安全")

    def measuring_depth(self):
        self.distance = []
        self.index = []
        for i in range (127):
            for j in range (95):
                if (self.depth_resize_image[j][i] / 1000) != 0:
                    self.distance.append(self.depth_resize_image[j][i] / 1000)
                    self.index.append([j,i])

        for cot in range (len(self.distance)):
            if self.distance[cot] < 0.5:
                cv2.circle(self.color_resize_image,
                           (int(self.index[cot][1]*3.75), int(self.index[
                                                                  cot][0]
                                                              *3.75)), 2,
                           (125,125, 250), 0)

    def add_label_button(self):
        pass
    # def calculating_normal_vector(self, point):
    #     n = 5
    #     x_1 = point[0] - n
    #     y_1 = point[1] - n
    #
    #     x_2 = point[0] + n
    #     y_2 = point[1] - n
    #
    #     x_3 = point[0]
    #     y_3 = point[1] + n
    #
    #
    #     click_z_1 = self.camera_depth_img_center[y_1][
    #                     x_1] * self.cam_depth_scale_center
    #     click_x_1 = np.multiply(x_1 - self.camera.intrinsics[0][2],
    #                             click_z_1 / self.camera.intrinsics[0][0])
    #     click_y_1 = np.multiply(y_1 - self.camera.intrinsics[1][2],
    #                             click_z_1 / self.camera.intrinsics[1][1])
    #
    #     click_z_2 = self.camera_depth_img_center[y_2][
    #                     x_2] * self.cam_depth_scale_center
    #     click_x_2 = np.multiply(x_2 - self.camera.intrinsics[0][2],
    #                             click_z_2 / self.camera.intrinsics[0][0])
    #     click_y_2 = np.multiply(y_2 - self.camera.intrinsics[1][2],
    #                             click_z_2 / self.camera.intrinsics[1][1])
    #
    #     click_z_3 = self.camera_depth_img_center[y_3][
    #                     x_3] * self.cam_depth_scale_center
    #     click_x_3 = np.multiply(x_3 - self.camera.intrinsics[0][2],
    #                             click_z_3 / self.camera.intrinsics[0][0])
    #     click_y_3 = np.multiply(y_3 - self.camera.intrinsics[1][2],
    #                             click_z_3 / self.camera.intrinsics[1][1])
    #
    #     p1 = np.array([click_x_1, click_y_1, click_z_1])
    #     p2 = np.array([click_x_2, click_y_2, click_z_2])
    #     p3 = np.array([click_x_3, click_y_3, click_z_3])
    #
    #     v1 = p3 - p1
    #     v2 = p2 - p1
    #
    #     normal_vector = np.cross(v1, v2)
    #     normal_vector[0] = -normal_vector[0]
    #     normal_vector[1] = -normal_vector[1]
    #     normal_vector[2] = -normal_vector[2]
    #     # print("normal_vector: ", normal_vector)
    #
    #     return normal_vector
    #
    # def calculate_rotation_vector(self, normal_vector, camera2robot):
    #
    #     normal_vector.shape = (3, 1)
    #     target_vector = np.dot(camera2robot[0:3, 0:3], normal_vector)
    #     target_vector.shape = (1, 3)
    #     tcp_vector = [-0.003, -0.009, 0.266]
    #     angl = utils.angle_between_two_vectors(target_vector[0], tcp_vector,
    #                                            'True')
    #     axis = np.cross(target_vector[0], tcp_vector)
    #     Rrotm = utils.angle2rotm(angl, axis)
    #     R = Rrotm[:3, :3]
    #     print("isRotm: ", utils.isRotm(R))
    #
    #     orig = cv2.Rodrigues(R)
    #
    #     return orig[0][0][0], orig[0][1][0], orig[0][2][0]
    #
    # def calculate_image_3d_coordinates(self):
    #     """
    #       Use the returned 2d coordinate array to get the depth coordinates
    #       through the camera class and save it to the path point
    #     """
    #     click_points = []
    #     pose = self.label_center.num_pos
    #     if len(pose) >= 1:
    #         for num in pose:
    #             for point in num:
    #                 x = point[0]
    #                 y = point[1]
    #                 click_z = self.camera_depth_img_center[y][x] * self.cam_depth_scale_center
    #                 click_x = np.multiply(x - self.camera.intrinsics[0][2], click_z / self.camera.intrinsics[0][0])
    #                 click_y = np.multiply(y - self.camera.intrinsics[1][2], click_z / self.camera.intrinsics[1][1])
    #                 normal_vector = self.calculating_normal_vector(point)
    #                 if click_z == 0:
    #                     print("No depth value under coordinates (", x,
    #                           y, ")", "(", click_x, click_y, ")")
    #                     # return
    #                 else:
    #                     print("click point(", click_x, click_y, ")")
    #                     click_point = np.asarray([click_x, click_y, click_z, normal_vector])
    #                     click_point.shape = (4, 1)
    #                     click_points.append(click_point)
    #
    #             self.image_meridian_point.append(click_points)
    #     else:
    #         print("not returned 2d coordinate array")
    #
    # def tool_orientation(self, point):
    #     # 20cm
    #     if point[1] < 0.05 and point[1] > -0.15:
    #         tool_orientation = np.asarray([2.20, 2.20, 0])
    #         return tool_orientation
    #     # Right offset 2cm
    #     elif point[1] > 0.05 and point[1] < 0.07:
    #         tool_orientation = np.asarray([2.20, 2.20, 0])
    #         return tool_orientation
    #
    #     elif point[1] > 0.07 and point[1] < 0.09:
    #         tool_orientation = np.asarray([2.20, 2.20, 0])
    #         return tool_orientation
    #
    #     elif point[1] > 0.09 and point[1] < 0.11:
    #         tool_orientation = np.asarray([2.20, 2.20, 0])
    #         return tool_orientation
    #
    #     elif point[1] > 0.11 and point[1] < 0.13:
    #         tool_orientation = np.asarray([2.20, 2.20, 0])
    #         return tool_orientation
    #
    #     elif point[1] > 0.11 and point[1] < 0.13:
    #         tool_orientation = np.asarray([2.20, 2.20, 0])
    #         return tool_orientation
    #
    #     elif point[1] > 0.13:
    #         tool_orientation = np.asarray([2.20, 2.20, 0])
    #         return tool_orientation
    #
    #     # Left
    #     elif point[1] < -0.15 and point[1] > -0.18:
    #         tool_orientation = np.asarray([2.20, 2.20, 0])
    #         return tool_orientation
    #
    #     elif point[1] < -0.18 and point[1] > -0.21:
    #         tool_orientation = np.asarray([2.20, 2.20, 0])
    #         return tool_orientation
    #
    #     elif point[1] < -0.21 and point[1] > -0.24:
    #         tool_orientation = np.asarray([2.20, 2.20, 0])
    #         return tool_orientation
    #
    #     elif point[1] < -0.25:
    #         tool_orientation = np.asarray([2.20, 2.20, 0])
    #         return tool_orientation
    #
    # def calculate_target_position(self):
    #     """
    #       Image coordinate and transformation matrix point
    #       multiplication calculation robot arm coordinates
    #     """
    #     self.calculate_image_3d_coordinates()
    #     camera2robot = self.cam_pose_center
    #     target_positions = []
    #     for num in self.image_meridian_point:
    #         for point in num:
    #             # calculate_rotation_vector
    #             tool_orientation = np.asarray(self.calculate_rotation_vector(
    #                 point[3:4, 0][0], camera2robot))
    #
    #             # fixed one orientation
    #             # tool_orientation = np.asarray([2.20, 2.20, 0])
    #
    #             # fixed orientation
    #             # tool_orientation = self.tool_orientation(point)
    #
    #             target_position = (np.dot(camera2robot[0:3, 0:3], point[0:3])
    #                                + camera2robot[0:3, 3:])
    #             target_position = target_position[0:3, 0]
    #             target_positions.append(np.concatenate((target_position, tool_orientation)))
    #
    #         self.target_meridian_point.append(target_positions)

    def closeApplication(self):
        choice = QtWidgets.QMessageBox.question(self, 'Message', 'Do you really want to exit?', QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            print("Closing....")
            sys.exit()
        else:
            pass


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = ControlWindow()
    window.show()
    sys.exit(app.exec_())