import subprocess
import os

def main():
    image_dir = "/home/aistudio/work/image/"
    image_files = os.listdir(image_dir)

    for image_file in image_files:
        image_path = os.path.join(image_dir, image_file)
        # 添加行人检测模型所在路径文件夹与人体关键点检测模型所在路径文件夹
        # #### 代码填空开始处 #### #              
        """            
            代码填空提示：   
            1. 代码一共两行；
            2. 行人检测模型变量名称设定为：det_model_dir，填写官方模型文件所在的路径；
            3. 人体关键点检测模型变量名称设定为：keypoint_model_dir，填写官方模型文件所在的路径；
            4. 注意事项：需要根据自己训练后模型导出的路径从而灵活调整索引地址。
        """              
        # #### 代码填空结束处 #### #  
        det_model_dir = "/home/aistudio/work/PaddleDetection/best_output_inference/picodet_s_192_lcnet_pedestrian"
        keypoint_model_dir = "/home/aistudio/work/PaddleDetection/best_output_inference/tinypose_128x96"
        keypoint_threshold = 0.35

        command = [
            "python",
            "/home/aistudio/work/PaddleDetection/deploy/python/det_keypoint_unite_infer.py",
            "--det_model_dir={}".format(det_model_dir),
            "--keypoint_model_dir={}".format(keypoint_model_dir),
            "--image_file={}".format(image_path),
            "--device=GPU",
            "--keypoint_threshold={}".format(keypoint_threshold)
        ]
        subprocess.run(command)

main()