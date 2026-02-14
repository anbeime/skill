#!/usr/bin/env python3
"""
图片质量校验脚本
功能：检测图片中的肢体异常、画质问题、商品完整性
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple

try:
    import cv2
    import mediapipe as mp
    import numpy as np
except ImportError as e:
    print(f"错误：缺少必要的依赖包")
    print(f"详细信息：{e}")
    print(f"请运行：pip install opencv-python mediapipe numpy")
    sys.exit(1)


class ImageQualityChecker:
    """图片质量校验器"""

    def __init__(self):
        """初始化人体姿态检测"""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            min_detection_confidence=0.8,
            model_complexity=1
        )

    def check_blur_quality(self, img: np.ndarray) -> Tuple[bool, str, float]:
        """
        检测画质（噪点、模糊度）

        Args:
            img: 图片数组

        Returns:
            (是否合格, 原因, 模糊度分数)
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 模糊度检测（拉普拉斯方差，值越大越清晰）
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # 阈值设置：低于100认为模糊
        if laplacian_var < 100:
            return False, "画面模糊，噪点过多", laplacian_var

        return True, "画质合格", laplacian_var

    def check_pose_quality(self, img: np.ndarray) -> Tuple[bool, List[str]]:
        """
        检测人体肢体异常

        Args:
            img: 图片数组

        Returns:
            (是否合格, 问题列表)
        """
        problems = []

        # 转换为RGB格式
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # 检测人体姿态
        results = self.pose.process(img_rgb)

        if not results.pose_landmarks:
            return False, ["未检测到人体，无法校验肢体"]

        # 提取手臂关键点（左手：11,13,15；右手：12,14,16）
        landmarks = results.pose_landmarks.landmark
        left_arm = [landmarks[11], landmarks[13], landmarks[15]]
        right_arm = [landmarks[12], landmarks[14], landmarks[16]]

        # 校验手臂数量（仅允许1-2只正常手臂，无多余肢体）
        arm_count = 0
        visible_arms = []

        for i, arm in enumerate([left_arm, right_arm]):
            if all(0 < lm.x < 1 and 0 < lm.y < 1 for lm in arm):
                arm_count += 1
                visible_arms.append(i)

        if arm_count not in [1, 2]:
            problems.append(f"存在多余手臂或肢体缺失（检测到{arm_count}只手臂）")

        # 校验手部比例（手腕-手肘-肩膀距离合理，无畸形）
        def calculate_distance(lm1, lm2):
            return np.sqrt((lm1.x - lm2.x)**2 + (lm1.y - lm2.y)**2)

        for i, arm in enumerate([left_arm, right_arm]):
            if all(0 < lm.x < 1 and 0 < lm.y < 1 for lm in arm):
                wrist_elbow = calculate_distance(arm[2], arm[1])  # 手腕到手肘
                elbow_shoulder = calculate_distance(arm[1], arm[0])  # 手肘到肩膀

                # 正常比例范围：0.3-0.8
                ratio = wrist_elbow / elbow_shoulder
                if ratio < 0.3 or ratio > 0.8:
                    problems.append(f"手臂{'左' if i == 0 else '右'}比例异常（{ratio:.2f}），存在畸形")

        # 检测手部关键点数量
        left_hand_landmarks = [landmarks[i] for i in range(17, 22)]  # 左手拇指、食指
        right_hand_landmarks = [landmarks[i] for i in range(18, 23)]  # 右手拇指、食指

        # 检测是否有异常的手部位置
        for i, lm in enumerate(landmarks):
            if lm.visibility < 0.5 and i not in [0, 1]:  # 忽略鼻子和眼睛
                # 检查是否有不可见但应该在画面内的关键点
                if 0.1 < lm.x < 0.9 and 0.1 < lm.y < 0.9:
                    problems.append(f"关键点{i}位置异常，存在重影或畸形")

        return len(problems) == 0, problems

    def check_product_visibility(self, img: np.ndarray, product_area: Dict = None) -> Tuple[bool, str]:
        """
        检测商品完整性和清晰度

        Args:
            img: 图片数组
            product_area: 商品区域 {'x': 0.5, 'y': 0.5, 'size': 0.2}（可选）

        Returns:
            (是否合格, 原因)
        """
        h, w = img.shape[:2]

        # 如果未指定商品区域，使用手腕位置（假设佩戴在手腕）
        if product_area is None:
            # 使用mediapipe检测手腕
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.pose.process(img_rgb)

            if not results.pose_landmarks:
                return False, "未检测到人体，无法定位商品"

            landmarks = results.pose_landmarks.landmark
            # 使用左手腕（关键点15）或右手腕（关键点16）
            wrist_lm = landmarks[15]
            x, y = wrist_lm.x, wrist_lm.y
            size = 0.1
        else:
            x, y, size = product_area['x'], product_area['y'], product_area['size']

        # 提取商品区域
        x_center = int(x * w)
        y_center = int(y * h)
        half_size = int(size * min(w, h))

        x1 = max(0, x_center - half_size)
        x2 = min(w, x_center + half_size)
        y1 = max(0, y_center - half_size)
        y2 = min(h, y_center + half_size)

        product_roi = img[y1:y2, x1:x2]

        if product_roi.size == 0:
            return False, "商品区域无效"

        # 检测商品区域是否有足够的细节（边缘检测）
        edges = cv2.Canny(product_roi, 100, 200)
        edge_count = cv2.countNonZero(edges)

        # 如果边缘数量过少，可能商品模糊或缺失
        if edge_count < 100:
            return False, "商品细节模糊或缺失，存在变形"

        # 检测商品区域是否有明显的色彩（避免全黑或全白）
        if np.mean(product_roi) < 30 or np.mean(product_roi) > 225:
            return False, "商品区域色彩异常，可能过曝或欠曝"

        return True, "商品清晰可见"

    def check_image(self, image_path: str) -> Dict:
        """
        综合校验图片质量

        Args:
            image_path: 图片路径

        Returns:
            校验结果字典
        """
        img = cv2.imread(image_path)
        if img is None:
            return {
                'image': image_path,
                'status': 'FAIL',
                'problems': ['图片读取失败']
            }

        result = {
            'image': image_path,
            'status': 'PASS',
            'problems': [],
            'details': {}
        }

        # 1. 画质检测
        is_blur_ok, blur_msg, blur_score = self.check_blur_quality(img)
        result['details']['blur_score'] = float(blur_score)
        if not is_blur_ok:
            result['status'] = 'FAIL'
            result['problems'].append(blur_msg)

        # 2. 肢体检测
        is_pose_ok, pose_problems = self.check_pose_quality(img)
        if not is_pose_ok:
            result['status'] = 'FAIL'
            result['problems'].extend(pose_problems)

        # 3. 商品完整性检测
        is_product_ok, product_msg = self.check_product_visibility(img)
        if not is_product_ok:
            result['status'] = 'FAIL'
            result['problems'].append(product_msg)

        return result

    def batch_check(self, image_dir: str, pattern: str = "*.jpg") -> Dict:
        """
        批量校验图片

        Args:
            image_dir: 图片目录
            pattern: 文件匹配模式

        Returns:
            批量校验结果
        """
        from glob import glob

        image_paths = glob(os.path.join(image_dir, pattern))
        if not image_paths:
            return {
                'status': 'FAIL',
                'message': f'未找到匹配的图片: {pattern}',
                'results': []
            }

        results = []
        qualified_images = []
        failed_images = []

        for img_path in sorted(image_paths):
            result = self.check_image(img_path)
            results.append(result)

            if result['status'] == 'PASS':
                qualified_images.append(img_path)
            else:
                failed_images.append({
                    'image': img_path,
                    'problems': result['problems']
                })

        return {
            'status': 'SUCCESS',
            'total': len(results),
            'qualified': len(qualified_images),
            'failed': len(failed_images),
            'qualified_images': qualified_images,
            'failed_images': failed_images,
            'results': results
        }


def main():
    parser = argparse.ArgumentParser(description='图片质量校验工具')
    parser.add_argument('--images', type=str, required=True, help='图片文件列表（支持通配符）')
    parser.add_argument('--output', type=str, required=True, help='输出质量报告文件路径（JSON格式）')
    parser.add_argument('--verbose', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    # 解析图片路径
    image_pattern = args.images
    if '*' in image_pattern:
        # 使用glob匹配
        from glob import glob
        images = sorted(glob(image_pattern))
    else:
        # 单个文件
        images = [image_pattern]

    if not images:
        print(f"错误：未找到匹配的图片: {args.images}")
        sys.exit(1)

    print(f"开始校验 {len(images)} 张图片...")

    # 创建校验器
    checker = ImageQualityChecker()

    # 批量校验
    if len(images) > 1:
        # 多个文件，批量处理
        image_dir = os.path.dirname(images[0])
        result = checker.batch_check(image_dir, os.path.basename(image_pattern))
    else:
        # 单个文件
        single_result = checker.check_image(images[0])
        result = {
            'status': 'SUCCESS',
            'total': 1,
            'qualified': 1 if single_result['status'] == 'PASS' else 0,
            'failed': 0 if single_result['status'] == 'PASS' else 1,
            'qualified_images': [images[0]] if single_result['status'] == 'PASS' else [],
            'failed_images': [] if single_result['status'] == 'PASS' else [{
                'image': images[0],
                'problems': single_result['problems']
            }],
            'results': [single_result]
        }

    # 输出结果
    print(f"\n校验完成:")
    print(f"  总计: {result['total']}")
    print(f"  合格: {result['qualified']}")
    print(f"  不合格: {result['failed']}")

    if args.verbose or result['failed'] > 0:
        print("\n详细信息:")
        for img in result['qualified_images']:
            print(f"  ✓ {os.path.basename(img)}")
        for img_info in result['failed_images']:
            print(f"  ✗ {os.path.basename(img_info['image'])}")
            for problem in img_info['problems']:
                print(f"      - {problem}")

    # 保存报告
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n质量报告已保存到: {args.output}")

    # 返回退出码（有不合格图片返回1）
    sys.exit(0 if result['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
