import os
import sys
from typing import Dict

import numpy as np
import tensorflow as tf

from config import LOG_LEVEL
from utils.logger_utils import LogManager
from captcha import zhihu_ocr_model as ocr_model
from captcha import zhihu_captcha_utils as utils

# 设置 tensorflow 日志等级
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
tf.compat.v1.get_logger().setLevel(tf.compat.v1.logging.ERROR)

logger = LogManager("__name__").get_logger_and_add_handlers(
    formatter_template=5, log_level_int=LOG_LEVEL
)

try:
    type(eval("model"))
except NameError:
    model = ocr_model.LSTMOCR("infer")
    model.build_graph()

# 知乎验证码调用类
config = tf.compat.v1.ConfigProto(allow_soft_placement=True)
checkpoint_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoint")


class ZhihuCaptcha:
    def __init__(self):
        if sys.path[0]:
            os.chdir(sys.path[0])  # 设置脚本所在目录为当前工作目录

        # 恢复权重
        self.__sess = self.__restore_session(checkpoint_dir)

    # 恢复权重
    @staticmethod
    def __restore_session(checkpoint: str = checkpoint_dir):
        sess = tf.compat.v1.Session(config=config)
        sess.run(tf.compat.v1.global_variables_initializer())
        saver = tf.compat.v1.train.Saver(
            tf.compat.v1.global_variables(), max_to_keep=100
        )
        ckpt = tf.train.latest_checkpoint(checkpoint)
        if ckpt:
            # 回复权限，这里连 global_step 也会被加载进来
            saver.restore(sess, ckpt)
            # print('restore from the checkpoint{0}'.format(ckpt))
            logger.debug(f"已加载 checkpoint {ckpt}")
        else:
            logger.warning("警告：未加载任何 checkpoint")
            logger.warning(f"如果这不是你预期中的，请确保以下目录存在可用的 checkpoint:\n{checkpoint_dir}")
        return sess

    def predict(self, img):
        """
        可以在线测试验证码识别功能
        参数：
            img 一个 (60, 150) 的图片
        """
        im = np.array(img.convert("L")).astype(np.float32) / 255.0
        im = np.reshape(im, [60, 150, 1])
        inp = np.array([im])
        seq_len_input = np.array([np.array([64 for _ in inp], dtype=np.int64)])
        # seq_len_input = np.asarray(seq_len_input)
        seq_len_input = np.reshape(seq_len_input, [-1])
        image_input = np.asarray([im])
        # 加载模型
        feed: Dict = {model.inputs: image_input, model.seq_len: seq_len_input}
        dense_decoded_code = self.__sess.run(model.dense_decoded, feed)
        expression = ""
        for i in dense_decoded_code[0]:
            if i == -1:
                expression += ""
            else:
                expression += utils.decode_maps[i]
        return expression
