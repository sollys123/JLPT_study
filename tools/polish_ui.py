#!/usr/bin/env python3
"""Apply the public-facing JLPT Study naming system to a built site artifact."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def replace_all(path: Path, replacements: list[tuple[str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
        elif new not in text:
            raise RuntimeError(f"UI copy marker not found in {path}: {old!r}")
    path.write_text(text, encoding="utf-8")


def polish_index(path: Path) -> None:
    replacements = [
        ('<title>JLPT 紫藤学习系统</title>', '<title>JLPT Study</title>'),
        ('<div class="brand"><div class="brand-mark">藤</div><div><h1>JLPT 紫藤计划</h1><small>N4 → N2 学习系统</small></div></div>', '<div class="brand"><div class="brand-mark">J</div><div><h1>JLPT Study</h1><small>N4 → N2 备考计划</small></div></div>'),
        ('<button data-view="today" class="active"><span class="ico">⌂</span>今日学习</button>', '<button data-view="today" class="active"><span class="ico">⌂</span>今日计划</button>'),
        ('<button data-view="calendar"><span class="ico">▦</span>完整日历</button>', '<button data-view="calendar"><span class="ico">▦</span>学习日历</button>'),
        ('<button data-view="roadmap"><span class="ico">◇</span>课程地图</button>', '<button data-view="roadmap"><span class="ico">◇</span>学习路线</button>'),
        ('<button data-view="vocab"><span class="ico">字</span>词典与SRS</button>', '<button data-view="vocab"><span class="ico">字</span>词卡复习</button>'),
        ('<button data-view="journal"><span class="ico">✎</span>学习日志</button>', '<button data-view="journal"><span class="ico">✎</span>学习记录</button>'),
        ('<button data-view="settings"><span class="ico">⚙</span>设置与备份</button>', '<button data-view="settings"><span class="ico">⚙</span>系统设置</button>'),
        ('<div class="page-title" id="pageTitle">今日学习</div><div class="page-sub" id="pageSub">把计划变成每天能完成的动作</div>', '<div class="page-title" id="pageTitle">今日计划</div><div class="page-sub" id="pageSub">查看并完成今天的学习安排</div>'),
        ('<h2>智能欠课队列</h2><p>核心任务顺延，重复复习自动合并，可选任务自动降级。</p>', '<h2>待补任务</h2><p>未完成的核心任务会顺延，重复复习自动合并，可选任务不累积。</p>'),
        ('<h2>专注计时</h2><p>选择任务后开始，也可直接自由计时。</p>', '<h2>学习计时</h2><p>选择任务后开始，也可直接自由计时。</p>'),
        ('<h2>当日记录</h2><p>保存后会进入统计与日志。</p>', '<h2>今日记录</h2><p>保存后会计入统计与学习记录。</p>'),
        ('<button class="mood" data-mood="濒死">🫠 濒死</button>', '<button class="mood" data-mood="很吃力">🫠 很吃力</button>'),
        ('<label>学习备注 / 错题线索</label><textarea id="dayNote" placeholder="今天最卡在哪里？明天要避开什么？"></textarea>', '<label>学习备注与错题线索</label><textarea id="dayNote" placeholder="今天最难的部分是什么？明天需要继续什么？"></textarea>'),
        ('<h2>本周脉搏</h2><p>不追求完美连续，只看有效推进。</p>', '<h2>本周进度</h2><p>查看有效学习天数与完成情况。</p>'),
        ('<h2>阶段路线</h2><p>阶段进度由每日任务完成情况自动计算。</p>', '<h2>阶段计划</h2><p>阶段进度由每日任务完成情况自动计算。</p>'),
        ('<h2>教材购买节奏</h2><p>少而完整，按阶段解锁。</p>', '<h2>教材安排</h2><p>按阶段准备，避免重复购买。</p>'),
        ('<h2>《新标日》48课地图</h2><p>点击任一课查看语法、视频策略与练习要求。</p>', '<h2>《新标日》48课进度</h2><p>查看各课语法、视频与练习要求。</p>'),
        ('<div><div class="eyebrow">FSRS-6 · JMdict English · local-first</div><h2>紫藤记忆舱</h2><p>课程、词典和复习合在一处。长期间隔由 FSRS-6 计算；学习步骤、同源卡错开、遗忘重学与完整日志按 Anki 的使用逻辑组织。</p></div>', '<div><div class="eyebrow">FSRS-6 · JMdict English · 本地存储</div><h2>词卡复习</h2><p>查词、制卡与复习集中管理。长期复习间隔由 FSRS-6 计算，学习步骤与同源卡处理遵循 Anki 的使用逻辑。</p></div>'),
        ('<button class="btn" id="srsQuickAdd">＋手动制卡</button>', '<button class="btn" id="srsQuickAdd">＋新建词卡</button>'),
        ('<button class="btn" id="srsFullBackup">完整备份</button>', '<button class="btn" id="srsFullBackup">导出备份</button>'),
        ('<button class="srs-tab" data-srs-tab="dictionary">词典制卡</button>', '<button class="srs-tab" data-srs-tab="dictionary">查词制卡</button>'),
        ('<button class="srs-tab" data-srs-tab="browser">卡片浏览</button>', '<button class="srs-tab" data-srs-tab="browser">卡片管理</button>'),
        ('<h3>当前记忆状态</h3>', '<h3>当前卡片</h3>'),
        ('<h3>今日原则</h3>', '<h3>评分说明</h3>'),
        ('<h3>本地 JMdict 词典</h3>', '<h3>JMdict 离线词典</h3>'),
        ('<div class="note-editor" id="noteEditor"><h3>词条与卡片</h3>', '<div class="note-editor" id="noteEditor"><h3>词条编辑</h3>'),
        ('<label>English meaning</label>', '<label>英文释义</label>'),
        ('<label>English example / 自己的解释</label>', '<label>英文例句 / 补充说明</label>'),
        ('<h2>词条与卡片浏览器</h2><p>搜索、批量暂停、恢复、加标签、删除，或导出为 Anki 可导入的 TSV。</p>', '<h2>卡片管理</h2><p>搜索、批量调整状态、编辑标签，或导出为 Anki 可导入的 TSV。</p>'),
        ('<h3>未来14天到期预测</h3>', '<h3>未来14天复习量</h3>'),
        ('<h3>记忆质量</h3>', '<h3>记忆表现</h3>'),
        ('<h3>最需要处理的卡片</h3>', '<h3>需处理卡片</h3>'),
        ('<h2>FSRS-6</h2><p>默认参数来自 FSRS-6。通常只调整目标记忆率。</p>', '<h2>复习算法</h2><p>当前使用 FSRS-6；通常只需调整目标记忆率。</p>'),
        ('<h2>数据与迁移</h2><p>词典可重装；词条、卡片和复习记录必须备份。</p>', '<h2>数据管理</h2><p>词典可以重新安装；词条、卡片和复习记录需要定期备份。</p>'),
        ('>导出完整 JSON</button>', '>导出完整备份</button>'),
        ('>导入完整 JSON</button>', '>导入完整备份</button>'),
        ('<h2>诊断与危险操作</h2><p>先运行自检，再考虑清空。</p>', '<h2>诊断与重置</h2><p>先运行自检，再执行清空。</p>'),
        ('>运行 FSRS / 数据库诊断</button>', '>运行数据诊断</button>'),
        ('<h2>录入模拟成绩</h2><p>保存各科分数和错误画像。</p>', '<h2>新增模拟成绩</h2><p>保存各科分数与薄弱项说明。</p>'),
        ('<h2>最近8周学习时长</h2>', '<h2>近8周学习时长</h2>'),
        ('<h2>半年热力图</h2>', '<h2>近半年学习热力图</h2>'),
        ('<h2>写一条学习日志</h2><p>可补写任意日期。</p>', '<h2>新增学习记录</h2><p>可以补写任意日期。</p>'),
        ('placeholder="今天学到了什么？出现了什么小胜利？"', 'placeholder="今天完成了什么？有哪些问题需要继续处理？"'),
        ('>保存日志</button>', '>保存记录</button>'),
        ('<h2>日志时间线</h2><p>当日记录中的备注也会显示。</p>', '<h2>记录时间线</h2><p>今日记录中的备注也会显示。</p>'),
        ('<h2>学习负荷</h2><p>欠课只会填入剩余容量，不会无限堆到明天。</p>', '<h2>学习负荷</h2><p>待补任务只会填入剩余时间，不会无限累积。</p>'),
        ('<label>欠课策略</label>', '<label>任务顺延方式</label>'),
        ('<option value="gentle">温柔：每天最多1项核心欠课</option>', '<option value="gentle">轻量：每天最多安排1项待补任务</option>'),
        ('<option value="balanced">均衡：按容量智能填充</option>', '<option value="balanced">均衡：按剩余时间自动安排</option>'),
        ('<h2>计划内特殊区间</h2><p>这些日期不会产生欠课。</p>', '<h2>特殊日期</h2><p>这些日期不会生成待补任务。</p>'),
        ('<h2>GPT Live脚本库</h2><p>一键复制，再进入语音模式。</p>', '<h2>GPT Live 提示词</h2><p>一键复制，再进入语音模式。</p>'),
        ('<h2>诊断与重置</h2><p>先导出备份，再碰红色按钮。</p>', '<h2>诊断与重置</h2><p>先导出备份，再执行清空。</p>'),
        ('<nav class="mobile-nav" id="mobileNav"><button data-view="today" class="active"><b>⌂</b>今日</button><button data-view="calendar"><b>▦</b>日历</button><button data-view="roadmap"><b>◇</b>课程</button><button data-view="vocab"><b>字</b>SRS</button><button data-view="stats"><b>▥</b>统计</button></nav>', '<nav class="mobile-nav" id="mobileNav"><button data-view="today" class="active"><b>⌂</b>今日</button><button data-view="calendar"><b>▦</b>日历</button><button data-view="roadmap"><b>◇</b>路线</button><button data-view="vocab"><b>字</b>词卡</button><button data-view="stats"><b>▥</b>统计</button></nav>'),
        ("const taskConfig={main:{label:'主线',kind:'core',weight:.08},vocab:{label:'词汇',kind:'review',weight:.14},grammar:{label:'语法',kind:'core',weight:.15},media:{label:'视频',kind:'optional',weight:.13},exercise:{label:'练习',kind:'core',weight:.22},listening:{label:'听力',kind:'review',weight:.12},gpt:{label:'GPT Live',kind:'optional',weight:.08},srs:{label:'SRS',kind:'review',weight:.08}};", "const taskConfig={main:{label:'主线',kind:'core',weight:.08},vocab:{label:'词汇',kind:'review',weight:.14},grammar:{label:'语法',kind:'core',weight:.15},media:{label:'视频',kind:'optional',weight:.13},exercise:{label:'练习',kind:'core',weight:.22},listening:{label:'听力',kind:'review',weight:.12},gpt:{label:'GPT Live',kind:'optional',weight:.08},srs:{label:'词卡复习',kind:'review',weight:.08}};"),
        ("'今天处于减负模式，历史欠课暂停调入。':'这一天属于计划内豁免。欠课调度已暂停，不会把旅行变成补习班。'", "'今天处于减负模式，暂不安排历史待补任务。':'这一天属于计划内休息，任务顺延已暂停。'"),
        ("今日容量不足，另有 ${backlog.queued} 项留在队列，系统会继续向后分摊。", "今日时间不足，另有 ${backlog.queued} 项保留在待补列表，系统会继续向后安排。"),
        ("'<div class=\"empty\">没有需要顺延的欠课。今天的桌面很干净。</div>'", "'<div class=\"empty\">没有待补任务。</div>'"),
        ("<span class=\"pill warn\">来自欠课${t.age?` · ${t.age}天`:''}</span>", "<span class=\"pill warn\">顺延任务${t.age?` · ${t.age}天`:''}</span>"),
        ("'旅行豁免'", "'旅行休息'"),
        ("'旅行模式：所有任务自愿，不生成欠课。'", "'旅行模式：所有任务均为可选，不生成待补任务。'"),
        ("'减负模式：只保留核心任务，今天不接收历史欠课。'", "'减负模式：只保留核心任务，今天不安排历史待补任务。'"),
        ("剩余约 ${remaining} 分钟；系统再安排 ${backlog.totalMinutes} 分钟欠课。", "剩余约 ${remaining} 分钟；系统再安排 ${backlog.totalMinutes} 分钟待补任务。"),
        ("document.title=timer.running?`${$('#timerDisplay').textContent} · JLPT 紫藤学习系统`:'JLPT 紫藤学习系统'", "document.title=timer.running?`${$('#timerDisplay').textContent} · JLPT Study`:'JLPT Study'"),
        ("const titles={today:['今日学习','把计划变成每天能完成的动作'],calendar:['完整日历','旅行、欠课与完成状态一眼可见'],roadmap:['课程地图','从五十音到N2的整条路线'],vocab:['词典与SRS','JMdict查词、FSRS复习与卡片管理'],mocks:['模拟考试','把分数变成可追踪的弱点'],stats:['学习统计','只看真实推进，不制造打卡焦虑'],journal:['学习日志','把卡点和小胜利留住'],settings:['设置与备份','负荷、特殊日期和数据安全']};", "const titles={today:['今日计划','查看并完成今天的学习安排'],calendar:['学习日历','按日期查看计划、旅行与完成状态'],roadmap:['学习路线','查看阶段目标、教材与课程进度'],vocab:['词卡复习','查词、制卡与间隔复习'],mocks:['模拟考试','记录成绩并分析薄弱环节'],stats:['学习统计','查看时长、完成率与长期进度'],journal:['学习记录','保存每日备注与错题线索'],settings:['系统设置','调整负荷、特殊日期与数据备份']};"),
        ("escapeHtml(t.phase||'欠课')", "escapeHtml(t.phase||'待补任务')"),
        ("download(`JLPT紫藤备份_${todayStr()}.json`,JSON.stringify({app:'JLPT紫藤学习系统'", "download(`JLPTStudy_学习备份_${todayStr()}.json`,JSON.stringify({app:'JLPT Study'"),
        ("<button class=\"btn small\" data-copy-prompt=\"${i}\">复制脚本</button>", "<button class=\"btn small\" data-copy-prompt=\"${i}\">复制提示词</button>"),
        ("showModal('欢迎来到紫藤学习系统'", "showModal('欢迎使用 JLPT Study'"),
        ("<div class=\"notice\"><b>法国旅行：</b>", "<div class=\"notice\"><b>旅行安排：</b>"),
        ("<div class=\"notice\"><b>欠课机制：</b>核心任务顺延，复习任务合并，可选任务不会堆成债务山。", "<div class=\"notice\"><b>任务顺延：</b>核心任务顺延，复习任务合并，可选任务不会无限累积。"),
        (">开始学习</button>", ">开始使用</button>"),
        ("在今日页查看", "在今日计划中查看"),
        ("title:`合并${taskConfig[key]?.label||'复习'}欠课（${arr.length}项）`", "title:`${taskConfig[key]?.label||'复习'}待补（${arr.length}项）`"),
        ("周测＋缓冲，不把欠债滚到下周", "周测＋缓冲，不把遗漏带到下周"),
    ]
    replace_all(path, replacements)

    phase_helper = """const phaseOrder=[...new Set(PLAN_DATA.schedule.map(x=>x.phase))];
const phaseLabels={'N4-准备':'N4 · 准备','N4-假名入门':'N4 · 假名','N4-新标日48课':'N4 · 基础课程','N4-旅行前整理':'N4 · 旅行前复习','法国旅行':'法国旅行','N4-旅行后恢复':'N4 · 恢复','N4-冲刺':'N4 · 冲刺','N4-正式考试':'N4 · 考试','N3-过渡':'N3 · 过渡','N3-学习':'N3 · 系统学习','N3-模拟':'N3 · 模拟','N2-学习':'N2 · 系统学习','N2-冲刺':'N2 · 冲刺','N2-暂定考试':'N2 · 考试'};
const phaseLabel=phase=>phaseLabels[phase]||String(phase||'自由安排').replace(/-/g,' · ');
const weekLabel=week=>{const value=String(week||'').trim();if(!value)return '自由安排';if(value==='TRIP-FR')return '旅行期间';const match=value.match(/^(N[1-5])-W(\\d+)$/);if(!match)return value;const n=Number(match[2]);return n===0?`${match[1]} 准备周`:`${match[1]} 第${n}周`;};"""
    replace_all(path, [
        ("const phaseOrder=[...new Set(PLAN_DATA.schedule.map(x=>x.phase))];", phase_helper),
        ("$('#sidePhase').textContent=`${p.phase} · ${p.week||'自由日'}`", "$('#sidePhase').textContent=`${phaseLabel(p.phase)} · ${weekLabel(p.week)}`"),
        ('<div><div class="eyebrow">${escapeHtml(p.phase)} · ${escapeHtml(p.week||\'\')}</div>', '<div><div class="eyebrow">${escapeHtml(phaseLabel(p.phase))} · ${escapeHtml(weekLabel(p.week))}</div>'),
        ('<div class="notice">${escapeHtml(plannedEntry(d).phase)} · ${escapeHtml(plannedEntry(d).goal||\'\')}</div>', '<div class="notice">${escapeHtml(phaseLabel(plannedEntry(d).phase))} · ${escapeHtml(plannedEntry(d).goal||\'\')}</div>'),
        ('<div class="stage-title">${escapeHtml(g.phase)}</div>', '<div class="stage-title">${escapeHtml(phaseLabel(g.phase))}</div>'),
        ('<span>${escapeHtml(ph)}</span><div class="bar">', '<span>${escapeHtml(phaseLabel(ph))}</span><div class="bar">'),
        ('[p.date,p.phase,p.main,p.planned,actualMinutesForDate(p.date)', '[p.date,phaseLabel(p.phase),p.main,p.planned,actualMinutesForDate(p.date)'),
    ])


def polish_srs(path: Path) -> None:
    replace_all(path, [
        ("'<div class=\"srs-empty\">去词典制卡，或者享受一张干净的桌面。</div>'", "'<div class=\"srs-empty\">前往“查词制卡”添加词条。</div>'"),
        ("toast('FSRS设置已保存','ok')", "toast('复习设置已保存','ok')"),
        ("download(`JLPT紫藤完整备份_${localDay(now())}.json`,JSON.stringify({app:'JLPT紫藤学习系统'", "download(`JLPTStudy_完整备份_${localDay(now())}.json`,JSON.stringify({app:'JLPT Study'"),
        ("throw new Error('不是紫藤完整备份')", "throw new Error('不是可识别的完整备份')"),
        ("lines.push(['Wisteria-Japanese'", "lines.push(['JLPT-Study-Japanese'"),
        ("download(`紫藤词卡_Anki_${localDay(now())}.tsv`", "download(`JLPTStudy_Anki_${localDay(now())}.tsv`"),
        ("toast('SRS数据已清空','ok')", "toast('词卡数据已清空','ok')"),
        ("toast('SRS初始化失败：'+e.message", "toast('词卡模块初始化失败：'+e.message"),
    ])


def polish_manifest(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update({
        "name": "JLPT Study",
        "short_name": "JLPT Study",
        "description": "N4 到 N2 学习计划、FSRS-6 词卡复习与 JMdict 离线词典。",
    })
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def polish_version(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = "4.2.0"
    data["built"] = "2026-08-04"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="_site")
    args = parser.parse_args()
    root = Path(args.root)
    polish_index(root / "index.html")
    polish_srs(root / "assets/js/srs-app.js")
    polish_manifest(root / "manifest.webmanifest")
    polish_version(root / "VERSION.json")
    replace_all(root / "sw.js", [("const CACHE='jlpt-wisteria-v4.1.0';", "const CACHE='jlpt-study-v4.2.0';")])

    index = (root / "index.html").read_text(encoding="utf-8")
    required = ["<title>JLPT Study</title>", "词卡复习", "学习路线", "待补任务", "系统设置"]
    for marker in required:
        if marker not in index:
            raise RuntimeError(f"Polished site is missing marker: {marker}")
    print(f"UI copy polished in {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
