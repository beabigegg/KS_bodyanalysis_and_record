## Why

目前 import pipeline 使用 component 檔名前綴（如 `CJ621A20/param_name`）來區分多組 PHY/PRM 參數，但這些檔名是 KS ConnX Elite 自動產生的時間戳記代碼，對使用者毫無語意意義。BND 主檔實際上已明確定義每個 component 的機台角色（`mag_handler`、`workholder` 等），應以此作為前綴的語意來源。

## What Changes

- **新增 BND Registry Parser**：解析 BND 主檔的 top-level 宣告區與 `master_device` block，建立 `ComponentRegistry`（stem → 角色的映射表）
- **語意化 param_name 前綴**：PHY 參數從 `CJ621A20/IN_FIRST_SLOT` 改為 `mag_handler/IN_FIRST_SLOT`；workholder PHY 改為 `workholder/`；PRM 改為 `parms/`；REF 改為 `die_ref/` 或 `lead_ref/`
- **BSG-aware parms_2 處理**：當一個 recipe 有多個 `parms` 宣告時，比較 PRM 值差異與 BSG 存在差異，決定是否保留為 `parms_2`；若值完全相同且 BSG 狀態相同則合併為單一 `parms`
- **唯一 component 不加前綴**：`LF`、`MAG`、`HB`、`IRS`、`WIR` 每個 PP 只有一個，不加前綴
- **BREAKING**：`param_name` 格式從時間戳記前綴改為語意前綴，現有資料需重新 import

## Capabilities

### New Capabilities
- `bnd-component-registry`: 從 BND 主檔提取 ComponentRegistry，建立 stem→role 映射，供 pipeline 解析各 component 時使用

### Modified Capabilities
- `recipe-parser`: 修改 pipeline 解析邏輯，改為先解析 BND 取得 ComponentRegistry，再以語意角色為前綴解析各 component 檔案

## Impact

**後端**
- `parsers/bnd_registry.py`（新增）：BND Registry Parser，輸出 `ComponentRegistry` dataclass
- `pipeline.py`：解析流程改為 BND-first，取得 registry 後再解析各 component，套用 `resolve_role()` 決定 param_name 前綴
- `parsers/registry.py`：現有 BND parser（`SectionedParser`）繼續處理 BND 的 machine-level 參數（`mc_serial`、`wire_size` 等），新增 registry parser 專責角色映射

**資料庫**
- `ksbody_recipe_params.param_name`：格式 **BREAKING** 變更，需清空並重新 import 所有資料
- schema 欄位無需變更（`param_name VARCHAR(1024)` 足夠）
