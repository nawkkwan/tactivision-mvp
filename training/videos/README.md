# Videos

วางไฟล์วิดีโอฟุตบอลสำหรับตัดภาพไว้ในโฟลเดอร์นี้

ชื่อไฟล์ไม่จำเป็นต้องตายตัว แต่แนะนำให้ใช้ภาษาอังกฤษ ไม่มีช่องว่าง เช่น:

- `train-match.mp4`
- `test-match.mp4`
- `bg-cup-u19.mp4`

เวลารันให้ใส่ชื่อให้ตรงกับไฟล์จริง เช่น:

```powershell
python training/extract_frames.py --video "training/videos/bg-cup-u19.mp4" --every-seconds 30
```

ไฟล์วิดีโอในโฟลเดอร์นี้จะไม่ถูก Commit ขึ้น Git
