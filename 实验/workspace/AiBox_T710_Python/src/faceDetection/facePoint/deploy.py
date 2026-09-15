from NetWork import FaceNet
import paddle
import os
from DataSet import FaceDataset
from PIL import ImageDraw, Image
import numpy as np

def draw_cross(image, label_pred, size, output_path):
    # 创建绘图对象
    draw = ImageDraw.Draw(image)

    label_pred = label_pred.round().astype(int)

    for i in range(len(label_pred)//2):
        # 绘制X形状
        x1 = label_pred[i*2] - size // 2
        y1 = label_pred[i*2+1] - size // 2
        x2 = label_pred[i*2] + size // 2
        y2 =label_pred[i*2+1] + size // 2
        draw.line((x1, y1, x2, y2), fill='red')
        draw.line((x1, y2, x2, y1), fill='red')
    
    # 保存结果图片
    image.save(output_path)


def deploy():
    # 创建模型实例
    model = FaceNet(15)
    # 加载模型参数
    model_dict = paddle.load('/home/aistudio/work/faceKeyPoint/model/model')
    model.load_dict(model_dict)
    model.eval()

    result_output_folder = "/home/aistudio/work/faceKeyPoint/result"

    # 创建输出文件路径
    os.makedirs(result_output_folder, exist_ok=True)

    Test_Dir = '/home/aistudio/data/data60/test.csv'
    test_dataset = FaceDataset(Test_Dir,  mode='test')

    # 取测试集前30张图片
    for i in range(30):

        img, label = test_dataset[i]
        img_tensor = paddle.to_tensor(img, dtype='float32')
        img_tensor = paddle.unsqueeze(img_tensor, axis=0)  # 增加 batch 维度，变为 [1, C, H, W]

        result = model(img_tensor)

        label_pred = result[0].numpy().reshape(-1)
        label_pred = label_pred*96
        result_image_path = os.path.join(result_output_folder, '{:03d}.jpg'.format(i + 1))
        size = 4  # X的大小（边长）

        # 将图像转换为灰度图
        gray_img = Image.fromarray(np.uint8(255-img[0] * 255)).convert('L')     
        rgb_img = gray_img.convert('RGB')
        draw_cross(rgb_img,label_pred,size,result_image_path)


deploy()