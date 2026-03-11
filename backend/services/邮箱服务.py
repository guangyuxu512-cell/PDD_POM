"""
邮箱服务模块

提供 IMAP 连接测试和验证码读取功能。
"""
import imaplib
import email
import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from backend.services.店铺服务 import 店铺服务实例


class 邮箱服务:
    """邮箱业务服务类"""

    async def 测试连接(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_pass: str
    ) -> Dict[str, Any]:
        """
        测试 IMAP 邮箱连接

        参数:
            smtp_host: IMAP 服务器地址
            smtp_port: IMAP 端口（通常是 993）
            smtp_user: 邮箱账号
            smtp_pass: 邮箱授权码

        返回:
            Dict[str, Any]: 包含 success 和 message 的字典
        """
        try:
            # 连接 IMAP 服务器（SSL）
            if smtp_port == 993:
                邮箱连接 = imaplib.IMAP4_SSL(smtp_host, smtp_port)
            else:
                邮箱连接 = imaplib.IMAP4(smtp_host, smtp_port)

            # 尝试登录
            邮箱连接.login(smtp_user, smtp_pass)

            # 登录成功，关闭连接
            邮箱连接.logout()

            return {
                "success": True,
                "message": "连接成功"
            }

        except imaplib.IMAP4.error as e:
            return {
                "success": False,
                "message": f"IMAP 错误: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接失败: {str(e)}"
            }

    async def 读取验证码(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_pass: str,
        发件人过滤: Optional[str] = None
    ) -> Optional[str]:
        """
        从邮箱读取验证码

        参数:
            smtp_host: IMAP 服务器地址
            smtp_port: IMAP 端口
            smtp_user: 邮箱账号
            smtp_pass: 邮箱授权码
            发件人过滤: 可选的发件人过滤条件

        返回:
            Optional[str]: 验证码字符串，未找到返回 None
        """
        try:
            # 连接 IMAP 服务器
            if smtp_port == 993:
                邮箱连接 = imaplib.IMAP4_SSL(smtp_host, smtp_port)
            else:
                邮箱连接 = imaplib.IMAP4(smtp_host, smtp_port)

            # 登录
            邮箱连接.login(smtp_user, smtp_pass)

            # 选择收件箱
            邮箱连接.select("INBOX")

            # 计算 5 分钟前的时间
            五分钟前 = datetime.now() - timedelta(minutes=5)
            日期字符串 = 五分钟前.strftime("%d-%b-%Y")

            # 搜索最近 5 分钟的邮件
            搜索条件 = f'(SINCE "{日期字符串}")'
            状态, 邮件ID列表 = 邮箱连接.search(None, 搜索条件)

            if 状态 != "OK" or not 邮件ID列表[0]:
                邮箱连接.logout()
                return None

            # 获取邮件 ID 列表（从新到旧）
            邮件IDs = 邮件ID列表[0].split()
            邮件IDs.reverse()

            # 验证码正则表达式（4-6 位数字）
            验证码模式 = re.compile(r'\b(\d{4,6})\b')

            # 遍历邮件查找验证码
            for 邮件ID in 邮件IDs:
                状态, 邮件数据 = 邮箱连接.fetch(邮件ID, "(RFC822)")
                if 状态 != "OK":
                    continue

                # 解析邮件
                原始邮件 = 邮件数据[0][1]
                邮件消息 = email.message_from_bytes(原始邮件)

                # 获取发件人
                发件人 = 邮件消息.get("From", "")

                # 如果指定了发件人过滤，检查是否匹配
                if 发件人过滤:
                    if 发件人过滤.lower() not in 发件人.lower():
                        continue
                else:
                    # 默认过滤抖店相关发件人
                    抖店关键词 = ["jinritemai", "douyin", "bytedance"]
                    if not any(关键词 in 发件人.lower() for 关键词 in 抖店关键词):
                        continue

                # 获取邮件主题
                主题 = 邮件消息.get("Subject", "")
                if 主题:
                    主题 = self._解码邮件头(主题)

                # 在主题中查找验证码
                匹配结果 = 验证码模式.search(主题)
                if 匹配结果:
                    邮箱连接.logout()
                    return 匹配结果.group(1)

                # 在邮件正文中查找验证码
                正文 = self._获取邮件正文(邮件消息)
                if 正文:
                    匹配结果 = 验证码模式.search(正文)
                    if 匹配结果:
                        邮箱连接.logout()
                        return 匹配结果.group(1)

            # 未找到验证码
            邮箱连接.logout()
            return None

        except Exception as e:
            return None

    def _解码邮件头(self, 邮件头: str) -> str:
        """
        解码邮件头

        参数:
            邮件头: 原始邮件头字符串

        返回:
            str: 解码后的字符串
        """
        try:
            解码结果 = email.header.decode_header(邮件头)
            解码文本 = ""
            for 文本, 编码 in 解码结果:
                if isinstance(文本, bytes):
                    解码文本 += 文本.decode(编码 or "utf-8", errors="ignore")
                else:
                    解码文本 += 文本
            return 解码文本
        except Exception:
            return 邮件头

    def _获取邮件正文(self, 邮件消息: email.message.Message) -> str:
        """
        获取邮件正文

        参数:
            邮件消息: 邮件消息对象

        返回:
            str: 邮件正文文本
        """
        正文 = ""
        try:
            if 邮件消息.is_multipart():
                for 部分 in 邮件消息.walk():
                    内容类型 = 部分.get_content_type()
                    if 内容类型 == "text/plain":
                        载荷 = 部分.get_payload(decode=True)
                        if 载荷:
                            字符集 = 部分.get_content_charset() or "utf-8"
                            正文 += 载荷.decode(字符集, errors="ignore")
            else:
                载荷 = 邮件消息.get_payload(decode=True)
                if 载荷:
                    字符集 = 邮件消息.get_content_charset() or "utf-8"
                    正文 = 载荷.decode(字符集, errors="ignore")
        except Exception:
            pass
        return 正文

    async def 测试店铺邮箱连接(self, 店铺ID: str) -> Dict[str, Any]:
        """
        测试店铺的邮箱连接

        参数:
            店铺ID: 店铺 ID

        返回:
            Dict[str, Any]: 包含 success 和 message 的字典
        """
        # 获取店铺完整信息（包含解密后的密码）
        店铺 = await 店铺服务实例.根据ID获取完整信息(店铺ID)
        if not 店铺:
            return {
                "success": False,
                "message": "店铺不存在"
            }

        # 检查邮箱配置是否完整
        if not all([
            店铺.get("smtp_host"),
            店铺.get("smtp_port"),
            店铺.get("smtp_user"),
            店铺.get("smtp_pass")
        ]):
            return {
                "success": False,
                "message": "邮箱配置不完整"
            }

        # 测试连接
        return await self.测试连接(
            smtp_host=店铺["smtp_host"],
            smtp_port=店铺["smtp_port"],
            smtp_user=店铺["smtp_user"],
            smtp_pass=店铺["smtp_pass"]
        )

    async def 读取店铺验证码(
        self,
        店铺ID: str,
        发件人过滤: Optional[str] = None
    ) -> Optional[str]:
        """
        读取店铺邮箱的验证码

        参数:
            店铺ID: 店铺 ID
            发件人过滤: 可选的发件人过滤条件

        返回:
            Optional[str]: 验证码字符串，未找到返回 None
        """
        # 获取店铺完整信息
        店铺 = await 店铺服务实例.根据ID获取完整信息(店铺ID)
        if not 店铺:
            return None

        # 检查邮箱配置
        if not all([
            店铺.get("smtp_host"),
            店铺.get("smtp_port"),
            店铺.get("smtp_user"),
            店铺.get("smtp_pass")
        ]):
            return None

        # 读取验证码
        return await self.读取验证码(
            smtp_host=店铺["smtp_host"],
            smtp_port=店铺["smtp_port"],
            smtp_user=店铺["smtp_user"],
            smtp_pass=店铺["smtp_pass"],
            发件人过滤=发件人过滤
        )


# 创建单例
邮箱服务实例 = 邮箱服务()
