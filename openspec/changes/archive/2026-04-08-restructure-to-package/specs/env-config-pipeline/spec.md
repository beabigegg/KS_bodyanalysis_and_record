## REMOVED Requirements

### Requirement: Pipeline settings from environment variables
**Reason**: 被 `unified-config` capability 取代。原本 `config/settings.py` 提供的 pipeline 專用設定功能已合併到 `ksbody/config.py` 中。
**Migration**: 所有原本使用 `from config.settings import load_settings` 的程式碼改為 `from ksbody.config import get_settings`。`AppSettings` dataclass 由統一的 `Settings` 取代。

### Requirement: Unified .env.example at project root
**Reason**: 此需求仍然存在但改由 `unified-config` spec 管理。`.env.example` 的內容和維護責任轉移至新的統一設定模組。
**Migration**: 無需遷移，`.env.example` 格式不變，仍位於專案根目錄。

### Requirement: Remove config.yaml dependency
**Reason**: 此需求已完成（config.yaml 依賴已在先前的 change 中移除），殘留的 `config.yaml` 檔案將在本次 change 中從 git 歷史中清除。
**Migration**: 執行 `git filter-repo --path config.yaml --invert-paths` 清理歷史。
