# Legal document sources

ไฟล์ PDF ในโฟลเดอร์นี้เป็น snapshot ที่ดาวน์โหลดเมื่อ 4 กันยายน 2569 (ค.ศ. 2026) เพื่อใช้กับ demo นี้ ไม่ควรถือว่าเป็นฉบับล่าสุดตลอดกาล เพราะกฎหมายอาจมีการแก้ไขภายหลัง

## ประมวลกฎหมายอาญา — ไม่ใช้ใน production index

- Local file: `penal_code_snapshot.pdf`
- Source page: <https://phrankratai.kamphaengphet.police.go.th/wp-content/uploads/2025/04/1.%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%A1%E0%B8%A7%E0%B8%A5%E0%B8%81%E0%B8%8E%E0%B8%AB%E0%B8%A1%E0%B8%B2%E0%B8%A2%E0%B8%AD%E0%B8%B2%E0%B8%8D%E0%B8%B2.pdf>
- หน้าต้นฉบับระบุว่า "ปรับปรุง 3 กุมภาพันธ์ 2567"

สถานะ: ตัดออกจาก production pipeline แล้ว (ดู src/chunk_documents.py, EXCLUDED_PDF_SOURCES)

เหตุผล: ไฟล์ PDF มีปัญหา font encoding (ตัวอักษรกลุ่ม Private Use Area แทนสระ/วรรณยุกต์บางส่วน) ทดลองแก้แล้วดังนี้:
- เปลี่ยนไลบรารี extract (pypdf, pdfplumber, PyMuPDF) - ผลเหมือนกันหมด ไม่ช่วย
- OCR ด้วย Tesseract Thai (250 DPI) - อ่านสระ/วรรณยุกต์ถูกแล้ว แต่เลขมาตราคลาดเคลื่อนหนัก (297/435 suspicious findings)
- ปรับปรุง OCR (400 DPI + OpenCV binarization/deskew + Tesseract psm 6) - แทบไม่ต่างจากเดิม (298/435) ยืนยันว่าไม่ใช่ปัญหา config แต่เป็นปัญหาคุณภาพภาพต้นฉบับ

ไฟล์และโค้ด OCR (src/ingest_pdf.py) ยังเก็บไว้ในโปรเจกต์เป็นทางเลือกสำรอง ดูกระบวนการตรวจสอบที่ scripts/validate_ocr_quality.py และ scripts/sample_ocr_findings.py

แหล่งข้อมูลอาญาที่ใช้จริงแทนคือ PyThaiNLP CSV ด้านล่าง

## ประมวลกฎหมายแพ่งและพาณิชย์ — ใช้งานจริงใน production

- Local file: `civil_commercial_code_snapshot.pdf`
- Source page: <https://www.sbpac.go.th/home/wp-content/uploads/2024/02/%E0%B8%9B.%E0%B8%9E.%E0%B8%9E.pdf>
- ไฟล์นี้เผยแพร่บนเว็บไซต์หน่วยงานรัฐและใช้เป็น snapshot สำหรับการสาธิต
- เป็น PDF แบบ text-based ไม่มีปัญหา encoding, extract ตรงๆ ได้เนื้อหาสะอาด

## PyThaiNLP Thai Law Dataset — แหล่งข้อมูลอาญาหลักที่ใช้จริงใน production

- Local file: `penal_code_pythainlp.csv`
- Repository: <https://github.com/PyThaiNLP/thai-law>
- Release: <https://github.com/PyThaiNLP/thai-law/releases/tag/criminal-csv-v0.1>
- Asset ที่ดาวน์โหลด: `criminal-datasets.csv`
- วันที่ดึงข้อมูล: 4 กันยายน 2569 (ค.ศ. 2026)
- License ที่ระบุสำหรับการใช้งานในโปรเจกต์: public domain
- ข้อจำกัด: dataset นี้เป็นข้อมูลที่ hand-labeled โดยบุคคลที่สาม ไม่ใช่ราชกิจจานุเบกษาโดยตรง ควรตรวจสอบกับแหล่งทางการและตรวจสอบความทันสมัยเป็นระยะ
- Sanity check: มาตรา 1-398 ครบทุกเลข, 0 out-of-order, 0 duplicate, 0 large gap (scripts/validate_pythainlp_csv.py)
- แก้ไขแล้ว: พบ article_id=371 ซ้ำ 1 จุด (แถวที่เนื้อหาจริงคือมาตรา 373 แต่ label ผิดเป็น 371) แก้ label ให้ตรงกับเนื้อหาแล้วเมื่อ 4 กันยายน 2569 ยืนยันด้วย sanity check ซ้ำ ผ่าน 100%

## Official verification

ควรตรวจฉบับแก้ไขเพิ่มเติมกับฐานกฎหมายของสำนักงานคณะกรรมการกฤษฎีกาและราชกิจจานุเบกษาก่อนใช้งานจริง:

- <https://www.ocs.go.th/searchlaw>
- <https://ratchakitcha.soc.go.th/>
