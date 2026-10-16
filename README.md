# TactiVision MVP

TactiVision เป็นเว็บทดลองวิเคราะห์ **Pass Interception Risk** จากภาพนิ่งฟุตบอล ระบบตรวจตำแหน่งผู้เล่น แบ่งทีม แปลงพิกัดภาพเป็นพิกัดสนาม และเปรียบเทียบลูกเรียดหรือลูกชิพไปยังผู้รับหรือพื้นที่ว่างได้สูงสุด 3 ทางเลือก ผลลัพธ์แสดงดัชนีความเสี่ยง 0–100% จากสมมติฐานของแบบจำลอง ไม่ใช่ความน่าจะเป็นจากข้อมูลการแข่งขันจริง

## เริ่มใช้งานด้วย Docker

ดาวน์โหลดโมเดลบอลลงเครื่องก่อนตามหัวข้อ “โมเดลตรวจบอลแยก” ด้านล่าง เพราะ Compose
mount โฟลเดอร์ `backend/models` จากเครื่องทับโฟลเดอร์ใน image

```powershell
docker compose up --build
```

จากนั้นเปิด `http://localhost:4173` และตรวจ API ได้ที่ `http://localhost:8000/docs`

ครั้งแรกที่ใช้ Generic YOLO อาจต้องดาวน์โหลดน้ำหนัก `yolo11n.pt` จึงต้องเชื่อมต่ออินเทอร์เน็ต หากยังไม่พร้อมใช้โมเดล สามารถกด “ลองฉากตัวอย่าง” เพื่อทดสอบ Calibration, การเลือกผู้เล่น และ Simulation ได้โดยข้อมูลตัวอย่างจะมีป้ายระบุชัดเจน

## เริ่มใช้งานแบบ Development

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements-dev.txt
uvicorn backend.app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

เปิด `http://localhost:5173`

## ใช้โมเดล Fine-tuned

วางไฟล์โมเดลไว้ที่ `backend/models/best.pt` แล้วกำหนด:

```powershell
$env:MODEL_PATH = "backend/models/best.pt"
```

หากไม่กำหนด ระบบใช้ `yolo11n.pt` และแมปคลาส `person` เป็น `player`, `sports ball` เป็น `ball` ชั่วคราว

## โมเดลตรวจบอลแยก

ระบบรองรับสองโมเดลในคำขอ `/detect` เดียว: โมเดลหลักตรวจคน ส่วนโมเดลเฉพาะตรวจบอล
โดยใช้ weights สำเร็จรูปจาก [Roboflow Sports](https://github.com/roboflow/sports/blob/main/examples/soccer/setup.sh)
ไม่ใช่การ Fine-tune บอลเพิ่ม และไม่เปลี่ยนไฟล์ `best.pt` ของเรา

หลังติดตั้ง requirements แล้ว รันครั้งเดียว:

```powershell
python -m backend.app.download_ball_model
$env:MODEL_PATH = "backend/models/best.pt"
$env:BALL_MODEL_PATH = "backend/models/football-ball-detection.pt"
$env:DETECTION_CONFIDENCE = "0.25"
$env:BALL_CONFIDENCE = "0.15"
$env:DETECTION_IMGSZ = "1280"
uvicorn backend.app.main:app --reload --port 8000
```

คำสั่งดาวน์โหลดตรวจ SHA-256 ของไฟล์ และไม่เขียนทับไฟล์เดิมที่ checksum ไม่ตรง
ไฟล์ `.pt` ไม่ถูกเก็บใน Git; Docker build ดาวน์โหลดไฟล์ที่ตรวจ checksum แล้วไว้ใน image เช่นกัน

ผลคนและบอลถูกรวมเป็น JSON แบบเดิม จึงไม่ต้องเปลี่ยน API ของนทีหรือ Frontend
เมื่อโมเดลบอลทำงานสำเร็จ จะใช้เฉพาะกรอบบอลจากโมเดลนี้ ไม่รวมกรอบบอลจากโมเดลหลักซ้ำ
หากโมเดลบอลหายหรือทำงานผิดพลาด จะใช้ผลบอลจากโมเดลหลักแทน ตรวจแหล่งที่ใช้งานจริงได้ที่
`GET /health` → `modules.ball_detection` (`lazy`, `ready`, `fallback`, `disabled`)

ค่า conf นี้เป็นค่าเริ่มต้น ยังไม่ได้เลือกจากการประเมิน Validation ทั้งชุด
รอบนี้ตรวจภาพเต็มที่ 1280 ไม่ใช่การตัดภาพเป็น tiles แบบตัวอย่างวิดีโอใน Sports
จึงยังอาจพลาดบอลหรือเจอบอลหลอกหลายจุดได้ ผู้ใช้ยังต้องเลือกคนถือบอลเอง
โมเดลทั้งสองโหลดค้างไว้และใช้ RAM เพิ่ม: ทดลองบน CPU กับภาพ Validation หนึ่งภาพ
ใช้ประมาณ 1.5 GiB เฉพาะ detector (ยังไม่รวม SigLIP); ต้องวัด RAM ของ pipeline เต็มก่อน Deploy
และไม่เรียกตรวจจับซ้ำเมื่อเปลี่ยนผู้รับบอล

อ่านรายละเอียด API ที่ [docs/API.md](docs/API.md) และสมมติฐานการจำลองที่ [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md)

อ่านหลักฐานและค่าความเร็วพาสที่เตรียมไว้สำหรับการสอบเทียบที่ [docs/PASS_SPEED_RESEARCH.md](docs/PASS_SPEED_RESEARCH.md)

อ่านฐานงานวิจัยของรูปแบบพาส การตัดบอล และ Automatic Calibration ที่ [docs/RESEARCH_FOUNDATIONS.md](docs/RESEARCH_FOUNDATIONS.md)

อ่านขั้นตอน Deploy Frontend บน Cloudflare Pages, Backend บน Render และตั้ง GitHub Actions ที่ [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## ทำงานร่วมกันบน GitHub

อ่านขั้นตอนแยก branch, ส่ง Pull Request และจุดเชื่อมงานแต่ละโมดูลที่ [docs/COLLABORATION.md](docs/COLLABORATION.md)

