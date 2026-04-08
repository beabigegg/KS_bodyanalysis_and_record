## Context

目前 watcher 已能遞迴掃描 SMB 掛載路徑與子資料夾，但 recipe body 判斷依賴固定 regex，只接受 `L_<machine>@<product>@<bop>@<wafer>_<version>`。實際 SMB 檔案新增了尾碼 timestamp，格式變成 `L_<machine>@<product>@<bop>@<wafer>_<version>_<timestamp>`，因此檔案在 watcher、掃描器、watcher API 與 metadata parser 的共同入口都被排除。

同時，系統資料表由 `ksbody.db.schema` 定義為 `ksbody_*` 實體表，但執行 `ksbody all`、`ksbody pipeline` 或 `ksbody web` 前若未先手動執行 `ksbody init-db`，服務流程可能在首次寫入或查詢時才發現資料表不存在。這讓部署成功與否依賴人工前置步驟，對 SMB watcher 與 web API 都是不穩定前提。

## Goals / Non-Goals

**Goals:**
- 讓 watcher、full scan、watcher file browser 與 metadata parser 一致接受 timestamp 尾碼 recipe 檔名。
- 保留舊格式檔名相容性，不改變 `recipe_version` 的意義。
- 定義並實作共用 MySQL schema bootstrap，確保服務啟動路徑能安全建立缺少的 `ksbody_*` 資料表。
- 明確文件化新的檔名契約與初始化行為。

**Non-Goals:**
- 不變更 SMB 掛載方式或檔案寫入端命名策略。
- 不引入 migration framework 或版本化 schema 遷移工具。
- 不改變既有 table 結構欄位設計，除非為了對齊既有 `ksbody_*` schema 命名。

## Decisions

### 1. Recipe 檔名改為支援可選的 timestamp 尾碼

將 recipe body 的檔名規則改為接受：
- `..._<recipe_version>`
- `..._<recipe_version>_<timestamp>`

其中 timestamp 視為可選附加欄位，不參與 metadata 寫庫，也不影響 `recipe_version`。這能維持既有資料模型不變，並讓 watcher 與 parser 共用同一份命名契約。

替代方案是把最後兩段都視為版本資訊的一部分，但這會破壞既有 `recipe_version` 欄位語意，也讓歷史資料不可比較，因此不採用。

### 2. 由 shared helper 統一 recipe 檔名辨識與解析

watcher 過濾與 metadata parser 目前各自持有相似但分離的 regex。實作時應集中到共享 helper 或共享 pattern 常數，讓「可否當 recipe body」與「如何提取欄位」遵循同一份規則，避免 watcher 接受但 parser 失敗，或反之。

替代方案是只各自修改 regex；這樣改動快，但之後很容易再次漂移，因此不採用。

### 3. 以 idempotent bootstrap 確保 `ksbody_*` schema 存在

保留 `ksbody init-db` 作為顯式初始化命令，同時在服務啟動路徑加入 `metadata.create_all()` 型 bootstrap，讓 pipeline、web 與 `ksbody all` 在首次連線 MySQL 時能自動補齊缺失表。此 bootstrap 必須是 idempotent，可重複執行而不破壞既有資料。

替代方案是只更新 README 要求手動先跑 `init-db`。這無法消除部署脆弱點，也不能避免 `all` 模式啟動後才在子程序撞到缺表，因此不採用。

### 4. 在主啟動路徑先完成 bootstrap，再啟動子服務

`ksbody all` 模式下，應由主程序先完成 schema bootstrap，再建立 pipeline / web 子程序。這可以避免兩個子程序同時競爭首次建表，並讓錯誤更集中在單一啟動點。

對單獨的 `ksbody pipeline` 與 `ksbody web`，各自啟動前也應執行相同 bootstrap，確保單服務模式不依賴 `all`。

## Risks / Trade-offs

- [Regex 放寬後誤收非 recipe 檔案] → 僅允許尾碼為數字 timestamp，且保留原本 `L_` / `@` / wafer / version 結構。
- [bootstrap 需要建表權限] → 文件中明確說明部署帳號需具備 `CREATE TABLE` / `CREATE INDEX` 權限；若無權限，啟動時應快速失敗並記錄明確錯誤。
- [舊規則散落多處] → 以共享 helper 或共同 pattern 收斂，並補 watcher、parser、API 的測試。
- [create_all 無法處理未來複雜 migration] → 本變更僅處理缺表 bootstrap，不涵蓋 schema 版本演進。

## Migration Plan

1. 更新 spec 後實作共享 recipe filename helper，支援 timestamp 尾碼。
2. 更新 watcher、scanner、watcher API 與 metadata parser，全部改用共享規則。
3. 在 DB 初始化模組提供可重用 bootstrap function，並在 `pipeline`、`web`、`all` 啟動路徑呼叫。
4. 補測試覆蓋舊檔名、新檔名、缺表啟動與 idempotent bootstrap。
5. 部署時直接以 `ksbody all` 或單服務模式啟動；若 MySQL schema 為空，系統自動建立表。

Rollback:
- 若新檔名規則造成誤判，可退回舊 regex 與 parser 邏輯。
- 若自動 bootstrap 導致啟動問題，可暫時改回顯式 `ksbody init-db` 流程。

## Open Questions

- 無。timestamp 已確認是檔名尾碼規則，且不需要入庫欄位。
