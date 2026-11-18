"""BƯỚC 2/4 — Sửa tự động những lỗi bắt buộc mà máy sửa được AN TOÀN.   ★★

Test:  pytest tests/test_autofix.py -q

`fix(ds, issues, cfg) -> list[dict]`: duyệt `issues` (chỉ lỗi severity ERROR), sửa thẳng vào thư mục `ds`,
và trả về danh sách thay đổi; mỗi phần tử có khoá: image, line, action, before, after
(đây chính là file `03_fixes.csv` — bằng chứng pipeline đã làm gì, người có thể kiểm lại).

| code lỗi                                       | cách sửa                                    | action           |
|------------------------------------------------|---------------------------------------------|------------------|
| BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO, DUP_BOX    | xoá dòng đó khỏi file nhãn                  | "drop_line"      |
| BOX_OUT_OF_IMAGE                               | cắt box về trong [0,1] (giữ nguyên lớp)     | "clip_box"       |
| MISSING_LABEL_FILE                             | KHÔNG sửa file (máy không thể bịa nhãn): ghi 1 dòng fix, before="(không có file)", after="chuyển người gán" | "needs_label" |
| BAD_CLASS_NAME                                 | ghi lại `names` trong data.yaml đúng `cfg["classes"]` | "rename_classes" |
| DUP_IMAGE_*, LEAK_TEST, CORRUPT_IMAGE, BAD_SIZE| xoá ảnh + nhãn khỏi `ds`                    | "remove_image"   |

Bẫy cần nghĩ tới (có test cho từng cái)
- Một file có NHIỀU dòng lỗi: số dòng trong `issues` là số dòng GỐC. Nếu xoá từng dòng một thì số dòng lệch.
  Gom theo file, rồi ghi lại MỘT lần.
- Sau khi cắt, box có thể không còn diện tích (nằm hẳn ngoài ảnh): lúc đó xoá dòng thay vì ghi box rỗng.
- Một dòng có 2 lỗi (vd. BOX_OUT_OF_IMAGE + DUP_BOX): xoá dòng thắng, chỉ ghi 1 fix `drop_line`, không ghi thêm `clip_box`. Dòng trống ở giữa file vẫn đếm vào số dòng gốc.
- Ảnh vừa bị xoá (DUP_IMAGE_*...) mà còn issue dòng của chính nó: bỏ qua êm, không được báo lỗi/chết.
- Không động tới lỗi WARN (cảnh báo là việc của người). Không sửa file ở `data/raw/` — chỉ sửa `ds`.
- Chạy lần 2 trên dữ liệu đã sửa phải không làm gì thêm (idempotent) — NGOẠI LỆ duy nhất: `needs_label` được ghi lại mỗi lần còn lỗi `MISSING_LABEL_FILE` (vì ảnh vẫn chưa có nhãn).

- `needs_label` KHÔNG tạo file nhãn rỗng (rỗng = "ảnh nền", khác với "chưa gán"). `review_queue` sẽ đẩy ảnh này lên đầu hàng đợi cho người.

Gợi ý: `yaml.safe_load / safe_dump`.
"""
from collections import defaultdict

import yaml

from ..common import ERROR, parse_yolo_line

DROP_CODES = {"BAD_FORMAT", "BAD_CLASS_ID", "BOX_ZERO", "DUP_BOX"}
REMOVE_IMG_PREFIXES = ("DUP_IMAGE_",)
REMOVE_IMG_CODES = {"LEAK_TEST", "CORRUPT_IMAGE", "BAD_SIZE"}


def _clip_yolo_box(cx: float, cy: float, w: float, h: float):
    x1 = max(0.0, min(1.0, cx - w / 2.0))
    y1 = max(0.0, min(1.0, cy - h / 2.0))
    x2 = max(0.0, min(1.0, cx + w / 2.0))
    y2 = max(0.0, min(1.0, cy + h / 2.0))
    nw = x2 - x1
    nh = y2 - y1
    if nw <= 0.0 or nh <= 0.0:
        return None
    ncx = (x1 + x2) / 2.0
    ncy = (y1 + y2) / 2.0
    return ncx, ncy, nw, nh


def fix(ds, issues, cfg):
    fixes = []
    err_issues = [iss for iss in issues if iss.severity == ERROR]

    # 1. Sửa data.yaml nếu có BAD_CLASS_NAME
    if any(iss.code == "BAD_CLASS_NAME" for iss in err_issues):
        old_names = ds.yaml_names()
        target_classes = list(cfg["classes"])
        if old_names != {i: n for i, n in enumerate(target_classes)}:
            data = {}
            if ds.yaml_path.exists():
                data = yaml.safe_load(ds.yaml_path.read_text(encoding="utf-8")) or {}
            data["names"] = target_classes
            data["nc"] = len(target_classes)
            ds.yaml_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
            fixes.append({
                "image": "data.yaml",
                "line": "",
                "action": "rename_classes",
                "before": str(old_names),
                "after": str({i: n for i, n in enumerate(target_classes)}),
            })

    # 2. Xóa các ảnh lỗi ở cửa vào (DUP_IMAGE_*, LEAK_TEST, CORRUPT_IMAGE, BAD_SIZE)
    removed_stems = set()
    for iss in err_issues:
        if iss.code in REMOVE_IMG_CODES or iss.code.startswith(REMOVE_IMG_PREFIXES):
            stem = iss.image
            if stem in removed_stems:
                continue
            img_p = ds.image_path(stem)
            lbl_p = ds.label_path(stem)
            if (img_p and img_p.exists()) or lbl_p.exists():
                if img_p and img_p.exists():
                    img_p.unlink()
                if lbl_p.exists():
                    lbl_p.unlink()
                removed_stems.add(stem)
                fixes.append({
                    "image": stem,
                    "line": "",
                    "action": "remove_image",
                    "before": iss.code,
                    "after": "(đã xoá ảnh và nhãn)",
                })

    # 3. Ghi nhận MISSING_LABEL_FILE -> needs_label (không tạo file rỗng)
    seen_missing = set()
    for iss in err_issues:
        if iss.code == "MISSING_LABEL_FILE":
            stem = iss.image
            if stem in removed_stems or stem in seen_missing:
                continue
            if not ds.label_path(stem).exists():
                seen_missing.add(stem)
                fixes.append({
                    "image": stem,
                    "line": "",
                    "action": "needs_label",
                    "before": "(không có file)",
                    "after": "chuyển người gán",
                })

    # 4. Gom lỗi theo từng file nhãn và xử lý một lần (tránh lệch số dòng gốc)
    line_issues_by_stem = defaultdict(list)
    for iss in err_issues:
        if iss.line is not None and (iss.code in DROP_CODES or iss.code == "BOX_OUT_OF_IMAGE"):
            if iss.image not in removed_stems:
                line_issues_by_stem[iss.image].append(iss)

    for stem, stem_issues in sorted(line_issues_by_stem.items()):
        lbl_p = ds.label_path(stem)
        if not lbl_p.exists():
            continue

        raw_lines = lbl_p.read_text(encoding="utf-8", errors="replace").splitlines()
        drop_lines = {iss.line for iss in stem_issues if iss.code in DROP_CODES}
        clip_lines = {iss.line for iss in stem_issues if iss.code == "BOX_OUT_OF_IMAGE"} - drop_lines

        new_lines = []
        changed = False

        for line_no, text in enumerate(raw_lines, 1):
            stripped = text.strip()
            if line_no in drop_lines:
                if stripped:
                    fixes.append({
                        "image": stem,
                        "line": line_no,
                        "action": "drop_line",
                        "before": stripped,
                        "after": "(xoá dòng)",
                    })
                    changed = True
                continue

            if line_no in clip_lines and stripped:
                try:
                    cls_id, cx, cy, w, h = parse_yolo_line(stripped)
                    clipped = _clip_yolo_box(cx, cy, w, h)
                    if clipped is None:
                        fixes.append({
                            "image": stem,
                            "line": line_no,
                            "action": "drop_line",
                            "before": stripped,
                            "after": "(xoá dòng — nằm hẳn ngoài ảnh)",
                        })
                        changed = True
                        continue
                    ncx, ncy, nw, nh = clipped
                    after_str = f"{cls_id} {ncx:.6f} {ncy:.6f} {nw:.6f} {nh:.6f}"
                    if after_str != stripped:
                        fixes.append({
                            "image": stem,
                            "line": line_no,
                            "action": "clip_box",
                            "before": stripped,
                            "after": after_str,
                        })
                        new_lines.append(after_str)
                        changed = True
                    else:
                        new_lines.append(text)
                except ValueError:
                    new_lines.append(text)
            else:
                new_lines.append(text)

        if changed:
            content = "\n".join(new_lines) + ("\n" if new_lines else "")
            lbl_p.write_text(content, encoding="utf-8")

    return fixes
