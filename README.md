# SUMMARIZER -- USING -- REASONING - CRITICAL

## PROJECT STRUCTURE

```
ROOT
│
├── Config/
│    ├── config.json
│    └── keys.json
│
├── Data/
│    ├── LongK171
│    │    └── VNexpress
│    └── SurAyush
│         └── News_Summary_Dataset
│
├── Libraries/
│    ├── __init__.py
│    ├── Client_Llama.py
│    ├── Common_*.py
│    ├── Flow_*.py
│    ├── Processor_*.py
│    └── Tools_Json_Parser.py
│
├── Models/
│    ├── microsoft
│    │    └── Phi-3-mini-4k-instruct-gguf
│    └── Qwen
│         └── Qwen2.5-3B-Instruct-GGUF
│
├── Output/
│    ├── Histories-Batch-EN.json
│    └── Histories-Batch-VI.json
│
├── Prompts/
│    ├── EN-*.txt
│    └── VI-*.txt
│
├── Reports/
│
├── .gitignore
├── env.yml
├── llama_run.py
├── Main_Pipeline.ipynb├── Reports/
└── README.md
END
```

---

## BÁO CÁO NGHIÊN CỨU [ TIẾNG VIỆT ]

### 1. GIỚI THIỆU

#### 1.1. BỐI CẢNH NGHIÊN CỨU

Trong NLP, các mô hình ngôn ngữ lớn (LLM) thể hiện năng lực mạnh mẽ trong sinh văn bản nhưng vẫn gặp vấn đề về độ chính xác và trung thực do lỗi “ảo giác”.

Để khắc phục, các khung cải tiến lặp (iterative refinement) được phát triển, mô phỏng quá trình con người viết – tự đánh giá – sửa chữa.

Phương pháp như Self-Refine và Critique–Improve giúp giảm suy diễn sai và tăng khả năng bám sát văn bản nguồn, nâng cao độ tin cậy và chất lượng đầu ra.

#### 1.2. HỆ THỐNG REASONING - CRITICAL

Nghiên cứu này tập trung vào một kiến trúc cụ thể: Reason–Critical
Đây là kiến trúc tóm tắt văn bản lặp hai pha gồm:

* **Reasoning model** : phân tích văn bản, tạo chuỗi suy luận và bản tóm tắt ban đầu, dùng nhiệt độ cao (≈0.3) để tăng đa dạng.
* **Critic model** : đối chiếu với văn bản gốc, chấm điểm theo 6 tiêu chí và đưa phản hồi ngắn gọn, dùng nhiệt độ thấp (≈0.1) để giữ ổn định.

Chu trình lặp lại, Reasoning ở vòng sau chỉnh sửa có chọn lọc theo phản hồi, chỉ sửa phần sai và giữ nguyên nội dung đúng.

#### 1.3. MỤC TIÊU VÀ PHẠM VI NGHIÊN CỨU

Nghiên cứu này được thực hiện nhằm mục đích phân tích chi tiết hiệu quả, các ưu điểm về phương pháp luận và các rủi ro tiềm ẩn của hệ thống Reason–Critic khi áp dụng cho tóm tắt văn bản có cấu trúc song ngữ (Anh–Việt).

Phạm vi triển khai của hệ thống được giới hạn trong các tham số sau:

```
{
  "System_Config": {
    "max_iters": {
      "value": 3,
      "description": "Vận hành tối đa 3 vòng lặp."
    },
    "min_improve": {
      "value": 0.1,
      "description": "Ngưỡng cải thiện tối thiểu giữa các vòng là 0.1."
    },
    "n_ctx": {
      "value": 4096,
      "description": "Sử dụng ngữ cảnh 4096 token."
    },
    "n_gpu_layers": {
      "value": -1,
      "description": "GPU layers được đặt ở chế độ toàn phần."
    }
  }
}

```

### 2. PHƯƠNG PHÁP LUẬN

> Phương pháp luận của nghiên cứu này bao gồm việc thiết kế một quy trình (pipeline) khép kín, định nghĩa các thành phần kiến trúc, thiết kế bộ prompt hướng dẫn chi tiết, và xác lập các ràng buộc đầu ra nghiêm ngặt.

#### 2.1. QUY TRÌNH TỔNG QUAN

* **Bước khởi đầu - Vòng 0 - No Reason:**  Mô hinh đọc văn bản gốc và tóm tắt, không có ràng buộc hay hướng dẫn suy luận Reasoning.
* **Bước 1 – Vòng 1 - Reasoning FIrst:** Mô hình đọc văn bản gốc và sinh JSON gồm *reasoning trace* [ topic, key_ideas, filtered_ideas ] và  *summary*.
* **Bước 2 – Vòng 1 - Critical FIrst:** Đánh giá kết quả từ Bước 1 theo 6 tiêu chí, trả về điểm số [ *scoring* ] và phản hồi [ *feedback_text* ].
* **Bước 3 – Vòng 2 -  Reasoning Refine:** Nhận văn bản gốc, tóm tắt và phản hồi trước, chỉ sửa phần cần thiết, giữ nguyên số liệu và nội dung đúng.
* **Bước 4 – Vòng 2 - Critical Refine:** Đánh giá lại, ưu tiên tiêu chí *Consistency*.
* **Bước 5 – Lặp:** Tiếp tục các vòng refine cho đến khi đạt giới hạn ma..

#### 2.2. CẤU TRÚC VÀ CẤU HÌNH

> Hệ thống sử dụng một mô hình ngôn ngữ duy nhất nhưng áp dụng hai cấu hình iêng biệt cho hai vai trò.

##### 2.2.1. Cấu trúc

1. **Reasoning model**

* **Đầu vào:** Văn bản gốc (vòng 1) hoặc Văn bản gốc + JSON cũ + Feedback (vòng refine).
* **Đầu ra:** Một đối tượng JSON duy nhất tuân thủ định dạng nghiêm ngặt, bao gồm reasoning: [ topic, key_ideas, filtered_ideas ] và summary.

2. **Critical model**

* **Đầu vào:** Văn bản gốc + JSON của Reasoning.
* **Đầu ra:** Một đối tượng JSON duy nhất chứa scoring [ 6 tiêu chí, thang 1–5 ] và feedback_text ngắn.

##### 2.2.2. Tham số

```
  "reason_params": {
    "max_new_tokens": 512,
    "temperature": 0.3,
    "top_p": 0.9,
    "seed": 42
  },
  "critic_params": {
    "max_new_tokens": 512,
    "temperature": 0.1,
    "top_p": 0.8,
    "seed": 314159
  },
  "llama_cpp_params": {
    "n_gpu_layers": -1,
    "n_ctx": 4096,
    "verbose": true
  },
  "flow_params": {
    "max_iters": 3,
    "min_improve": 0.1
  }
```

Việc hạ nhiệt độ của Critic (0.1) so với Reasoning (0.3) là lựa chọn có cơ sở, giúp ổn định chấm điểm, giảm phản hồi ngẫu nhiên, đồng thời vẫn giữ cho Reasoning có độ sáng tạo cần thiết trong quá trình sinh và tinh chỉnh nội dung.

#### 2.3. RÀNG BUỘC

Hệ thống áp dụng các **ràng buộc cứng** để đảm bảo chất lượng:

* **JSON hợp lệ:** chỉ một đối tượng JSON, không có văn bản thừa.
* **Không trường rỗng:** mọi trường phải có giá trị.
* **Bảo toàn thông tin:** giữ nguyên số liệu, ngày tháng, tên riêng.
* **Giới hạn độ dài:** tóm tắt ≤100 từ.
* **Không suy diễn:** cấm thêm hoặc bịa thông tin ngoài nguồn.

#### 2.4. PROMPT VÀ TIÊU CHÍ ĐÁNH GIÁ

##### 2.4.1. Thiết kế Prompt

* **Reasoning:**

  * *Vòng 1:* Xác định topic, key_ideas, filtered_ideas; tự kiểm tra bằng  checklist ; tuân thủ JSON và  không suy diễn.
  * *Vòng 2-n:* Đọc JSON + feedback, chỉ sửa điểm nêu, giữ phần đúng,  không viết lại toàn bộ.
* **Critical:**

  * *Vòng 1:* Chấm 6 tiêu chí (1–5) theo Verification Rule, phản hồi ngắn, có kiểm chứng.
  * *Vòng 2-n:* Ưu tiên Consistency, giữ rule cũ, chỉ nêu lỗi trọng yếu kế tiếp.

##### 2.4.2. Tiêu chí đánh giá

**Critic đánh giá tóm tắt theo  6 tiêu chí chính :**

* Factuality: phản ánh đúng, không sai lệch hay bịa đặt.
* Clarity: rõ ràng, mạch lạc, dễ hiểu.
* Logical Coherence: các ý kết nối hợp lý, không mâu thuẫn.
* Coverage: bao quát đủ ý chính, chi tiết quan trọng.
* Utility: hữu ích cho cải thiện hoặc tổng hợp.
* Consistency: nhất quán nội tại.

**Trọng số từng tiêu chí:**

* Factuality: 0.30
* Clarity: 0.20,
* Logical Coherence: 0.15,
* Coverage: 0.15,
* Utility: 0.10,
* Consistency: 0.10

### 3. THIẾT KẾ THỰC NGHIỆM

> Phần này mô tả các tập dữ liệu, các mô hình được sử dụng và các chỉ số đo lường hiệu suất được định nghĩa trong nghiên cứu.

#### 3.1. DATASETS

Nghiên cứu dùng hai tập dữ liệu tóm tắt tin tức gồm:

* **Tiếng Anh:** *SurAyush / News_Summary_Dataset*
* **Tiếng Việt:** *LongK171 / VNexpress*

Mỗi bộ có 1000 mẫu, lấy ngẫu nhiên đồng đều trên toàn tâp, mỗi tập 500 văn bản.

#### 3.2. MODELS

Sử dụng các mô hình Quantized quy mô nhỏ, phù hợp với tài nguyên hạn chế:

* microsoft/Phi-3-mini-4k-instruct (3.8B): mạnh về tiếng Anh.
* meta-llama/Llama-3.2-1B - 3B: cân bằng hai ngôn ngữ.
* Qwen/Qwen2.5-3B-Instruct-GGUF (q5_k_m, 2.6B): mạnh về tiếng Việt

#### 3.3. CHỈ SỐ ĐÁNH GIÁ

Nhắc lại:

* Vòng 0: Tóm tắt mà không thực hiện reasoning
* Vòng 1: Tóm tắt có reasoning và chưa áp dụng critical
* Vòng 2 - n: Tóm tắt có reasoning và critical

Với mỗi văn bản được xử lý, gọi điểm trung bình ( average_score ) ở vòng thứ i là AVG[i]:

* **Reasoning:**
  * Số lần thành công  = Số lần AVG[1] - AVG[0] >= 0.1
  * Tỉ lệ thành công = Số lần thành công / Tổng số văn bản
* **Critical:**
  * Số lần thành công  = Số lần AVG[1] - AVG[0] >= 0.1
  * Tỉ lệ thành công = Số lần thành công / Tổng số vòng Critical

### 4. KẾT QUẢ VÀ PHÂN TÍCH

> Phần này trình bày các kết quả định tính và định lượng được ghi nhận từ các tệp log.

#### 4.1. KẾT QUẢ ĐỊNH LƯỢNG

##### 4.1.1. Mô hình Phi-3-mini-4k-instruct (Trên 496 bộ dữ liệu tiếng Anh)

1. **Tóm tắt mà không thực hiện reasoning:**
   * Điểm thấp nhất: 3.00
   * Điểm cao nhất: 4.45
   * Điểm trung bình: 3.7311
2. **Tóm tắt với reasoning:**
   * Điểm thấp nhất: 2.10
   * Điểm cao nhất: 4.85
   * Điểm trung bình: 4.4383
   * Số lần reason thành công: 434 / 496
   * Tỉ lệ reason thành công: 87.50%
3. **Tóm tắt với reasoning-critical:**
   * Điẻm thấp nhất: 3.0
   * Điểm cao nhất: 4.85
   * Điểm trung bình: 4.5545
   * Số lần critic thành công: 202 / 233
   * Tỉ lệ critic thành công: 86.70%
   * Tỉ lệ critic thất bại: 0%

##### 4.1.2. Mô hình Qwen2.5-3B-Instruct-GGUF (Trên 386 bộ dữ liệu tiếng Việt)

1. **Tóm tắt mà không thực hiện reasoning:**
   * Điểm thấp nhất: 2.85
   * Điểm cao nhất: 4.70
   * Điểm trung bình: 3.9527
2. **Tóm tắt với reasoning:**
   * Điểm thấp nhất: 3.00
   * Điểm cao nhất: 4.70
   * Điểm trung bình: 4.1643
   * Số lần reason thành công: 243 / 386
   * Tỉ lệ reason thành công: 62.95%
3. **Tóm tắt với reasoning-critical:**
   * Điẻm thấp nhất: 3.15
   * Điểm cao nhất: 5.00
   * Điểm trung bình: 4.2933
   * Số lần critic thành công: 350 / 586
   * Tỉ lệ critic thành công: 59.73%
   * Tỉ lệ critic thất bại: 0%

#### 4.2. KẾT QUẢ ĐỊNH TÍNH

Kết quả định lượng cho thấy các bản tóm tắt có kèm suy luận (reasoning-based summarization) đạt chất lượng cao hơn đáng kể so với các tóm tắt được sinh trực tiếp  không có bước suy luận trung gian. Việc buộc mô hình lý giải logic trước khi tóm tắt giúp nó tập trung hơn vào cấu trúc, quan hệ nhân quả và trọng tâm thông tin, thay vì chỉ rút gọn bề mặt văn bản.

Kết quả định lượng cũng cho thấy hầu hết các chuỗi suy luận (reasoning trace) và bản tóm tắt do mô hình Reasoning sinh ra đều cải thiện đáng kể sau khi nhận phản hồi từ Critic, phù hợp với kỳ vọng lý thuyết của các hệ thống learning-by-feedback (học qua phản hồi).

**Kết luận tổng quát:**

> Sự kết hợp hai mô hình Reasoning và Critic không chỉ cải thiện độ chính xác và tính nhất quán của kết quả mà còn chứng minh rằng tóm tắt có suy luận là hướng tiếp cận ưu việt hơn so với  tóm tắt thuần sinh, nhờ khả năng tái lập quy trình tư duy phản biện và tự điều chỉnh dựa trên phản hồi có cấu trúc.

#### 4.3. PHÂN TÍCH KẾT QUẢ

**Thành công định tính của hệ thống xuất phát từ ba cơ chế chính:**

* Ràng buộc JSON: Quy định “một JSON hợp lệ duy nhất, không văn bản thừa” giúp giảm lỗi cú pháp và đảm bảo đủ trường dữ liệu nhờ checklist trong prompt.
* Quy tắc xác minh: Buộc Critic kiểm tra kỹ trước khi phê bình, giảm “báo động giả” và ngăn Reasoning sửa sai phần đúng, tránh hồi quy chất lượng.
* Cơ chế tinh chỉnh có kiểm soát: Prompt *reason_refine* yêu cầu “chỉ sửa đúng điểm feedback nêu”, kết hợp với việc Critic ưu tiên tiêu chí *Consistency*, giúp tập trung vào sửa lỗi thay vì viết lại toàn bộ.
