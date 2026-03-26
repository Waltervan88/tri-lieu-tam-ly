# ERD Toàn Hệ Thống — DDH PMS MVP1

## Comment về Approach

Hierarchy **flatten** theo D-031 (2026-03-26):

- **Trustify (Super Admin)** chỉ tạo `Enterprise` + `Admin Account` → đúng vai trò platform operator
- **Admin Doanh nghiệp** tạo `Building` (tòa nhà) qua M01.1 → đúng vai trò business owner
- **Bỏ entity Property** — không cần layer trung gian cho MVP
- **1 Enterprise → nhiều Building**. Pricing, OTA, User scope gắn trực tiếp vào Enterprise.

> [!IMPORTANT]
> D-031 supersedes D-030 và các P-013, P-017, P-018 trước đó.

---

## ERD — System-wide Entity Relationship Diagram

---

### ERD — User & Building Access Model (D-031)

```mermaid
erDiagram

    TRUSTIFY {
        string name "Trustify Technology"
    }

    ENTERPRISE {
        uuid id PK
        string name
        enum status "ACTIVE | INACTIVE"
        string tax_id
        string address
        string logo_url
    }

    BUILDING {
        uuid id PK
        uuid enterprise_id FK
        string name "Toa A, Toa B..."
        enum business_type "HOTEL | RESORT | SERVICED_APT | OTHER"
        int settlement_day "1-31"
        string timezone "default Asia/Ho_Chi_Minh"
        string currency "default VND"
        enum status "ACTIVE | INACTIVE"
    }

    USER {
        uuid id PK
        uuid enterprise_id FK
        uuid building_id FK "nullable - admin has none"
        enum user_level "SUPER_ADMIN | ENTERPRISE_ADMIN | BUILDING_USER"
        enum status "ACTIVE | INACTIVE"
    }

    %% ── PLATFORM LAYER ──
    TRUSTIFY ||--o{ ENTERPRISE : "creates & manages"

    %% ── ENTERPRISE ──
    ENTERPRISE ||--o{ BUILDING : "has many"
    ENTERPRISE ||--o{ USER : "has many"

    %% ── BUILDING ──
    BUILDING ||--o{ USER : "assigns staff"

    %% ── USER ACCESS RULES ──
    USER {
        SUPER_ADMIN:        building_id = NULL
        ENTERPRISE_ADMIN:  building_id = NULL
        BUILDING_USER:      building_id = FK (tied to 1 building)
    }

    %% ── LEGEND ──
    USER }o--o{ BUILDING : "BUILDING_USER: 1 Building (no switcher)"
    USER }o--|| BUILDING : "ENTERPRISE_ADMIN: all Buildings in Enterprise"
    USER }o--o| ENTERPRISE : "SUPER_ADMIN: all Enterprises"
```

| User Level | `building_id` | Building Switcher | Scope |
|---|---|---|---|
| **SUPER_ADMIN** | `NULL` | Yes (Enterprise switcher) | Tất cả DN trên nền tảng |
| **ENTERPRISE_ADMIN** | `NULL` | Yes (Building switcher) | Tất cả Buildings trong DN |
| **BUILDING_USER** (Lễ tân, Buồng phòng...) | `FK` | **No** | Chỉ 1 Building được assign |

---

```mermaid
erDiagram
    %% ========================================
    %% LAYER 1: PLATFORM (SaaS Admin)
    %% ========================================

    ENTERPRISE {
        uuid id PK
        string name
        string tax_id
        string address
        string representative_name
        string representative_email
        string representative_phone
        string logo_url
        string plan_note "placeholder - not enforced"
        enum status "ACTIVE | INACTIVE"
        timestamp created_at
        timestamp updated_at
        uuid created_by FK "Super Admin"
    }

    %% ========================================
    %% LAYER 2: BUILDING CONFIG (M01.1) — D-031
    %% ========================================

    BUILDING {
        uuid id PK
        uuid enterprise_id FK
        string name "Toa A - Main Building / Toa B - Annex"
        enum business_type "HOTEL | RESORT | SERVICED_APT | OTHER"
        string address
        int settlement_day "1-31 — ngày quyết toán tòa nhà (BIZ-12)"
        string timezone "default Asia/Ho_Chi_Minh"
        string currency "default VND"
        enum status "ACTIVE | INACTIVE"
        timestamp created_at
        timestamp updated_at
    }

    FLOOR {
        uuid id PK
        uuid building_id FK
        string name
        int floor_number
        int sort_order
    }

    %% ========================================
    %% LAYER 3: ROOM & PRICING (M01.2)
    %% ========================================

    ROOM_TYPE {
        uuid id PK
        uuid enterprise_id FK "pricing shared across all buildings"
        string name "Free text"
        string description
        int standard_occupancy
        enum status "ACTIVE | INACTIVE"
    }

    ROOM {
        uuid id PK
        uuid room_type_id FK
        uuid floor_id FK
        uuid building_id FK "phòng thuộc building nào"
        string name "Free text"
        enum status "AVAILABLE | RESERVED | OCCUPIED | DIRTY | OUT_OF_ORDER | DUE_OUT | NO_SHOW"
        enum clean_status "CLEAN | DIRTY | INSPECTED"
        boolean is_active
    }

    PRICE_POLICY {
        uuid id PK
        uuid enterprise_id FK "chung cho tất cả buildings trong enterprise"
        string name "eg. Chính sách Mặc định"
        boolean has_hourly
        boolean has_daily
        boolean has_nightly
        boolean has_weekly
        boolean has_monthly
        enum status "ACTIVE | INACTIVE"
    }

    PRICE_HOURLY {
        uuid id PK
        uuid price_policy_id FK
        int hours
        decimal price
    }

    PRICE_DAILY {
        uuid id PK
        uuid price_policy_id FK
        time checkin_time
        time checkout_time
        decimal price
        decimal early_checkin_fee
        decimal late_checkout_fee
        decimal extra_adult_fee
        decimal extra_child_fee
    }

    PRICE_NIGHTLY {
        uuid id PK
        uuid price_policy_id FK
        time checkin_time
        time checkout_time
        decimal price
        time auto_night_from "22:00 - giá giờ chuyển giá đêm"
        decimal early_checkin_fee
        decimal late_checkout_fee
        decimal extra_adult_fee
        decimal extra_child_fee
    }

    PRICE_WEEKLY {
        uuid id PK
        uuid price_policy_id FK
        decimal price_per_week
        decimal price_per_extra_day "Ngày lẻ sau 7"
    }

    PRICE_MONTHLY {
        uuid id PK
        uuid price_policy_id FK
        enum calc_method "FULL_30_DAYS | CALENDAR_MONTH"
        decimal price_per_month
        decimal price_per_extra_day
    }

    ROOM_TYPE_PRICE_POLICY {
        uuid id PK
        uuid room_type_id FK
        uuid price_policy_id FK
        boolean is_default
    }

    %% ========================================
    %% LAYER 4: EQUIPMENT & SERVICES (M01.4, M01.6)
    %% ========================================

    EQUIPMENT_GROUP {
        uuid id PK
        uuid enterprise_id FK
        string name
    }

    EQUIPMENT {
        uuid id PK
        uuid equipment_group_id FK
        string name
        int quantity
    }

    ROOM_EQUIPMENT {
        uuid id PK
        uuid room_id FK
        uuid equipment_id FK
        int quantity
    }

    SERVICE_CATEGORY {
        uuid id PK
        uuid enterprise_id FK
        string name "eg. Buồng phòng, Giặt là"
    }

    SERVICE_GROUP {
        uuid id PK
        uuid service_category_id FK
        string name "eg. Thức uống"
        boolean is_active
    }

    SERVICE_ITEM {
        uuid id PK
        uuid service_group_id FK
        string name
        string code
        decimal price
        string unit
        boolean allow_price_edit
        boolean exclude_from_invoice
        enum status "ACTIVE | INACTIVE"
    }

    %% ========================================
    %% LAYER 5: TIME CONFIG (M01.5)
    %% ========================================

    TIME_CONFIG {
        uuid id PK
        uuid enterprise_id FK
        time default_checkin
        time default_checkout
        time night_audit_time "default 02:00"
        time hourly_cutoff "22:00 - after this, charge nightly"
    }

    %% ========================================
    %% LAYER 6: RESERVATION & GUEST (M02, M04)
    %% ========================================

    GUEST {
        uuid id PK
        uuid enterprise_id FK
        string full_name
        string phone
        string email
        string id_number "CCCD/Passport"
        enum id_type "CCCD | PASSPORT | OTHER"
        string nationality
        string address
        string notes
        timestamp created_at
    }

    RESERVATION {
        uuid id PK
        uuid enterprise_id FK
        uuid room_id FK
        uuid guest_id FK
        uuid booked_by FK "User who created"
        string confirmation_code
        enum source "DIRECT | WALK_IN | PHONE | OTA_AGODA | OTA_BOOKING | OTA_TRAVELOKA | OTA_TRIP | OTA_EXPEDIA"
        string ota_booking_ref "OTA reference number"
        datetime checkin_date
        datetime checkout_date
        datetime actual_checkin
        datetime actual_checkout
        int adults
        int children
        enum price_type "HOURLY | DAILY | NIGHTLY | WEEKLY | MONTHLY"
        decimal room_charge
        decimal discount_amount
        decimal tax_amount
        decimal total_amount
        enum status "CONFIRMED | IN_HOUSE | CHECKED_OUT | CANCELLED | NO_SHOW"
        string notes
        timestamp created_at
        timestamp updated_at
    }

    %% ========================================
    %% LAYER 7: FOLIO & PAYMENT (M07, M10)
    %% ========================================

    FOLIO {
        uuid id PK
        uuid reservation_id FK
        decimal total_charges
        decimal total_payments
        decimal balance "charges - payments"
        enum status "OPEN | CLOSED"
        timestamp created_at
    }

    FOLIO_CHARGE {
        uuid id PK
        uuid folio_id FK
        enum charge_type "ROOM | SERVICE | TAX | EARLY_CHECKIN | LATE_CHECKOUT | EXTRA_PERSON | OTHER"
        uuid reference_id "room_id or service_item_id"
        string description
        decimal amount
        date charge_date
        uuid posted_by FK
        timestamp created_at
    }

    PAYMENT {
        uuid id PK
        uuid folio_id FK
        enum method "CASH | BANK_TRANSFER | POS_CARD | OTA_PREPAID | ONLINE_LINK"
        decimal amount
        string currency "default VND"
        decimal foreign_amount "OTA ngoại tệ"
        string reference_number
        string ota_name "if OTA prepaid"
        string payment_link_url "if online link"
        enum payment_link_status "PENDING | PAID | EXPIRED"
        uuid received_by FK
        timestamp created_at
    }

    %% ========================================
    %% LAYER 8: HOUSEKEEPING (M06)
    %% ========================================

    HOUSEKEEPING_TASK {
        uuid id PK
        uuid room_id FK
        uuid assigned_to FK "User"
        date task_date
        enum service_type "FULL_CLEAN | TURNDOWN | INSPECT | OTHER"
        enum status "PENDING | IN_PROGRESS | COMPLETED"
        string notes
        string guest_name
        int guest_count
        timestamp completed_at
    }

    %% ========================================
    %% LAYER 9: NIGHT AUDIT (M08)
    %% ========================================

    NIGHT_AUDIT {
        uuid id PK
        uuid enterprise_id FK
        date business_date
        decimal total_revenue
        int total_rooms_sold
        decimal adr
        decimal occupancy_rate
        enum status "PENDING | COMPLETED"
        uuid run_by FK
        timestamp started_at
        timestamp completed_at
    }

    %% ========================================
    %% LAYER 10: OTA & CHANNEL MANAGER (M09)
    %% ========================================

    OTA_CONNECTION {
        uuid id PK
        uuid enterprise_id FK
        enum ota_name "AGODA | BOOKING | TRAVELOKA | TRIP | EXPEDIA"
        string api_credential
        string endpoint
        boolean is_enabled
        enum sync_status "CONNECTED | DISCONNECTED | ERROR"
        timestamp last_sync_at
    }

    OTA_ROOM_MAPPING {
        uuid id PK
        uuid ota_connection_id FK
        uuid room_type_id FK
        string ota_room_code
        string ota_rate_code
    }

    OTA_SYNC_LOG {
        uuid id PK
        uuid ota_connection_id FK
        enum sync_type "INVENTORY | RATE | BOOKING | RECONCILIATION"
        enum direction "PUSH | PULL"
        enum status "SUCCESS | FAILED | RETRY"
        int retry_count
        string request_payload
        string response_payload
        string error_message
        timestamp created_at
    }

    %% ========================================
    %% LAYER 11: USER & AUTH (M12)
    %% ========================================
    %%
    %% User - Property Assignment:
    %% - SUPER_ADMIN:          property_id = NULL (platform-wide, Trustify only)
    %% - ENTERPRISE_ADMIN:      property_id = NULL (enterprise-wide, can switch properties)
    %% - PROPERTY_USER:        property_id = FK  (tied to specific property)
    %%
    %% Staff (PROPERTY_USER) chỉ belongsTo 1 property -> không cần switcher.
    %% Admin/Manager (ENTERPRISE_ADMIN) belongsTo 0 property -> switch được tất cả KS trong DN.
    %% Super Admin (SUPER_ADMIN) belongsTo 0 property -> switch được tất cả DN.
    %%

    USER {
        uuid id PK
        uuid enterprise_id FK
        uuid enterprise_id FK "nullable - platform admin has no property"
        string email
        string password_hash
        string full_name
        string phone
        enum user_level "SUPER_ADMIN | ENTERPRISE_ADMIN | PROPERTY_USER"
        enum status "ACTIVE | INACTIVE | INVITED"
        timestamp last_login_at
        timestamp created_at
        uuid invited_by FK
    }

    ROLE {
        uuid id PK
        uuid enterprise_id FK
        string name "Admin, Quản lý, Lễ tân, Buồng phòng, Kinh doanh, Kế toán, Quyền khác"
        boolean is_system_role
    }

    USER_ROLE {
        uuid id PK
        uuid user_id FK
        uuid role_id FK
    }

    PERMISSION {
        uuid id PK
        string module "M01, M02, M06..."
        string action "CREATE, READ, UPDATE, DELETE"
        string resource "reservation, room, folio..."
    }

    ROLE_PERMISSION {
        uuid id PK
        uuid role_id FK
        uuid permission_id FK
    }

    %% ========================================
    %% LAYER 12: NOTIFICATION (M13)
    %% ========================================

    NOTIFICATION {
        uuid id PK
        uuid enterprise_id FK
        uuid target_user_id FK
        enum severity "CRITICAL | WARNING | INFO"
        string title
        string message
        string deep_link_url
        enum channel "IN_APP | EMAIL"
        boolean is_read
        timestamp read_at
        timestamp created_at
    }

    %% ========================================
    %% LAYER 13: SHIFT HANDOVER
    %% ========================================

    SHIFT_HANDOVER {
        uuid id PK
        uuid enterprise_id FK
        uuid from_user_id FK
        uuid to_user_id FK
        datetime shift_start
        datetime shift_end
        text shift_summary "Log thông tin ca trước"
        decimal system_cash_balance
        decimal actual_cash_balance
        decimal cash_difference
        enum status "DRAFT | SUBMITTED | CONFIRMED"
        timestamp created_at
    }

    SHIFT_CHECKLIST_ITEM {
        uuid id PK
        uuid shift_handover_id FK
        string item_name
        boolean is_checked
        string notes
    }

    %% ========================================
    %% LAYER 14: AUDIT LOG
    %% ========================================

    AUDIT_LOG {
        uuid id PK
        uuid user_id FK
        uuid enterprise_id FK
        uuid enterprise_id FK
        enum action "LOGIN | LOGOUT | CREATE | UPDATE | DELETE | STATUS_CHANGE"
        string entity_type "Enterprise, Property, Room, Reservation..."
        uuid entity_id
        jsonb old_value
        jsonb new_value
        string ip_address
        string user_agent
        timestamp created_at
    }

    %% ========================================
    %% RELATIONSHIPS (D-031 — No Property)
    %% ========================================

    ENTERPRISE ||--o{ BUILDING : "has many"
    ENTERPRISE ||--o{ USER : "has many"

    %% ── ENTERPRISE-level entities ──
    ENTERPRISE ||--o{ ROOM_TYPE : "has many"
    ENTERPRISE ||--o{ PRICE_POLICY : "has many"
    ENTERPRISE ||--o{ EQUIPMENT_GROUP : "has many"
    ENTERPRISE ||--o{ SERVICE_CATEGORY : "has many"
    ENTERPRISE ||--|{ TIME_CONFIG : "has one"
    ENTERPRISE ||--o{ OTA_CONNECTION : "has many"
    ENTERPRISE ||--o{ RESERVATION : "has many"
    ENTERPRISE ||--o{ GUEST : "has many"
    ENTERPRISE ||--o{ NIGHT_AUDIT : "has many"
    ENTERPRISE ||--o{ NOTIFICATION : "has many"
    ENTERPRISE ||--o{ SHIFT_HANDOVER : "has many"

    BUILDING ||--o{ USER : "assigns to"
    %% BUILDING_USER: building_id FK set -> staff tied to 1 building
    %% SUPER_ADMIN/ENTERPRISE_ADMIN: building_id = NULL (platform-level)

    BUILDING ||--o{ FLOOR : "has many"
    FLOOR ||--o{ ROOM : "has many"
    BUILDING ||--o{ ROOM : "owns rooms"

    ROOM_TYPE ||--o{ ROOM : "categorizes"
    ROOM_TYPE ||--o{ ROOM_TYPE_PRICE_POLICY : "links"
    PRICE_POLICY ||--o{ ROOM_TYPE_PRICE_POLICY : "links"

    PRICE_POLICY ||--o{ PRICE_HOURLY : "has"
    PRICE_POLICY ||--o{ PRICE_DAILY : "has"
    PRICE_POLICY ||--o{ PRICE_NIGHTLY : "has"
    PRICE_POLICY ||--o{ PRICE_WEEKLY : "has"
    PRICE_POLICY ||--o{ PRICE_MONTHLY : "has"

    EQUIPMENT_GROUP ||--o{ EQUIPMENT : "has many"
    ROOM ||--o{ ROOM_EQUIPMENT : "has"
    EQUIPMENT ||--o{ ROOM_EQUIPMENT : "in"

    SERVICE_CATEGORY ||--o{ SERVICE_GROUP : "has many"
    SERVICE_GROUP ||--o{ SERVICE_ITEM : "has many"

    ROOM ||--o{ RESERVATION : "booked"
    GUEST ||--o{ RESERVATION : "stays"
    RESERVATION ||--|{ FOLIO : "has one"

    FOLIO ||--o{ FOLIO_CHARGE : "has many"
    FOLIO ||--o{ PAYMENT : "has many"

    ROOM ||--o{ HOUSEKEEPING_TASK : "assigned"

    OTA_CONNECTION ||--o{ OTA_ROOM_MAPPING : "maps"
    OTA_CONNECTION ||--o{ OTA_SYNC_LOG : "logs"
    ROOM_TYPE ||--o{ OTA_ROOM_MAPPING : "mapped to"

    USER ||--o{ USER_ROLE : "has"
    ROLE ||--o{ USER_ROLE : "assigned to"
    ROLE ||--o{ ROLE_PERMISSION : "has"
    PERMISSION ||--o{ ROLE_PERMISSION : "granted to"

    SHIFT_HANDOVER ||--o{ SHIFT_CHECKLIST_ITEM : "has"
```

---

## Tổng kết

| Layer | Entities | Source |
|-------|----------|--------|
| Platform | `ENTERPRISE` | Quản lý nền tảng |
| Building Config | `BUILDING`, `FLOOR` (D-031 — bỏ Property) | M01.1 |
| Room & Pricing | `ROOM_TYPE`, `ROOM`, `PRICE_POLICY`, 5 price tables, `ROOM_TYPE_PRICE_POLICY` | M01.2 |
| Equipment | `EQUIPMENT_GROUP`, `EQUIPMENT`, `ROOM_EQUIPMENT` | M01.4 |
| Services | `SERVICE_CATEGORY`, `SERVICE_GROUP`, `SERVICE_ITEM` | M01.6 |
| Time Config | `TIME_CONFIG` | M01.5 |
| Reservation | `GUEST`, `RESERVATION` | M02, M04 |
| Folio & Payment | `FOLIO`, `FOLIO_CHARGE`, `PAYMENT` | M07, M10 |
| Housekeeping | `HOUSEKEEPING_TASK` | M06 |
| Night Audit | `NIGHT_AUDIT` | M08 |
| OTA & CM | `OTA_CONNECTION`, `OTA_ROOM_MAPPING`, `OTA_SYNC_LOG` | M09 |
| User & Auth | `USER`, `ROLE`, `USER_ROLE`, `PERMISSION`, `ROLE_PERMISSION` | M12 |
| Notification | `NOTIFICATION` | M13 |
| Shift Handover | `SHIFT_HANDOVER`, `SHIFT_CHECKLIST_ITEM` | Bàn giao ca |
| Audit Log | `AUDIT_LOG` | Audit Log |

**Tổng: ~33 entities** covering toàn bộ 17 modules MVP1.
