# วิธีทำงานร่วมกัน

## เริ่มต้นบนเครื่องของสมาชิกทีม

```powershell
git clone <repository-url>
cd tactivision-mvp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements-dev.txt
cd frontend
npm install
```

เปิด Backend จากโฟลเดอร์หลัก:

```powershell
uvicorn backend.app.main:app --reload --port 8000
```

เปิด Frontend ในอีกหน้าต่างหนึ่ง:

```powershell
cd frontend
npm run dev
```

## ขั้นตอนส่งงาน

สมาชิกแต่ละคนสร้าง branch ของตนเองจาก `main` และตั้งชื่อให้สื่อถึงงาน เช่น:

```powershell
git switch main
git pull
git switch -c feature/team-classification
```

เมื่อทำเสร็จให้ commit, push และเปิด Pull Request เข้า `main` เพื่อให้สมาชิกอีกคนตรวจสอบก่อนรวมงาน

```powershell
git add <files>
git commit -m "Improve team classification"
git push -u origin feature/team-classification
```

ไม่ควร commit `best.pt`, `.venv`, `node_modules`, ภาพที่ไม่มีสิทธิ์เผยแพร่ หรือไฟล์ที่มี secret ลง repository

## จุดเชื่อมงานสำหรับสมาชิกคนที่ 3

- Team Classification: `backend/app/services/team_classifier.py`
- API ตรวจจับและแบ่งทีม: `backend/app/services/detection.py`
- รูปแบบข้อมูล API: `backend/app/schemas.py`
- หน้าตรวจและแก้ทีม: `frontend/src/components/DetectionReview.tsx`
- เอกสาร API: `docs/API.md`

หากเปลี่ยนรูปแบบข้อมูล ให้แก้ Backend schema, Frontend type และเอกสาร API ใน Pull Request เดียวกัน เพื่อป้องกันสองฝั่งใช้ข้อมูลคนละรูปแบบ

## ตรวจงานก่อนเปิด Pull Request

จากโฟลเดอร์หลัก:

```powershell
.\.venv\Scripts\python.exe -m pytest
cd frontend
npm run build
```
