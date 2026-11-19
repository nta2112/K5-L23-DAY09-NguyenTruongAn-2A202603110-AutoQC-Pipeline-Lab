# Báo cáo Day 09 — Nguyễn Trường An, 2A202603110

## 1. Kết luận trước
Kết luận cuối cùng: HOLD với mã thoát 10. Từ 224 ảnh ban đầu, hệ thống giữ lại 203 ảnh hợp lệ để đưa vào xử lý và loại bỏ 21 ảnh ngay từ bước kiểm tra đầu vào. Lý do chưa thể phát hành vì sau khi máy tự sửa các lỗi cú pháp và người duyệt dùng hết ngân sách 80 ảnh, vẫn còn 38 trên tổng số 203 ảnh (chiếm 18,72%) mang cảnh báo chưa được kiểm tra, vượt quá mức trần cho phép là 10,00%.

## 2. Lỗi và phân việc

| Mã lỗi | Số ảnh/dòng | Ai sửa (máy/người) | Vì sao |
|---|---:|---|---|
| POSSIBLE_MISSING | 53 | Người | Cần mắt người xác nhận vật thể bị sót nhãn vì mô hình lớn cũng có thể nhận diện nhầm. |
| POSSIBLE_FALSE_POS | 29 | Người | Cần kiểm tra thực tế xem khung bao dư thừa là do gán nhầm hay mô hình kiểm tra bỏ sót. |
| POSSIBLE_LOOSE_BOX | 28 | Người | Cần người điều chỉnh lại mép khung bao cho ôm sát vật thể theo đúng quy chuẩn. |
| POSSIBLE_WRONG_CLASS | 18 | Người | Lỗi ngữ nghĩa giữa hai lớp hợp lệ, máy không thể tự quyết định lớp nào đúng. |
| EMPTY_LABEL | 12 | Người | Cần xác định đây là ảnh nền sạch hay ảnh bị quên gán nhãn toàn bộ. |
| BOX_OUT_OF_IMAGE | 8 | Máy | Tọa độ tràn ra ngoài biên ảnh, máy có thể cắt gọn an toàn về trong khoảng từ 0 đến 1. |
| DUP_IMAGE_EXACT | 8 | Máy | Ảnh trùng lặp từng byte so với ảnh đã nhận trước đó, loại bỏ ở bước đầu vào. |
| DUP_BOX | 7 | Máy | Hai khung bao cùng lớp trùng khớp gần như hoàn toàn trên một ảnh, máy tự xóa dòng dư. |
| BAD_CLASS_ID | 6 | Máy | Mã lớp nằm ngoài danh sách quy định (từ 0 đến 3), xóa dòng lỗi để tránh hỏng lúc huấn luyện. |
| MISSING_LABEL_FILE | 6 | Người | Máy không thể tự bịa ra nhãn cho ảnh trắng nên đẩy lên đầu hàng đợi để người gán bổ sung. |
| BOX_TINY | 6 | Người | Khung bao có cạnh ngắn dưới 12 pixel, cần người xem lại để quyết định giữ hay bỏ theo quy định. |
| LEAK_TEST | 5 | Máy | Ảnh bị trùng với tập kiểm thử hoặc tập đánh giá, loại bỏ ngay để chống rò rỉ dữ liệu. |
| BOX_ZERO | 4 | Máy | Chiều rộng hoặc chiều cao khung bao bằng 0, không có giá trị huấn luyện nên máy tự xóa. |
| CLASS_RARE | 4 | Người | Cảnh báo tần suất thấp phát sinh do các mã lớp lạ trước khi được máy dọn dẹp. |
| BAD_FORMAT | 3 | Máy | Dòng nhãn thiếu cột hoặc chứa giá trị không hợp lệ, máy tự xóa để tránh làm dừng chương trình. |
| BAD_SIZE | 3 | Máy | Kích thước ảnh nhỏ hơn mức tối thiểu 250 pixel, loại bỏ ở bước đầu vào. |
| DUP_IMAGE_NEAR | 3 | Máy | Ảnh gần như trùng lặp về mặt thị giác với ảnh đã có (khoảng cách băm nhỏ hơn ngưỡng 8), loại bỏ. |
| BOX_HUGE | 3 | Người | Khung bao chiếm trên 95% diện tích ảnh, cần người kiểm tra xem có phải khoanh nhầm toàn khung hình không. |
| BAD_CLASS_NAME | 2 | Máy | Tên lớp trong file data.yaml viết hoa sai chuẩn, máy tự động chuẩn hóa lại theo cấu hình. |
| CORRUPT_IMAGE | 2 | Máy | File ảnh bị hỏng dữ liệu không thể đọc được, loại bỏ ngay ở cửa vào. |

05_review_queue.csv xếp ảnh đầu hàng như vậy bởi vì hệ thống sắp xếp ảnh đầu hàng theo điểm ưu tiên, tính bằng tổng trọng số các mã lỗi trên ảnh. Những ảnh bị thiếu file nhãn được đẩy lên đầu vì đây là lỗi bắt buộc làm chặn toàn bộ quy trình, máy không thể tự đoán để sinh nhãn thay con người.

## 3. Calibration (2 ngưỡng)
| Tham số | Khởi đầu | Đã chọn | Precision / Recall (trước và sau) | Lý do đánh đổi |
|---|---|---|---|---|
| duplicates.phash_dist | 2 | 8 | DUP_IMAGE_NEAR từ 1.00 / 0.50 lên 1.00 / 0.67 (DUP_IMAGE_EXACT giữ nguyên 1.00 / 1.00) | Nếu bắt nhầm ảnh khác nhau thành trùng thì sẽ xóa dữ liệu tốt nên  ưu tiên giữ độ chính xác tuyệt đối 1.00. Nới ngưỡng lên 8 giúp bắt thêm được các ảnh trùng biến đổi nhẹ. Không chọn mức 20 vì ngưỡng quá lỏng làm tụt khả năng phát hiện ngay cả với ảnh trùng tuyệt đối xuống còn 0.33. |
| second_opinion.conf | 0.25 | 0.6 | WRONG_CLASS từ 0.56 / 0.83 lên 0.62 / 0.83; MISSING từ 0.50 / 1.00 lên 0.57 / 1.00; LOOSE_BOX từ 0.29 / 0.40 thành 0.20 / 0.20 | Ngưỡng 0.6 giúp lọc bớt các cảnh báo nhiễu từ mô hình phụ nhưng vẫn giữ nguyên tỷ lệ bắt trúng cho các lỗi quan trọng. Không tăng lên 0.16 vì mức này làm bỏ sót khá nhiều vật thể chưa được gán nhãn. |

Tập calib hay các tập dataset nhỏ chỉ cần bắt thêm hoặc sót một cặp là tỷ lệ đã tăng cao, khiến các con số chưa thực sự ổn định. Bên cạnh đó, các lỗi chèn trong tập mẫu đều là những biến đổi đơn giản như thu nhỏ hay chỉnh sáng nhẹ, khác với độ phức tạp của dữ liệu thực tế. Nếu chỉ nhìn vào chỉ số F1 cao mà chọn ngưỡng quá lớn như 16, hệ thống rất dễ gộp nhầm hai ảnh đường phố khác nhau có bố cục na ná thành ảnh trùng và xóa nhầm. Do đó, sau khi chạy với ngưỡng 8, cần kiểm tra các cặp bị báo để chắc chắn không có ảnh tốt nào bị bỏ.

## 4. Cửa chặn và điều pipeline KHÔNG bắt được

Khi chạy thử lệnh với budgett bằng 0 (python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb), 6 ảnh bị thiếu file nhãn không có người gán bổ sung nên vẫn tồn tại dưới dạng lỗi bắt buộc ở vòng kiểm tra cuối. Cửa chặn từ chối, trả về kết quả Rework với mã thoát 20.

Về các điểm mù mà hệ thống không thể tự bắt được, có thể kể đến ba trường hợp sau:
* Các quy định gán nhãn cho các trường hợp như bỏ qua người ngồi sâu bên trong xe qua lớp kính tối màu hoặc vật thể bị che khuất quá một tỷ lệ nhất định. Những quy tắc này không thể kiểm tra tự động bằng AI.
* Trường hợp nhầm lẫn giữa các lớp có ngoại hình tương đồng trong điều kiện thiếu sáng hoặc góc khuất. 
* Các cặp ảnh trùng lặp nhưng đã qua cắt cúp khung hình quá sâu hoặc lật ngược góc nhìn.

## 5. Train: raw vs clean (tùy chọn, chấm riêng)
Đã train trên Google Colab (T4 GPU): `yolo26n.pt`, 20 epoch, imgsz 640, batch 16, 2 seed (0, 1), cùng val (gold_val, 40 ảnh) và cùng test (100 ảnh nhãn người); chỉ khác dữ liệu train.

| biến thể | #ảnh train | số seed | map50 (TB ± độ lệch) | map50_95 (TB ± độ lệch) | precision (TB ± độ lệch) | recall (TB ± độ lệch) |
|---|---|---|---|---|---|---|
| raw | 224 | 2 | 0.726 ± 0.000 | 0.512 ± 0.004 | 0.764 ± 0.061 | 0.649 ± 0.028 |
| clean | 203 | 2 | 0.699 ± 0.025 | 0.486 ± 0.013 | 0.796 ± 0.050 | 0.596 ± 0.049 |

Độ chênh lệch mAP50 giữa bản sạch và bản thô là -0.027, xấp xỉ độ lệch chuẩn giữa 2 seed của bản sạch. Với chỉ 2 lần chạy thử nghiệm, chưa thể kết luận dữ liệu sạch làm mô hình tệ đi và cũng không có bằng chứng nào cho thấy nó tốt hơn

giải thích vì sao clean không hơn raw:

- 5 ảnh mã lỗi LEAK_TEST trùng với ảnh test vẫn nằm trong raw khi train — model học thuộc đúng ảnh nằm trong tập test. Kiểm: bỏ 5 ảnh này khỏi raw rồi train lại, mAP50 của raw tụt.
- Raw có 8 ảnh trùng lặp đến từng byte. Do đó vài cảnh được học gấp đôi trọng số, lợi nhẹ. Kiểm: bỏ bản sao rồi train lại.
- Budget duyệt chỉ đủ 80/125 ảnh hàng đợi, 38/203 ảnh vẫn còn cảnh báo; lỗi ngữ nghĩa (nhầm lớp, thiếu box) mà tool không tự sửa được vẫn ở lại.

## 6. Quyết định và ghi chú AI

 Quyết định cuối cùng: Giữ nguyên trạng thái Hold, chỉ dùng bộ dữ liệu xuất ra làm bản nháp thử nghiệm nội bộ chứ chưa phát hành chính thức. Để đưa lô dữ liệu này sang trạng thái Release, cần  duyệt thủ công cho ít nhất 18 ảnh nữa nhằm kéo tỷ lệ ảnh xuống dưới 10,00%.
Về quá trình sử dụng công cụ AI hỗ trợ viết mã:
* Sủ dụng AI để hỗ trợ viết 4 module theo yêu cầu.
* Kiểm tra lại toàn bộ mã nguồn do AI sinh ra bằng cách đối chiếu từng nhánh điều kiện với mô tả yêu cầu.
