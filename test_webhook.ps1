# Test Webhook Script for VoC Analytics
# ทดสอบส่ง feedback ผ่าน webhook API

$WEBHOOK_SECRET = "dev-pp-webhook-secret-change-in-production"

Write-Host "🧪 Testing VoC Analytics ML Pipeline..." -ForegroundColor Cyan
Write-Host ""

# Test data - feedback ภาษาไทย
$body = @{
    email_id = "test-ml-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    sender_email = "test@example.com"
    subject = "รีวิวสนามกีฬา"
    body = "อุปกรณ์ออกกำลังกายดีมาก สะอาดด้วย พนักงานน่ารักทุกคน บรรยากาศดี แต่ที่จอดรถน้อยไปหน่อย ราคาแพงไปนิด มีคลาสโยคะวันอาทิตย์ไหมครับ"
    received_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

Write-Host "📤 Sending feedback to webhook..." -ForegroundColor Yellow
Write-Host "URL: http://localhost:8000/api/v1/webhooks/email"
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/webhooks/email" `
        -Method POST `
        -Headers @{
            "X-Webhook-Token" = $WEBHOOK_SECRET
            "Content-Type" = "application/json"
        } `
        -Body $body

    Write-Host "✅ Webhook Success!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 5
    Write-Host ""

    $recordId = $response.record_id
    Write-Host "📝 Record ID: $recordId" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "⏳ Waiting for ML processing (5 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5

    Write-Host ""
    Write-Host "📊 Fetching analysis results..." -ForegroundColor Yellow
    $results = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/feedback/$recordId"

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "🔮 ML ANALYSIS RESULTS" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "📝 Feedback Text:" -ForegroundColor Green
    Write-Host $results.text_content
    Write-Host ""

    Write-Host "📊 Processing Status: $($results.processing_status)" -ForegroundColor Green
    Write-Host ""

    if ($results.sentiment_results -and $results.sentiment_results.Count -gt 0) {
        $sentiment = $results.sentiment_results[0]
        Write-Host "💭 Overall Sentiment:" -ForegroundColor Magenta
        Write-Host "   Label: $($sentiment.sentiment)"
        Write-Host "   Confidence: $([math]::Round($sentiment.confidence * 100, 2))%"
        Write-Host ""
    }

    if ($results.intent_results -and $results.intent_results.Count -gt 0) {
        Write-Host "🎯 Intent Classification:" -ForegroundColor Magenta
        foreach ($intent in $results.intent_results) {
            Write-Host "   • $($intent.intent): $([math]::Round($intent.confidence * 100, 2))%"
        }
        Write-Host ""
    }

    if ($results.aspect_sentiment_results -and $results.aspect_sentiment_results.Count -gt 0) {
        Write-Host "📋 Aspect-Based Sentiment:" -ForegroundColor Magenta
        foreach ($aspect in $results.aspect_sentiment_results) {
            $emoji = switch ($aspect.sentiment) {
                "positive" { "😊" }
                "negative" { "😞" }
                "neutral" { "😐" }
                default { "📌" }
            }
            Write-Host "   $emoji $($aspect.aspect): $($aspect.sentiment) ($([math]::Round($aspect.confidence * 100, 2))%)"
        }
        Write-Host ""
    }

    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "✅ TEST COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan

} catch {
    Write-Host "❌ Error occurred:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    if ($_.ErrorDetails.Message) {
        Write-Host "Details:" $_.ErrorDetails.Message
    }
}
