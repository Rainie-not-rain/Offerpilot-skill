#!/usr/bin/env python3
"""Deterministic P0/P1/P2 checks for an offerpilot_skill case manifest and outputs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

STATUSES = {"confirmed", "needs_confirmation", "forbidden"}
SOURCE_GRADES = {"A", "B", "C", "D"}
ROUND_CONFIDENCE = {"confirmed", "high", "medium", "low", "unknown"}
PUBLIC_SUFFIXES = {".md", ".txt"}
INTERNAL_LABELS = re.compile(r"(?:Claim\s*→\s*evidence|JD\s*→\s*简历|Bullet\s*→\s*面试|P0|P1|P2)\s*[:：]", re.I)
PLACEHOLDERS = re.compile(r"(?:待补|待确认|TBD|TODO|xxx+|示例·求职者)", re.I)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("manifest 顶层必须是 object")
    return data


def add(bucket: list[dict], code: str, message: str, path: str = "") -> None:
    bucket.append({"code": code, "message": message, "path": path})


def validate_manifest(data: dict) -> tuple[list[dict], list[dict]]:
    failures: list[dict] = []
    warnings: list[dict] = []
    if str(data.get("schema_version", "")) != "2.0":
        add(failures, "P0_SCHEMA_VERSION", "新版 Word 流程要求 schema_version=2.0", "schema_version")
    health = data.get("input_health") or {}
    for key in ("company_role", "market_language", "jd", "resume", "application_status"):
        if health.get(key) not in {"complete", "workable"}:
            add(failures, "P0_INPUT_HEALTH", f"input_health.{key} 必须为 complete/workable", key)

    sources = data.get("sources") or []
    source_ids: set[str] = set()
    for i, source in enumerate(sources):
        sid = str(source.get("id", "")).strip()
        if not sid or sid in source_ids:
            add(failures, "P0_SOURCE_ID", "来源 id 缺失或重复", f"sources[{i}]")
        source_ids.add(sid)
        if source.get("grade") not in SOURCE_GRADES:
            add(failures, "P0_SOURCE_GRADE", "来源 grade 必须为 A/B/C/D", f"sources[{i}]")
        if source.get("grade") in {"A", "B"} and not source.get("url") and source.get("kind") != "user_material":
            add(warnings, "P1_SOURCE_URL", "A/B级非用户材料建议提供可点击 URL", f"sources[{i}]")

    claims = data.get("claims") or []
    claim_map: dict[str, dict] = {}
    for i, claim in enumerate(claims):
        cid = str(claim.get("id", "")).strip()
        if not cid or cid in claim_map:
            add(failures, "P0_CLAIM_ID", "claim id 缺失或重复", f"claims[{i}]")
            continue
        claim_map[cid] = claim
        if claim.get("status") not in STATUSES:
            add(failures, "P0_CLAIM_STATUS", "claim status 非法", f"claims[{i}]")
        if claim.get("status") == "confirmed" and not claim.get("evidence"):
            add(failures, "P1_CLAIM_EVIDENCE", "confirmed claim 必须说明证据口径", f"claims[{i}]")
        if claim.get("status") == "confirmed" and not claim.get("owner_boundary"):
            add(warnings, "P1_OWNER_BOUNDARY", "强 claim 建议说明个人贡献边界", f"claims[{i}]")

    resume = data.get("resume") or {}
    input_format = str(resume.get("input_format", "unknown")).strip().lower()
    if input_format == "text" and not resume.get("text_input_checked"):
        add(
            failures,
            "P0_TEXT_INPUT_UNCHECKED",
            "对话框粘贴内容尚未完成简历模块完整性检查，禁止生成终稿",
            "resume.text_input_checked",
        )
    for key in ("name", "contact"):
        value = str(resume.get(key, "")).strip()
        if not value or PLACEHOLDERS.search(value):
            add(failures, "P0_RESUME_IDENTITY", f"resume.{key} 缺失或含占位文本", f"resume.{key}")

    if resume.get("application_type") == "internship" and not str(resume.get("availability", "")).strip():
        if not resume.get("availability_confirmed"):
            add(failures, "P0_AVAILABILITY_UNCONFIRMED", "实习岗位缺少可实习时间，需询问用户或确认不展示", "resume.availability")
    if resume.get("page_target", 1) != 1:
        add(warnings, "P2_PAGE_TARGET", "默认应以一页为目标；多页仅在用户明确确认后使用", "resume.page_target")
    if resume.get("photo_provided") and not str(resume.get("photo_path", "")).strip():
        add(failures, "P0_PHOTO_MISSING", "用户已提供证件照，生成简历时必须填写并使用 photo_path", "resume.photo_path")

    sections = resume.get("sections") or []
    section_types = [str(section.get("type", "")) for section in sections]
    for required in ("education", "projects", "skills", "self_evaluation"):
        if required not in section_types:
            add(failures, "P1_REQUIRED_SECTION", f"缺少基础模块: {required}", "resume.sections")

    education_entries = sum(len(s.get("entries") or []) for s in sections if s.get("type") == "education")
    education_input_count = int(resume.get("education_input_count") or 0)
    if education_input_count and education_entries != education_input_count:
        add(
            failures,
            "P0_EDUCATION_LOSS",
            f"用户提供了{education_input_count}段涉及学校的教育经历，当前仅保留{education_entries}段；学校经历不得删减或合并",
            "resume.sections",
        )

    experience_count = sum(len(s.get("entries") or []) for s in sections if s.get("type") == "experience")
    project_count = sum(len(s.get("entries") or []) for s in sections if s.get("type") == "projects")
    over_budget = experience_count > 3 or project_count > 3 or (experience_count >= 2 and project_count > 1)
    if over_budget and not resume.get("content_selection_confirmed"):
        add(
            failures,
            "P0_CONTENT_SELECTION",
            "经历超过一页常规预算，必须先询问用户确认删减或保留",
            "resume.content_selection_confirmed",
        )
    elif over_budget:
        add(warnings, "P2_PAGE_DENSITY", "用户已确认超出常规预算，仍需渲染检查是否超过一页")

    bullet_ids: set[str] = set()
    used_claims: set[str] = set()
    for si, section in enumerate(sections):
        section_type = section.get("type")
        if not section_type:
            add(failures, "P1_SECTION_TYPE", "section 缺少 type", f"resume.sections[{si}]")
        if section_type in {"education", "projects"} and not (section.get("entries") or []):
            add(failures, "P1_REQUIRED_CONTENT", f"{section_type} 模块为空", f"resume.sections[{si}].entries")
        if section_type in {"skills", "self_evaluation"}:
            items = section.get("items") or []
            if not items:
                add(failures, "P1_REQUIRED_CONTENT", f"{section_type} 模块为空", f"resume.sections[{si}].items")
            for ii, item in enumerate(items):
                loc = f"resume.sections[{si}].items[{ii}]"
                if not isinstance(item, dict):
                    add(failures, "P1_ITEM_SCHEMA", "技能/自我评价每条必须为 object", loc)
                    continue
                title = str(item.get("category", item.get("title", ""))).strip()
                content = str(item.get("content", "")).strip()
                if not title or not content:
                    add(failures, "P1_ITEM_TITLE", "技能/自我评价每条必须含小标题和内容", loc)
            continue
        for ei, entry in enumerate(section.get("entries") or []):
            bullets = entry.get("bullets") or []
            if section_type in {"experience", "projects"} and not str(entry.get("background", "")).strip():
                add(failures, "P1_PROJECT_BACKGROUND", "工作/项目经历必须包含一句项目背景", f"resume.sections[{si}].entries[{ei}]")
            if len(bullets) > 3 and section_type in {"experience", "projects"}:
                add(warnings, "P2_BULLET_DENSITY", "单段经历超过3条，检查是否影响扫读", f"resume.sections[{si}].entries[{ei}]")
            for bi, bullet in enumerate(bullets):
                loc = f"resume.sections[{si}].entries[{ei}].bullets[{bi}]"
                if not isinstance(bullet, dict):
                    if section_type in {"experience", "projects"}:
                        add(failures, "P1_BULLET_SCHEMA", "工作/项目 bullet 必须为 object", loc)
                    continue
                if section_type not in {"experience", "projects"}:
                    continue
                bid = str(bullet.get("id", "")).strip()
                title = str(bullet.get("title", "")).strip()
                text = str(bullet.get("text", "")).strip()
                if not bid or bid in bullet_ids:
                    add(failures, "P1_BULLET_ID", "bullet id 缺失或重复", loc)
                bullet_ids.add(bid)
                if not title:
                    add(failures, "P1_BULLET_TITLE", "工作/项目每条内容必须有小标题", loc)
                if not text or PLACEHOLDERS.search(text) or PLACEHOLDERS.search(title):
                    add(failures, "P0_PLACEHOLDER", "bullet 小标题/正文为空或含占位文本", loc)
                elif len(text) < 45:
                    add(warnings, "P2_ITEM_LENGTH", "该条正文可能不足Word版2行；应保留场景、动作与结果，避免过度精炼", loc)
                elif len(text) > 150:
                    add(warnings, "P2_ITEM_LENGTH", "该条正文可能超过Word版3行；应去除重复但不得删除关键事实", loc)
                for cid in bullet.get("claim_ids") or []:
                    used_claims.add(cid)
                    claim = claim_map.get(cid)
                    if not claim:
                        add(failures, "P0_UNKNOWN_CLAIM", f"引用未知 claim: {cid}", loc)
                    elif claim.get("status") != "confirmed":
                        add(failures, "P0_UNSAFE_CLAIM", f"正文引用未确认/禁用 claim: {cid}", loc)

    coverage = (data.get("interview") or {}).get("bullet_coverage") or []
    covered = {str(item.get("bullet_id", "")) for item in coverage}
    for bid in sorted(bullet_ids - covered):
        add(failures, "P1_BULLET_COVERAGE", f"面试准备未覆盖 bullet: {bid}", "interview.bullet_coverage")
    for item in coverage:
        bid = str(item.get("bullet_id", ""))
        if bid not in bullet_ids:
            add(warnings, "P1_ORPHAN_COVERAGE", f"面试覆盖引用不存在的 bullet: {bid}")
        if len(item.get("questions") or []) < 2 or not item.get("evidence") or not item.get("boundaries"):
            add(failures, "P1_INTERVIEW_DEPTH", f"{bid} 需≥2个追问、证据和表达边界")

    for i, round_item in enumerate((data.get("interview") or {}).get("rounds") or []):
        confidence = round_item.get("confidence", "unknown")
        refs = set(round_item.get("source_ids") or [])
        if confidence not in ROUND_CONFIDENCE:
            add(failures, "P0_ROUND_CONFIDENCE", "轮次 confidence 非法", f"interview.rounds[{i}]")
        if confidence in {"medium", "low", "unknown"}:
            add(failures, "P0_ROUND_GUESS", "中低置信或未知轮次不得生成专属轮次", f"interview.rounds[{i}]")
        if not refs or not refs.issubset(source_ids):
            add(failures, "P0_ROUND_SOURCE", "轮次必须引用存在的来源", f"interview.rounds[{i}]")

    if not used_claims and claims:
        add(warnings, "P1_UNUSED_CLAIMS", "存在 claims，但简历 bullet 未建立 claim_ids 映射")
    return failures, warnings


def scan_outputs(root: Path) -> tuple[list[dict], list[dict]]:
    failures: list[dict] = []
    warnings: list[dict] = []
    if not root.exists():
        add(failures, "P0_OUTPUT_PATH", "输出目录不存在", str(root))
        return failures, warnings
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in PUBLIC_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if PLACEHOLDERS.search(text):
            add(failures, "P0_PUBLIC_PLACEHOLDER", "公开文件含占位文本", str(path))
        if INTERNAL_LABELS.search(text):
            add(warnings, "P2_INTERNAL_LABEL", "公开文件可能泄漏内部检查标签", str(path))
        if re.search(r"(?:一面|二面|三面|HR面)", path.name) and not re.search(r"(?:确认|高置信)", text):
            add(warnings, "P0_ROUND_FILE", "轮次文件需能证明已确认或高置信", str(path))
    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="执行 offerpilot_skill P0/P1/P2 机器质量检查")
    parser.add_argument("manifest", type=Path, help="UTF-8 offerpilot_skill case JSON")
    parser.add_argument("--outputs", type=Path, help="可选：扫描公开交付目录")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args()
    try:
        failures, warnings = validate_manifest(load_json(args.manifest))
        if args.outputs:
            f2, w2 = scan_outputs(args.outputs)
            failures.extend(f2)
            warnings.extend(w2)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures, warnings = ([{"code": "P0_MANIFEST", "message": str(exc), "path": str(args.manifest)}], [])
    result = {"status": "blocked" if failures else ("pass_with_gaps" if warnings else "pass"), "failures": failures, "warnings": warnings}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for item in warnings:
            print(f"[WARN] {item['code']}: {item['message']} {item['path']}")
        for item in failures:
            print(f"[FAIL] {item['code']}: {item['message']} {item['path']}")
        print(f"offerpilot_skill quality gate: {result['status']}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
