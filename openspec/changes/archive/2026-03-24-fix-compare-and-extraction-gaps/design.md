## Context

KS body recipe 一個壓縮檔內含多種副檔名的檔案，分屬「機台共用設定」（BND、APP、RPM…）與「die 專屬設定」（PHY、PRM、LF、MAG、REF 等，以 die 代碼為檔名前綴，如 `CJ621A20.PRM`）。目前 import pipeline 將所有解析結果以 `(file_type, param_name)` 作為唯一鍵寫入 `recipe_params`，沒有區分 die 身份。比較功能（`compare.py`）雖涵蓋 recipe_params / app_spec / bsg 三個資料源，但完全漏掉 RPM 資料，且 `_diff_rows` 的 None 判斷邏輯存在邏輯錯誤。

已知兩個 sample recipe（PJA3406、PJS6400）的 die 配置：
- Die 1（`CJ621A20` / `AP643419`）：PHY 34 params（handler slot 設定）
- Die 2（`CJ621A41` / `AP643441`）：PHY 419 params（主要 bonding 物理）
- 兩組 die 的 PHY param_name 零重疊，PRM param_value 也完全一致

## Goals / Non-Goals

**Goals:**
- 修正 `_diff_rows` None 判斷，讓「一方有值、另一方 NULL」正確標為差異
- 將 BSG 從 params 查詢中排除，消除重複
- 新增 RPM limits 與 RPM reference 的跨機台 diff 邏輯（後端 + 前端）
- 在 import 時為 die 專屬檔案的 param_name 加上 die 代碼前綴
- 停止將 AID 資料寫入 recipe_params（無比較價值）

**Non-Goals:**
- 不改變 APP / BSG / RPM 各自的獨立比較區塊設計
- 不新增 die 層級的獨立資料表（die 前綴方案足夠，不需 schema 變更）
- 不實作 RPM 統計值的圖形化比較，只做數值 diff 表格
- 不對現有 import 記錄做 migration（重新 import 即可）

## Decisions

### Decision 1：die 前綴格式選 `<die_code>/<param_name>` 而非新增欄位

**選擇**：在現有 `param_name` 欄位前加上 die 代碼，格式為 `CJ621A20/Bond1_Force_Seg_01`。

**理由**：
- `recipe_params` 欄位 `VARCHAR(1024)` 足以容納
- 無需 schema migration，只改 pipeline 邏輯
- 查詢時用 `LIKE 'CJ621A20/%'` 或前端用 `/` 分割即可解析
- 替代方案「新增 `die_code` 欄位」需要 ALTER TABLE 並破壞現有 EAV index

**判斷 die 專屬 vs. 機台共用的規則**：
```
die 專屬（加前綴）：PHY, PRM, LF, MAG, REF
機台共用（不加前綴）：BND, APP, BSG, AIC, LHM, VHM, PPC, RPM, AID
```
規則依據：die 專屬檔案的檔名以 die 代碼開頭（如 `CJ621A20.PRM`），機台共用檔案的檔名以機台/工件 ID 開頭（如 `MR192600.BND`、`PJA3406_.AIC`）。

### Decision 2：die 代碼從檔名前綴提取，而非外部映射表

從解壓後的檔案路徑中提取 die 代碼，例如 `CJ621A20.PRM` → die_code = `CJ621A20`。這個資訊在 parse 時即可取得（`path.stem`），不需額外設定。

### Decision 3：AID 在 pipeline 層過濾，不改 CsvParser

`CsvParser` 保持通用，由 `pipeline.py` 在 parse 後丟棄 AID 的 params（`if file_type == "AID": skip`）。這樣 CsvParser 不需要知道業務語義。

### Decision 4：RPM compare 的 key 設計

`recipe_rpm_limits` 的複合 key：`(signal_name, property_name, rpm_group, bond_type, measurement_name, limit_type, statistic_type, parameter_set)`
比較值：`lower_limit`、`upper_limit`、`active`

`recipe_rpm_reference` 的複合 key：`(signal_name, property_name, rpm_group, bond_type, measurement_name, source)`
比較值：`average`、`median`、`std_dev`、`median_abs_dev`、`minimum`、`maximum`、`sample_count`

由於 RPM 資料的比較值有多個欄位（不像 recipe_params 只有一個 param_value），需要新的 diff 函數 `_diff_rpm_rows` 支援多值欄位輸出。

### Decision 5：修正後的 None 判斷邏輯

```python
# 修正前（錯誤：None 被排除，導致「有 vs. 沒有」被視為相同）
is_diff = len({str(v) for v in values if v is not None}) > 1

# 修正後：只要有任何一方為 None、另一方非 None，就算差異
non_null_values = {str(v) for v in values if v is not None}
has_any_value = len(non_null_values) > 0
all_have_value = all(v is not None for v in values)
is_diff = len(non_null_values) > 1 or (has_any_value and not all_have_value)
```

## Risks / Trade-offs

**[BREAKING 資料格式]** die 前綴讓所有 PHY/PRM/LF/MAG/REF 的 param_name 格式改變
→ 緩解：這是改善，舊資料需重新 import。因為現有資料少且正確性已有疑慮，重新 import 成本可接受。

**[die 前綴規則的邊界情境]** 若未來有新機型，die 代碼命名規則可能不同
→ 緩解：Decision 2 的判斷方式是動態提取（從 path.stem），不是寫死對照表，對新機型自然適用。

**[RPM diff 輸出格式]** RPM 一行有多個比較值（lower_limit / upper_limit / active），前端需要新的表格格式
→ 緩解：設計成 `{"key": {...key fields...}, "field": "lower_limit", "values": {...}}` 的展開格式，與現有 DiffTable 元件保持相容。

**[AID 資料移除]** 已匯入的 AID params 在重新 import 後會消失
→ AID 只有 measurement name 與 unit 定義，沒有數值，從未產生比較差異，移除無業務影響。

## Migration Plan

1. 停止服務（或等待低峰）
2. 清空 `ksbody_recipe_params`、`ksbody_recipe_import`（及所有 FK 關聯表）
3. 部署新版 pipeline（含 die 前綴邏輯、AID 過濾）
4. 重新觸發 import 所有現有 recipe body 檔案（watcher 重掃目錄，或手動執行 import）
5. 部署新版 API（含 RPM compare、修正 None 邏輯、BSG 排除）
6. 部署新版前端（含 RPM Diff 區塊）

**Rollback**：回退 pipeline 版本後重新 import 即可還原，無不可逆操作。

## Open Questions

- `recipe_params.param_name` 欄位目前是 `VARCHAR(1024)`，`<die_code>/<param_name>` 最長約 20 + 1 + 1024 = 1045，需確認是否需要 ALTER TABLE 擴大欄位（或縮短 param_name 上限）
- 前端 `ComparePage` 的 RPM Diff 區塊：limits 與 reference 是否合併為一個摺疊表格，或分開兩個 section？
- `show_all=False` 時，RPM reference 的統計值（average、std_dev 等連續值）幾乎永遠不同——是否對 RPM reference 的 diff 設計不同的顯示邏輯（如顯示差異百分比）？
