# ฐานงานวิจัยสำหรับ TactiVision

เอกสารนี้สรุปว่างานแต่ละส่วนของระบบควรอ้างอิงหลักฐานใด และแยกสิ่งที่มีอยู่แล้วออกจากสิ่งที่ยังเป็นสมมติฐานของ MVP

## 1. รูปแบบการส่งบอล

### Ground pass

- ข้อมูล Tracking จาก 258 นัดของ Dutch Eredivisie รายงานความเร็วพาสเฉลี่ยประมาณ 11.67–11.87 m/s และความเร็วสูงของพาสในลำดับการบุกประมาณ 15.36–16.41 m/s
- การจำลองแมตช์ในนักเตะ Academy รายงานความเร็วพาส 13.0 ± 0.5 m/s ในครึ่งแรกและ 12.2 ± 0.5 m/s ในครึ่งหลัง
- งานด้าน pass availability ระบุว่าบอลช้าลงจากแรงต้านอากาศและพื้น โดยช่วงลอย/ไถลกับช่วงกลิ้งมี dynamics ต่างกัน และเสนอให้เรียนรู้ฟังก์ชันเวลาเดินทางจาก Tracking Data

ข้อเสนอสำหรับ MVP:

- Controlled ground: ค่ากลางทดลอง 12.5 m/s
- Fast/driven ground: ค่ากลางทดลอง 16.0 m/s
- เมื่อมีคลิป Tracking จริง ให้เปลี่ยนจากความเร็วคงที่เป็นโมเดลสองช่วง หรือเรียนรู้ `time(distance, initial_speed, launch_angle)` จากข้อมูล

### Chip / lofted pass

- การทดลองในนักเตะเยาวชนระดับ Elite รายงาน chip kick ประมาณ 64–66 km/h หรือ 17.8–18.3 m/s
- งานวิเคราะห์ long pass หนึ่งชิ้นรายงานความเร็วหลังเตะประมาณ 15.69–15.90 m/s และความสูงประมาณ 3.76–3.87 m

ข้อควรระวัง:

- ความเร็วหลังเตะเป็นขนาดเวกเตอร์สามมิติ ไม่เท่ากับความเร็วแนวราบคงที่
- สมการ `height = 4 × apex × r × (1-r)` ใช้เป็น approximation ของ MVP เท่านั้น
- รุ่นถัดไปควรใช้ projectile motion, drag, spin, bounce และการสอบเทียบจากคลิปจริง

### Curved pass

- งาน motion capture ของลูกโค้งระยะมากกว่า 20 เมตรพบว่า Magnus force ทำให้บอลเบนด้านข้าง และแรงด้านข้างลดลงระหว่างทางเมื่อความเร็วบอลลดลง
- ตัวอย่างการทดลองที่ความเร็วต้นประมาณ 19 m/s เบนด้านข้างมากกว่า 0.7 เมตรภายใน 1 วินาที

ข้อเสนอสำหรับ MVP:

- ใช้ Quadratic Bézier เป็นเส้นทางประมาณเพื่อทดลอง UI และการตัดบอล
- ต้องติดป้ายว่าไม่ใช่ Magnus physics
- หากต้องการผลเชิงฟิสิกส์ ต้องมี initial velocity, spin axis, spin rate, drag coefficient และ Magnus coefficient

### Through ball

Through ball ไม่ใช่วิถีบอลชนิดเดียวกับ ground/chip/curve แต่เป็นการเลือกเป้าหมายอนาคตของผู้รับ โดยหน้า MVP ให้ผู้ใช้เลือกผู้วิ่งและคลิกจุดนำบอลเอง

- งาน pass availability คำนวณว่าผู้รับจะไปถึงจุดบนแนวบอลทันหรือไม่ แล้วรวมโอกาสที่กองหลังจะตัดบอลก่อนจุดเหล่านั้น
- ระบบจึงควรแยก `trajectory_type` ออกจาก `target_type`
- การทำนายจุดวิ่งอัตโนมัติ (`target_type=lead`) ต้องใช้ velocity vector ของผู้เล่นจากหลายเฟรม; ในภาพนิ่งระบบจึงไม่เดาทิศทางเอง และสมมติการวิ่งตรงไปยังจุดที่ผู้ใช้คลิก

### Long aerial / เปิดยาว

- MVP เพิ่ม `long_ball` เป็นวิถีบอลโด่งพาราโบลาแยกจาก `chip` ด้วยค่าตั้งต้นทดลอง 15.8 m/s และ apex 3.8 m จากรายงานกลุ่มตัวอย่างหนึ่งชุด (Ashidiq et al., 2024)
- ความเร็วที่รายงานเป็นความเร็วหลังปะทะ ไม่ใช่ความเร็วแนวราบเฉลี่ยตลอดทาง จึงเป็นค่าทดลองสำหรับเปรียบเทียบใน UI เท่านั้น ไม่ใช่โมเดลฟิสิกส์หรือค่ามาตรฐาน
- ผู้ใช้ยังเลือกจุดตกของบอลเอง; ระบบประเมินการตัดบอลตามแนวเส้นตรงบนพื้นสนามและระดับสูงตามพาราโบลา แต่ยังไม่จำลองลม แรงต้าน สปิน การกระดอน หรือตำแหน่งรับบอล 3 มิติ

## 2. การเคลื่อนที่และการตัดบอล

งาน *Who can receive the pass?* สนับสนุนหลักการสำคัญของระบบ:

1. ประเมินว่าผู้รับไปถึงตำแหน่งบนแนวบอลทันหรือไม่
2. ประเมินว่ากองหลังตัดบอลก่อนตำแหน่งรับได้หรือไม่
3. รวมผลตลอดแนวบอลเป็นค่าความสำเร็จของพาส

ระบบปัจจุบันใช้ time-to-arrival แบบง่าย:

```text
arrival_time = reaction_time + max(0, distance - reach_radius) / player_speed
```

และให้กองหลังผ่านเงื่อนไขทั้งการถึงบอลและการชนะเพื่อนร่วมทีม:

```text
effective_margin = max(defender_time - ball_time,
                       defender_time - fastest_teammate_time)
```

ข้อจำกัดคือยังไม่รวม acceleration, orientation, body pose, maximum speed รายบุคคล และความไม่แน่นอนจาก Detection

## 3. Automatic Calibration

### หลักฐานจากงานวิจัย

- Homayounfar et al. ใช้ semantic cues ของพื้นสนาม เส้น และวงกลม เพื่อทำ field localization อัตโนมัติจากภาพ broadcast เพียงภาพเดียว
- SoccerNet Calibration แบ่งงานเป็น pitch marking/goal-post localization และ camera calibration โดยมีภาพ 20,028 ภาพจาก 500 นัด
- TVCalib ใช้ segment correspondences และลด segment reprojection error เพื่อประมาณ camera pose, focal length และ distortion โดยไม่ต้องพึ่งจุดตัด 4 จุดจากผู้ใช้ทุกภาพ
- งาน Flexible Intersection Selection and Refinement ใช้ตำแหน่งและความยาวเส้นสนามที่ทราบล่วงหน้า พร้อมปรับตำแหน่งจุดตัดเพื่อเพิ่มความแม่นยำของ Homography

### Flow ที่ควรใช้

```text
อัปโหลดภาพ
  → ตรวจ Pitch Marking แบบ Semantic Segmentation
  → จำแนกเส้น เช่น touchline, halfway, penalty box, circle, goal line
  → จับคู่ Segment กับแม่แบบสนาม 105 × 68 เมตร
  → ประมาณ Camera/Homography
  → ฉาย Grid กลับลงภาพ
  → วัด Segment Reprojection Error และความสมเหตุสมผล
  → Auto accept หรือ Manual fallback
```

### เกณฑ์ Engineering ที่เสนอ

คะแนน Auto Calibration ควรรวมอย่างน้อย:

- จำนวนและความหลากหลายของเส้นที่ตรวจพบ
- Inlier ratio ของ RANSAC หรือ optimizer
- Segment reprojection error
- สัดส่วน Grid ที่สอดคล้องกับเส้นจริง
- ความสมเหตุสมผลของ camera pose และพิกัดผู้เล่นหลังแปลง

Flow สำหรับผู้ใช้:

- `confidence ≥ 0.80`: ใช้อัตโนมัติและแสดง Grid ให้ตรวจได้
- `0.60–0.79`: แสดง Preview ให้ผู้ใช้กดยืนยันหรือแก้จุดบางจุด
- `< 0.60`: เปิด Manual Calibration อย่างน้อย 4 จุด
- ถ้าพิกัดผู้เล่นจำนวนมากหลุดสนาม หรือ reprojection error เกินเกณฑ์ ให้ลดระดับเป็น Manual แม้ confidence จากโมเดลสูง

ตัวเลข threshold ข้างต้นเป็นเกณฑ์ Engineering เริ่มต้น ต้องสอบเทียบใหม่กับ Validation Set ของภาพที่จะใช้งานจริง

### สถานะของโค้ดปัจจุบัน

ระบบปัจจุบันทำ Auto-first แล้ว โดยใช้ HSV green mask, contour, Canny/Hough lines และรับผลเมื่อ confidence อย่างน้อย 0.70 จากนั้นจึง fallback ไป Manual

ข้อจำกัดสำคัญคือ heuristic ปัจจุบันสมมติว่ารูปสี่เหลี่ยมสีเขียวที่ใหญ่ที่สุดคือสนามเต็ม 105 × 68 เมตร จึงเหมาะกับภาพที่เห็นขอบสนามครบหรือฉากตัวอย่าง แต่ไม่ควรถือว่าแม่นยำสำหรับ broadcast view ที่เห็นเพียงบางส่วนของสนาม ต้องเปลี่ยนเป็น line-class segmentation และ pitch-template fitting ก่อนใช้กับผลวิจัยจริง

## 4. แหล่งอ้างอิงหลัก

- Forcher, L. et al. (2021). *The “Hockey” Assist Makes the Difference*. DOI: https://doi.org/10.3390/e23121607
- Russell, M. et al. (2011). *The Effects of Fatigue on Soccer Skills Performed During a Soccer Match Simulation*. DOI: https://doi.org/10.1123/ijspp.6.2.221
- McLean, B. D. & Tumilty, D. M. (1993). *Left-right asymmetry in two types of soccer kick*. DOI: https://doi.org/10.1136/bjsm.27.4.260
- Brefeld, U. et al. (2022). *Who can receive the pass? A computational model for quantifying availability in soccer*. DOI: https://doi.org/10.1007/s10618-022-00827-2
- Hong, S. et al. (2020). *Measurements of the Flight Trajectory of a Spinning Soccer Ball and the Magnus Force Acting on It*. https://www.mdpi.com/2504-3900/49/1/88
- Homayounfar, N. et al. (2017). *Sports Field Localization via Deep Structured Models*. https://openaccess.thecvf.com/content_cvpr_2017/html/Homayounfar_Sports_Field_Localization_CVPR_2017_paper.html
- Theiner, J. & Ewerth, R. (2023). *TVCalib: Camera Calibration for Sports Field Registration in Soccer*. https://openaccess.thecvf.com/content/WACV2023/html/Theiner_TVCalib_Camera_Calibration_for_Sports_Field_Registration_in_Soccer_WACV_2023_paper.html
- SoccerNet Camera Calibration task and baseline: https://www.soccer-net.org/tasks/camera-calibration

