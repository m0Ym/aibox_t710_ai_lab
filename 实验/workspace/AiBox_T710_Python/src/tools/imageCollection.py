import cv2
import os
from lib.utils import res_path

def video(capture):
    index = 0
    codec = cv2.VideoWriter_fourcc("M", "J", "P", "G")
    capture.set(cv2.CAP_PROP_FOURCC, codec)
    capture.set(cv2.CAP_PROP_FPS, 50)

    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
     
    cv2.namedWindow("frame", cv2.WINDOW_NORMAL)

    cv2.resizeWindow("frame", 640, 480)

    while True:
        ret, frame = capture.read()
        #检查是否成功读取视频帧
        if not ret:
            break

        frame=cv2.flip(frame, 1)#手机画面水平翻转
        #执行旋转
        frame =cv2.rotate(frame, cv2.ROTATE_180)
        if cv2.waitKey(1) & 0xFF ==32:
            #创建用于储存照片的文件夹
            saveDir = res_path('res','images','sample')
            if not os.path.exists(saveDir):
                os.makedirs(saveDir)
            path = os.path.join(saveDir, f"{index}.jpg")
            cv2.imwrite(path, frame)
            print("saveimage: {}. jpg". format(index))
            index +=1

        #将已获取的照片数量打印到屏幕上
        cv2.putText(
            frame,
            str(index),
            (10, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            5,
            (0,0, 254),
            3,
            cv2.LINE_AA,
        )

        cv2.putText(
            frame,
            "Please press [space] to collect imgs!",
            (20,450),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0,255,0),
            2,
        )
        cv2.imshow("frame",frame)
        if cv2.waitKey(1) == 27:
            break
    
    capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture = cv2.VideoCapture("/dev/video1")
    video(capture)

