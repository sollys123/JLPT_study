#!/usr/bin/env python3
"""Normalize the public-facing copy of the built JLPT Study site.

The source application keeps its stable storage keys and internal identifiers.
Only files in the Pages build artifact are rewritten.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PLAIN_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("JLPT 紫藤学习系统", "JLPT Study"),
    ("JLPT 紫藤计划", "JLPT Study"),
    ("N4 → N2 学习系统", "N4 → N2 备考计划"),
    ("紫藤记忆舱", "词卡复习"),
    ("词典与SRS", "词卡复习"),
    ("词典与 SRS", "词卡复习"),
    ("今日学习", "今日计划"),
    ("完整日历", "学习日历"),
    ("课程地图", "学习路线"),
    ("学习日志", "学习记录"),
    ("设置与备份", "系统设置"),
    ("智能欠课队列", "待补任务"),
    ("专注计时", "学习计时"),
    ("当日记录", "今日记录"),
    ("本周脉搏", "本周进度"),
    ("阶段路线", "阶段计划"),
    ("教材购买节奏", "教材安排"),
    ("《新标日》48课地图", "《新标日》48课进度"),
    ("手动制卡", "新建词卡"),
    ("词典制卡", "查词制卡"),
    ("卡片浏览", "卡片管理"),
    ("词条与卡片浏览器", "卡片管理"),
    ("当前记忆状态", "当前卡片"),
    ("今日原则", "评分说明"),
    ("本地 JMdict 词典", "JMdict 离线词典"),
    ("未来14天到期预测", "未来14天复习量"),
    ("记忆质量", "记忆表现"),
    ("最需要处理的卡片", "需处理卡片"),
    ("录入模拟成绩", "新增模拟成绩"),
    ("最近8周学习时长", "近8周学习时长"),
    ("半年热力图", "近半年学习热力图"),
    ("写一条学习日志", "新增学习记录"),
    ("保存日志", "保存记录"),
    ("日志时间线", "记录时间线"),
    ("计划内特殊区间", "特殊日期"),
    ("GPT Live脚本库", "GPT Live 提示词"),
    ("复制脚本", "复制提示词"),
    ("诊断与危险操作", "诊断与重置"),
    ("运行 FSRS / 数据库诊断", "运行数据诊断"),
    ("导出完整 JSON", "导出完整备份"),
    ("导入完整 JSON", "导入完整备份"),
    ("FSRS设置已保存", "复习设置已保存"),
    ("SRS数据已清空", "词卡数据已清空"),
    ("SRS初始化失败", "词卡模块初始化失败"),
    ("不是紫藤完整备份", "不是可识别的完整备份"),
    ("Wisteria-Japanese", "JLPT-Study-Japanese"),
    ("紫藤词卡_Anki_", "JLPTStudy_Anki_"),
    ("JLPT紫藤完整备份_", "JLPTStudy_完整备份_"),
    ("JLPT紫藤备份_", "JLPTStudy_学习备份_"),
    ("欢迎来到紫藤学习系统", "欢迎使用 JLPT Study"),
    ("法国旅行：", "旅行安排："),
    ("欠课机制：", "任务顺延："),
    ("欠课策略", "任务顺延方式"),
    ("旅行豁免", "旅行休息"),
)


def replace_plain(text: str) -> str:
    for old, new in PLAIN_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def polish_index(path: Path) -> None:
    text = replace_plain(path.read_text(encoding="utf-8"))

    exact = (
        ("<div class=\"brand-mark\">藤</div>", "<div class=\"brand-mark\">J</div>"),
        ("data-mood=\"很吃力\">🫠 很吃力", "data-mood=\"濒死\">💀 濒死"),
        ("data-mood=\"濒死\">🫠 濒死", "data-mood=\"濒死\">💀 濒死"),
        (">SRS</button>", ">词卡</button>"),
        ("label:'SRS'", "label:'词卡复习'"),
        ("<h3>词条与卡片</h3>", "<h3>词条编辑</h3>"),
        ("<label>English meaning</label>", "<label>英文释义</label>"),
        ("<label>English example / 自己的解释</label>", "<label>英文例句 / 补充说明</label>"),
        (">完整备份</button>", ">导出备份</button>"),
        (">开始学习</button>", ">开始使用</button>"),
        ("今天处于减负模式，历史欠课暂停调入。", "今天处于减负模式，暂不安排历史待补任务。"),
        ("这一天属于计划内豁免。欠课调度已暂停，不会把旅行变成补习班。", "这一天属于计划内休息，任务顺延已暂停。"),
        ("旅行模式：所有任务自愿，不生成欠课。", "旅行模式：所有任务均为可选，不生成待补任务。"),
        ("减负模式：只保留核心任务，今天不接收历史欠课。", "减负模式：只保留核心任务，今天不安排历史待补任务。"),
        ("没有需要顺延的欠课。今天的桌面很干净。", "没有待补任务。"),
        ("来自欠课", "顺延任务"),
        ("另有 ${backlog.queued} 项留在队列，系统会继续向后分摊。", "另有 ${backlog.queued} 项保留在待补列表，系统会继续向后安排。"),
        ("系统再安排 ${backlog.totalMinutes} 分钟欠课。", "系统再安排 ${backlog.totalMinutes} 分钟待补任务。"),
        ("核心任务顺延，复习任务合并，可选任务不会堆成债务山。", "核心任务顺延，复习任务合并，可选任务不会无限累积。"),
        ("周测＋缓冲，不把欠债滚到下周", "周测＋缓冲，不把遗漏带到下周"),
        ("在今日页查看", "在今日计划中查看"),
        ("温柔：每天最多1项核心欠课", "轻量：每天最多安排1项待补任务"),
        ("均衡：按容量智能填充", "均衡：按剩余时间自动安排"),
        ("这些日期不会产生欠课。", "这些日期不会生成待补任务。"),
        ("欠课只会填入剩余容量，不会无限堆到明天。", "待补任务只会填入剩余时间，不会无限累积。"),
        ("只看真实推进，不制造打卡焦虑", "查看时长、完成率与长期进度"),
        ("把卡点和小胜利留住", "保存每日备注与错题线索"),
    )
    for old, new in exact:
        text = text.replace(old, new)

    text = re.sub(
        r'<button class="mood" data-mood="(?:濒死|很吃力)">.*?(?:濒死|很吃力)</button>',
        '<button class="mood" data-mood="濒死">💀 濒死</button>',
        text,
    )

    text = re.sub(r'(<button data-view="roadmap"><b>◇</b>)(?:课程|路线)(</button>)', r'\1路线\2', text)
    text = re.sub(r'(<button data-view="vocab"><b>字</b>)(?:SRS|词卡)(</button>)', r'\1词卡\2', text)

    marker = "const phaseOrder=[...new Set(PLAN_DATA.schedule.map(x=>x.phase))];"
    if marker in text and "const phaseLabels=" not in text:
        helper = """const phaseOrder=[...new Set(PLAN_DATA.schedule.map(x=>x.phase))];
const phaseLabels={'N4-准备':'N4 · 准备','N4-假名入门':'N4 · 假名','N4-新标日48课':'N4 · 基础课程','N4-旅行前整理':'N4 · 旅行前复习','法国旅行':'法国旅行','N4-旅行后恢复':'N4 · 恢复','N4-冲刺':'N4 · 冲刺','N4-正式考试':'N4 · 考试','N3-过渡':'N3 · 过渡','N3-学习':'N3 · 系统学习','N3-模拟':'N3 · 模拟','N2-学习':'N2 · 系统学习','N2-冲刺':'N2 · 冲刺','N2-暂定考试':'N2 · 考试'};
const phaseLabel=phase=>phaseLabels[phase]||String(phase||'自由安排').replace(/-/g,' · ');
const weekLabel=week=>{const value=String(week||'').trim();if(!value)return '自由安排';if(value==='TRIP-FR')return '旅行期间';const match=value.match(/^(N[1-5])-W(\\d+)$/);if(!match)return value;const n=Number(match[2]);return n===0?`${match[1]} 准备周`:`${match[1]} 第${n}周`;};"""
        text = text.replace(marker, helper)

    phase_replacements = (
        ("`${p.phase} · ${p.week||'自由日'}`", "`${phaseLabel(p.phase)} · ${weekLabel(p.week)}`"),
        ("${escapeHtml(p.phase)} · ${escapeHtml(p.week||'')}", "${escapeHtml(phaseLabel(p.phase))} · ${escapeHtml(weekLabel(p.week))}"),
        ("${escapeHtml(plannedEntry(d).phase)} · ${escapeHtml(plannedEntry(d).goal||'')}", "${escapeHtml(phaseLabel(plannedEntry(d).phase))} · ${escapeHtml(plannedEntry(d).goal||'')}"),
        ("${escapeHtml(g.phase)}", "${escapeHtml(phaseLabel(g.phase))}"),
        ("${escapeHtml(ph)}</span><div class=\"bar\">", "${escapeHtml(phaseLabel(ph))}</span><div class=\"bar\">"),
        ("[p.date,p.phase,p.main,p.planned,actualMinutesForDate(p.date)", "[p.date,phaseLabel(p.phase),p.main,p.planned,actualMinutesForDate(p.date)"),
    )
    for old, new in phase_replacements:
        text = text.replace(old, new)

    path.write_text(text, encoding="utf-8")


def polish_srs(path: Path) -> None:
    text = replace_plain(path.read_text(encoding="utf-8"))
    text = text.replace("去词典制卡，或者享受一张干净的桌面。", "前往“查词制卡”添加词条。")
    path.write_text(text, encoding="utf-8")


def polish_manifest(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(
        {
            "name": "JLPT Study",
            "short_name": "JLPT Study",
            "description": "N4 到 N2 学习计划、FSRS-6 词卡复习与 JMdict 离线词典。",
        }
    )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def polish_version(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = "4.2.1"
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

    sw_path = root / "sw.js"
    sw = sw_path.read_text(encoding="utf-8")
    sw = re.sub(r"const CACHE='[^']+';", "const CACHE='jlpt-study-v4.2.1';", sw, count=1)
    sw_path.write_text(sw, encoding="utf-8")

    index = (root / "index.html").read_text(encoding="utf-8")
    required = ("<title>JLPT Study</title>", "词卡复习", "学习路线", "待补任务", "系统设置", "💀 濒死")
    missing = [marker for marker in required if marker not in index]
    if missing:
        raise RuntimeError(f"Polished site is missing required markers: {missing}")

    print(f"UI copy polished in {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
