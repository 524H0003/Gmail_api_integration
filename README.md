# Google Cloud

## Tạo project

```
provider "google" {
  project = "{ID project}"
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
    push_endpoint = "{Webhook Endpoint}/api/webhooks/gmail"
  }
}
```

## Lấy credentials.json

- Đầu tiên, cấu hình OAuth consent screen tại [Google Auth Platform](https://console.cloud.google.com/auth/overview) và chọn **External**.
- Tiếp theo, vào trang [web](https://console.cloud.google.com/apis/credentials). Chọn **Create Credentials** -> **OAuth client ID** -> **Desktop app**.

# Scripts

## Tạo người dùng

```bash
python -m backend.helper create-user --name "Nguyen Viet Anh" --username vanh --password test.com.vn --email anhvietng62@gmail.com
```

## Khởi động ứng dụng

```bash
python -m backend.app.main
```

## Khởi động script nhỏ

```bash
python -m "script.send&recieve" --help
```
