# Google Cloud
## Tạo project
```bash
# 1. Đặt ID cho project
export PROJECT_ID="gmail-pubsub-$(date +%s)"
export WEBHOOK_URL="https://your-domain.com/api/webhook" # Thay URL webhook của bạn ở đây

# 2. Tạo Project mới
gcloud projects create $PROJECT_ID --name="Gmail PubSub Automation"

# 3. Đặt Project làm mặc định cho gcloud CLI
gcloud config set project $PROJECT_ID

# 4. Tự động liên kết Billing Account (Bắt buộc để Pub/Sub hoạt động)
BILLING_ID=$(gcloud billing accounts list --format="value(name)" | head -n 1)
if [ -n "$BILLING_ID" ]; then
  echo "Đang liên kết Billing Account: $BILLING_ID"
  gcloud billing projects link $PROJECT_ID --billing-account=$BILLING_ID
else
  echo "CẢNH BÁO: Không tìm thấy Billing Account nào trong tài khoản!"
fi

# 5. Kích hoạt Gmail API & Pub/Sub API
gcloud services enable gmail.googleapis.com pubsub.googleapis.com
sleep 60

# 6. Tạo Pub/Sub Topic
gcloud pubsub topics create gmail-notifications

# 7. Cấp quyền Publisher cho Gmail Service Account
gcloud pubsub topics add-iam-policy-binding gmail-notifications \
  --member="serviceAccount:gmail-api-push@system.gserviceaccount.com" \
  --role="roles/pubsub.publisher"

# 8. Tạo Push Subscription trỏ trực tiếp đến Webhook URL
gcloud pubsub subscriptions create gmail-push-sub \
  --topic=gmail-notifications \
  --push-endpoint="$WEBHOOK_URL" \
  --ack-deadline=30
```

## Lấy credentials.json
- Đầu tiên, cấu hình OAuth consent screen tại [Google Auth Platform](https://console.cloud.google.com/auth/overview) và chọn **External**.
- Tiếp theo, vào trang [web](https://console.cloud.google.com/apis/credentials). Chọn **Create Credentials** -> **OAuth client ID** -> **Desktop app**.