#!/usr/bin/env python3
"""Create a minimal offerpilot_skill case manifest without guessing facts or interview rounds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TEMPLATE = {
    "schema_version": "2.0",
    "delivery_mode": "full",
    "input_health": {
        "company_role": "workable",
        "market_language": "workable",
        "jd": "workable",
        "resume": "workable",
        "application_status": "workable",
        "interview_rounds": "unknown"
    },
    "sources": [],
    "claims": [],
    "resume": {
        "input_format": "unknown",
        "text_input_checked": False,
        "name": "",
        "contact": "",
        "objective": "",
        "availability": "",
        "application_type": "internship",
        "availability_confirmed": False,
        "photo_provided": False,
        "photo_path": "",
        "education_input_count": 0,
        "page_target": 1,
        "content_selection_confirmed": False,
        "sections": [
            {"type": "education", "title": "教育背景", "entries": []},
            {"type": "experience", "title": "实习经历", "entries": []},
            {"type": "projects", "title": "项目经历", "entries": []},
            {"type": "skills", "title": "个人技能", "items": []},
            {"type": "self_evaluation", "title": "自我评价", "items": []}
        ]
    },
    "interview": {
        "bullet_coverage": [],
        "rounds": []
    },
    "iteration_log": []
}


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化 offerpilot_skill case manifest")
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=("research", "resume", "interview", "full"), default="full")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        parser.error("目标已存在；如确需覆盖请显式使用 --force")
    data = json.loads(json.dumps(TEMPLATE, ensure_ascii=False))
    data["delivery_mode"] = args.mode
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Initialized: {args.output}")
    print("Fill confirmed facts only. Keep interview.rounds empty until a round is confirmed or high-confidence with sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
