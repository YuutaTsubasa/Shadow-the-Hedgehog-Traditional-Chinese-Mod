# Shadow the Hedgehog 繁體中文 — translator guide

Source: Japanese GameCube disc GUPJ8P. Text is in `text/ja/<FILE>.json`; translations go to
`text/zh/<FILE>.json` **only through `tools/tl.py`**. Never edit `text/ja`. Run everything from
the project root with `PYTHONUTF8=1`.

```bash
python tools/tl.py next <FILE> 40                       # next batch + glossary + similar TM lines
python tools/tl.py commit <FILE> work/tl/<FILE>_<n>.json  # check and save
python tools/tl.py lookup <日文>                          # search glossary / TM
python tools/tl.py status
```

Batch file: `{"strings": [{"id": "...", "zh": "..."}], "terms": {"新名詞": {"zh": "譯名", "note": "角色/關卡/用語"}}}`.
Fix every `REJECTED` line and commit it again. A `TERM CONFLICT` means the glossary wins: change the sentence.
Repeat until `remaining: 0`. Strings already in the TM are filled automatically.

## Files

- `_shared1`…`_shared4`: lines used in several stages (hint lines, partner chatter, menu text). They are translated first.
- `Movie`: CG movie subtitles. `Advertise`: menus, Library story texts, memory-card messages (the PS2 ones too).
- `Save`: save messages. `stgNNNN`: one stage's voice lines. `speaker` gives who is talking.

## Rules (checked automatically)

- Never more lines than the Japanese. Keep line widths within `max_units` (full-width = 2, ASCII = 1; up to +2 allowed).
- No kana left. Big5 characters only: Taiwanese Traditional Chinese (戰 氣 發 為 裡 著 祕).
- Full-width Chinese punctuation: ，。！？：；「」『』～. The Japanese `...` → `……`. `・` in names → `·`.
- Subtitles must still fit the voice: keep them about as short as the Japanese.

## Names (the glossary in `text/glossary.json` is final)

夏特 Shadow · 索尼克 · 塔爾斯 · 納克魯斯 · 艾咪 · 露姬 · E-123「Omega」 (written in English) · 蛋頭博士 ·
黑暗末日 Black Doom · 黑暗軍團 Black Arms · 瑪莉亞 · 傑拉德（教授） · GUN · 艾斯皮歐 · 貝庫特 · 查米 ·
克琳姆 · 起司 · 混沌翡翠 · 混沌控制 · 混沌爆破 · 方舟 · 黑色彗星 · 金環.
English stage and boss names (WESTOPOLIS, BLACK BULL…) are translated with the glossary names.

## UI words

ボタン 按鈕 (Ａボタン → Ａ按鈕, STARTボタン → START按鈕) · コントローラ 控制器 · コントロールスティック 控制桿 ·
コントローラ端子 控制器插槽 · メモリーカード 記憶卡 · スロットA 插槽A · ゲームデータ 遊戲資料 · セーブ 儲存 ·
ロード 讀取 · ステージ 關卡 · ポーズメニュー 暫停選單 · ミッション 任務.

## Voices

- **夏特:** cool, terse, proud. 僕 → 我. フン → 哼.
- **黑暗末日:** solemn, archaic, commanding. Calls himself 吾 and Shadow 你. His hints are short orders (「注意腳下。」).
- **Omega:** blunt and mechanical, with short clipped sentences. No kana tricks; the katakana-mixed Japanese just means 'robotic'.
- **蛋頭博士:** pompous. ワシ → 我. じゃ endings → 啦/了/吧 as fits.
- **索尼克:** breezy and cocky. **納克魯斯:** gruff. **露姬:** teasing and flirty. **艾咪:** cheerful.
- **貝庫特:** loud big brother. **查米:** childish. **艾斯皮歐:** stiff, ninja-like. **克琳姆:** polite.
- **GUN士兵/指揮官:** military radio style.
