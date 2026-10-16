# งานคนที่ 1: AI Detection

เป้าหมายคือสร้าง `best.pt` ที่ตรวจได้ 4 อย่าง:

- `player`
- `goalkeeper`
- `referee`
- `ball`

ยังไม่ต้องแยก Team A/Team B เพราะเป็นงานของคนที่ 2

## เริ่ม Fine-tune รอบสองบน Colab

ใช้สองไฟล์นี้:

1. `finetune_round2.ipynb` — เปิดผ่าน Colab → File → Upload notebook
2. `training/data/prepared/football-v3-training-ready.zip` — อัปโหลดเมื่อ Notebook ถามหา Dataset

เลือก Runtime → Change runtime type → T4 GPU แล้ว Run all จากบนลงล่าง
**ใช้ ZIP ชื่อ training-ready เท่านั้น** ไม่ใช่ ZIP ดิบจาก Roboflow หรือ `football-v3-ready.zip`
ZIP training-ready มี Train 141 / Valid 71 และ `initial_model.pt` ซึ่งตรงกับ `best.pt` รอบแรกตาม SHA-256
ไม่มีภาพ/Label Test และไม่ต้องอัปโหลดโมเดลแยกหรือใช้ Roboflow API key

Notebook ตรึง Ultralytics 8.4.177, ฝึกต่อจากน้ำหนักรอบแรก (ไม่ resume optimizer)
สูงสุด 40 epochs, patience 10, AdamW, lr0=0.0001, batch 1, imgsz 1280 และ seed 42
เป็นค่าเริ่มต้นทดลอง ไม่ได้อ้างว่าเป็นค่าที่เหมาะที่สุด
ถ้า GPU หน่วยความจำไม่พอ ให้เริ่มรอบใหม่จาก Setup และลด IMGSZ เป็น 960
ต้องใช้ขนาดเดียวกันทั้งการวัดก่อนเทรน การเทรน และการวัดหลังเทรน

ท้าย Notebook มี:

- Precision / Recall / mAP50 / mAP50-95 รวมและรายคลาส ก่อน–หลัง บน Valid เดียวกัน
- ผลแยก Valid เดิม 36 / Valid ใหม่ 35 / รวม 71 ภาพ เพื่อดูการลืมข้อมูลเดิม
- TP / FP / FN ที่ conf 0.15 / 0.30 / 0.50 จับคู่ Label แบบคลาสตรงกันและ IoU ≥ 0.50
- ภาพครบ 71 คู่เทียบ (3 คอลัมน์ Label / ก่อน / หลัง) แสดงคน conf 0.50 และบอล 0.15 เหมือนกันทั้งสองโมเดล
- กราฟฝึก confusion matrices, raw predictions, การตั้งค่า, checksum และข้อมูลการแบ่งชุด

ดาวน์โหลด **`tactivision_round2_results.zip`** ตอนจบแล้วส่ง ZIP นี้กลับมาให้ตรวจ
มี `best_round2.pt` ซึ่งยังไม่ควรนำไปแทนโมเดลบนเว็บจนกว่าจะตรวจผล
คะแนนที่ใช้เลือก best.pt และแสดงท้าย Notebook เป็น Validation ไม่ใช่ผล Test อิสระ
รอบนี้ไม่ได้ฝึกโมเดลบอลเฉพาะแยก และไม่ได้เปลี่ยนโมเดล Backend

สร้าง ZIP สำหรับ Colab ซ้ำจากไฟล์ที่เตรียมไว้ได้ด้วยคำสั่งนี้ (ไม่เขียนทับ ZIP เดิม):

```powershell
.venv\Scripts\python.exe training/prepare_round2_bundle.py
```

`round2_workflow.py` เป็นตัวช่วยชุดเดียวกับที่ฝังใน Notebook มี unit tests ตรวจความตรงกัน
ตรวจ Notebook และการโหลด Dataset บนเครื่องแล้ว ผู้ใช้รัน GPU training รอบสองใน Colab
และส่งผลกลับมาแล้ว อ่านผลที่ตรวจยืนยันได้ที่ [ROUND2_RESULTS.md](ROUND2_RESULTS.md)

ทดสอบโมเดลรอบสองกับภาพต้นฉบับ `candidate/test` ครบ 30 ภาพแล้ว:
อ่าน [CANDIDATE_TEST_ROUND2_RESULTS.md](CANDIDATE_TEST_ROUND2_RESULTS.md)
มีภาพ Label / รอบแรก / รอบสอง ครบทุกภาพ และแยกผลออกจาก Dataset ต้นฉบับ
ทดสอบซ้ำได้ด้วย `.venv\Scripts\python.exe -m training.test_round2_candidates`

## ข้อมูลเสื้อเหลือง/ดำรอบสอง: v3

ผู้ใช้ยืนยันว่า 35 ภาพใหม่ที่ Export เป็น Test ตั้งใจใช้เป็น Validation
จัดสำเนาด้วยคำสั่งนี้ โดยคืน split เก่าจากชุดที่ใช้จริง ไม่ใช้ split เก่าในหน้า Roboflow:

```powershell
.venv\Scripts\python.exe training/prepare_hardcases_export.py --zip "C:/Users/ADMIN/Downloads/Tactivision-detection.v3-football-v3-hardcases.yolov8.zip" --output training/data/prepared/football-v3-ready --new-test-is-validation --approved-polygons training/hardcases_v3_label_review.json
```

ได้ Train 141 / Validation 71 / Test เดิม 30 ภาพ และคืน Label Train เดิมที่ลบกรอบซ้ำ 13 กรอบไว้แล้ว
Test และ Validation เก่าคง Label เดิมทุกไบต์ ZIP ต้นฉบับไม่เปลี่ยน
ผู้ใช้ยืนยันตำแหน่งบอลใน `frame_0071_02h20m00s_jpg.rf.89f3e8ee1f7429426972575181a98420.jpg` แล้ว
จึงแปลง Polygon บรรทัด 16 เป็น Bounding Box ที่ครอบขอบเขตเดิมประมาณ 6×7 พิกเซล
ไม่ย้ายไปวัตถุอื่น ไม่เปลี่ยนคลาส และคง Label อีก 15 บรรทัดไว้ทุกไบต์
`hardcases_v3_label_review.json` บันทึกการยืนยัน พร้อม checksum ของ ZIP และบรรทัดที่อนุญาต
สคริปต์ปฏิเสธการแปลงหาก checksum เปลี่ยน และไม่แปลง Polygon อื่นอัตโนมัติ
ข้อมูลใน `football-v3-ready.zip` ผ่านการตรวจรูปแบบแล้ว มี `data.yaml` ที่ชี้เฉพาะ Train/Valid ไม่มี key Test
ใช้ Notebook รอบสองข้างต้น ไม่ควรใช้ Notebook รอบแรกโดยไม่ปรับ เพราะ Notebook เดิมล็อกจำนวนภาพไว้ 37/36
ZIP `football-v3-split-review.zip` เป็นสำเนารอตรวจก่อนการยืนยัน เก็บไว้เป็นหลักฐาน ไม่ใช่ชุดพร้อมเทรน
ใช้โฟลเดอร์ปลายทางใหม่เมื่อรันซ้ำ
ชื่อไฟล์ใหม่ไม่มีรหัสแมตช์ การแยกตามแมตช์จึงอาศัยการจัดกลุ่มของผู้ใช้ ไม่ได้ยืนยันอิสระจากชื่อไฟล์

## เทียบโมเดลบอลเก่าและใหม่บน Validation

รันจาก root ของโปรเจกต์ เมื่อมี Dataset ที่เตรียมไว้และโมเดลทั้งสองไฟล์แล้ว:

```powershell
.venv\Scripts\python.exe training/compare_ball_detectors.py
```

สคริปต์ใช้เฉพาะ Validation 36 ภาพจาก `football-v1-ready` ตรวจ checksum ภาพและโมเดล
ไม่อ่านภาพ/Label Train หรือ Test และไม่เทรนหรือปรับค่าบน Backend
รัน `best.pt` และโมเดลบอลแยกใน environment เดียวกัน เพื่อเทียบเฉพาะคลาสบอลอย่างยุติธรรม
ที่ conf 0.15 / 0.30 / 0.50, imgsz 1280, NMS IoU 0.70 และเกณฑ์จับคู่ IoU ≥ 0.50
เป็นการตรวจภาพเต็ม ไม่มี tiling; NMS 0.70 ใช้ให้ตรงกับการทดลอง conf ก่อนหน้า
ไม่ใช่ NMS 0.55 ของ Backend จึงไม่ใช่คะแนนยืนยัน pipeline ที่ Deploy

ผลอยู่ใน `training/artifacts/ball_comparison_<เวลา>/` และ ZIP ชื่อเดียวกัน:
`ball_summary.csv`, `ball_per_image.csv`, `ball_report.json`, ผลทำนายดิบ และภาพเทียบครบ 36 ภาพต่อค่า conf
ภาพเรียงซ้าย Label / กลางโมเดลเดิม / ขวาโมเดลบอลเฉพาะ วงกลมใช้เน้นตำแหน่งบอลเล็ก ๆ
สีเขียวคือจับคู่ Label ได้ สีแดงคือกรอบที่จับคู่ไม่ได้ ผลขึ้นกับคุณภาพ Label และไม่ใช่ mAP
การนับเป็นจำนวนกรอบรวมทุกภาพ ไม่ใช่จำนวนบอลไม่ซ้ำตลอดคลิป

อ่านผลทดลองรอบแรกได้ที่ [BALL_COMPARISON_RESULTS.md](BALL_COMPARISON_RESULTS.md)

## เริ่มงานแบบง่าย

### หลัง Fine-tune: ทดสอบแมตช์ที่กันไว้

เปิด `test_roboflow.ipynb` ใน Google Colab (T4 GPU) แล้วอัปโหลด `training/data/prepared/football-v2-test-ready.zip` ไฟล์เดียว ZIP นี้รวม Dataset กับ `models/best.pt` จาก `tactivision_finetune_results.zip` ที่ผู้ใช้เทรนเสร็จแล้ว

- ตรวจ Roboflow v2 แล้วมี Test 30 ภาพ พร้อม Label ไม่ว่างครบทุกภาพ แม้หน้าสร้าง Version เคยขึ้น Unannotated 30
- พิกัดกรอบและ Class ID ผ่านการตรวจรูปแบบ ไม่มีภาพซ้ำแบบตรงกันกับ Train/Validation และไม่พบกรอบซ้ำตามเกณฑ์เดิม
- Test มาจาก `idq95Xp5RI0` เท่านั้น ขนาด 1280×720 ทั้งหมด มี 278 player, 17 goalkeeper, 27 referee และ 37 ball annotations
- คง Label ของ Test ตาม Export ทุกไบต์ ไม่มีการแก้คำตอบจากผลทำนาย
- คง Train 37 / Validation 36 ตามชุดที่ใช้ฝึกโมเดลจริง ไม่ใช้การแบ่ง 73 Train ใน Roboflow มาทับชุดที่ตรึงไว้
- ใช้ `split='test'`, imgsz=1280, batch=1, conf=0.001, iou=0.7 เท่ากันทั้งสองโมเดล และตรึง Ultralytics 8.4.177 ตามรอบ Fine-tune
- ภาพซ้ายเดิม/ขวาใหม่แสดงที่ conf=0.15 ซึ่งเป็นค่าที่ใช้ดูภาพใน Validation เดิม
- Notebook ไม่มีคำสั่งเทรน และดาวน์โหลดรายงาน `tactivision_test_results.zip` เมื่อเสร็จ **ยังไม่ได้คำนวณคะแนน Test บนเครื่องนี้**

สคริปต์เตรียมชุดทดสอบ: `prepare_test_export.py` รายงานตรวจไฟล์: `training/data/prepared/football-v2-test-ready/test_audit.json` การตรวจไฟล์ไม่รับรองว่า Label ที่มนุษย์/AI วาดถูกต้องทุกกรอบ

```powershell
python training/prepare_test_export.py --zip "C:/Users/ADMIN/Downloads/Tactivision-detection.v2-football-v2-test.yolov8.zip" --frozen-dataset training/data/prepared/football-v1-ready --trained-results "C:/Users/ADMIN/Downloads/tactivision_finetune_results.zip" --output training/data/prepared/football-v2-test-ready
```

ใช้โฟลเดอร์ปลายทางใหม่เมื่อรันซ้ำ รูปแบบ ZIP ต้นทาง v2 มี `data.yaml` ซ้ำสองรายการแต่เนื้อหาเหมือนกัน สคริปต์ยอมรับเฉพาะกรณีเนื้อหาซ้ำตรงกันและเขียน config ฉบับเดียวที่แก้พาธแล้วในชุดสำเนา

### เส้นทางที่ใช้ตอนนี้: Fine-tune โมเดลฟุตบอลเดิมจาก Roboflow Sports

ใช้ `finetune_roboflow.ipynb` บน Google Colab (T4 GPU) กับ `training/data/prepared/football-v1-ready.zip`

- Train: 37 ภาพจาก `PFYsHN24C3k` (Assumption Thonburi vs Assumption Sriracha รอบชิงฯ)
- Validation: 36 ภาพจาก `tJnScrAKJfI` (Assumption Sriracha vs Phattharaborphit รอบก่อนรองฯ)
- Test: แมตช์ `idq95Xp5RI0` ยังแยกไว้ ไม่อยู่ใน ZIP และไม่ใช้เลือกโมเดล
- ทั้ง 73 ภาพขนาด 1280×720 มีไฟล์ Label จับคู่ครบ ไม่มีภาพซ้ำแบบไบต์หรือพิกเซลตรงกัน
- ลำดับคลาส: `0 ball`, `1 goalkeeper`, `2 player`, `3 referee`
- พบกรอบซ้ำ 13 กรอบในภาพ `PFYsHN24C3k_01-04-00` และลบเฉพาะกรอบซ้ำออกจากชุดสำเนา ZIP ต้นฉบับไม่เปลี่ยน
- `audit.json` บันทึกผลตรวจและรายการแก้ไข, `split_manifest.json` บันทึกว่าภาพใดอยู่ชุดใด

Notebook ดาวน์โหลด `football-player-detection.pt` จากลิงก์ใน `roboflow/sports/examples/soccer/setup.sh` วัด Validation ก่อน/หลัง แล้ว Fine-tune โมเดลนี้ต่อ (ไม่ได้เริ่มจาก `yolo11n.pt`) บันทึกภาพเทียบซ้าย/ขวาครบ 36 ภาพ และดาวน์โหลด `best.pt` พร้อมรายงานเมื่อเสร็จ **ยังไม่ได้รัน GPU training จากเครื่องนี้**

รอบนี้ใช้ข้อมูลของเรา 73 ภาพเท่านั้น ยังไม่ได้รวม Dataset สาธารณะ 372 ภาพ และยังไม่ได้ Fine-tune โมเดลบอลแยกต่างหาก Train มีแค่หนึ่งแมตช์จึงเป็นการทดลองรอบแรก การตรวจรูปแบบ Label ไม่รับรองความถูกต้องของ Label ที่ AI สร้าง ต้องตรวจโดยมนุษย์ด้วย

สร้างชุดสำเนาซ้ำได้ด้วยคำสั่งนี้ (ต้องมี Pillow และใช้โฟลเดอร์ปลายทางใหม่):

```powershell
python training/prepare_roboflow_export.py --zip "C:/Users/ADMIN/Downloads/Tactivision-detection.v1-football-v1.yolov8.zip" --output training/data/prepared/football-v1-ready --valid-clip tJnScrAKJfI --review training/artifacts/label_review_ready --deduplicate
```

`--deduplicate` ใช้เมื่อได้ตรวจกรอบซ้ำแล้ว: ลบเฉพาะกรอบคลาสเดียวกันที่ IoU ≥ 0.8 และพิกัดมุมทั้งสี่ต่างกันไม่เกิน 2 พิกเซล ข้อมูล Train/Validation ถูกแบ่งตามคลิปทั้งแมตช์ ไม่สุ่มเฟรม

ขั้นตอนด้านล่างเป็นเครื่องมือเตรียมภาพและทางเลือกเทรน YOLO11n เดิม หากต้องการ Fine-tune ไฟล์ฟุตบอลเดิม ให้ใช้ Notebook ใหม่ข้างต้น

### 1. ตัดภาพจากคลิป

วางไฟล์วิดีโอไว้ที่ `training/videos/` แล้วรัน:

```powershell
python training/extract_frames.py --video "training/videos/match.mp4" --every-seconds 30
```

ภาพสำหรับเทรนให้เก็บใน `training/data/candidates/train/` และภาพจากอีกแมตช์ที่กันไว้ทดสอบให้เก็บใน `training/data/candidates/test/` ห้ามนำภาพใน `test/` ไปเทรน

ถ้าเป็นลิงก์ YouTube ไม่ต้องดาวน์โหลดวิดีโอเต็ม ให้ติดตั้งเครื่องมือครั้งแรก:

```powershell
python -m pip install --target training/.capture_deps -r training/requirements-capture.txt
```

สำหรับคลิปตัวอย่างของโปรเจกต์นี้ ช่วงแข่งเริ่มประมาณนาที 12 ให้ดึงหนึ่งภาพทุก 2 นาที:

```powershell
python training/extract_youtube_frames.py --url "https://www.youtube.com/live/tJnScrAKJfI" --output "training/data/candidates/train/tJnScrAKJfI" --start-seconds 720 --end-seconds 7500 --every-seconds 120
```

สคริปต์จะกระโดดไปตามเวลาแล้วเก็บเฉพาะไฟล์ JPG ไม่บันทึกวิดีโอเต็มลงเครื่อง คลิป 2 ชั่วโมงจะได้ประมาณ 60 ภาพ หลังจากนั้นให้ลบภาพพักครึ่ง ภาพรีเพลย์ ภาพโฆษณา และภาพที่คล้ายกันออก แล้วคัด 40–50 ภาพไป Annotate

คลิปเพิ่มเติมที่แบ่งไว้ (แคปทุก 2 นาที ตั้งแต่ต้นจนจบคลิป แล้วคัดภาพภายหลัง):

| ชุด | คลิป | โฟลเดอร์ |
| --- | --- | --- |
| Train เดิม | `tJnScrAKJfI` | `training/data/candidates/train/tJnScrAKJfI/` |
| Train เพิ่ม | `PFYsHN24C3k` | `training/data/candidates/train/PFYsHN24C3k/` |
| Test | `idq95Xp5RI0` | `training/data/candidates/test/idq95Xp5RI0/` |

```powershell
python training/extract_youtube_frames.py --url "https://www.youtube.com/live/PFYsHN24C3k" --output "training/data/candidates/train/PFYsHN24C3k" --every-seconds 120 --workers 3
python training/extract_youtube_frames.py --url "https://www.youtube.com/live/idq95Xp5RI0" --output "training/data/candidates/test/idq95Xp5RI0" --every-seconds 120 --workers 3
```

ชื่อภาพเป็น `รหัสคลิป_ชั่วโมง-นาที-วินาที.jpg` เพื่อย้อนดูจังหวะเดิมได้ รันคำสั่งเดิมซ้ำได้เมื่อเครือข่ายหลุด สคริปต์จะข้ามภาพที่มีแล้ว หากสองคลิปเป็นแมตช์เดียวกันต้องอยู่ชุดเดียวกัน แม้จะมาจากคนละช่องหรือคนละลิงก์ก็ตาม ภาพ Test ใช้ประเมินหลังเลือกโมเดลและค่าตั้งจาก Train/Validation แล้วเท่านั้น

### 2. รวมกับ Dataset ฟุตบอลเดิม

ใช้ Dataset เดิมเป็นฐาน แล้วเพิ่มภาพจากคลิปของเรา โดยใช้ชื่อคลาสเดิมทั้ง 4 คลาส ห้ามสร้าง `team_a` หรือ `team_b` ใน Dataset นี้

หลัง Export แบบ YOLO ให้ใช้ `data.yaml` ที่ Roboflow สร้างให้ อย่าเปลี่ยนลำดับ Class ID เอง ไฟล์ตัวอย่างอยู่ที่ `data.example.yaml`

### 3. ทดลองเทรน 3 Epoch

```powershell
python training/train_detector.py --data "path/to/data.yaml" --epochs 3 --name smoke
```

ถ้าจบโดยไม่มี Error ค่อยเทรนจริง:

```powershell
python training/train_detector.py --data "path/to/data.yaml" --epochs 50 --name tactivision-yolo11n
```

หรือเปิด `train.ipynb` ด้วย Google Colab แล้วรันทีละ Cell

### 4. ทดสอบโมเดล

```powershell
python training/evaluate_detector.py --model "training/runs/tactivision-yolo11n/weights/best.pt" --data "path/to/data.yaml"
```

### 5. ส่งให้คนที่ 5

ส่งไฟล์ต่อไปนี้:

- `best.pt`
- `data.yaml`
- `train.ipynb`
- `training/reports/metrics.json`
- ภาพตัวอย่างผลตรวจจับ

คนที่ 5 จะนำ `best.pt` ไปวางที่ `backend/models/best.pt` แล้วผล Bounding Box จะถูกส่งต่อให้คนที่ 2 แบ่ง Team A/Team B

## ข้อควรจำ

- Train และ Test ห้ามใช้ภาพเดียวกันหรือเฟรมติดกัน
- ถ้าเป็นไปได้ให้ Test ด้วยคนละแมตช์
- ลูกบอลมองไม่เห็นไม่ต้องเดาแล้ววาดกรอบ
- ไม่ commit วิดีโอ Dataset หรือไฟล์ `.pt` ขนาดใหญ่ลง Git

## แยก threshold สำหรับประเมินกับใช้งานจริง

- ประเมิน mAP ด้วย `scripts/evaluate_detector.py` ซึ่งใช้ `conf=0.001` เป็นค่าเริ่มต้น เพื่อให้ Ultralytics สร้าง precision-recall curve จาก prediction ช่วงกว้าง
- Backend เรียกโมเดลเดิมด้วย `INFERENCE_CONFIDENCE_THRESHOLD=0.15` แล้วกรองแยกคลาสด้วย `PERSON_CONFIDENCE_THRESHOLD=0.50` และ `BALL_CONFIDENCE_THRESHOLD=0.15`

ค่าเหล่านี้มีคนละวัตถุประสงค์กับ threshold สำหรับประเมิน mAP ห้ามนำ threshold ใช้งานจริงไปใช้รายงาน mAP เพราะจะตัด prediction confidence ต่ำออกก่อนคำนวณและอาจทำให้ผลประเมินคลาดเคลื่อน

ค่าแยกคลาสข้างต้นเป็นข้อเสนอจาก Validation เพียงหนึ่งแมตช์ จึงต้องทดสอบกับภาพจากแมตช์อื่นต่อ ส่วนโมเดลบอลแยกสามารถทดลองที่ `conf=0.50` ได้ แต่ยังไม่ใช่โมเดลหรือค่าเริ่มต้นของระบบ

```powershell
python scripts/evaluate_detector.py --model backend/models/best.pt --data training/data.yaml
```

