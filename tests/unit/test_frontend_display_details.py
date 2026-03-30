"""
前端显示细节回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_前端显示细节:
    """校验流程页和店铺页的显示细节。"""

    def test_流程页_失败策略显示中文_任务下拉不拼描述(self):
        """失败策略应中文显示，任务下拉只显示任务名。"""
        流程页 = 读取文件("frontend/src/views/FlowManage.vue")

        for 原值, 中文标签 in {
            "skip_shop": "跳过该店铺",
            "continue": "继续执行",
            "log_and_skip": "记录并跳过",
            "retry:N": "重试N次",
            "abort": "终止全部",
        }.items():
            assert f"value: '{原值}'" in 流程页
            assert 中文标签 in 流程页

        assert "{{ task.name }} · {{ task.description }}" not in 流程页
        assert "{{ task.name }}" in 流程页
        assert 'class="field-hint"' in 流程页
        assert "getTaskDescription(step.task)" in 流程页
        assert "step.barrier" in 流程页
        assert "step.merge" in 流程页

    def test_店铺页_编辑密码字段不回显(self):
        """编辑店铺时密码输入框应为 password 且提示留空不修改。"""
        店铺页 = 读取文件("frontend/src/views/ShopManage.vue")

        assert 'v-model="formData.password"' in 店铺页
        assert 'type="password"' in 店铺页
        assert "留空则不修改" in 店铺页
        assert "password: ''" in 店铺页
