#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@file          :utils.py
@Description   :公共类
@Date          :2023/08/01 20:03:47
@Autor         :Leo
@Version       :v1.0
'''
import os

def project_root():
    """Return the repository root absolute path."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def res_path(*parts):
    """Return an absolute path under the repo root. Example: res_path('res','images','panel','img.png')"""
    return os.path.join(project_root(), *parts)

class Shield:
    """
    抑制python库的多余输出
    """

    def __init__(self):
        self.nullFds = [os.open(os.devnull, os.O_RDWR) for x in range(2)]
        self.saveFds = (os.dup(1), os.dup(2))

    def __enter__(self):
        os.dup2(self.nullFds[0], 1)
        os.dup2(self.nullFds[1], 2)

    def __exit__(self, *_):
        os.dup2(self.saveFds[0], 1)
        os.dup2(self.saveFds[1], 2)
        os.close(self.nullFds[0])
        os.close(self.nullFds[1])

def cutImageFromDet(img, cube, size):
    """
    截取图像(基于目标检测结果)
    img: 被截取图像
    cube: AI检测结果(xMin,yMin,xMax,xMin)
    size: [320,240]截取图像的size(仅参考比例系数)
    使用完该函数再将图像cv2.resize成size的大小即可
    """
    # width
    if size[0] > img.shape[1]:  # 数据保护
        size[0] = img.shape[1]
    # height
    if size[1] > img.shape[0]:
        size[1] = img.shape[0]

    width = cube[2]-cube[0]
    height = cube[3]-cube[1]
    xMin = cube[0] - 60
    xMax = cube[2] + 60
    yMin = cube[1] - 10
    yMax = cube[3] + 10

    if width > height:  # 长 > 高
        pix = int((img.shape[1] - width)/8)  # 图像截取冗余度
        wPix = 0
        i = 0
        for i in range(pix):
            if cube[0] - i <= 0 or cube[2] + i >= img.shape[1]-1:
                break
            wPix = i
        if cube[0] - i <= 0:
            xMin = cube[0] - wPix  # 截取目标框外的图像
            xMax = cube[2] + 2*pix - wPix  # 截取目标框外的图像
        elif cube[2] + i >= img.shape[1]-1:
            xMin = cube[0] - 2*pix + wPix  # 截取目标框外的图像
            xMax = cube[2] + wPix  # 截取目标框外的图像
        else:
            xMin = cube[0] - wPix  # 截取目标框外的图像
            xMax = cube[2] + wPix  # 截取目标框外的图像
        pix = int((xMax-xMin) * size[1] / size[0]) - height
        i = 0
        for i in range(pix):
            if cube[1] - i <= 0 or cube[3] + i >= img.shape[0]-1:
                break
            wPix = i
        if cube[1] - i <= 0:
            yMin = cube[1] - wPix
            yMax = cube[3] + 2*pix - wPix
        elif cube[3] + i >= img.shape[0]-1:
            yMin = cube[1] - 2*pix + wPix
            yMax = cube[3] + wPix
        else:
            yMin = cube[1] - wPix
            yMax = cube[3] + wPix

    if xMin < 0:
        xMin = 0
    if yMin < 0:
        yMin = 0
    if xMax > img.shape[1]-1:
        xMax = img.shape[1]-1
    if yMax > img.shape[0]-1:
        yMax = img.shape[0]-1

    return img[yMin:yMax, xMin:xMax]  # 截取照片
