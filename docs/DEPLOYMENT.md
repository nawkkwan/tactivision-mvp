# Deployment: Cloudflare Pages + Azure Container Apps

โครงสร้างที่ใช้มี Frontend แบบ Static บน Cloudflare Pages และ Backend API บน Render

## 1. Deploy Backend บน Render (ทางเลือกสำหรับ Staging)

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

`Backend / Azure deployment` build Docker image ด้วย commit SHA, push เข้า Azure Container Registry และอัปเดต Azure Container App อัตโนมัติเมื่อไฟล์ Backend บน `main` เปลี่ยน นอกจากนี้ยังกด `Run workflow` เพื่อ deploy ด้วยตนเองได้ การยืนยันตัวตนใช้ GitHub OIDC ที่ผูกเฉพาะ branch `main` จึงไม่มี Azure client secret อายุยาวเก็บใน repository

`Backend / production health` ตรวจ Azure API ทุกชั่วโมง โดยตรวจทั้ง `/health` และ `/simulate` พร้อม retry สำหรับช่วงที่ Container App กำลังตื่นจาก scale-to-zero และสามารถกด `Run workflow` เพื่อตรวจทันทีได้

เพิ่ม Repository variable ที่ GitHub > Settings > Secrets and variables > Actions > Variables:

```text
AZURE_API_URL=https://tactivision-api.bravesea-5e18ac68.eastasia.azurecontainerapps.io
```

ตัวแปรนี้เป็น optional; หากไม่ตั้ง workflow จะใช้ Production API ด้านบน จึงไม่ถูกข้ามแบบ workflow รุ่นเดิม

## 4. Azure Container Apps (Production)

หากโมเดล `best.pt` ใช้หน่วยความจำเกินขีดจำกัดของ Render ให้ย้ายเฉพาะ Backend ไป Azure Container Apps แบบ Consumption โดย Frontend ยังคงอยู่บน Cloudflare Pages

จาก repository root รัน:

```powershell
.\scripts\deploy_azure.ps1
```

ค่าเริ่มต้นของสคริปต์คือ `1 vCPU`, RAM `2 GiB`, ขั้นต่ำ `0` replica และสูงสุด `1` replica เพื่อให้ scale-to-zero และควบคุมค่าใช้จ่าย สคริปต์จะพิมพ์ URL ของ API เมื่อ deploy เสร็จ

ตรวจสอบ `https://<azure-fqdn>/health` และทดสอบ `POST /detect` ก่อนแก้ตัวแปร Cloudflare Pages:

```text
VITE_API_URL=https://<azure-fqdn>
```

หลังแก้ตัวแปร ให้ deploy Cloudflare Pages ใหม่หนึ่งครั้ง จากนั้น Render เดิมสามารถหยุดใช้งานได้เมื่อยืนยันว่า Azure ทำงานครบแล้ว

Production API ปัจจุบัน:

```text
https://tactivision-api.bravesea-5e18ac68.eastasia.azurecontainerapps.io
```
