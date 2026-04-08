## Context

Pipeline 的 folder-watcher 依賴 `WATCH_PATHS` 環境變數指定監控目錄。目前 `.env` 缺少此變數，且 `.env.example` 使用 Windows UNC 路徑（`\\10.1.1.43\eap_recipe_tracebility\WBK_ConnX Elite`），在 Linux 上 `Path.exists()` 回傳 `False`，導致 observer 啟動失敗。

SMB 共享結構（已驗證）：
```
//10.1.1.43/eap_recipe_tracebility/
└── WBK_ConnX Elite/
    ├── GWBK_TEST1/
    │   └── L_WBK_ConnX Elite@PJA3406@ECC17@WAF903898_1_1775539423
    └── GWBK_TEST2/
        └── L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1_1775539396
```

SMB 認證資訊已存在於 `.env`（`RECIPE_TRACE_SMB_*` 系列變數）。

## Goals / Non-Goals

**Goals:**
- Pipeline 部署後即可正常啟動 watcher，不再因路徑不存在而 crash
- `deploy.sh` 自動處理 SMB 掛載，部署即就緒
- `.env` 和 `.env.example` 使用正確的 Linux 本地路徑格式

**Non-Goals:**
- 不修改 observer / scanner / handler 程式碼邏輯
- 不處理多台 SMB server 或多個 share 的情境
- 不實作 SMB 斷線自動重連（由 cifs mount 選項處理）

## Decisions

### 1. 掛載路徑：`/mnt/eap_recipe`

將 `//10.1.1.43/eap_recipe_tracebility` 掛載到 `/mnt/eap_recipe`。

`WATCH_PATHS` 設為 `/mnt/eap_recipe/WBK_ConnX Elite`，observer `recursive=True` 自動遍歷所有機台子資料夾。

**替代方案**: 使用 `smbclient` 或 `pysmb` 在 Python 層直接存取 → 拒絕，因為 watchdog PollingObserver 需要本地檔案系統路徑，無法直接操作 SMB protocol。

### 2. 掛載方式：deploy.sh 中 idempotent mount

在 `deploy.sh` 的 Main 區塊、Python/npm 安裝之前，加入掛載邏輯：
1. 確認 `cifs-utils` 已安裝
2. 建立 `/mnt/eap_recipe` 目錄（如不存在）
3. 檢查是否已掛載（`mountpoint -q`），若已掛載則跳過
4. 使用 `.env` 中的 `RECIPE_TRACE_SMB_*` 變數執行 `mount.cifs`

認證方式使用 `credentials file`（從 `.env` 變數動態產生臨時檔案），避免密碼出現在 `ps` 指令的命令列中。

**替代方案**: 使用 `/etc/fstab` 靜態掛載 → 拒絕，因為需要 root 權限編輯系統檔案，且認證資訊與 `.env` 重複維護。

### 3. mount 選項

```
mount.cifs //10.1.1.43/eap_recipe_tracebility /mnt/eap_recipe \
  -o credentials=/tmp/.smb_creds,vers=3.0,uid=$(id -u),gid=$(id -g),file_mode=0444,dir_mode=0555
```

- `vers=3.0`: 明確指定 SMB 版本
- `uid/gid`: 使用部署使用者身份，確保 watcher 可讀取
- `file_mode=0444,dir_mode=0555`: 唯讀掛載，watcher 只需讀取

### 4. 複用 `.env` 中既有的 SMB 認證變數

不新增環境變數。`deploy.sh` 直接讀取 `.env` 中已有的：
- `RECIPE_TRACE_SMB_HOST` → mount server
- `RECIPE_TRACE_SMB_SHARE` → share name
- `RECIPE_TRACE_SMB_USER` → 認證帳號
- `RECIPE_TRACE_SMB_PASSWORD` → 認證密碼

`WATCH_PATHS` 由使用者在 `.env` 中設定掛載後的本地路徑。

## Risks / Trade-offs

- **[需要 sudo]** → `mount.cifs` 通常需要 root 權限。Mitigation: deploy.sh 以 sudo 執行掛載步驟，或將使用者加入適當群組。
- **[SMB 斷線]** → 網路中斷時掛載點變為不可存取。Mitigation: cifs mount 內建重連機制；observer 的 `path.exists()` 檢查會 log warning 但不影響其他路徑。
- **[認證臨時檔案]** → credentials file 短暫存在於 `/tmp`。Mitigation: mount 完成後立即刪除。
