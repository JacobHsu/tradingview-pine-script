# Williams Fractals 1H 監控腳本

`scripts/check_crypto_fractals.py` 偵測 Williams Fractals（n=2）訊號，
比對 [jacobhsu/crypto-watch](https://jacobhsu.github.io/crypto-watch/) 第一格圖表，
找到後印到終端機並（若有設定 TG）推播到 Telegram。

## 涵蓋標的

| 標的 | 來源 | 對照頁面 |
|---|---|---|
| BTCUSDT | Binance | https://jacobhsu.github.io/crypto-watch/btc |
| ETHUSDT | Binance | https://jacobhsu.github.io/crypto-watch/eth |
| XAUT | Pionex | https://jacobhsu.github.io/crypto-watch/rwa?s=XAUT |
| SLVX | Pionex (PERP) | https://jacobhsu.github.io/crypto-watch/rwa?s=SLVX |
| USOX | Pionex (PERP) | https://jacobhsu.github.io/crypto-watch/rwa?s=USOX |
| EWJX | Pionex (PERP) | https://jacobhsu.github.io/crypto-watch/rwa?s=EWJX |
| EWYX | Pionex (PERP) | https://jacobhsu.github.io/crypto-watch/rwa?s=EWYX |

所有時間與 crypto-watch 一致（`Asia/Taipei`）。

## Fractal 邏輯（與 `Williams-Fractals.pine` 對齊）

n=2：bar `k` 為 fractal pivot 須比左右各 2 根都更極端。

- Up fractal（向上三角）：`high[k]` > 左右 ±2 根所有 high
- Down fractal（向下三角）：`low[k]` < 左右 ±2 根所有 low

⚠️ 因為要看右側 2 根，**最新可確認的 pivot 是倒數第 3 根**（`bars[-3]`）。
腳本從 `bars[-3]` 往回掃，找到第一個 fractal 即為「最近的三角形」。

## 本地端運行

### 前置一次性設定

```bash
cd d:/32-tv/tradingview-pine-script
pip install -r requirements.txt
```

`.env` 需含（已建立，不會被 commit）：

```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

未設定也能跑，只是會略過 TG 推播。

### 執行

Git Bash / WSL / macOS / Linux：

```bash
set -a && source .env && set +a
python scripts/check_crypto_fractals.py
```

Windows PowerShell：

```powershell
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([^#=]+?)\s*=\s*(.+)\s*$') { $env:($matches[1]) = $matches[2] }
}
python scripts/check_crypto_fractals.py
```

### 預期輸出

```
🕐 2026-06-05 11:44 (台北時間)

【 Williams Fractals 】

BTCUSDT   $62,650  ▲  08:00  High $63,978
ETHUSDT    $1,731  ▼  06:00  Low  $1,752
XAUT       $4,419  ▼  02:00  Low  $4,451
SLVX          $66  ▲  07:00  High $67
USOX         $137  ▼  09:00  Low  $136
EWJX          $93  ▼  09:00  Low  $93
EWYX         $194  ▼  09:00  Low  $190

https://jacobhsu.github.io/crypto-watch/eth
```

- `▲` 綠色 = up fractal（swing high，TV 圖上 olive 向上三角）
- `▼` 紅色 = down fractal（swing low，TV 圖上 maroon 向下三角）
- 時間是該 pivot K 線的開盤時間（台北時間）

ANSI 顏色在 Windows Terminal / VS Code 內建 terminal / git-bash mintty / PowerShell 都會渲染。
Telegram 不支援 ANSI，所以 TG 訊息中三角形為純黑色。

## 對帳流程

1. 跑 `python scripts/check_crypto_fractals.py`
2. 對照每個標的的 crypto-watch 頁面第一格（圖表時區設為 Asia/Taipei）
3. 在 K 線上找腳本印出的時間點，應有對應顏色與方向的三角形

對不上的話檢查順序：
- crypto-watch 圖表的時區是否真是 Asia/Taipei
- TV 的圖表來源是 Binance / Pionex（與本腳本一致）
- 該 pivot 是否仍在「未確認」狀態（最末 2 根 K 線的 fractal 還沒被未來資料驗證）

## 架構

```
fetch_binance(symbol) → list[Bar]   # BTC, ETH
fetch_pionex(symbol)  → list[Bar]   # XAUT, SLVX, USOX, EWJX, EWYX
                                    # 注意 Pionex 回傳新→舊，內部已 reverse

Bar = (open_time_ms, high, low, close)  # oldest → newest 排序

is_up_fractal(highs, k)  / is_down_fractal(lows, k)
report_line(display, bars) → 一行文字（含 ▲ 或 ▼）

main(): 抓所有標的 → 組 header + rows + footer → 印終端 + 送 TG
```

## 已知差異

| 項目 | 行為 |
|---|---|
| 收盤價 | Pionex API 與 TradingView 顯示偶有小數差異（不同撮合源），通常 < 0.1% |
| 最末 2 根 | Pine 圖上會「等」未來資料才畫三角形；本腳本同樣不對這 2 根判斷，避免假訊號 |
| 推送頻率 | 目前每次執行都會推一次完整快照，**尚未做去重** |

## GitHub Actions 排程

`.github/workflows/tv-crypto-alert.yml` 已設定：

- **排程**：cron `0 23 * * *` UTC = **每日台北時間 07:00**
- **手動觸發**：Actions 頁面點 *Run workflow*
- **環境變數**：repo secrets `TELEGRAM_BOT_TOKEN` 與 `TELEGRAM_CHAT_ID`

部署檢查清單：

1. GitHub repo → Settings → Secrets and variables → Actions
2. 新增 `TELEGRAM_BOT_TOKEN`（與 `.env` 同值）
3. 新增 `TELEGRAM_CHAT_ID`（與 `.env` 同值）
4. push 後到 Actions 頁面手動 *Run workflow* 跑一次驗證
5. 確認 TG 收到訊息

注意：每日 07:00 推一次完整 7 個標的最近 fractal 快照，**未做去重**（每天的訊號通常會不同，因 1H pivot 一天可能出現多個）。

## References

- [Williams Fractals with Alerts by MrTuanDoan](https://tw.tradingview.com/script/TblGMJyQ-Williams-Fractals-with-Alerts-by-MrTuanDoan/)
