#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file          :cameraCalibration.py
@Description   :相机标定程序（张正友标定）
@Date          :2023/07/07 14:26:41
@Autor         :Leo
@Version       :v1.0
@Note          :拍摄棋盘格标定板，存储至 "res/calibration/temp" 目录
"""
import sys
import os
import numpy as np
import cv2
import glob
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
import shutil


def CalibrationCamera(
    calibrationPlateSize, latticeLength, inputFolder, imageType, outputFolder
):
    """
    用相机对张正友标定法的棋盘格进行不同角度的拍摄，得到一组图像；
    对图像中的特征点如标定板角点进行检测，得到标定板角点的像素坐标值，根据已知的棋盘格大小和世界坐标系原点，计算得到标定板角点的物理坐标值；
    根据物理坐标值和像素坐标值的关系，求解相机内参矩阵，计算径向畸变参数。
    :param calibrationPlateSize: 标定板尺寸
    :param latticeLength: 格点长度
    :param inputFolder: 输入文件夹
    :param imageType: 图片类型
    :outputFolder:输出路径
    :return: 内参矩阵，畸变参数，平均误差，标注角点集图片
    """
    width, height = calibrationPlateSize  # 标定板规格
    cornerPointInt = np.zeros((width * height, 3), np.float32)  # 初始化角点
    cornerPointInt[:, :2] = np.mgrid[0:width,
                                     0:height].T.reshape(-1, 2)  # 初始化多维结构
    cornerPointWorld = cornerPointInt * latticeLength  # 初始化世界坐标

    objectPoints = []  # 保存世界坐标
    imagePoints = []  # 保存像素坐标
    imageNames = []  # 保存有效照片名称
    imageCorners = []  # 保存标注角点的图片
    # 角点照片保存路径
    outputCorners = outputFolder + "corners/"
    if not os.path.exists(outputCorners):  # 判断文件夹是否存在
        os.makedirs(outputCorners)  # 如果文件夹不存在，则创建文件夹
    else:
        shutil.rmtree(outputFolder + "corners")
        os.makedirs(outputCorners)  # 如果文件夹不存在，则创建文件夹

    images = glob.glob(inputFolder + os.sep + "**." +
                       imageType)  # 获取指定文件夹下的指定文件
    print("正在读取标定图像, Loading...")
    for fileName in images:
        image = cv2.imread(fileName)  # 获取图像数据
        grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 图像转换为灰度
        mark, cornerPointImage = cv2.findChessboardCorners(
            grayImage, (width, height), None
        )  # 查找棋盘内角的位置，cornerPointImage为像素空间中的角点。
        if mark == True:  # 如果ret为True，则保存。
            objectPoints.append(cornerPointWorld)  # 世界坐标集
            imagePoints.append(cornerPointImage)  # 像素坐标集
            cv2.drawChessboardCorners(
                image, (width, height), cornerPointImage, mark
            )  # 将检测到的角点集画出来。
            imageCorners.append(image)  # 保存绘制角点集的图片

            # 保存角点照片名称
            imageName = fileName.split(os.sep)[-1]  # 获取图片名称
            imageNames.append(imageName)
    try:
        (
            mark,
            internalMatrix,
            distortionCofficients,
            rotationVectors,
            translationVectors,
        ) = cv2.calibrateCamera(
            objectPoints, imagePoints, grayImage.shape[::-1], None, None
        )  # 标定相机，依据世界坐标和像素坐标
    except:
        print("failure:相机标定-棋盘尺寸/格点长度/图片类型有误！")
        sys.exit(0)
    with open("../../res/calibration/assessment.txt", "w") as f:
        head = "相机标定分辨率: 320x240"
        f.write(head)  # 写入头
        f.write("\n")
        head = "每幅图像的标定误差: "
        f.write(head)
        f.write("\n")
        f.close()
    totalError = 0
    for i in range(len(objectPoints)):
        imagePointsPlane, temp = cv2.projectPoints(
            objectPoints[i],
            rotationVectors[i],
            translationVectors[i],
            internalMatrix,
            distortionCofficients,
        )  # 投影3D指向一个图像平面。
        error = cv2.norm(imagePoints[i], imagePointsPlane, cv2.NORM_L2) / len(
            imagePoints
        )  # 计算数组的绝对范数
        with open("../../res/calibration/assessment.txt", "a") as f:
            errorprint = "第" + str(i + 1) + "幅图像的平均误差:" + str(error)
            print(errorprint)
            f.write(errorprint)  # 写入每一幅图像的误差
            f.write("\n")
            f.close()
        cv2.putText(
            imageCorners[i],
            "error:" + str(round(error, 3)),
            (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            1,
        )
        cv2.imwrite(
            outputCorners + os.sep + imageNames[i],
            imageCorners[i],
        )  # 存储角点图片
        cv2.imshow("calibration", imageCorners[i])
        cv2.waitKey(500)

        totalError += error
    averageError = totalError / len(objectPoints)  # 平均误差
    with open("../../res/calibration/assessment.txt", "a") as f:
        averageerror = "总体平均误差:" + str(averageError)
        internalmatrix = "相机内参数矩阵: " + str(internalMatrix)
        cofficients = "相机畸变系数: " + str(distortionCofficients)
        f.write("\n")
        f.write(averageerror)  # 写入平均误差
        f.write("\n")
        f.write(internalmatrix)  # 写入内参矩阵
        f.write("\n")
        f.write(cofficients)  # 写入相机畸变系数
        f.write("\n")
        f.close()

    return (
        internalMatrix,
        distortionCofficients,
        averageError,
    )  # 返回内参矩阵，畸变参数，平均误差，标注角点集图片


def DedistortionDeal(
    inputFolder,
    imageType,
    outputFolder,
    internalMatrix,
    distortionCofficients,
):
    """
    根据内参矩阵和畸变参数对原图进行校准，并且拼接保存
    :param inputFolder: 输入文件夹
    :param imageType: 图片类型
    :param outputFolder: 输出文件夹
    :param internalMatrix: 内参矩阵
    :param distortionCofficients: 畸变参数
    """
    images = glob.glob(inputFolder + os.sep + "**." +
                       imageType)  # 获取指定文件夹下的指定文件
    outputCorrent = outputFolder + "correct/"

    if not os.path.exists(outputCorrent):  # 判断文件夹是否存在
        os.makedirs(outputCorrent)  # 如果文件夹不存在，则创建文件夹
    else:
        shutil.rmtree(outputFolder + "correct")
        os.makedirs(outputCorrent)  # 如果文件夹不存在，则创建文件夹

    for index, fileName in enumerate(images):
        imageName = fileName.split(os.sep)[-1]  # 获取图片名称
        image = cv2.imread(fileName)  # 获取图片数据
        imageCorrect = cv2.undistort(
            image, internalMatrix, distortionCofficients, None, internalMatrix
        )  # 变换图像以补偿镜头畸变

        cv2.putText(image, "old", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1)
        cv2.putText(
            imageCorrect,
            "New",
            (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            1,
        )

        jointImage = np.concatenate([image, imageCorrect], axis=1)  # 水平拼接
        cv2.imwrite(outputCorrent + os.sep + imageName, jointImage)  # 存储图片
        cv2.imshow("calibration", jointImage)
        cv2.waitKey(500)


# 输出内参矩阵参数到Xml文件
def creatMatrixTree(matrix):
    rowsMatrix = 3
    colsMatrix = 3
    cameraMatrix = Element("cameraMatrix", {"type_id": "opencv-matrix"})
    rows = Element("rows")
    rows.text = str(rowsMatrix)
    cols = Element("cols")
    cols.text = str(colsMatrix)
    dt = Element("dt")
    dt.text = "d"
    data = Element("data")
    # data.text = str(matrix)
    text = ""
    for i in range(rowsMatrix):
        for j in range(colsMatrix):
            text += str(matrix[i, j]) + " "

    data.text = text

    cameraMatrix.append(rows)
    cameraMatrix.append(cols)
    cameraMatrix.append(dt)
    cameraMatrix.append(data)
    return cameraMatrix


# 输出内参矩阵参数到Xml文件
def creatCoeffsTree(coeffs):
    rowsMatrix = 1
    colsMatrix = 5
    distCoeffs = Element("distCoeffs", {"type_id": "opencv-matrix"})
    rows = Element("rows")
    rows.text = str(rowsMatrix)
    cols = Element("cols")
    cols.text = str(colsMatrix)
    dt = Element("dt")
    dt.text = "d"
    data = Element("data")

    text = ""
    for i in range(rowsMatrix):
        for j in range(colsMatrix):
            text += str(coeffs[i, j]) + " "

    data.text = text
    distCoeffs.append(rows)
    distCoeffs.append(cols)
    distCoeffs.append(dt)
    distCoeffs.append(data)
    return distCoeffs


def __indent(elem, level=0):
    i = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            __indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


if __name__ == "__main__":
    inputFolder = "../../res/calibration/temp/"  # 输入图像文件夹
    outputFolder = "../../res/calibration/"  # 输出图像文件夹
    calibrationPlateSize = (11, 8)  # opencv输入参数为内角点个数，所以输入参数为11*
    latticeLength = 0.02  # 格点长度20mm
    imageType = "jpg"  # 图像类型
    (internalMatrix, distortionCofficients, averageError,) = CalibrationCamera(
        calibrationPlateSize, latticeLength, inputFolder, imageType, outputFolder
    )  # 相机标定
    if not os.path.exists(outputFolder):  # 判断文件夹是否存在
        os.makedirs(outputFolder)  # 如果文件夹不存在，则创建文件夹
    DedistortionDeal(
        inputFolder,
        imageType,
        outputFolder,
        internalMatrix,
        distortionCofficients,
    )  # 处理畸变图片

    print("successful:(PhotoCollections)相机-标定成功，内参阵矩：", end="")
    print(
        "[[",
        round(internalMatrix[0][0], 3),
        ",",
        round(internalMatrix[0][1], 3),
        ",",
        round(internalMatrix[0][2], 3),
        "] [",
        round(internalMatrix[1][0], 3),
        ",",
        round(internalMatrix[1][1], 3),
        ",",
        round(internalMatrix[1][2], 3),
        "] [",
        round(internalMatrix[2][0], 3),
        ",",
        round(internalMatrix[2][1], 3),
        ",",
        round(internalMatrix[2][2], 3),
        "]]",
        end="",
    )
    print("，畸变参数：", end="")
    print(
        "[[",
        round(distortionCofficients[0][0], 3),
        ",",
        round(distortionCofficients[0][1], 3),
        ",",
        round(distortionCofficients[0][2], 3),
        ",",
        round(distortionCofficients[0][3], 3),
        ",",
        round(distortionCofficients[0][4], 3),
        "]]",
        end="",
    )
    print("，平均误差：", round(averageError, 3), "。")

    # 将相机标定参数写入Xml文件
    root = ET.Element("opencv_storage")
    tree = ET.ElementTree(root)
    root.append(creatMatrixTree(internalMatrix))
    root.append(creatCoeffsTree(distortionCofficients))

    __indent(root)

    # [temp]文件夹下存放临时测试文件，[valid]文件夹下放置有效的标定文件
    tree.write(
        "../../res/calibration/calibration.xml",
        encoding="utf-8",
        xml_declaration=True,
    )
