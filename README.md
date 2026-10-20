# Google Cloud

## Yêu cầu

- [python](https://www.python.org/downloads/)
- [pnpm](https://pnpm.io/installation)
- [ngrok cli](https://ngrok.com/download) (kèm với tài khoản)
- Tài khoản Google

## Tạo project

### Bước 1

Tạo một project tại [đây](https://console.cloud.google.com/projectcreate)

### Bước 2

Xác thực ngrok theo [hướng dẫn](https://dashboard.ngrok.com/get-started/your-authtoken) và khởi chạy ngrok với cổng 8080

```bash
ngrok http 8080
```

### Bước 3

Lấy project id và tên miền ngrok lần lượt dán vào `{ID_project}` và `{Web_URL}` vào script này

```
provider "google" {
  project = "{ID_project}"
}

# 1. Bật các API cần thiết
resource "google_project_service" "services" {
  for_each = toset([
    "gmail.googleapis.com",
    "pubsub.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# 2. Tạo Pub/Sub Topic
resource "google_pubsub_topic" "gmail_topic" {
  name       = "gmail-notifications-topic"
  depends_on = [google_project_service.services]
}

# 3. Cấp quyền cho hệ thống Gmail push tin nhắn vào Topic
resource "google_pubsub_topic_iam_member" "gmail_publisher" {
  topic  = google_pubsub_topic.gmail_topic.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:gmail-api-push@system.gserviceaccount.com"
}

# 4. Tạo Push Subscription trỏ về Webhook của bạn
resource "google_pubsub_subscription" "gmail_sub" {
  name  = "gmail-notifications-sub"
  topic = google_pubsub_topic.gmail_topic.name

  push_config {
    push_endpoint = "{Web_URL}/api/webhooks/gmail"
  }
}
```

### Bước 4

Vào [web](https://console.cloud.google.com/welcome?cloudshell=true) này và chạy lệnh sau đây trong terminal

```bash
cat << 'EOF' > main.tf
{Script_ở_bước_3}
EOF
```

### Bước 5

Cài terraform

```bash
wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
bash
```

Kích hoạt [service](https://console.cloud.google.com/apis/api/cloudresourcemanager.googleapis.com) và chạy lệnh

```bash
terraform init
terraform apply
```

## Lấy credentials.json

- Đầu tiên, cấu hình OAuth consent screen tại [Google Auth Platform](https://console.cloud.google.com/auth/overview) và chọn **External**.
- Tiếp theo, vào trang [web](https://console.cloud.google.com/apis/credentials). Chọn **Create Credentials** -> **OAuth client ID** -> **Desktop app**. Tải file json và đặt vào thư mục với tên `credentials.json`
- Cuối cùng, thêm email vào test user tại [đây](https://console.cloud.google.com/auth/audience)

# Scripts

Từ thư mục gốc repository, tạo một môi trường ảo riêng cho script:

```bash
python -m venv .venv
source .venv/bin/activate # Linux
.venv/Scripts/Activate.ps1 # Windows
python -m pip install -r requirements.txt
```

## Tạo người dùng

```bash
python -m backend.helper create-user --name "Nguyen Viet Anh" --username vanh --password test.com.vn --email anhvietng62@gmail.com
```

## Khởi động ứng dụng

### Yêu cầu

Truyền giá trị project id và 2 địa chỉ email vào câu lệnh này và chạy trước khi khởi chạy ứng dụng

**Linux/Mac:**

```bash
cat << 'EOF' > .env
pubsub_oidc_topic=projects/{ID_project}/topics/gmail-notifications-topic
manager_email={Email_người_quản_lý}
sender_email={Email_hệ_thống}
EOF
```

**Windows (Command Prompt):**

```cmd
echo pubsub_oidc_topic=projects/{ID_project}/topics/gmail-notifications-topic >> .env
echo manager_email={Email_người_quản_lý} >> .env
echo sender_email={Email_hệ_thống} >> .env
```

Biên dịch frontend trước khi chạy lệnh

```bash
cd frontend && pnpm build && cd ..
```

### Lệnh khởi chạy

```bash
python -m backend.app.main
```

## Khởi động script nhỏ

```bash
python -m "script.send&recieve" --help
```
