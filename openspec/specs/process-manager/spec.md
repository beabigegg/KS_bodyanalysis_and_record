## ADDED Requirements

### Requirement: Multi-process orchestration
系統 SHALL 提供 `ProcessManager`，能同時啟動並管理 pipeline 和 web 兩個子 process。

#### Scenario: Start both services
- **WHEN** 使用者執行 `python -m ksbody all`
- **THEN** `ProcessManager` 啟動兩個子 process（pipeline 和 web），並進入健康檢查迴圈

#### Scenario: Graceful shutdown on SIGTERM
- **WHEN** 主 process 收到 SIGTERM 或 SIGINT
- **THEN** 系統 SHALL 向所有子 process 發送終止信號，等待最多 10 秒後強制終止，並記錄關閉日誌

#### Scenario: Child process isolation
- **WHEN** pipeline 子 process 發生未捕獲的 exception 而崩潰
- **THEN** web 子 process SHALL 不受影響繼續運行

### Requirement: Process health check
系統 SHALL 定期檢查子 process 的健康狀態。

#### Scenario: Process alive check
- **WHEN** 健康檢查迴圈每 10 秒執行一次
- **THEN** 系統透過 `Process.is_alive()` 檢查每個子 process 是否存活

#### Scenario: Web HTTP health check
- **WHEN** web 子 process 存活
- **THEN** 系統每 30 秒額外發送 `GET /api/health` 請求，預期回傳 HTTP 200

#### Scenario: Web startup grace period
- **WHEN** web 子 process 剛啟動
- **THEN** 系統 SHALL 等待 15 秒的 grace period 後才開始 HTTP 健康檢查

#### Scenario: HTTP health check timeout
- **WHEN** `/api/health` 在 5 秒內未回應
- **THEN** 系統視該子 process 為不健康，觸發重啟流程

### Requirement: Automatic restart with backoff
系統 SHALL 在子 process 異常退出時自動重啟，並實施退避策略。

#### Scenario: Auto restart on crash
- **WHEN** 子 process 異常退出（exit code != 0）
- **THEN** 系統 SHALL 記錄 exit code 並自動重啟該子 process

#### Scenario: Exponential backoff
- **WHEN** 同一子 process 連續崩潰
- **THEN** 重啟間隔 SHALL 按指數退避增長：`min(base_delay * 2^n, max_delay)`，預設 base=2s, max=60s

#### Scenario: Max restarts exceeded
- **WHEN** 同一子 process 在觀察窗口內連續重啟超過 `max_restarts`（預設 5 次）
- **THEN** 系統 SHALL 停止重啟該 process，記錄 CRITICAL 級別日誌，其他子 process 繼續運行

#### Scenario: Reset restart counter on stable run
- **WHEN** 子 process 成功運行超過穩定閾值（預設 120 秒）後才崩潰
- **THEN** 重啟計數器 SHALL 重置為 0，退避間隔回到 base_delay
