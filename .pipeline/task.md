审查清单：
1. 密码字段是否 AES 加密存储，API 返回是否遮蔽
2. 是否有硬编码密钥或明文存储
3. 所有 API 是否用 成功()/失败() 统一封装
4. 响应格式是否一致：{"code": 0, "msg": "ok", "data": {...}}
5. 异常是否有 try/except 兜底
6. 命名规范：后端中文、前端英文、API路径英文、JSON字段英文
7. 删除操作是否有依赖检查
8. SSE 连接断开是否正常清理
9. 数据库 session 是否正确关闭
10. Windows --pool=threads + nest_asyncio 是否正常
11. 前端：错误处理、loading 防重复、密码框 type="password"
￼
发现问题直接修复。不要新增接口，不要改现有接口行为。
￼
验收：python -m pytest -c tests/pytest.ini -q 全部通过
￼
Commit：任务09：生产环境全面审查