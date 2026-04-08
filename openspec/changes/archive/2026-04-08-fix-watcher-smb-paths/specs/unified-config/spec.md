## MODIFIED Requirements

### Requirement: Graceful defaults for mode-specific settings
系統 SHALL 對只有特定服務需要的設定提供合理預設值，使單獨啟動 pipeline 或 web 時不需要配置對方的必要變數。

#### Scenario: Run web without WATCH_PATHS
- **WHEN** 僅啟動 web 服務且 `WATCH_PATHS` 未設定
- **THEN** `get_settings().watch_paths` 回傳空 list，不拋出錯誤

#### Scenario: Run pipeline without APP_HOST
- **WHEN** 僅啟動 pipeline 且 `APP_HOST` 未設定
- **THEN** `get_settings().app_host` 使用預設值 `0.0.0.0`

#### Scenario: WATCH_PATHS uses Linux local mount path
- **WHEN** `.env` 設定 `WATCH_PATHS=/mnt/eap_recipe/WBK_ConnX Elite`
- **THEN** `get_settings().watch_paths` 回傳包含該 `Path` 物件的 list

#### Scenario: .env.example documents mount path format
- **WHEN** 使用者參考 `.env.example` 設定 `WATCH_PATHS`
- **THEN** 範例值 SHALL 為 Linux 本地掛載路徑格式（如 `/mnt/eap_recipe/WBK_ConnX Elite`），而非 Windows UNC 路徑
