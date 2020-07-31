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


def hmac_encrypt_sha256_base64(
    key: bytes, encrypt_str: str, encoding: str = "utf-8"
) -> str:
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


def md5_str(encrypt_str: str, encoding: str = "utf-8", is_upper: bool = False) -> str:
    """
    MD5 摘要
    :param encrypt_str: 需要转换 MD5 的字符串
    :param encoding: 编码格式
    :param is_upper: 是否转换为全部大写
    :return: 摘要结果
    """
    m = hashlib.md5(encrypt_str.encode(encoding=encoding))
    md5_result = m.hexdigest()
    if is_upper:
        return md5_result.upper()
    return md5_result
