刺蝟夏特（Shadow the Hedgehog）台灣繁體中文化補丁
==================================================

補丁檔：Shadow.the.Hedgehog.Japan.zh-TW.xdelta

■ 需要的原版遊戲
  Shadow the Hedgehog (Japan) (En,Ja,Fr,De,Es,It)　GameCube 日版，遊戲代碼 GUPJ8P
  必須是未修改的 ISO（1,459,978,240 bytes）：
    CRC32  529BAA3A
    MD5    dfb476c117536bbb1a1e1c103fb65216
    SHA-1  1d4d1a069d87bdcc6985ffd16d1d19328bb3ae69

  如果手上是 .rvz / .gcz 等壓縮格式，先用 Dolphin 轉回 ISO：
    遊戲清單上按右鍵 →「轉換檔案…」→ 格式選「ISO」
  或用命令列：
    DolphinTool.exe convert -i "原檔.rvz" -o "Shadow (Japan).iso" -f iso

■ 套用補丁
  任選一種：
  ・Delta Patcher（Windows 圖形介面）：Original file 選原版 ISO，
    XDelta patch 選本補丁，按「Apply patch」
  ・xdelta3 命令列：
    xdelta3 -d -s "Shadow (Japan).iso" "Shadow.the.Hedgehog.Japan.zh-TW.xdelta" "Shadow the Hedgehog (zh-TW).iso"

  套用後的 ISO：
    SHA-1  {out_sha1}

■ 遊玩
  ・用 Dolphin 或支援 ISO 的 GameCube 載入器開啟。
  ・中文取代的是遊戲的「日文」文字：遊戲內選項的字幕語言請維持日文。
    （英、法、德、西、義文維持原樣。）
  ・語音不變，可在選項中切換日語／英語語音。

■ 內容
  ・全部 12,405 句文字：選單、資料庫、存檔訊息、CG 影片字幕、各關卡語音字幕
  ・標題 LOGO、23 張關卡標題卡、主選單／故事模式／暫停選單／選擇模式／
    遊戲結束／對戰模式等介面圖片
  ・記憶卡存檔註解、光碟錯誤訊息、逐行掃描模式提示
  ・譯名依 SEGA 官方繁體中文（夏特、露姬、蛋頭博士、混沌翡翠……），
    E-123「Omega」保留英文，黑暗末日（Black Doom）、黑暗軍團（Black Arms）

■ 技術說明
  為了讓每段文字的字型容納中文，補丁新增了字型頁，並修改 main.dol，
  讓遊戲在內建檔案清單之外也能找到新增的檔案。
