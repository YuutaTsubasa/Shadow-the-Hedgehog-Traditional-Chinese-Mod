# 刺蝟夏特 繁體中文化 MOD

GameCube《Shadow the Hedgehog》（日版 GUPJ8P）的台灣繁體中文化補丁與建置工具。

> 《Shadow the Hedgehog》及其文字、圖片的權利屬於 SEGA；本 MOD 為非官方的粉絲作品。
> 本 repo 不含任何遊戲資料，需要自備正版遊戲。

## 內容

- 全部 12,405 句文字：選單、資料庫、存檔訊息、CG 影片字幕、各關卡語音字幕
- 標題 LOGO、23 張關卡標題卡、主選單／故事模式／暫停選單／選擇模式／遊戲結束／對戰模式等介面圖片
- 記憶卡存檔註解、光碟錯誤訊息、逐行掃描模式提示
- 譯名依 SEGA 官方繁體中文（夏特、露姬、蛋頭博士、混沌翡翠……）；E-123「Omega」保留英文；
  黑暗末日（Black Doom）、黑暗軍團（Black Arms）；關卡名稱譯成中文（西方都市、空中艦隊……）

## 玩家：套用補丁

到 [Releases](../../releases) 下載 `.xdelta` 補丁，依附帶的 README 操作：

1. 準備未修改的日版 ISO（`Shadow the Hedgehog (Japan) (En,Ja,Fr,De,Es,It)`，SHA-1 `1d4d1a069d87bdcc6985ffd16d1d19328bb3ae69`）。
   `.rvz` 可用 Dolphin 右鍵「轉換檔案…」轉成 ISO。
2. 用 Delta Patcher 或 `xdelta3 -d -s 原版.iso 補丁.xdelta 中文版.iso` 套用。
3. 用 Dolphin 開啟。中文取代的是遊戲的日文文字，遊戲選項的字幕語言請維持日文。

## 開發：自己建置

需要 Python 3.10+、Pillow、Windows 的 Noto Sans TC（`C:/Windows/Fonts/NotoSansTC-VF.ttf`）、Dolphin 的 `DolphinTool.exe`、xdelta3（放在 `work/bin/xdelta3.exe` 或設定 `XDELTA3`）。

```bash
PYTHONUTF8=1 python tools/prepare.py "Shadow the Hedgehog (Japan).rvz" path/to/DolphinTool.exe
PYTHONUTF8=1 python tools/build.py      # -> out/*.iso, out/*.xdelta, out/README.txt
```

| 檔案 | 用途 |
| --- | --- |
| `tools/prepare.py` | 從自己的 rvz/iso 產生 `work/original.iso`、`work/disc/`、`text/ja/` |
| `tools/extract.py` | `.fnt` 訊息表 → `text/ja/<FILE>.json`（含講話者） |
| `tools/tl.py` | 翻譯流程：`next` / `commit` / `check` / `status`，見 [TRANSLATING.md](TRANSLATING.md) |
| `tools/build.py` | 文字＋字型＋貼圖＋DOL 補丁 → ISO，並產生、驗證 xdelta 補丁 |
| `tools/fnt.py` | `.fnt` 訊息表（UTF-16LE）讀寫 |
| `tools/font.py` | 每個訊息表專用的字型頁（RenderWare TXD + `.met`），用 Noto Sans TC 重畫中文 |
| `tools/txd.py` | RenderWare GameCube 貼圖（C4/C8/RGB5A3）讀寫 |
| `tools/tex.py` | 介面圖片上的文字換成中文 |
| `tools/dolpatch.py` | `main.dol` 補丁：讓遊戲讀得到新增的字型頁；系統訊息中文化 |
| `tools/gcm.py` | GameCube 光碟映像：重建 FST、寫入或新增檔案 |

譯文在 `text/zh/<FILE>.json`（`{訊息ID: 譯文}`），譯名表在 `text/glossary.json`。

### 技術筆記

- 每個訊息表（`fonts/<F>/<F>_JP.fnt`）都有自己的字型：TXD 裡的 256×256 C4 頁 + `<F>_JPnn.met` 字元座標，
  以 Unicode 碼查表。字型物件最多 10 頁，字多的檔案改用 256×512 頁。
- 遊戲開檔前會先查 `main.dol` 內建的檔名清單，新增的 `.met` 不在清單上；
  補丁讓清單查不到時改查光碟 FST（`DVDConvertPathToEntrynum`）。
- 系統訊息用主機的 Shift-JIS 字型顯示，只能用 JIS 裡有的漢字。

## 授權

工具程式與譯文以 [MIT](LICENSE) 授權。遊戲本身的權利屬於 SEGA。
