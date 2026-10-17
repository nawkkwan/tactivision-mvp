# ข้อมูลอ้างอิงความเร็วการส่งบอล

เอกสารนี้รวบรวมค่าจากงานวิจัยเพื่อใช้ปรับ Pass Interception Simulation หลังเชื่อมโมเดลตรวจจับจริงแล้ว ข้อมูลชุดนี้ยังไม่เปลี่ยนค่าเริ่มต้นของระบบ เพราะ `ball_speed` และ `chip_speed` ปัจจุบันแทนความเร็วคงที่ตลอดเส้นทาง ขณะที่งานทดลองบางชิ้นรายงานความเร็วทันทีหลังเตะหรือขนาดความเร็วสามมิติ ซึ่งนำมาแทนกันตรง ๆ ไม่ได้

## หลักฐานที่นำมาใช้

| บริบท | ค่าที่รายงาน | การตีความสำหรับระบบ |
| --- | ---: | --- |
| การจ่ายในเกมอาชีพ 258 นัด Eredivisie ฤดูกาล 2018/19 | ความเร็วเฉลี่ย 11.67 และ 11.87 m/s; ค่าเฉลี่ยของความเร็วสูงสุด 15.36 และ 15.42 m/s; พาสแรกของลำดับการบุก 15.55 และ 16.41 m/s | เหมาะเป็นฐานสำหรับพาสปกติประมาณ 12 m/s และพาสเร็วประมาณ 16 m/s |
| การทดสอบพาสระหว่าง Soccer Match Simulation ในนักเตะ Academy 15 คน | ครึ่งแรก 13.0 ± 0.5 m/s; ครึ่งหลัง 12.2 ± 0.5 m/s | สนับสนุนช่วงพาสควบคุม 12–13 m/s และแสดงว่าความล้าส่งผลต่อความเร็ว |
| Low drive และ chip kick ในนักเตะเยาวชนระดับ Elite 12 คน | Chip ขาขวา 66 ± 5 km/h และขาซ้าย 64 ± 5 km/h หรือประมาณ 18.3 ± 1.4 และ 17.8 ± 1.4 m/s | ใช้เป็นหลักฐานของความเร็วออกจากเท้าสำหรับลูกชิพ ไม่ควรใช้เป็นความเร็วแนวราบคงที่โดยตรง |
| Long pass ในงานวิเคราะห์ชีวกลศาสตร์ | ความเร็วหลังปะทะประมาณ 15.69–15.90 m/s, ความสูงประมาณ 3.76–3.87 m, ระยะประมาณ 23.17–23.53 m | ใช้เป็นค่าตั้งต้นทดลองของลูกยาวลอย หากเปลี่ยนระบบเป็นวิถีแบบ ballistic |

## ชุดค่าที่เสนอสำหรับการทดลองภายหลัง

| Profile | ค่ากลาง | ช่วงทดลอง | สถานะ |
| --- | ---: | ---: | --- |
| Controlled ground pass | 12.5 m/s | 11–14 m/s | ใช้กับโมเดลความเร็วคงที่ได้ |
| Fast/driven ground pass | 16.0 m/s | 15–17 m/s | ใช้กับโมเดลความเร็วคงที่ได้ แต่ไม่ใช่การยิงเต็มแรง |
| Chip launch speed | 18.0 m/s | 16–20 m/s | ต้องแยกความเร็วแนวราบและแนวดิ่งก่อนใช้จริง |
| Long aerial experimental | 15.8 m/s, apex 3.8 m | รอสอบเทียบจากวิดีโอ | เป็นเพียงค่าทดลองจากงานหนึ่งชิ้น |

## ข้อจำกัดและสิ่งที่ต้องทำเมื่อโมเดลพร้อม

1. ความเร็วเฉลี่ยจาก Tracking คือ `ระยะพาส ÷ เวลาจากเตะถึงรับ` จึงเหมาะกับสูตรเวลาบอลปัจจุบันกว่าความเร็วทันทีหลังเตะ
2. ลูกเรียดควรมีแรงต้านแบบช่วงไถลและช่วงกลิ้ง แทนความเร็วคงที่ หากต้องการความแม่นยำสูงขึ้น
3. ลูกชิพควรแยกความเร็วต้นแกนราบ/แกนดิ่ง ใช้แรงโน้มถ่วง และพิจารณาจังหวะตกหรือกระดอน
4. ต้องวัดเวลาบอลจากคลิปจริงหลายระยะ แล้วสอบเทียบแยกตามชนิดพาส ระยะ และระดับการแข่งขัน
5. ห้ามนำความเร็วการยิงประตู 20–35 m/s มาเป็นค่าเริ่มต้นของการส่งบอล เพราะวัตถุประสงค์และข้อจำกัดด้านความแม่นยำต่างกัน

## แหล่งอ้างอิง

- Forcher, L. et al. (2021). *The “Hockey” Assist Makes the Difference—Validation of a Defensive Disruptiveness Model to Evaluate Passing Sequences in Elite Soccer*. Entropy, 23(12), 1607. DOI: https://doi.org/10.3390/e23121607
- Russell, M., Benton, D., & Kingsley, M. (2011). *The Effects of Fatigue on Soccer Skills Performed During a Soccer Match Simulation*. International Journal of Sports Physiology and Performance, 6(2), 221–233. DOI: https://doi.org/10.1123/ijspp.6.2.221
- McLean, B. D., & Tumilty, D. M. (1993). *Left-right asymmetry in two types of soccer kick*. British Journal of Sports Medicine, 27(4), 260–262. DOI: https://doi.org/10.1136/bjsm.27.4.260
- Ashidiq, M. O. et al. (2024). *The Difference of the Effects of Regular Strength and Core Strength Training Programs on the Biomechanics of Football Long Pass Judging from Eye-Foot Coordination*. Revista Iberoamericana de Psicología del Ejercicio y el Deporte, 19(3), 303–312. https://www.riped-online.com/articles/the-difference-of-the-effects-of-regular-strength-and-core-strength-training-programs-on-the-biomechanics-of-football-long-pass-ju-108054.html

