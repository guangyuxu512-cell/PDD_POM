"""
验证码识别模块单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class 测试_验证码识别器:
    """测试验证码识别器的各种方法"""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_识别滑块_成功(self, mock_client_class):
        """测试识别滑块成功的场景"""
        from browser.验证码识别 import 验证码识别器

        # 模拟 httpx.AsyncClient
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # 模拟创建任务响应（使用 MagicMock，因为 json() 是同步方法）
        创建任务响应 = MagicMock()
        创建任务响应.json.return_value = {
            "errorId": 0,
            "taskId": "test_task_id_123"
        }

        # 第一次轮询返回 processing，第二次返回 ready
        获取结果响应1 = MagicMock()
        获取结果响应1.json.return_value = {
            "status": "processing"
        }

        获取结果响应2 = MagicMock()
        获取结果响应2.json.return_value = {
            "status": "ready",
            "solution": {
                "coordinates": [[150, 200]]
            }
        }

        mock_client.post.side_effect = [创建任务响应, 获取结果响应1, 获取结果响应2]

        识别器 = 验证码识别器("capsolver", "test_api_key")
        距离 = await 识别器.识别滑块(b"background", b"slider")

        assert 距离 == 150

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_识别超时(self, mock_client_class):
        """测试识别超时的场景"""
        from browser.验证码识别 import 验证码识别器

        # 模拟 httpx.AsyncClient
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # 模拟创建任务响应（使用 MagicMock，因为 json() 是同步方法）
        创建任务响应 = MagicMock()
        创建任务响应.json.return_value = {
            "errorId": 0,
            "taskId": "test_task_id_123"
        }

        # 所有轮询都返回 processing
        获取结果响应 = MagicMock()
        获取结果响应.json.return_value = {
            "status": "processing"
        }

        # 第一次是创建任务，后面30次都是轮询
        mock_client.post.side_effect = [创建任务响应] + [获取结果响应] * 30

        识别器 = 验证码识别器("capsolver", "test_api_key")

        with pytest.raises(TimeoutError, match="验证码识别超时"):
            await 识别器.识别滑块(b"background", b"slider")
