from DataSet import FaceDataset
from NetWork import FaceNet
import paddle

def train():
    # 添加训练集合文件夹路径
    # #### 代码填空开始处 #### #              
    """            
        代码填空提示：   
        1. 代码一共一行；
        2. 训练集合文件夹变量名称设定为：Train_Dir，路径地址设置为训练集合training.csv所在地址。
        3. 注意事项：需要根据自己训练后模型导出的路径从而灵活调整索引地址。
    """ 
    Train_Dir = "./data/train/"  # 训练集合文件夹路径
                 
    # #### 代码填空结束处 #### #  
    # 训练数据集和验证数据集
    train_dataset = FaceDataset(Train_Dir, mode='train')
    val_dataset = FaceDataset(Train_Dir, mode='val')

    # 模型
    model = paddle.Model(FaceNet(num_keypoints=15))
    # 优化器设置
    optim = paddle.optimizer.Adam(learning_rate=1e-3,parameters=model.parameters())
    # 损失函数定义
    model.prepare(optim, paddle.nn.MSELoss())
    # 训练
    model.fit(train_dataset, val_dataset, epochs=20, batch_size=256)
    # 模型保存
    model.save("./model/model",False) 

train()