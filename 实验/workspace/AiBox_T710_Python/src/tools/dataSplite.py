#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
@file        : dataSplite.py
@Description : AI数据集划分
@Date        : 2023/08/02 14:43:47
@Autor       : Leo
@Version     : v1.0
"""

# 不生成数据集文件而是保存数据的位置索引
# 对每个类别的数据进行整合
# 生成: train.txt、valid.txt 文件中每行依次是图像(jpg格式图片)地址、标签文件(xml文件)地址
# 需要根据实际的数据集路径来修改(label_list.txt、img_dir、xml_dir、train_f、valid_f)

import random
import os

# 读取标签列表文件，获取所有label名称
count = len(open("label_list.txt").readlines())
labelNameList = [0]*count
random.seed(2010)  # 设置随机种子，保证划分结果可复现

with open("label_list.txt") as file:
    for i in range(count):
        content = file.readline()
        if len(content) != 0:
            # 去除换行符，添加到标签列表
            labelNameList[i] = content.strip("\n")

# 初始化训练集和验证集地址列表
listTrain = list()  # 训练集数据地址列表
listValid = list()  # 验证集数据地址列表
ratio = 0.8  # 划分比例：训练集占80%，验证集占20%

# 依次对每个类别进行数据处理
for i in range(len(labelNameList)):
    print("current class:", labelNameList[i])
    # 拼接当前类别的图像和标签文件路径

    img_dir = "" + labelNameList[i] + "/Images"
    xml_dir = "" + labelNameList[i] + "/Annotations"
    print(img_dir, xml_dir)
    
    tempLabelList = []  # 暂存当前类别的所有数据（图像+标签路径）
    # 遍历当前类别下所有图像文件
    for img in os.listdir(img_dir):
        # 拼接图像完整路径
        img_path = os.path.join(img_dir, img)
        # 替换图像后缀为xml，拼接标签文件完整路径
        xml_path = os.path.join(xml_dir, img.replace("jpg", "xml"))
        # 将当前数据对（图像+标签）添加到暂存列表
        tempLabelList.append((img_path, xml_path))
    
    # 随机打散当前类别的数据
    random.shuffle(tempLabelList)
    # 按比例划分训练集和验证集，并添加到总列表
    split_idx = int(len(tempLabelList) * ratio)
    listTrain.extend(tempLabelList[:split_idx])
    listValid.extend(tempLabelList[split_idx:])

# 生成并保存训练集文件
train_f = open("./train.txt", "w")
for i, content in enumerate(listTrain):
    img, xml = content
    text = img + " " + xml + "\n"
    train_f.write(text)

# 生成并保存验证集文件
valid_f = open("./valid.txt", "w")
for i, content in enumerate(listValid):
    img, xml = content
    text = img + " " + xml + "\n"
    valid_f.write(text)

# 关闭文件流
train_f.close()
valid_f.close()