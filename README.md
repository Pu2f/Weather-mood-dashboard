# Weather-mood-dashboard

Dashboard สำหรับดูความสัมพันธ์ระหว่างอากาศกับ mood/productivity พร้อมฟอร์มบันทึกประจำวัน

## Features

- Dashboard แสดงผลสถิติและกราฟความสัมพันธ์ระหว่างสภาพอากาศกับ productivity
- มีกราฟอย่างน้อย 3 กราฟ (Line, Scatter + Regression, Bar)
- มีฟอร์มบันทึกข้อมูลรายวัน (mood / productivity)
- มี interactive filters (ช่วงวัน, ตัวแปรแกน X, เกณฑ์ฝนตก) และอัปเดตผลแบบสอดคล้องกันทั้งหน้า

## Requirements

- Python 3.10+
- Node.js 20+

## Setup

1. ติดตั้ง Python dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. ติดตั้ง frontend dependencies

```bash
npm install
```

3. ตั้งค่า environment

```bash
cp .env.example .env
```

จากนั้นแก้ค่า `FLASK_SECRET_KEY` ในไฟล์ `.env` ก่อนใช้งานจริง

## Run (Development)

เปิด 2 terminal:

Terminal A (watch CSS)

```bash
npm run tw:watch

```

Terminal B (run Flask)

```bash
source venv/bin/activate
set -a && source .env && set +a
python3 app.py
```

เข้าใช้งานที่ `http://127.0.0.1:5000`

## Build CSS (one-time)

```bash
npm run tw:build
```
