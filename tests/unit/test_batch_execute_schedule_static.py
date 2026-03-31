"""
批量执行与定时任务页面静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_批量执行页静态结构:
    def test_批量执行页_状态区改为表格并保留详情入口(self):
        页面文件 = 读取文件("frontend/src/views/BatchExecute.vue")

        for 关键字 in [
            'class="inline-stats"',
            'class="status-table"',
            '店铺名称',
            '当前步骤',
            '进度',
            '状态',
            '耗时',
            '操作',
            'class="progress-bar"',
            'class="progress-fill"',
            '查看详情',
            '收起详情',
            'class="detail-table"',
            'getBatchShopName(shop)',
            'getStatusLabel(shop.status)',
            "if (status === 'waiting') return '等待中'",
            "if (status === 'running') return '执行中'",
            "if (status === 'completed') return '已完成'",
            "if (status === 'failed') return '失败'",
            "if (status === 'stopped') return '已停止'",
        ]:
            assert 关键字 in 页面文件

        assert 'BatchStatusPanel' not in 页面文件

    def test_批量执行页_表格样式保持紧凑和彩色标签(self):
        页面文件 = 读取文件("frontend/src/views/BatchExecute.vue")

        for 关键字 in [
            '.status-table {',
            '.status-table td {',
            'height: 44px;',
            '.status-tag.is-waiting {',
            '.status-tag.is-running {',
            '.status-tag.is-completed {',
            '.status-tag.is-failed {',
            '.status-tag.is-stopped {',
            '.progress-bar {',
            '.progress-fill {',
        ]:
            assert 关键字 in 页面文件


class 测试_定时任务页静态结构:
    def test_定时任务页_列表改为表格且弹窗尺寸统一(self):
        页面文件 = 读取文件("frontend/src/views/ScheduleManage.vue")

        for 关键字 in [
            'class="inline-stats"',
            'class="schedule-table"',
            '开关',
            '任务名称',
            '执行流程',
            '执行周期',
            '上次执行',
            '下次执行',
            '目标店铺数',
            'class="switch"',
            'class="switch-slider"',
            'class="count-badge"',
            'width="min(80vw, 900px)"',
            ':deep(.modal-container)',
            'max-height: 80vh',
        ]:
            assert 关键字 in 页面文件

        for 旧结构 in [
            'class="summary-grid"',
            'class="summary-card"',
            'class="schedule-grid"',
            'class="schedule-card"',
        ]:
            assert 旧结构 not in 页面文件

    def test_定时任务页_表格样式保持紧凑(self):
        页面文件 = 读取文件("frontend/src/views/ScheduleManage.vue")

        for 关键字 in [
            '.schedule-table {',
            '.schedule-table td {',
            'height: 44px;',
            '.cell-actions {',
            '.name-link {',
            '.switch-slider {',
            '.count-badge {',
        ]:
            assert 关键字 in 页面文件
