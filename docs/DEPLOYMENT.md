# Deployment: Cloudflare Pages + Render

โครงสร้างที่ใช้มี Frontend แบบ Static บน Cloudflare Pages และ Backend API บน Render

## 1. Deploy Backend บน Render

สร้าง Blueprint จาก `render.yaml` ใน repository นี้ แล้วกำหนดค่าที่ Render ขอระหว่างสร้างบริการ:

- `CORS_ORIGINS`: URL Production ของ Cloudflare Pages เช่น `https://tactivision-mvp.pages.dev`
- `CORS_ORIGIN_REGEX`: Regex สำหรับ Preview URL เช่น `^https://([a-z0-9-]+\.)?tactivision-mvp\.pages\.dev$`

บริการใช้ `/health` เป็น Health Check และ Docker image จะดาวน์โหลด `yolo11n.pt` ระหว่าง Build เพื่อใช้เป็นโมเดล Staging โดยไม่ commit ไฟล์ `.pt` ลง Git

หลัง Deploy ให้ทดสอบ:

- `https://<render-service>.onrender.com/health`
- `https://<render-service>.onrender.com/docs`

เมื่อ `best.pt` พร้อม ให้ทดสอบบนเครื่องก่อน แล้วจัดเก็บเป็น artifact ที่มี version และ checksum จากนั้นสร้าง Production image ที่บรรจุโมเดลรุ่นนั้น โดยยังคง `backend/models/*.pt` ไว้ใน `.gitignore`

## 2. Deploy Frontend บน Cloudflare Pages

เชื่อม GitHub repository กับ Cloudflare Pages แล้วตั้งค่า:

- Production branch: `main`
- Preview branches: `All non-Production branches`
- Framework preset: `React (Vite)`
- Root directory: `frontend`
- Build command: `npm run build`
- Build output directory: `dist`

Environment variable สำหรับทั้ง Production และ Preview:

```text
VITE_API_URL=https://<render-service>.onrender.com
```

Production deployment จะมาจาก `main` ส่วน branch และ Pull Request อื่นจะได้ Preview URL แยกสำหรับให้สมาชิกทีมทดสอบก่อน merge

## 3. GitHub Actions

`CI` ทำงานเมื่อเปิด Pull Request หรือ push เข้า `main`:

- รัน Backend tests
- Build Frontend

ตั้ง Branch Protection ของ `main` ให้ต้องผ่าน `Backend tests` และ `Frontend build` ก่อน merge

`Production API health` ตรวจ Render API ทุกชั่วโมง โดยตรวจทั้ง `/health` และ `/simulate` พร้อม retry สำหรับช่วงที่ Render Free กำลังตื่นจาก idle

เพิ่ม Repository variable ที่ GitHub > Settings > Secrets and variables > Actions > Variables:

```text
RENDER_API_URL=https://<render-service>.onrender.com
```

หากยังไม่ตั้งตัวแปรนี้ งานตรวจ API จะถูกข้าม และสามารถกด Run workflow เองได้จากหน้า Actions หลังตั้งค่าแล้ว
