# 🚀 Multi-modal Smart Personal Assistant

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B%20%2F%20Supabase-4169E1.svg?logo=postgresql&logoColor=white)](https://supabase.com/)
[![LangChain](https://img.shields.io/badge/LangChain-Integration-1C3C3C.svg?logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![Groq](https://img.shields.io/badge/Groq-Cloud%20Inference-f55036.svg)](https://groq.com/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-PP--OCRv3%2Fv6-red.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Hệ thống Trợ lý Cá nhân Đa phương thức thông minh (Multi-modal Smart Personal Assistant)**
*Tự động hóa toàn diện quy trình tiếp nhận, phân tích cuộc họp đa nguồn, lập kế hoạch thực thi công cụ và khởi tạo báo cáo / thư điện tử chuyên nghiệp.*

[Tính Năng](#-tính-năng-nổi-bật) • [Kiến Trúc](#-kiến-trúc-hệ-thống--pipeline) • [Cơ Sở Dữ Liệu](#-cơ-sở-dữ-liệu--migrations) • [Cài Đặt](#-hướng-dẫn-cài-đặt) • [Cấu Hình](#-cấu-hình-biến-môi-trường--oauth) • [Sử Dụng](#-hướng-dẫn-sử-dụng) • [Cấu Trúc Thư Mục](#-cấu-trúc-thư-mục)

</div>

---

## 📖 Giới Thiệu Tổng Quan

**Multi-modal Smart Personal Assistant** là giải pháp trợ lý AI tự hành (Autonomous Multi-Agent System) được thiết kế để xử lý dữ liệu cuộc họp phức tạp từ nhiều phương thức đầu vào khác nhau:
1. **Âm thanh cuộc họp (Audio)**: Ghi âm trao đổi thoại (.mp3, .wav, .m4a) $\rightarrow$ Speech-to-Text qua Groq Whisper.
2. **Hình ảnh tài liệu (Image)**: Slide trình chiếu, biên bản viết tay, bảng trắng (.png, .jpg) $\rightarrow$ OCR tiếng Việt chuyên sâu qua PaddleOCR.
3. **Văn bản kịch bản (Script/Doc)**: Biên bản họp, ghi chép thô (.txt, .md, .docx, .pdf) $\rightarrow$ Phân tích cấu trúc hội thoại.

Hệ thống điều phối các Agent thông minh để:
- **Trích xuất thông tin** (Summary, Decisions, Action Items) song song theo cơ chế Map-Reduce.
- **Truy vết bằng chứng chéo** (Cross-modal Evidence Linking) chống ảo giác (Anti-Hallucination).
- **Lập kế hoạch công việc** (Execution Planner) và kiểm soát an toàn (Policy Gate).
- **Lưu trữ đa người dùng (Multi-tenant Database)**: Lưu trữ lịch sử phiên họp, file đính kèm, phân công công việc và bảo vệ bằng Row Level Security (RLS).
- **Thực thi công cụ ngoại vi**: Tra cứu web đối tác (Tavily), kiểm tra lịch Google Calendar, xuất báo cáo PDF chuẩn A4 tiếng Việt và tự động soạn bản nháp email Gmail.
- **Thẩm định chất lượng (Reflection Audit)**: Đánh giá 5 tiêu chí trước khi hoàn tất phiên làm việc.

---

## 📐 Kiến Trúc Hệ Thống & Pipeline

### 1. Sơ đồ Kiến Trúc & Luồng Xử Lý Toàn Diện (System Architecture Pipeline)

```mermaid
flowchart TD
    %% =============================================================
    %% 1. TẦNG ĐẦU VÀO ĐA PHƯƠNG THỨC
    %% =============================================================
    subgraph L1 ["📥 1. MULTI-MODAL INGESTION & PREPROCESSING"]
        direction LR
        A1["🎙️ <b>Audio Stream</b><br/>Groq Whisper STT"]
        A2["🖼️ <b>Visual Stream</b><br/>PaddleOCR PP-OCRv6"]
        A3["📄 <b>Doc / Script</b><br/>LangChain Parser"]
        
        A1 & A2 & A3 --> EV["📑 <b>Unified Evidence Stream</b><br/><i>EvidenceRef (UUID, SHA256, Source Hash)</i>"]
    end

    %% =============================================================
    %% 2. TẦNG ĐIỀU PHỐI MULTI-AGENT
    %% =============================================================
    subgraph L2 ["🧠 2. COGNITIVE MULTI-AGENT ORCHESTRATION"]
        direction LR
        AG1["⚡ <b>Extractor Agent</b><br/><i>Async Map-Reduce</i>"]
        AG2["🔍 <b>Fact Validator</b><br/><i>Cross-Modal Grounding</i>"]
        AG3["📋 <b>Planner Agent</b><br/><i>DAG Tool Execution Plan</i>"]
        AG4["🛡️ <b>Policy Gate</b><br/><i>Human-in-the-Loop</i>"]
        
        AG1 --> AG2 --> AG3 --> AG4
    end

    %% =============================================================
    %% 3. TẦNG CÔNG CỤ NGOẠI VI
    %% =============================================================
    subgraph L3 ["🛠️ 3. TOOL EXECUTION MESH"]
        direction LR
        T1["🌐 <b>Tavily Search</b><br/><i>Web Reconnaissance</i>"]
        T2["📅 <b>Google Calendar</b><br/><i>FreeBusy & Events</i>"]
        T3["✉️ <b>Gmail API</b><br/><i>OAuth2 Draft Creator</i>"]
        T4["📄 <b>ReportLab</b><br/><i>A4 Unicode PDF</i>"]
    end

    %% =============================================================
    %% 4. KHO CƠ SỞ DỮ LIỆU DOANH NGHIỆP (DATABASE & STORAGE)
    %% =============================================================
    subgraph L_DB ["🗄️ 4. KHO DỮ LIỆU DOANH NGHIỆP (POSTGRESQL / SUPABASE PERSISTENCE)"]
        direction LR
        DB_POOL[("⚡ <b>AsyncPG Pool</b><br/><i>Zero-Cache Manager</i>")]
        
        DB1["👥 <b>Danh Bạ Liên Hệ</b><br/><i>contacts (pg_trgm Fuzzy)</i>"]
        DB2["🔄 <b>Phiên Họp & File</b><br/><i>workflow_runs & input_files</i>"]
        DB3["✅ <b>Nhiệm Vụ & Phê Duyệt</b><br/><i>action_items & approval_requests</i>"]
        DB4["🔐 <b>Tài Khoản & Quyền</b><br/><i>users & credentials (RLS)</i>"]
        
        DB_POOL --- DB1 & DB2 & DB3 & DB4
    end

    %% =============================================================
    %% 5. TẦNG THẨM ĐỊNH & ĐẦU RA
    %% =============================================================
    subgraph L4 ["📤 5. REFLECTION AUDIT & EXECUTIVE DELIVERABLES"]
        direction LR
        REF["🛡️ <b>Reflection Validator</b><br/><i>5-Criteria Quality Gate (Score ≥ 0.7)</i>"]
        
        OUT1["📜 <b>Meeting Summary</b>"]
        OUT2["✅ <b>Action Items</b>"]
        OUT3["📑 <b>PDF Report</b>"]
        OUT4["📨 <b>Gmail Draft</b>"]
        
        REF --> OUT1 & OUT2 & OUT3 & OUT4
    end

    %% =============================================================
    %% MAIN PIPELINE FLOW CONNECTIONS
    %% =============================================================
    EV ==> AG1
    AG2 <===>|"Tra danh bạ mờ"| DB1
    AG4 ==> L3
    L3 ==> REF
    REF ==>|"Đồng bộ kết quả & lưu trữ"| DB_POOL
    REF ==> L4

    %% =============================================================
    %% STYLING
    %% =============================================================
    classDef default fill:#1e1e2e,stroke:#45475a,stroke-width:1px,color:#cdd6f4;
    classDef layerBox fill:#181825,stroke:#89b4fa,stroke-width:2px,color:#89b4fa;
    classDef dbBox fill:#181825,stroke:#a6e3a1,stroke-width:2px,color:#a6e3a1;
    classDef toolBox fill:#181825,stroke:#fab387,stroke-width:1.5px,color:#fab387;

    class L1,L2,L4 layerBox;
    class L3 toolBox;
    class L_DB,DB_POOL dbBox;
```

---

### 2. Sơ đồ Tuần Tự Tương Tác (Sequence Flow)

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng / API Client
    participant API as FastAPI Router
    participant Pre as Preprocessors (STT / OCR / Parser)
    participant Ext as Extractor Agent (Map-Reduce)
    participant Val as Fact Validator & Aligner
    participant DB as PostgreSQL (AsyncPG Pool)
    participant Plan as Planner Agent
    participant Exec as Tool Executor
    participant Ref as Reflection Validator

    User->>API: Gửi yêu cầu kèm File (Audio / Image / Script)
    API->>Pre: Chuyển đổi tệp sang EvidenceRef
    Pre-->>Ext: Dòng bằng chứng chuẩn hóa (Evidence Stream)
    Ext->>Ext: Chạy Map-Reduce chia batch & gọi LLM trích xuất
    Ext-->>Val: MeetingExtraction (Summary, Decisions, Actions)
    Val->>DB: Fuzzy search tìm danh bạ người phụ trách (pg_trgm + unaccent)
    DB-->>Val: Trả về email & chức danh chính xác
    Val->>Plan: State đã chuẩn hóa
    Plan->>Plan: Sinh ExecutionPlan (Web Search, Calendar, PDF, Gmail)
    Plan-->>Exec: Thực thi các bước công cụ
    Exec->>Exec: Gọi Tavily Search / Google Calendar / Tạo PDF Report / Soạn Thư Nháp Gmail
    Exec->>Ref: Gửi trạng thái RunState hoàn tất
    Ref->>Ref: Kiểm định 5 tiêu chí (Coverage, Evidence, Consistency, Tools, Safety)
    Ref->>DB: Ghi nhận lịch sử cuộc họp & danh sách việc cần làm
    Ref-->>API: Trả về kết quả hoàn chỉnh & File đính kèm
    API-->>User: Phản hồi JSON + PDF + Gmail Draft ID
```

---

## ✨ Tính Năng Nổi Bật

| Tính năng | Chi tiết kỹ thuật |
| :--- | :--- |
| 🎙️ **Multi-modal Ingestion** | Tích hợp **Groq Whisper** (nhận diện giọng nói siêu tốc) và **PaddleOCR PP-OCRv6** (nhận diện chữ tiếng Việt chính xác cao). |
| ⚡ **Map-Reduce Parallel Extraction** | Bóc tách thông tin song song theo từng batch bằng LLM bất đồng bộ (`ainvoke`), hỗ trợ xử lý biên bản họp dài mà không lo tràn context window. |
| 🗄️ **Multi-tenant Database & RLS** | Quản lý dữ liệu người dùng, cuộc họp, phân công công việc trên **PostgreSQL / Supabase** qua connection pool `asyncpg`, phân quyền độc lập bằng Row Level Security. |
| 🔍 **Fuzzy Contact Matching** | Sử dụng PostgreSQL extension `pg_trgm` & `unaccent` để tìm kiếm danh bạ thông minh theo biệt danh (`aliases`), tên không dấu hoặc gõ nhầm chữ. |
| 🛡️ **Anti-Hallucination Evidence Tracking** | Mọi Action Item và Decision đều được liên kết trực tiếp với mã định danh bằng chứng gốc (`AUDIO_001`, `IMAGE_002`, `SCRIPT_003`). |
| 🔍 **Cross-Source Conflict Detection** | Tự động phát hiện khi có sự bất đồng thông tin giữa các nguồn (ví dụ: Audio nói một đằng, Slide ghi một nẻo) và đánh dấu trạng thái `CONFLICTED`. |
| 📅 **Google Calendar Integration** | Tự động tra cứu lịch rảnh (`freebusy`) của các thành viên tham gia và đề xuất khung giờ họp tiếp theo. |
| 📄 **Professional PDF Generator** | Tạo báo cáo cuộc họp PDF chuẩn A4, hỗ trợ đầy đủ phông chữ tiếng Việt Unicode (`DejaVuSans`), kẻ bảng và định dạng chuyên nghiệp. |
| ✉️ **Executive Email Copywriter** | Tự động dùng LLM biên soạn email báo cáo trang trọng, tự nhiên theo văn phong công sở và đẩy trực tiếp vào mục **Thư nháp (Drafts)** của Gmail qua OAuth2. |
| 🧠 **Self-Correction & Reflection** | Đánh giá lại toàn bộ kết quả qua 5 tiêu chí: *Coverage, Evidence, Consistency, Tool Execution, Safety*. Tự động kích hoạt cơ chế `repair_output` hoặc `ask_user` khi có sự cố. |

---

## 🗄️ Cơ Sở Dữ Liệu & Migrations

Hệ thống sử dụng **PostgreSQL (Supabase)** với kiến trúc **Production-Grade Multi-tenant** gồm 7 bảng nghiệp vụ cốt lõi, quản lý qua Connection Pool siêu tốc `asyncpg` (không qua ORM cồng kềnh để tối ưu độ trễ).

### 1. Sơ Đồ Thực Thể Liên Kết CSDL (Entity Relationship Diagram - ERD)

```mermaid
erDiagram
    users ||--o{ user_credentials : "has"
    users ||--o{ contacts : "owns"
    users ||--o{ workflow_runs : "creates"
    users ||--o{ input_files : "owns"
    users ||--o{ action_items : "owns"
    users ||--o{ approval_requests : "owns"
    
    workflow_runs ||--o{ input_files : "contains (CASCADE)"
    workflow_runs ||--o{ action_items : "extracts (CASCADE)"
    workflow_runs ||--o{ approval_requests : "queues (CASCADE)"
    
    contacts ||--o{ action_items : "assigned_to (SET NULL)"

    users {
        uuid id PK "gen_random_uuid()"
        text email UK "Unique user email"
        text full_name "Full name"
        text avatar_url "Avatar URL"
        jsonb preferences "Settings & preferences"
        timestamptz created_at
        timestamptz updated_at
    }

    user_credentials {
        uuid id PK "gen_random_uuid()"
        uuid user_id FK "References users(id)"
        text provider "Google / Microsoft"
        text account_email "OAuth account"
        text encrypted_refresh_token "Mã hóa bảo mật"
        jsonb scopes "Granted scopes"
        jsonb metadata "Extra metadata"
        timestamptz token_expires_at
        timestamptz created_at
        timestamptz updated_at
    }

    contacts {
        uuid id PK "gen_random_uuid()"
        uuid user_id FK "References users(id)"
        text name "Tên liên hệ (GIN Trigram indexed)"
        text email "Email liên hệ"
        text role "Chức vụ / Vị trí"
        text company "Tên công ty / Tổ chức"
        text phone "Số điện thoại"
        jsonb aliases "Biệt danh tìm kiếm mờ"
        jsonb metadata "Metadata bổ sung"
        timestamptz created_at
        timestamptz updated_at
        timestamptz deleted_at "Soft delete"
    }

    workflow_runs {
        uuid id PK "gen_random_uuid()"
        uuid user_id FK "References users(id)"
        text session_id UK "Unique run session"
        text title "Tiêu đề cuộc họp"
        text user_request "Yêu cầu ban đầu từ user"
        text status "created | extracting | planning | executing | completed | failed"
        text script_type "transcript | minutes | agenda"
        jsonb extraction_summary "Tóm tắt & quyết định JSON"
        text report_path "Đường dẫn báo cáo PDF"
        text email_draft_id "Mã bản nháp Gmail"
        text error_message "Chi tiết lỗi nếu fail"
        integer duration_ms "Thời gian xử lý (ms)"
        timestamptz created_at
        timestamptz completed_at
    }

    input_files {
        uuid id PK "gen_random_uuid()"
        uuid user_id FK "References users(id)"
        uuid run_id FK "References workflow_runs(id)"
        text kind "audio | image | script | document"
        text original_name "Tên file gốc"
        text storage_path "Đường dẫn lưu trữ"
        text storage_url "Public/Signed URL"
        text sha256_hash "Băm chống trùng lặp"
        bigint file_size_bytes "Dung lượng tệp (bytes)"
        text mime_type "MIME Type"
        timestamptz created_at
    }

    action_items {
        uuid id PK "gen_random_uuid()"
        uuid user_id FK "References users(id)"
        uuid run_id FK "References workflow_runs(id)"
        uuid owner_contact_id FK "References contacts(id)"
        text action_id "ACT_001, ACT_002..."
        text description "Nội dung công việc"
        text owner_name "Tên người phụ trách"
        timestamptz deadline "Hạn chót hoàn thành"
        text priority "low | medium | high | urgent"
        integer duration_minutes "Thời lượng ước tính"
        text verification_status "verified | unverified | conflicted"
        text task_status "pending | in_progress | done | cancelled"
        jsonb evidence_refs "Mã bằng chứng liên kết"
        timestamptz created_at
        timestamptz updated_at
    }

    approval_requests {
        uuid id PK "gen_random_uuid()"
        uuid user_id FK "References users(id)"
        uuid run_id FK "References workflow_runs(id)"
        text tool_name "Tên công cụ yêu cầu duyệt"
        jsonb arguments "Tham số payload thực thi"
        text status "pending | approved | rejected | expired"
        text decided_by "Người đưa ra quyết định"
        text reason "Lý do phê duyệt/từ chối"
        timestamptz expires_at "Thời hạn phê duyệt"
        timestamptz decided_at "Thời điểm quyết định"
        timestamptz created_at
    }
```

---

### 2. Chi Tiết Các File Migration (`migrations/`)

| Thứ tự File Migration | Mục đích |
| :--- | :--- |
| [`001_initial_schema.sql`](file:///media/tutran27/DATA/project/multimodal-smart-personal-assistant/migrations/001_initial_schema.sql) | Khởi tạo cấu trúc 7 bảng cốt lõi (`users`, `user_credentials`, `contacts`, `workflow_runs`, `input_files`, `action_items`, `approval_requests`). |
| [`002_enable_extensions.sql`](file:///media/tutran27/DATA/project/multimodal-smart-personal-assistant/migrations/002_enable_extensions.sql) | Kích hoạt các extension: `pgcrypto`, `pg_trgm`, `unaccent`, `"uuid-ossp"`, `vector`. |
| [`003_create_indexes.sql`](file:///media/tutran27/DATA/project/multimodal-smart-personal-assistant/migrations/003_create_indexes.sql) | Thiết lập B-Tree Indexes và GIN Trigram Indexes phục vụ tìm kiếm mờ cực nhanh. |
| [`004_rls_policies.sql`](file:///media/tutran27/DATA/project/multimodal-smart-personal-assistant/migrations/004_rls_policies.sql) | Thiết lập bảo mật phân quyền đa người dùng (Row Level Security). |
| [`005_seed_contacts.sql`](file:///media/tutran27/DATA/project/multimodal-smart-personal-assistant/migrations/005_seed_contacts.sql) | Chuyển đổi và nạp dữ liệu danh bạ mẫu vào bảng `contacts`. |

> **Cách chạy Migration:** Thực thi tuần tự các file từ `001` đến `005` trong Supabase SQL Editor hoặc qua công cụ quản lý PostgreSQL.

---

## 📁 Cấu Trúc Thư Mục

```text
Multi-modal-Smart-Personal-Assistant/
├── app/
│   ├── agents/                   # Các tác tử thông minh (Multi-Agent System)
│   │   ├── extractor.py          # Map-Reduce Information Extractor
│   │   ├── planner.py            # Execution Plan Generator
│   │   └── reflector.py          # Reflection Validator & Self-Correction
│   ├── api/                      # Tầng giao diện REST API
│   │   └── routes.py             # FastAPI Endpoints
│   ├── core/                     # Cấu hình & Tiện ích cốt lõi
│   │   ├── config.py             # Pydantic Settings & Quản lý Env
│   │   ├── constants.py          # Enums & System Constants
│   │   ├── exceptions.py         # Custom Exception Classes
│   │   ├── json_utils.py         # Trích xuất & tự sửa lỗi JSON payload
│   │   └── prompts.py            # Hệ thống Prompt chuẩn hóa
│   ├── db/                       # Tầng kết nối & truy vấn CSDL
│   │   ├── pool.py               # AsyncPG Connection Pool Manager
│   │   └── queries/              # Các hàm truy vấn SQL thuần
│   ├── orchestration/            # Điều phối quy trình (Workflow)
│   │   ├── conflict_detector.py  # Phát hiện xung đột dữ liệu đa nguồn
│   │   ├── executor.py           # Bộ thực thi kế hoạch công cụ
│   │   ├── plan_validator.py     # Thẩm định cấu trúc kế hoạch
│   │   ├── policy_gate.py        # Kiểm soát chính sách & an toàn
│   │   ├── reference_resolver.py # Phân giải biến động giữa các bước
│   │   ├── source_aligner.py     # Căn chỉnh ngữ nghĩa đa phương thức
│   │   └── workflow.py           # Luồng điều phối End-to-End
│   ├── schemas/                  # Pydantic Schemas & DTOs
│   │   ├── evidence.py           # EvidenceRef schema
│   │   ├── extraction.py         # ActionItem & MeetingExtraction
│   │   ├── plan.py               # ExecutionPlan & PlanStep schema
│   │   ├── state.py              # RunState schema
│   │   └── validation.py         # FactValidation & ReflectionResult
│   ├── services/                 # Tầng Dịch vụ & Kết nối
│   │   ├── contact_repository.py # Quản lý danh bạ liên hệ
│   │   ├── document_reader.py    # Bộ đọc tệp văn bản đa định dạng
│   │   ├── llm_service.py        # Khởi tạo kết nối ChatGroq / OpenRouter
│   │   ├── oauth_service.py      # Xác thực Google OAuth2 (Calendar & Gmail)
│   │   └── storage_service.py    # Quản lý lưu trữ tệp & hashing SHA256
│   ├── tools/                    # Tập hợp Công cụ ngoại vi (Tools)
│   │   ├── audio_stt.py          # Chuyển đổi giọng nói thành văn bản
│   │   ├── fact_validator.py     # Thẩm định bằng chứng & chuẩn hóa danh bạ
│   │   ├── gmail_draft.py        # Tạo bản nháp email Gmail
│   │   ├── google_calendar.py    # Kiểm tra & quản lý Google Calendar
│   │   ├── image_ocr.py          # Nhận diện chữ tiếng Việt từ hình ảnh
│   │   ├── pdf_generator.py      # Sinh báo cáo PDF ReportLab
│   │   ├── script_parser.py      # Phân tích kịch bản họp
│   │   └── web_search.py         # Tra cứu thông tin web (Tavily)
│   └── main.py                   # FastAPI Application Entrypoint
├── assets/fonts/                 # Phông chữ tiếng Việt (DejaVuSans.ttf)
├── credentials/                  # Thư mục chứa khóa Google OAuth2 (bảo mật)
├── data/
│   ├── inputs/                   # Thư mục lưu tệp đầu vào
│   └── temp/                     # Thư mục lưu tệp tạm
├── migrations/                   # Các script khởi tạo và di chuyển CSDL SQL
│   ├── 001_initial_schema.sql
│   ├── 002_enable_extensions.sql
│   ├── 003_create_indexes.sql
│   ├── 004_rls_policies.sql
│   └── 005_seed_contacts.sql
├── outputs/                      # Thư mục xuất báo cáo PDF
├── .env.example                  # File mẫu biến môi trường
├── .gitignore                    # Quy tắc loại trừ Git (Bảo vệ bí mật)
├── requirements.txt              # Danh sách thư viện phụ thuộc
└── README.md                     # Tài liệu hướng dẫn dự án
```

---

## 🛠️ Hướng Dẫn Cài Đặt

### 1. Yêu Cầu Môi Trường
- **Python**: Phiên bản `3.10` trở lên (Khuyến nghị dùng `Python 3.10` hoặc `3.11`).
- **PostgreSQL**: Phiên bản `15+` hoặc tài khoản **Supabase**.
- **Conda / Virtualenv** để cô lập môi trường.

### 2. Cài Đặt Các Gói Phụ Thuộc
```bash
# 1. Clone repository
git clone https://github.com/tutran27/multimodal-meeting-assistant.git
cd multimodal-meeting-assistant

# 2. Tạo và kích hoạt môi trường ảo
python -m venv .venv
source .venv/bin/activate   # Trên Linux/macOS
# .venv\Scripts\activate    # Trên Windows

# 3. Cài đặt thư viện
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔐 Cấu Hình Biến Môi Trường & OAuth

### 1. Cấu hình File `.env`
Sao chép file `.env.example` thành `.env` và điền các cấu hình kết nối:

```bash
cp .env.example .env
```

```env
# --- Cấu hình chung ---
ENV=development
DEBUG=True

# --- Database & Supabase (asyncpg Connection Pool) ---
DATABASE_URL=postgresql://postgres.your-project-ref:your-password@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
DB_POOL_MIN_SIZE=2
DB_POOL_MAX_SIZE=10
DB_POOL_TIMEOUT=30

SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
SUPABASE_JWT_SECRET=your_supabase_jwt_secret_here

# --- PaddleOCR ---
PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

# --- Google Calendar & Gmail API ---
GOOGLE_ENABLED=true
GOOGLE_CLIENT_SECRET_PATH=credentials/credentials.json
GOOGLE_TOKEN_PATH=credentials/token_calendar.json
GOOGLE_CALENDAR_ID=primary
DEFAULT_BOSS_EMAIL=boss@example.com

# --- LLM API Keys (Groq) ---
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_LLM_MODEL=llama-3.1-8b-instant
GROQ_STT_MODEL=whisper-large-v3-turbo

# --- OpenRouter (Tùy chọn) ---
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_LLM_MODEL=qwen/qwen-2.5-72b-instruct

# --- Tra cứu Web (Tavily Search) ---
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-your_tavily_api_key_here

# --- Hugging Face Token (Reranker & Models) ---
HF_TOKEN=your_huggingface_token_here

# --- LangSmith Tracing (Tùy chọn giám sát) ---
LANGCHAIN_TRACING_V2=false
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langchain_api_key_here
LANGCHAIN_PROJECT=smart-personal-assistant
```

### 2. Cài Đặt Google OAuth (Calendar & Gmail)
1. Truy cập [Google Cloud Console](https://console.cloud.google.com/) $\rightarrow$ Tạo một Project mới.
2. Bật 2 thư viện API:
   - **Google Calendar API**
   - **Gmail API**
3. Cấu hình **OAuth consent screen** (Chọn *External*, thêm email của bạn vào danh sách *Test Users*).
4. Vào mục **Credentials** $\rightarrow$ **Create Credentials** $\rightarrow$ **OAuth client ID** (Loại ứng dụng: **Desktop App**).
5. Tải file JSON vừa tạo về và lưu vào: `credentials/credentials.json`.
6. Khi chạy công cụ lần đầu, trình duyệt sẽ tự động bật lên để bạn đăng nhập và cấp quyền; file `credentials/token_calendar.json` sẽ được sinh ra tự động.

---

## 🚀 Hướng Dẫn Sử Dụng

### 1. Chạy Thử Nghiệm Từng Công Cụ Độc Lập (CLI Testing)

```bash
# 🎙️ Kiểm tra Speech-to-Text âm thanh:
python -m app.tools.audio_stt "path/to/meeting_audio.mp3"

# 🖼️ Kiểm tra OCR hình ảnh:
python -m app.tools.image_ocr "path/to/whiteboard_slide.png"

# 📄 Kiểm tra phân tích kịch bản cuộc họp:
python -m app.tools.script_parser

# 🔍 Kiểm tra Fact Validator & Tra danh bạ:
python -m app.tools.fact_validator

# 🌐 Kiểm tra Web Search đối tác:
python -m app.tools.web_search "Công ty Cổ phần Công nghệ ABC"

# 📅 Kiểm tra tra cứu Google Calendar:
python -m app.tools.google_calendar

# 📄 Kiểm tra tạo file PDF Báo cáo:
python -m app.tools.pdf_generator

# ✉️ Kiểm tra tạo Bản nháp Email Gmail:
python -m app.tools.gmail_draft
```

---

### 2. Khởi Động Máy Chủ REST API (FastAPI)

```bash
python -m app.main
```
Hoặc:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

* Swagger UI tài liệu API trực quan: [http://localhost:8000/docs](http://localhost:8000/docs)
* Healthcheck API & DB Connection: [http://localhost:8000/health](http://localhost:8000/health)

---

### 3. Khởi Động Giao Diện Người Dùng (Streamlit Web UI)

```bash
streamlit run frontend/streamlit_app.py
```

* Truy cập giao diện trực quan tại: [http://localhost:8501](http://localhost:8501)
* Tải lên âm thanh, hình ảnh bảng trắng, file kịch bản họp và theo dõi quá trình thực thi của các Agent theo thời gian thực.

---

### 4. Gọi API Xử lý Cuộc Họp Toàn Diện (`/api/v1/process-meeting`)

Gửi request đa phương thức (gồm file ghi âm, file ảnh bảng trắng và ghi chép cuộc họp):

```bash
curl -X POST "http://localhost:8000/api/v1/process-meeting" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "user_request=Trích xuất toàn bộ việc cần làm, kiểm tra lịch tuần sau và soạn email nháp gửi sếp" \
  -F "audio_file=@data/inputs/meeting_recording.mp3" \
  -F "image_file=@data/inputs/whiteboard_note.jpg" \
  -F "script_file=@data/inputs/meeting_minutes.docx"
```

---

## 🛡️ Chính Sách An Toàn & Bảo Mật

1. **Multi-tenant Row Level Security (RLS)**:
   - Dữ liệu giữa các người dùng được cô lập hoàn toàn ở tầng CSDL PostgreSQL. Người dùng không thể truy cập chéo dữ liệu của nhau.
2. **Human-in-the-Loop Email Draft**:
   - Hệ thống được cấu hình mặc định `ENABLE_EMAIL_SEND=false`. 
   - AI **chỉ tạo bản nháp (Draft)** trong hòm thư Gmail của bạn, tuyệt đối không tự ý gửi thư đi khi chưa có sự xác nhận của người dùng.
3. **Policy Gate Check**:
   - Mọi thao tác ghi dữ liệu vào Google Calendar hay gửi thông tin ra ngoài đều phải qua bước kiểm tra chính sách an toàn.
4. **Bảo Vệ Bí Mật Tuyệt Đối**:
   - Tất cả các file token, client secrets và file `.env` chứa API key đều đã được thiết lập quy tắc trong `.gitignore` để không bao giờ bị lộ lên hệ thống quản lý mã nguồn.

---

## 🤝 Đóng Góp & Phát Triển

Dự án mở cho các đóng góp nâng cao tính năng:
- [ ] Mở rộng tích hợp họp trực tuyến (Zoom / Google Meet webhook).
- [ ] Tích hợp RAG tra cứu tri thức doanh nghiệp chuyên sâu qua `pgvector`.
- [ ] Hỗ trợ đa ngôn ngữ (Tiếng Anh, Tiếng Nhật).

Nếu bạn có bất kỳ thắc mắc hay đề xuất cải tiến nào, hãy tạo một **Issue** hoặc gửi **Pull Request**!

---

---

<div align="center">
  <sub>Phát triển với sự tận tâm và tiêu chuẩn kỹ thuật cao cấp dành cho Trợ lý AI thế hệ mới.</sub>
</div>

