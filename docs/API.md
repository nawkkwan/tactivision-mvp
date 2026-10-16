# TactiVision API Contract

## `GET /health`

คืนสถานะบริการ ชื่อโมเดลที่กำหนด และสถานะการโหลดโมเดลจริง โมเดลโหลดแบบ lazy เมื่อเรียก `/detect` ครั้งแรก

`modules.ball_detection` ระบุ `model`, `mode`, `loaded`, `source`, `confidence`, `error`
โดย `mode` เป็น `lazy` ก่อนตรวจภาพครั้งแรก, `ready` เมื่อโมเดลบอลเฉพาะทำงานสำเร็จ,
`fallback` เมื่อโหลด/ตรวจบอลไม่สำเร็จ และ `disabled` เมื่อไม่ได้กำหนดโมเดลบอล
`source` เป็น `specialized`, `combined` (โมเดลหลัก) หรือ `pending` ก่อนเรียกใช้งาน
สถานะนี้ไม่ใช่คะแนนความแม่นยำ; `status: ok` ไม่รับรองว่าโมเดลบอลพร้อมแล้ว

## `POST /detect`

รับไฟล์ `multipart/form-data` ชื่อ `file` รองรับ JPEG, PNG และ WebP ขนาดไม่เกิน 10 MB

คืนข้อมูล:

- ขนาดและ SHA-256 fingerprint ของภาพ
- โมเดลและโหมด `generic` หรือ `fine_tuned`
- Detection ID, class, confidence, bounding box, จุดเท้า และ Team ID
- ผล Auto Calibration ซึ่งอาจเป็น `success` หรือ `needs_manual`
- ตำแหน่งสนามของผู้เล่นเมื่อ Auto Calibration สำเร็จ

### โมเดลบอลเฉพาะ

ตั้ง `BALL_MODEL_PATH` (default `backend/models/football-ball-detection.pt`)
และดาวน์โหลดด้วย `python -m backend.app.download_ball_model` ก่อนเริ่มบริการ
ไม่มีการดาวน์โหลดโมเดลบอลระหว่างคำขอ API
ค่า `DETECTION_CONFIDENCE=0.25`, `BALL_CONFIDENCE=0.15`, `DETECTION_IMGSZ=1280`
เป็นค่าเริ่มต้นที่ปรับผ่าน environment ได้; การตั้ง `BALL_MODEL_PATH` เป็นค่าว่างใน environment
จะปิดโมเดลบอลเฉพาะ (ใน PowerShell ใช้ค่า whitespace `" "` เพราะ `""` อาจลบตัวแปรแทน)

โมเดลหลักคืนคนและวัตถุอื่นตามเดิม แต่กรอบ `ball` จะถูกแทนที่ด้วยผลจากโมเดลบอลเฉพาะ
เมื่อรันสำเร็จ แม้ผลเป็นศูนย์บอลก็ไม่ดึงกรอบบอลเดิมกลับมา หากรันไม่สำเร็จจึงใช้ผลจากโมเดลหลักแทน
ID `p1...` สำหรับคน, `b1...` สำหรับบอล; จุด `foot_pixel` ของบอลเป็นกึ่งกลางกรอบ
ไม่เพิ่ม field ใหม่ใน `/detect` และไม่เลือกคนถือบอลอัตโนมัติ
ตรวจภาพเต็ม ไม่ใช้ video tracking หรือ tiled inference; อาจคืนบอลหลาย candidate
และยังไม่ได้ยืนยันคะแนนความแม่นยำของ pipeline สองโมเดลบน Test Set

การแยกทีมใช้ LAB color histogram ร่วมกับ SigLIP embeddings โดย reuse กรอบจาก YOLO เดิม
SigLIP โหลดแบบ lazy ในการเรียก `/detect` ครั้งแรกจาก `SIGLIP_SOURCE` (ค่าเริ่มต้น
`google/siglip-base-patch16-224`) และเก็บไว้ใช้ซ้ำใน process; กำหนด `MODEL_OFFLINE=1`
เมื่อต้องการบังคับใช้ไฟล์ที่ cache ไว้เท่านั้น ค่า `SIGLIP_DEVICE` เริ่มต้นเป็น `cpu`
เพื่อไม่แย่งหน่วยความจำ accelerator กับ YOLO สามารถตั้งเป็น `cuda` หากเครื่องมีหน่วยความจำ GPU เหลือ
ตรวจ `GET /health` ที่ `modules.team_classification.mode`: `lazy`, `siglip_ready`, หรือ
`color_fallback`. เมื่อ SigLIP โหลดไม่ได้ ระบบยังทำงานด้วย LAB histogram อย่างเดียว.

การจัดกลุ่มต้องมีผู้เล่นที่อ่านสีเสื้อได้อย่างน้อย 4 คน; กรณีไม่พอหรือแยกกลุ่มไม่ชัดจะคงเป็น
`unassigned`. Team A/B เป็นกลุ่มเฉพาะภาพ ไม่ใช่ชื่อทีมถาวร และค่า `team_confidence` เป็น
ระยะห่างของกลุ่ม ไม่ใช่เปอร์เซ็นต์ความแม่นยำ.

## `POST /calibrate`

รับ JSON ที่มีขนาดภาพ จุดจับคู่ระหว่างพิกัดภาพและพิกัดสนามอย่างน้อย 4 จุด และ Detection ปัจจุบัน คืน Homography matrix, reprojection error และตำแหน่งสนามของแต่ละ Detection

## `POST /simulate`

รับผู้เล่นที่มีพิกัดสนาม Ball Carrier, `pass_type` แบบ `ground`, `chip` หรือ `long_ball`, เป้าหมายแบบ `receiver`, `space` หรือ `through_ball` และค่าการจำลอง คืนรูปแบบการจ่าย ระยะ เวลา ระดับ Risk, `risk_percent` ซึ่งเป็นดัชนีความเสี่ยง 0–100, ผู้รับบอลฝ่ายเดียวกันที่ถึงจุดเร็วที่สุด, ผู้สกัด จุดสกัด ความสูงบอล ณ จุดสกัด และรายการผู้เล่นฝ่ายตรงข้ามที่มีโอกาสตัดบอลเรียงตาม `time_margin` ระบบจะเทียบเวลาของคู่แข่งกับทั้งเวลาบอลและเพื่อนร่วมทีมที่เร็วที่สุดในแต่ละจุด ตำแหน่งเป้าหมายแบบ `receiver` ใช้พิกัดล่าสุดของผู้เล่น ส่วน `through_ball` ใช้จุดนำหน้าที่ผู้ใช้เลือกและผู้เล่นร่วมทีมที่เลือกเป็นผู้วิ่งรับ

Backend ไม่มี Session และ Database หน้าเว็บต้องส่ง State ปัจจุบันมากับแต่ละคำขอ Simulation

