# dotclaude

繁體中文 | [English](README.en.md)

## Overview

這個 repo 是 Claude Code 的 **user-scope 設定集**，內容會被部署到家目錄 `~/.claude/`，同時服務本機 Claude Desktop、VS Code 內的 Claude Code、以及終端機的 Claude Code。裡面沒有任何可執行程式碼 — 交付物就是 markdown 規則檔與一份 JSON 設定：一份全域行為準則（`CLAUDE.md`）、15 個 skills、3 條 rules、1 個 subagent，以及 `settings.json` 的權限與模型設定。部分 skill 附帶給模型直接執行的 PowerShell / Python 輔助腳本，但不需要 build。

## Architecture

真正的架構在於「哪個檔案在什麼時機被載入」。Claude Code 有四層載入機制，本 repo 的目錄結構就是照這四層切的：

| 層級 | 檔案 | 載入時機 | 代價 |
| --- | --- | --- | --- |
| 永遠在 context | `CLAUDE.md` | 每個 session、每個專案，開場即載入 | 每次對話都付 token |
| 命中檔案類型才載入 | `rules/*.md` | 該次任務碰到符合 `paths:` glob 的檔案時 | 只在相關時付費 |
| 命中任務才載入 | `skills/*/SKILL.md` | `description` 與請求相符，或使用者打 `/<name>` | 只有 description 常駐，body 按需載入 |
| 被呼叫才載入 | `agents/*.md` | 主 session 用 Agent tool 指定 `subagent_type` | 獨立 context，不污染主對話 |

skill 若帶 `paths:`，就多一道限制：**它只有在模型實際碰到符合的檔案之後才會載入**，開場的 skill 清單裡看不到它。這是刻意的取捨 — 適合「一定是從既有檔案開始」的任務（`python-ui`），不適合「使用者開口時手邊還沒有檔案」的任務（繪圖），所以 `python-plot` 不用 `paths:`，改靠 description 觸發。

skill 內的 `references/` 是第三層漸進揭露：SKILL.md 的 body 在任務命中時整份載入，`references/` 只有在 body 明確指示「什麼時候該讀它」時才被讀進來。目前只有 `text-watermark-cleaner-zh-tw` 用到。`scripts/` 與 `assets/` 則是給模型執行或複製進專案的檔案，不會讀進 context（`exe-verify`、`office-com`、`project-icon`、`text-watermark-cleaner-zh-tw` 帶 `scripts/`，`python-ui` 帶 `assets/`）。

部署後的對應關係：

```
dotclaude/                      ~/.claude/
├── CLAUDE.md          ──────►  ├── CLAUDE.md       全域準則，一律載入
├── settings.json      ──────►  ├── settings.json   權限 / 模型 / 清理週期
├── rules/             ──────►  ├── rules/          paths: glob 命中才載入
├── skills/            ──────►  ├── skills/         description 命中或 /<name>
└── agents/            ──────►  └── agents/         subagent_type 指定才載入
```

部署時**只搬 `rules/`、`skills/`、`agents/` 與根目錄的三個檔案**。

分類原則寫在 `rules/skill-authoring.md` 的第 1 節，新增內容前先讀那張表決定歸屬：可重複的多步驟流程 → skill；每次碰到某類檔案都要遵守的慣例 → rule（加 `paths:`）；只在特定任務內成立的慣例 → 帶 `paths:` 的 skill；單一 repo 的 build/test 指令 → 該專案自己的 CLAUDE.md；尚未成形的一次性教訓 → `LESSONS.md`。

## Directory structure

```
dotclaude/
├── CLAUDE.md                    全域行為準則（10 節）。★ 使用者手動維護，模型不得編輯，含 append
├── CLAUDE.zh-TW.md              上面那份的中譯，同樣由使用者手動維護
├── LESSONS.md                   跨專案教訓暫存區；目前只有標題。模型唯一可 append 的檔案
├── settings.json                model=opus / effortLevel=high / git 讀寫權限分流
├── rules/
│   ├── markdown.md              **/*.md — 不硬換行、區塊間空一行
│   ├── powershell.md            **/*.ps1 — 三種預設編碼、5.1 沒有的語法、原生指令互通、驗證清單
│   └── skill-authoring.md       **/SKILL.md — 撰寫 skill 的完整規範與 pre-ship checklist
├── skills/
│   ├── exe-verify/              驗證打包後的 .exe 真的能開視窗；讀隱藏錯誤對話框、擷取單一視窗
│   │   └── scripts/             wait-for-window / read-error-dialog（.ps1）、capture-window（.py）
│   ├── git-commit/              Conventional Commits 1.0.0 + house emoji 前綴，只印指令不執行
│   ├── handoff/                 /handoff：寫給下一個 session 的交接信，只能手動觸發
│   ├── humanizer/               去除英文 AI 寫作痕跡（源自 Wikipedia 指南）
│   ├── humanizer-zh-tw/         中文版；本檔以中文撰寫（語言規則的例外）
│   ├── null-calibration/        小樣本篩選門檻先在 placebo / shuffle null 上量偽陽性率
│   ├── office-com/              PowerShell / win32com 操作 Office 時不關到使用者的視窗；.xlsx 開檔驗證
│   │   └── scripts/             verify-xlsx.ps1
│   ├── project-icon/            用專案內的 tools/make_icon.py 產生多解析度 app.ico
│   │   └── scripts/             preview_ico.py（16px 可讀性檢查）
│   ├── python-plot/             matplotlib / seaborn 繪圖慣例
│   ├── python-ui/               tkinter / ttkbootstrap 桌面 UI；與 ui-project 成對使用
│   │   └── assets/              win_icon.py（標題列 / 工作列分槽設定圖示）
│   ├── readme/                  README.md 必備章節 + 多語言切換列與翻譯同步
│   ├── stock-research-note/     單一個股的中文研究筆記，數字皆標來源與 as_of
│   ├── stock-score-review/      跨名單的評分排名與篩選
│   ├── text-watermark-cleaner-zh-tw/  清理不可見 Unicode 與文字型 AI provenance；本檔以中文撰寫
│   │   ├── references/          chinese-text.md，body 指名才讀
│   │   └── scripts/             inspect / clean / score_stylometry（.py）與 .ps1 包裝
│   └── ui-project/              UI_README.html / 使用者指引.html / /design / PyInstaller 打包
└── agents/
    └── doc-verifier.md          唯讀文件稽核 subagent
```

### Skills 一覽

frontmatter 的常態是**只有 `name` 與 `description`**。帶額外欄位的 skill 列在下表，各有理由。

| Skill | 觸發方式 | 額外 frontmatter |
| --- | --- | --- |
| `exe-verify` | description 命中（打包驗證、exe 閃退、圖示沒換到） | 無；含 `scripts/` |
| `git-commit` | description 命中，或手動 `/git-commit` | 無 |
| `handoff` | 只能手動 `/handoff` | `disable-model-invocation: true` |
| `humanizer` | description 命中（編修英文文稿） | `license`、`metadata`（版本） |
| `humanizer-zh-tw` | description 命中，或手動 `/humanizer-zh-tw` | `metadata`（來源與修訂日期） |
| `null-calibration` | description 命中（篩選特徵、閾值怎麼設） | 無 |
| `office-com` | description 命中（`-ComObject`、`win32com`、Excel 打不開） | 無；含 `scripts/` |
| `project-icon` | description 命中（需要 .ico、圖示模糊） | 無；含 `scripts/` |
| `python-plot` | description 命中（畫圖、存圖、調圖） | 無 |
| `python-ui` | `paths: **/*.py`、`**/*.spec` | `paths`；含 `assets/` |
| `readme` | description 命中（寫 / 更新 README、加語言版本） | 無；被 `doc-verifier` 以 `skills:` 預載 |
| `stock-research-note` | description 命中（單一個股名稱） | 無 |
| `stock-score-review` | description 命中（多檔排名、掃名單） | 無 |
| `text-watermark-cleaner-zh-tw` | description 命中（去文字浮水印、清理不可見字元） | 無；含 `references/`、`scripts/` |
| `ui-project` | description 命中（UI_README / 使用者指引 / 打包） | 無；被 `doc-verifier` 以 `skills:` 預載 |

成對關係：

- `readme` 與 `ui-project` 原本是同一個 skill。README 規則適用於每一個專案，UI_README.html 與 PyInstaller 打包只適用於 App 專案 —— 觸發條件不同卻綁在一起，會讓寫 README 的任務被迫載入整份打包規則，因此拆開。
- `python-ui` 是下位層，`ui-project` 是上位層。`.ico`、`sys._MEIPASS` 等規則只寫在 `ui-project`，`python-ui` 指過去而不重抄，並在開頭要求兩個一起載入。
- `exe-verify` 負責打包後的驗證與診斷，預防失敗的 .spec 慣例留在 `ui-project`；`project-icon` 負責畫出 `.ico`，.spec 設定與三處圖示的一致性仍歸 `ui-project`，程式內的圖示呼叫歸 `python-ui`。
- `humanizer` 處理英文、`humanizer-zh-tw` 處理中文。`humanizer-zh-tw` 只改寫語氣；不可見 Unicode 與文字浮水印由 `text-watermark-cleaner-zh-tw` 處理，前者的 description 會指路過去。
- `stock-research-note` 寫單一個股，`stock-score-review` 排多檔名次，兩邊 description 互相指路。

`doc-verifier` 是這裡唯一的 subagent：`tools: Read, Grep, Glob, PowerShell`（無寫入工具）、`skills: [readme, ui-project]`、`model: sonnet` / `effort: medium`，只回報問題、絕不改檔。

## Setup & run

沒有 build、沒有測試框架、沒有 lint。「部署」就是把檔案放進家目錄：

```powershell
# 首次部署（PowerShell）
Copy-Item -Path .\CLAUDE.md, .\settings.json, .\LESSONS.md -Destination "$env:USERPROFILE\.claude\" -Force
Copy-Item -Path .\rules, .\agents -Destination "$env:USERPROFILE\.claude\" -Recurse -Force
Copy-Item -Path .\skills -Destination "$env:USERPROFILE\.claude\" -Recurse -Force
```

已刪除的 skill（例如 `officecli`）不會因為重新複製而從 `~/.claude/skills/` 消失，要手動刪掉該目錄。

**注意 `settings.json` 會覆蓋既有設定**，不是合併。先備份或手動比對 `permissions` 區塊再覆蓋。

### 驗證

改完規則後要跑的檢查：

1. **格式** — 依 `rules/markdown.md`：每個段落一個實體行、每個區塊前後各空一行、檔尾有換行、無 BOM、無行尾空白。

2. **章節引用** — 檔案裡每個 `(global: X)` 與 `CLAUDE.md **X**` 都必須對得上 `CLAUDE.md` 現有的 10 個章節名稱。章節被改名或刪掉時，這些引用會無聲失效。

3. **frontmatter 逐欄對照** — 對照 `rules/skill-authoring.md` 第 2 節的清單人工檢查。`claude plugin validate --strict` 通過**不能**證明欄位有效：它只型別檢查 `description`、`name`、`allowed-tools`、`metadata`、`shell` 五項，對不認得的欄位一律靜默忽略，而且完全不掃 `rules/`。

4. **實際觸發** — 依 `rules/skill-authoring.md` 第 8 節，用「使用者真的會怎麼打」的 2–3 句 prompt 試跑。載入失敗是 `description` 的問題，產出錯誤才是 body 的問題，兩者修法不同。

5. **設定生效** — 在任一專案跑 `/status`、`/model`、`/effort` 核對是否與 `settings.json` 一致；產品顯示與本 repo 不一致時，以產品為準並回報漂移。

## Dependencies

- **Claude Code**（CLI / VS Code extension / Desktop）— 唯一的執行環境。
- **Windows PowerShell 5.1** — `exe-verify`、`office-com`、`text-watermark-cleaner-zh-tw` 的 `.ps1` 腳本。
- **Python 3** — `exe-verify`、`project-icon`、`text-watermark-cleaner-zh-tw` 的 `.py` 腳本，以及 `python-ui` 的 `win_icon.py`；除 `project-icon` 需要 **Pillow** 外只用標準函式庫。
- **Microsoft Office** — 只有 `office-com` 需要（COM 自動化與 .xlsx 開檔驗證）。
- 沒有 package manager，本 repo 本身不安裝任何套件。

## Configuration

`settings.json`（user scope）目前設定：

- `model: "opus"`、`effortLevel: "high"`、`cleanupPeriodDays: 21`
- `permissions.defaultMode: "auto"`
- `attribution.commit` / `attribution.pr` 設為空字串 — commit 與 PR 不加署名
- `permissions.allow`：唯讀 git（`status` / `diff` / `log` / `show` / `branch --list`）免詢問
- `permissions.ask`：`add` / `commit` / `push` / `tag` / `merge` / `rebase` 六個操作在任何權限模式下都強制跳確認，對應 `CLAUDE.md` 的 Git 一節
- `theme: "dark"`、`autoUpdatesChannel: "latest"`、`agentPushNotifEnabled: true`

本 repo 不含任何密鑰，`settings.json` 也沒有 `env` 區塊；若日後要加 API key，走環境變數，不要寫進這裡。

## 維護慣例

1. **`CLAUDE.md` 只由使用者手動修改** — 模型連 append 都不行，只能在對話中提案。這條寫在檔案本身第 6 行。
2. **`LESSONS.md` 是模型唯一可 append 的檔案**，且僅限跨專案成立的教訓，格式 `- [YYYY-MM-DD] 症狀 → 建議的全域規則`。它不會被任何 session 載入，寫進去不改變行為，要等使用者手動升級成規則。超過約 10 行要主動告知。
3. **skill / rule / agent 檔的修改需要當次 session 的明確同意** — 可以隨時提案，不能自行套用。
4. **語言規則**：對話用台灣繁體中文；rule / skill / agent 檔一律英文。例外是主題本身就是某語言的檔案（`humanizer-zh-tw`、`text-watermark-cleaner-zh-tw`），該檔以它所處理的語言撰寫。
5. **`model:` / `effort:` 預設省略** — 省略即繼承 `settings.json`。要 override 就得在同一份檔案寫下理由。關鍵差異：inline skill 的 override 會改掉**整輪對話**的模型，波及同一輪裡不相干的工作；`context: fork` 的 skill 只影響 fork 內部。所以 override 在 forked skill 上便宜、在 inline skill 上昂貴 —— 與其把一整輪降級，不如把該 skill 改成 fork。
6. **`background:` 只在 `context: fork` 下有效**，inline skill 上是無效欄位，卻會讓人以為設定了某個從未生效的行為。
7. **引用 `CLAUDE.md` 時用章節名稱，不要用章節編號** — 編號會隨編輯漂移。
