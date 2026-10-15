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

รับผู้เล่นที่มีพิกัดสนาม Ball Carrier, `pass_type` แบบ `ground`, `chip` หรือ `long_ball`, เป้าหมายแบบ `receiver`, `space` หรือ `through_ball` และค่าการจำลอง คืนรูปแบบการจ่าย ระยะ เวลา ระดับ Risk, `risk_percent` ซึ่งเป็นดัชนีความเสี่ยง 0–100, ผู้รับบอลฝ่ายเดียวกันที่ถึงจุดเร็วที่สุด, ผู้สกัด จุดสกัด ความสูงบอล ณ จุดสกัด และรายการผู้เล่นฝ่ายตรงข้ามที่มีโอกาสตัดบอลเรียงตาม `time_margin` ระบบจะเทียบเวลาของคู่แข่งกับทั้งเวลาบอลและเพื่อนร่วมทีมที่เร็วที่สุดในแต่ละจุด `receiver` ใช้ตำแหน่งผู้เล่นจาก `players`; `through_ball` ต้องส่ง `receiver_id` ของผู้วิ่งและพิกัด `position` ที่ผู้ใช้กำหนดเป็นจุดนำบอล

`long_ball` ใช้ค่าเริ่มต้นทดลอง `long_ball_speed=15.8 m/s` และ `long_ball_apex_height=3.8 m` ส่วน `through_ball` ยังคงเลือกวิถีบอลด้วย `pass_type` ได้ เช่น แทงเรียดด้วย `ground` หรือแทงโด่งด้วย `chip`/`long_ball`

Backend ไม่มี Session และ Database หน้าเว็บต้องส่ง State ปัจจุบันมากับแต่ละคำขอ Simulation

