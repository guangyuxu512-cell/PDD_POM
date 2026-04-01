"""
Celery 动态配置刷新测试
"""
from __future__ import annotations

from unittest.mock import patch

from tasks import celery_app as celery应用模块


class 测试_Celery配置刷新:
    def test_刷新Celery配置_会更新连接地址并清理缓存(self):
        应用实例 = celery应用模块.celery_app
        原始broker = getattr(应用实例.conf, "broker_url", None)
        原始读地址 = getattr(应用实例.conf, "broker_read_url", None)
        原始写地址 = getattr(应用实例.conf, "broker_write_url", None)
        原始redbeat地址 = getattr(应用实例.conf, "redbeat_redis_url", None)
        原始backend = getattr(应用实例.conf, "result_backend", None)
        原始连接池 = getattr(应用实例, "_pool", None)
        原始生产者池 = getattr(应用实例.amqp, "_producer_pool", None)
        原始backend缓存 = getattr(应用实例, "_backend_cache", None)
        原有本地backend = hasattr(应用实例._local, "backend")
        原始本地backend = getattr(应用实例._local, "backend", None)

        try:
            应用实例.conf.broker_url = "redis://old-host:6379/0"
            应用实例.conf.broker_read_url = "redis://old-host:6379/0"
            应用实例.conf.broker_write_url = "redis://old-host:6379/0"
            应用实例.conf.redbeat_redis_url = "redis://old-host:6379/0"
            应用实例.conf.result_backend = "redis://old-host:6379/1"
            应用实例._pool = object()
            应用实例.amqp._producer_pool = object()
            应用实例._backend_cache = object()
            应用实例._local.backend = object()

            with patch.object(celery应用模块.配置实例, "REDIS_URL", "redis://new-host:6380/0"), \
                    patch.object(celery应用模块.配置实例, "CELERY_RESULT_BACKEND", "redis://new-host:6380/1"):
                celery应用模块.刷新Celery配置()

            assert 应用实例.conf.broker_url == "redis://new-host:6380/0"
            assert 应用实例.conf.broker_read_url == "redis://new-host:6380/0"
            assert 应用实例.conf.broker_write_url == "redis://new-host:6380/0"
            assert 应用实例.conf.redbeat_redis_url == "redis://new-host:6380/0"
            assert 应用实例.conf.result_backend == "redis://new-host:6380/1"
            assert 应用实例._pool is None
            assert 应用实例.amqp._producer_pool is None
            assert 应用实例._backend_cache is None
            assert getattr(应用实例._local, "backend", None) is None
        finally:
            应用实例.conf.broker_url = 原始broker
            应用实例.conf.broker_read_url = 原始读地址
            应用实例.conf.broker_write_url = 原始写地址
            应用实例.conf.redbeat_redis_url = 原始redbeat地址
            应用实例.conf.result_backend = 原始backend
            应用实例._pool = 原始连接池
            应用实例.amqp._producer_pool = 原始生产者池
            应用实例._backend_cache = 原始backend缓存
            if 原有本地backend:
                应用实例._local.backend = 原始本地backend
            elif hasattr(应用实例._local, "backend"):
                delattr(应用实例._local, "backend")
