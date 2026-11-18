# Báo cáo Day 09 — <Họ và tên>, <MSHV>

> Xoá mọi `TODO(học viên)` và dòng gợi ý. Mỗi ý trả lời bằng **số lấy từ `submission/reports/`**, kèm mẫu số. Cả báo cáo ~1–2 trang.

## 1. Kết luận trước
TODO(học viên): pipeline kết luận **Release / Hold / Rework**? Bao nhiêu ảnh vào, bao nhiêu ảnh ra dataset? Lý do chính (1–3 câu).

## 2. Lỗi và phân việc
Lấy từ `02_error_list_v1` (gom theo mã lỗi). Cột "ai sửa": **máy** (autofix) hay **người** (hàng đợi); chỉ ghi những mã có mặt trong lô của bạn.

| Mã lỗi | Số ảnh/dòng | Ai sửa (máy/người) | Vì sao |
|---|---:|---|---|
| TODO(học viên) | | | |

TODO(học viên): vì sao `05_review_queue.csv` xếp ảnh đầu hàng như vậy? Với ngân sách 80 ảnh, người xem được bao nhiêu lỗi ngữ nghĩa?

## 3. Calibration (2 ngưỡng)
| Tham số | Khởi đầu | Đã chọn | Precision / Recall (trước → sau) | Lý do (đánh đổi) |
|---|---|---|---|---|
| `duplicates.phash_dist` | 2 | **16** | DUP_IMAGE_NEAR: 1.00 / 0.50 → 1.00 / **0.83** (DUP_IMAGE_EXACT giữ nguyên 1.00 / 1.00) | Cờ sai = xoá nhầm ảnh tốt nên ưu tiên precision = 1.00 tuyệt đối. Nới từ 2 lên 16 tăng recall NEAR từ 0.50 lên 0.83 mà vẫn không có FP nào. Không chọn 20: recall của cả EXACT tụt còn 0.33. |
| `second_opinion.conf` | 0.25 | **0.6** | WRONG_CLASS 0.56 / 0.83 → **0.62** / 0.83 · MISSING 0.50 / 1.00 → **0.57** / 1.00 · LOOSE_BOX 0.29 / 0.40 → 0.20 / 0.20 | Cảnh báo cho người xem nên ưu tiên giữ recall; 0.6 nâng precision (giảm báo động giả) mà không mất recall nào so với 0.25. Không chọn 0.8 dù WRONG_CLASS đạt 1.00 / 0.83: recall MISSING rơi 1.00 → 0.75 — box thiếu là FN nguy hiểm nhất (lỗi lọt thẳng vào dataset). LOOSE_BOX tụt còn 0.20 / 0.20 nhưng đây là cảnh báo nhẹ (trọng số 1.5), chấp nhận. |

**Một chỗ calibration có thể đánh lừa:** bộ calib chỉ có 39 ảnh với 6 cặp NEAR chèn sẵn, nên mỗi cột precision/recall nhảy từng bước ~17% — ô "0.83" nghĩa là bỏ sót đúng 1/6, không phải con số ổn định. Hơn nữa lỗi chèn là biến đổi "dễ" (thu nhỏ, đổi sáng), trong khi raw là ảnh model gán nhãn: recall 0.83 trên calib **không** có nghĩa là bắt được 83% trùng trên raw. Với `phash_dist` = 16 (ngưỡng nới khá xa), rủi ro thực tế là ảnh **khác nhau** bị ghép thành trùng và bị loại oan ở cửa vào — cần mở `01_intake` sau khi `make run` và xem bằng mắt các cặp bị cho là trùng (qua `viz_labels.py`) để xác nhận; nếu thấy ảnh khác nhau bị gộp thì hạ về 12.

## 4. Cửa chặn và điều pipeline KHÔNG bắt được
TODO(học viên): (a) chứng minh gate chặn đúng: chạy `python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb` (không có người duyệt nên ảnh thiếu file nhãn còn nguyên), chỉ ra kết luận **Rework**, mã thoát 20 và việc **không xuất** dataset. (Đừng sửa tay `work/run/ds`: pipeline dựng lại thư mục này từ raw mỗi lần chạy.) (b) ≥ 2 điểm mù có bằng chứng (box lỏng nhẹ, nhầm lớp mà model lớn cũng nhầm, ảnh trùng biến đổi mạnh…).

## 5. Train: raw vs clean (tùy chọn, chấm riêng)
Chưa train: ghi "chưa chạy" và lý do, rồi bỏ qua phần còn lại của mục này. Nếu đã train: dán bảng từ `submission/results/comparison.md` (model, epoch, seed, số ảnh train mỗi biến thể).

TODO(học viên): chênh mAP50 (clean − raw) so với **độ lệch chuẩn giữa các seed**; kết luận **trung thực** (nằm trong nhiễu thì nói là chưa kết luận được); ≥ 2 giả thuyết giải thích (ảnh trùng/rò rỉ test trong `raw`, nhãn máy còn lại trong `clean`, test chỉ 100 ảnh…) và cách kiểm.

## 6. Quyết định và ghi chú AI
TODO(học viên): (a) quyết định cuối; nếu Hold/Rework cần làm gì để thành Release? (b) Dùng AI viết code? Ghi 3 dòng: prompt chính, cách bạn kiểm code AI, 1 lần AI sai. Không dùng: ghi "không dùng".

*(Thưởng +2, tùy chọn)* CVAT: lọc `width < 20`, ảnh/số box khớp, đối chiếu `BOX_TINY` (xem docs/CVAT_FILTER.md), 1 câu về `can_review`.
