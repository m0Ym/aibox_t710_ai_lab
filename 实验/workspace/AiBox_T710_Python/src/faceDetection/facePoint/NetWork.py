import paddle
from paddle.vision.models import resnet18
from paddle.nn import functional as F

class FaceNet(paddle.nn.Layer):
    def __init__(self, num_keypoints, pretrained=False):
        super(FaceNet, self).__init__()
        self.backbone = resnet18(pretrained)
        self.outLayer1 = paddle.nn.Sequential(
            paddle.nn.Linear(1000, 512),
            paddle.nn.ReLU(),
            paddle.nn.Dropout(0.1))
        self.outLayer2 = paddle.nn.Linear(512, num_keypoints*2)
    def forward(self, inputs):
        out = self.backbone(inputs)
        out = self.outLayer1(out)
        out = self.outLayer2(out)
        return out