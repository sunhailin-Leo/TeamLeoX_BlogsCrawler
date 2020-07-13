import hmac
import base64
import hashlib


def hmac_encrypt_sha1(key: bytes, encrypt_str: str, encoding: str = "utf-8") -> str:
    """
    HMAC SHA1 加密
    :param key: 密钥
    :param encrypt_str: 加密字符串
    :param encoding: 编码格式
    :return: 加密后的结果
    """
    signature = hmac.new(key=key, digestmod=hashlib.sha1)
    signature.update(bytes(encrypt_str, encoding))
    return signature.hexdigest()


def hmac_encrypt_sha256_base64(key: bytes, encrypt_str: str, encoding: str = "utf-8") -> str:
    """
    HMAC SHA256 Base64 加密
    :param key: 密钥
    :param encrypt_str: 加密字符串
    :param encoding: 编码格式
    :return: 加密后的结果
    """
    signature = hmac.new(key=key, digestmod=hashlib.sha256)
    signature.update(bytes(encrypt_str, encoding))
    return base64.b64encode(signature.digest()).decode(encoding)
