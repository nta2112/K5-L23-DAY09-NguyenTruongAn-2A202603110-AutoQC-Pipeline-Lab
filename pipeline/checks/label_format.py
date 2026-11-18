"""CHECK 2 — Dòng nhãn YOLO: sai định dạng, ID lớp lạ, box tràn ảnh, box rỗng, box lặp.   (Script 2 trong slide)   ★★

Test:  pytest tests/test_label_format.py -q

Mỗi dòng nhãn: `id cx cy w h` (5 số, toạ độ 0–1). Trả về list[Issue]; `Issue.line` = số dòng (đếm từ 1).

| code             | severity | khi nào                                                                  |
|------------------|----------|--------------------------------------------------------------------------|
| BAD_FORMAT       | ERROR    | không đúng 5 cột số (dùng `parse_yolo_line`, bắt `ValueError`)           |
| BAD_CLASS_ID     | ERROR    | id lớp ngoài 0..len(ds.classes)-1                                        |
| BOX_ZERO         | ERROR    | w <= 0 hoặc h <= 0                                                       |
| BOX_OUT_OF_IMAGE | ERROR    | mép box vượt [0,1] quá `cfg["label_format"]["overflow_tol"]`; extra={"overflow": mức tràn} |
| DUP_BOX          | ERROR    | cùng lớp với một dòng TRƯỚC ĐÓ và IoU > `dup_box_iou`; báo ở dòng SAU    |
| BOX_TINY         | WARN     | cạnh ngắn của box (px) < `min_box_px`  (cần `ds.image_size(stem)`)       |
| BOX_HUGE         | WARN     | w*h > `max_box_frac`                                                     |

Gợi ý
- Mép trái = x - w/2, mép phải = x + w/2 (xem câu hỏi "dòng YOLO nào lỗi?" trong slide).
- Một dòng hỏng (BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO) thì `continue`, đừng kiểm tiếp hình học của dòng đó.
- Dòng thiếu cột làm script của slide dừng giữa chừng: đây là lý do phải `try/except`.
- `iou_xywh(a, b)` có sẵn trong common.py.
- Ngưỡng nằm trong `cfg["label_format"]` — đừng viết cứng số vào code.
"""
from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line  # noqa: F401


from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line


def run(ds, cfg):
    c = cfg["label_format"]
    overflow_tol = c["overflow_tol"]
    min_box_px = c["min_box_px"]
    max_box_frac = c["max_box_frac"]
    dup_box_iou = c["dup_box_iou"]
    num_classes = len(ds.classes)

    issues = []

    for lf in ds.label_files():
        stem = lf.stem
        lines = ds.read_label_lines(stem)
        if not lines:
            continue

        img_size = ds.image_size(stem)
        seen_boxes = []  # lưu (cls_id, cx, cy, w, h) của các box hợp lệ trước đó trong cùng file

        for line_no, text in lines:
            # 1. BAD_FORMAT
            try:
                cls_id, cx, cy, w, h = parse_yolo_line(text)
            except ValueError as e:
                issues.append(
                    Issue("label_format", ERROR, "BAD_FORMAT", stem, f"sai định dạng dòng: {e}", line=line_no)
                )
                continue

            # 2. BAD_CLASS_ID
            if not (0 <= cls_id < num_classes):
                issues.append(
                    Issue("label_format", ERROR, "BAD_CLASS_ID", stem, f"id lớp không hợp lệ: {cls_id}", line=line_no)
                )
                continue

            # 3. BOX_ZERO
            if w <= 0 or h <= 0:
                issues.append(
                    Issue("label_format", ERROR, "BOX_ZERO", stem, f"kích thước box <= 0 ({w}, {h})", line=line_no)
                )
                continue

            # 4. BOX_OUT_OF_IMAGE
            left = cx - w / 2.0
            right = cx + w / 2.0
            top = cy - h / 2.0
            bottom = cy + h / 2.0
            overflow = max(0.0, -left, right - 1.0, -top, bottom - 1.0)
            if overflow > overflow_tol:
                issues.append(
                    Issue(
                        "label_format",
                        ERROR,
                        "BOX_OUT_OF_IMAGE",
                        stem,
                        f"box tràn ảnh {overflow:.4f}",
                        line=line_no,
                        extra={"overflow": round(overflow, 6)},
                    )
                )

            # 5. DUP_BOX (cùng lớp với box trước đó và IoU > dup_box_iou)
            curr_box = (cx, cy, w, h)
            is_dup = any(
                prev_cls == cls_id and iou_xywh((prev_cx, prev_cy, prev_w, prev_h), curr_box) > dup_box_iou
                for prev_cls, prev_cx, prev_cy, prev_w, prev_h in seen_boxes
            )
            if is_dup:
                issues.append(
                    Issue("label_format", ERROR, "DUP_BOX", stem, "box trùng lặp với dòng trước", line=line_no)
                )
            seen_boxes.append((cls_id, cx, cy, w, h))

            # 6. BOX_TINY (cảnh báo khi cạnh ngắn px < min_box_px)
            if img_size is not None:
                img_w, img_h = img_size
                short_side_px = min(w * img_w, h * img_h)
                if short_side_px < min_box_px:
                    issues.append(
                        Issue(
                            "label_format",
                            WARN,
                            "BOX_TINY",
                            stem,
                            f"box quá nhỏ ({short_side_px:.1f}px < {min_box_px}px)",
                            line=line_no,
                        )
                    )

            # 7. BOX_HUGE (cảnh báo khi diện tích tỉ lệ > max_box_frac)
            if w * h > max_box_frac:
                issues.append(
                    Issue(
                        "label_format",
                        WARN,
                        "BOX_HUGE",
                        stem,
                        f"box quá lớn ({w * h:.2f} > {max_box_frac})",
                        line=line_no,
                    )
                )

    return issues