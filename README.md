# TactiVision MVP

TactiVision เป็นเว็บทดลองวิเคราะห์ **Pass Interception Risk** จากภาพนิ่งฟุตบอล ระบบตรวจตำแหน่งผู้เล่น แบ่งทีม แปลงพิกัดภาพเป็นพิกัดสนาม และเปรียบเทียบลูกเรียดหรือลูกชิพไปยังผู้รับหรือพื้นที่ว่างได้สูงสุด 3 ทางเลือก ผลลัพธ์แสดงดัชนีความเสี่ยง 0–100% จากสมมติฐานของแบบจำลอง ไม่ใช่ความน่าจะเป็นจากข้อมูลการแข่งขันจริง

## เริ่มใช้งานด้วย Docker

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

อ่านรายละเอียด API ที่ [docs/API.md](docs/API.md) และสมมติฐานการจำลองที่ [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md)

อ่านขั้นตอน Deploy Frontend บน Cloudflare Pages, Backend บน Render และตั้ง GitHub Actions ที่ [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## ทำงานร่วมกันบน GitHub

อ่านขั้นตอนแยก branch, ส่ง Pull Request และจุดเชื่อมงานแต่ละโมดูลที่ [docs/COLLABORATION.md](docs/COLLABORATION.md)

