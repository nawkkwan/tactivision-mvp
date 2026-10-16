# TactiVision API Contract

## `GET /health`

คืนสถานะบริการ ชื่อโมเดลที่กำหนด และสถานะการโหลดโมเดลจริง โมเดลโหลดแบบ lazy เมื่อเรียก `/detect` ครั้งแรก

## `POST /detect`

รับไฟล์ `multipart/form-data` ชื่อ `file` รองรับ JPEG, PNG และ WebP ขนาดไม่เกิน 10 MB

คืนข้อมูล:

- ขนาดและ SHA-256 fingerprint ของภาพ
- โมเดลและโหมด `generic` หรือ `fine_tuned`
- Detection ID, class, confidence, bounding box, จุดเท้า และ Team ID
- ผล Auto Calibration ซึ่งอาจเป็น `success` หรือ `needs_manual`
- ตำแหน่งสนามของผู้เล่นเมื่อ Auto Calibration สำเร็จ

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

รับผู้เล่นที่มีพิกัดสนาม Ball Carrier เป้าหมายแบบ `receiver` หรือ `space` และค่าการจำลอง คืนระยะ เวลา Risk, ผู้สกัด จุดสกัด และเหตุผลภาษาไทย

Backend ไม่มี Session และ Database หน้าเว็บต้องส่ง State ปัจจุบันมากับแต่ละคำขอ Simulation

