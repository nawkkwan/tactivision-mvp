# ร่าง Pull Request

ยังไม่เปิด PR บน GitHub และยังไม่ push branch ไฟล์นี้เตรียมข้อความไว้สำหรับส่งภายหลัง

## Title

feat(training): add audited round-two fine-tuning and detector evaluation

## Branches

- Base: `main`
- Head: `codex/detection-round2`
- แยกจากงาน Backend โมเดลบอลใน `codex/ball-detection` ไม่พ่วง commit ของ branch นั้น

## Summary

เพิ่ม workflow ของงาน Detection ตั้งแต่ตรวจ Dataset hard cases เสื้อเหลือง/ดำ
เตรียมชุด Fine-tune บน Colab ไปจนถึงเปรียบเทียบโมเดลเดิม/ใหม่และตรวจภาพ candidate Test
PR นี้เป็นเครื่องมือทดลอง, tests และเอกสาร ไม่ใช่การเปลี่ยนโมเดลบนระบบจริง

## Changes

1. เตรียม Dataset v3 พร้อม checksum และ audit trail
   - คืน Train/Validation เดิมตามชุดที่ใช้จริง ไม่ใช้ split ใน Roboflow มาทับ
   - Train 141 / Validation 71 / Test เดิม 30 ภาพ
   - ย้าย 35 ภาพใหม่ที่ผู้ใช้ยืนยันจาก Test ไป Validation
   - แปลงเฉพาะ polygon บอลที่ผู้ใช้อนุมัติเป็นกรอบขอบเขตเดิม ไม่ย้ายวัตถุหรือเปลี่ยนคลาส
   - ปฏิเสธ checksum ที่เปลี่ยนและ ZIP/Label ที่ไม่ปลอดภัยหรือผิดรูปแบบ
2. เพิ่มการเทียบโมเดลรวมเดิมกับโมเดลบอลเฉพาะบน Validation 36 ภาพ
   - ค่าทดลองเดียวกันและจับคู่ Label แบบหนึ่งต่อหนึ่ง
   - แสดงข้อแลกเปลี่ยน Precision/Recall ไม่สรุปว่าโมเดลบอลเฉพาะดีกว่าเสมอ
3. เพิ่ม Notebook Fine-tune รอบสองและเครื่องมือสร้าง input bundle
   - Train 141 / Validation 71; ไม่ใส่ภาพหรือ Label Test ใน training bundle
   - เริ่มจากน้ำหนักรอบแรกที่ตรึง SHA-256 ไม่ resume optimizer
   - สูงสุด 40 epochs, patience 10, AdamW, lr0 0.0001, imgsz 1280, batch 1
   - เปรียบเทียบ Validation เดิม 36 / ใหม่ 35 / รวม 71 และส่งออกโมเดลพร้อมรายงาน
4. เพิ่มการประเมินบนภาพต้นฉบับ candidate/test ครบ 30 ภาพ
   - ตรวจชื่อภาพ ขนาด ความใกล้เคียงกับภาพอ้างอิง และ checksum ของ Label ก่อนใช้
   - เทียบโมเดลรอบแรก/รอบสองด้วยค่าตั้งเดียวกัน ไม่เทรนหรือเลือกค่า conf จาก Test
   - เก็บภาพ Label / รอบแรก / รอบสอง ครบทุกภาพ พร้อมรายงานรายภาพ
5. เพิ่ม regression tests และเอกสารผลทดลอง/การส่งต่องาน

## Results

Validation รวม 71 ภาพ: mAP50–95 จาก **0.4828 → 0.6879**
ใช้ Validation นี้เลือก checkpoint จึงไม่ใช่คะแนน Test อิสระ

candidate/test 30 ภาพ:

| Metric | Round 1 | Round 2 |
|---|---:|---:|
| mAP50 | 0.5506 | 0.7984 |
| mAP50–95 | 0.4019 | 0.6082 |

ที่ conf คน 0.50 / บอล 0.15 เทียบกับ Label ที่ตรึงไว้:

| Class | TP ก่อน → หลัง | FP ก่อน → หลัง | FN ก่อน → หลัง |
|---|---:|---:|---:|
| player | 219 → 261 | 50 → 21 | 59 → 17 |
| goalkeeper | 1 → 8 | 73 → 6 | 16 → 9 |
| referee | 24 → 23 | 25 → 2 | 3 → 4 |
| ball | 25 → 24 | 26 → 8 | 12 → 13 |

รอบสองดีขึ้นโดยรวม แต่ไม่ดีขึ้นทุกด้าน บอลและผู้ตัดสินจับถูกน้อยลงอย่างละ 1 กรอบที่ค่า conf เดิม
ผู้รักษาประตูยังตรวจตกหล่น และภาพมุมใกล้บางภาพยังไม่มีกรอบผ่านค่า conf ใช้งาน

## Testing

ผ่านชุดทดสอบทั้งหมดใน `tests/`: **82 passed** บน branch นี้

```powershell
.venv\Scripts\python.exe -m pytest tests -q --basetemp training/artifacts/pytest-round2-tests-final
```

ตรวจ Notebook ไม่มี saved outputs/execution counts และไม่พบคีย์ลับจากการตรวจรูปแบบเบื้องต้น
ตรวจไฟล์ที่จะ commit ไม่ให้มี Dataset, ภาพผลตรวจ, ZIP, weights, cache หรือไฟล์ environment

## Scope / caveats

- ไม่เปลี่ยน Backend, Frontend, API contract หรือค่าเริ่มต้น inference ของ `main`
- ไม่รวมโมเดล `.pt`, Dataset หรือภาพผลตรวจใน Git ส่งไฟล์เหล่านี้แยกให้ทีม
- รายงาน Test ใช้แมตช์เดิม 30 ภาพที่เคยประเมินแล้ว ไม่ใช่แมตช์อิสระใหม่
- ภาพ candidate ต้นฉบับกับ Roboflow มี JPEG encoding ต่างกัน จึงไม่เทียบคะแนนเก่าคนละ runtime ตรง ๆ
- คะแนนขึ้นกับคุณภาพ Label; ยังไม่ได้ยืนยันความถูกต้องทุกกรอบด้วยตา
- รายงานนี้ไม่รวมโมเดลบอลเฉพาะ ตัวแยกทีม หรือ pipeline เว็บ และไม่ใช่ benchmark API
- ต้องมี Dataset/โมเดลตามเอกสารในเครื่องจึงรันงานทดลองจริงซ้ำได้; unit tests ใช้ fixture

## Handoff

- ขวาน: รับ `best_round2.pt` แยกจาก Git ทดสอบ Backend โดยเก็บโมเดลเดิมไว้
  ตรึง Class ID `0 ball / 1 goalkeeper / 2 player / 3 referee`
  ค่าใช้งานจาก Validation คือคน 0.50 / บอล 0.15 โดยกรองแยกคลาส
- นที: ใช้ภาพต้นฉบับและกรอบ player ที่ผ่าน confidence filter ไปแยกทีมต่อ
  ผู้รักษาประตูต้องจัดทีมแยก และไม่ต้องเทรนตัวตรวจนักเตะซ้ำเพื่อเริ่มเชื่อมงาน
- หากเปิดโมเดลบอลแยกใน branch อื่น ผลบอลบนเว็บจะไม่ใช่โมเดลรวมรอบสองที่รายงานนี้ประเมิน
- การแทนโมเดลจริงและการ deploy ให้เป็นงานรวมระบบแยกหลังทดสอบร่วมกับทีม

## References

- `training/README.md`
- `training/BALL_COMPARISON_RESULTS.md`
- `training/ROUND2_RESULTS.md`
- `training/CANDIDATE_TEST_ROUND2_RESULTS.md`
