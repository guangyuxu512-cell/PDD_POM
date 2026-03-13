"""
任务参数任务类型动态化静态测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_任务参数任务类型动态化:
    """校验任务参数页的任务类型下拉已改为动态获取。"""

    def test_页面通过可用任务接口动态加载三个下拉(self):
        """导入弹窗和两个筛选下拉都应读取后端可用任务列表。"""
        页面文件 = 读取文件("frontend/src/views/TaskParamsManage.vue")

        for 关键字 in [
            "listAvailableTasks",
            "AvailableTask",
            "const availableTasks = ref<AvailableTask[]>([])",
            "const taskOptions = computed(() => availableTasks.value.map((task) => task.name))",
            "async function loadAvailableTaskOptions()",
            "availableTasks.value = await listAvailableTasks()",
            "void loadAvailableTaskOptions()",
        ]:
            assert 关键字 in 页面文件

        assert 页面文件.count('v-for="task in availableTasks"') >= 3
        assert "const taskOptions = ['发布相似商品', '发布换图商品']" not in 页面文件

    def test_限时限量模板与异常提示已补齐(self):
        """新增任务类型应有导入模板说明，并覆盖加载失败/空列表提示。"""
        页面文件 = 读取文件("frontend/src/views/TaskParamsManage.vue")

        for 关键字 in [
            "加载任务类型失败",
            "暂无可导入的任务类型",
            "请选择任务类型",
            "if (importTaskName.value === '限时限量')",
            "return ['店铺ID', 'batch_id', '折扣']",
            "return '示例店铺名称,batch-20260313,6'",
            "return '示例：店铺ID、batch_id、折扣'",
            "`batch_id` 需要填写同批次成功发布商品对应的批次号。",
        ]:
            assert 关键字 in 页面文件
