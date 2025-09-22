# File Upload & Processing Service (Python, stdlib only)

This simulates a **file upload and processing service**.  
It was built step-by-step to demonstrate clean code, logging, error handling, persistence, testing, and even a minimal web interface.

---

## ✨ Features

- **Validation** → only `.txt` and `.csv` files allowed
- **Uploader** → safe copy to `uploads/` with unique UUID filenames
- **Processing** → robust text decoding, counts **lines** and **words**
- **Persistence** → in-memory DB mirrored to `data/db.json`
- **Logging** → console + rotating log file `logs/app.log`
- **CLI** → upload / process / list
- **HTTP server** → minimal frontend & JSON API:
    - `GET /` → basic HTML page to upload & list records
    - `POST /upload` → upload and process a file
    - `GET /records` → JSON array of all records
- **Testing** → stdlib `unittest` covering validation, upload, process, persistence

---

## 📂 Project Structure
```bash
file-upload-service/
├── data/ # runtime persistence (db.json)
├── logs/ # rotating log file (app.log)
├── sample_files/ # example inputs for testing
│ ├── sample.txt
│ └── sample.csv
├── src/
│ └── app/
│ ├── init.py
│ ├── cli.py # CLI entrypoint
│ ├── config.py # paths & constants
│ ├── exceptions.py # clean exception hierarchy
│ ├── logger.py # console + file logger
│ ├── models.py # FileRecord dataclass
│ ├── processor.py # line/word counting
│ ├── server.py # tiny HTTP server + frontend
│ ├── storage.py # in-memory DB + JSON persistence
│ └── uploader.py # file validation + upload
├── tests/
│ └── test_upload_process.py # unittest coverage
├── README.md
└── requirements.txt
```


---

## 🚀 Quick Start

Requires **Python 3.10+**

### 1. Clone & setup
```bash
git clone https://github.com/Sabidabdulkalam/file-upload-service.git
cd file-upload-service
python -m venv .venv
# activate venv
# Windows:
.\.venv\Scripts\activate
```
📌 This project uses only the Python standard library. Nothing else to install.

### 2. 🖥️ CLI Usage

- **Upload a file python**  
```bash
*python -m src.app.cli upload sample_files/sample.txt*
````
- **List records**  
```bash
*python -m src.app.cli list*
```

- **Process a record (copy ID from list output)** 
```bash
*python -m src.app.cli process <record-id>*
````

- **List again (should now show PROCESSED + counts)**
```bash
*python -m src.app.cli list*
````

### 3. 🌐 Minimal Web UI
Run the HTTP server:  
```bash
*python -m src.app.server*
```
Then open: http://127.0.0.1:8000/
- Upload .txt or .csv files
- Success message shows id, lines, and words
- Records table auto-refreshes (or click Refresh)

API endpoints:
- POST /upload (multipart form, field name file)
- GET /records (JSON of all records)


### 4. ✅ Run Tests
```bash
*python -m unittest discover -s tests -v*  
```
You should see all tests pass:
```bash
Ran 7 tests in 0.08s
OK
```
Covers:  
- validation (allowed vs blocked extensions)

- missing file raises error

- upload creates a record

- processing updates status + counts

- persistence across reloads

## ⚙️ Design Notes
- **Separation of concerns**: uploader, processor, storage, logger, exceptions

- **Error handling**: meaningful exceptions for invalid type, file access, decode errors, missing records

- **Logging**: simple user messages in CLI; detailed logs in console & file

- **Persistence**: lightweight JSON mirror to simulate database

## 📌 Exceptions Overview  
- **UploadError** (base)  
  - InvalidFileTypeError
  - FileAccessError
- **ProcessingError** (base)
  - RecordNotFoundError
  - DecodeError
- **PersistenceError** (future-proof, not currently raised)

## 🙌 Notes

- No third-party dependencies (only stdlib).

- Tested on Python 3.12 

