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

## `POST /calibrate`

รับ JSON ที่มีขนาดภาพ จุดจับคู่ระหว่างพิกัดภาพและพิกัดสนามอย่างน้อย 4 จุด และ Detection ปัจจุบัน คืน Homography matrix, reprojection error และตำแหน่งสนามของแต่ละ Detection

## `POST /simulate`

รับผู้เล่นที่มีพิกัดสนาม Ball Carrier เป้าหมายแบบ `receiver` หรือ `space` และค่าการจำลอง คืนระยะ เวลา Risk, ผู้สกัด จุดสกัด และเหตุผลภาษาไทย

Backend ไม่มี Session และ Database หน้าเว็บต้องส่ง State ปัจจุบันมากับแต่ละคำขอ Simulation

