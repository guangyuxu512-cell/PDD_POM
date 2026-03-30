"""
任务参数任务类型动态化静态测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_任务参数任务类型动态化:
    def test_schema类型与动态模板逻辑已接入(self):
        类型文件 = 读取文件("frontend/src/api/types.ts")
        store文件 = 读取文件("frontend/src/views/task-params/useTaskParamsStore.ts")

        for 关键字 in [
            "export interface TaskFieldSchema",
            "export interface TaskInputSchema",
            "input_schema?: TaskInputSchema | null",
            "output_schema?: TaskInputSchema | null",
        ]:
            assert 关键字 in 类型文件

        for 关键字 in [
            "getSchemaFieldMap",
            "collectFlowTemplateFields",
            "currentTask = computed",
            "currentTemplateColumns = computed",
            "currentTemplateSampleRow = computed",
            "currentRequiredFields = computed",
            "input_schema",
            "properties",
            "model_fields",
        ]:
            assert 关键字 in store文件

    def test_已移除按任务名硬编码的模板分支(self):
        store文件 = 读取文件("frontend/src/views/task-params/useTaskParamsStore.ts")
        弹窗文件 = 读取文件("frontend/src/views/task-params/ImportCsvModal.vue")

        for 关键字 in ["发布换图商品", "限时限量", "supportsPublishCount", "batch-20260313"]:
            assert 关键字 not in store文件

        assert "CSV 模板说明" in 弹窗文件
        assert "currentTemplateColumns.join('、')" in 弹窗文件
        assert "currentRequiredFields.join('、')" in 弹窗文件
        assert "流程模式下，除“店铺ID”外的列都会进入流程共享参数。" in 弹窗文件
