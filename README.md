# DQE AE Tool (Auto Exposure Analyzer)

![Version](https://img.shields.io/badge/Version-DQE__20260317-blue.svg)
![Status](https://img.shields.io/badge/Status-Stable-success.svg)
![Type](https://img.shields.io/badge/Internal-DQE%20Only-red.svg)

**DQE AE Tool** 是一款專為相機影像品質測試（DQE）設計的自動曝光（AE）穩定度判定工具。本工具能自動化讀取影像數據，計算指定範圍的亮度值（Y 值），並產出專業的數據報表與影像長圖。

---

## 🚀 核心功能

*   **自動化分析流程**：一鍵選取主資料夾，自動偵測不同亮度 `lv` 子目錄。
*   **精準取樣技術 (ROI)**：鎖定感光元件正中心 `100 x 100` 像素範圍進行亮度分析。
*   **影像視覺化報表**：
    *   即時預覽：介面顯示帶有 **紅色取樣框** 的縮圖。
    *   詳細參數：顯示檔名、解析度、RGB 平均值與 Y 亮度平均值。
*   **自動化存檔系統**：分析完成後，自動於主目錄建立 `Results/AE` 並存入：
    *   **Excel 數據表** (.txt 格式，Tab 分隔，支援 Excel 直接開啟)。
    *   **完整報告長圖** (.png 格式，包含所有 33 張影像細節與判定)。
*   **智慧排序邏輯**：
    *   資料夾：採用自然排序法（Natural Sort），正確排序 `lv4` 到 `lv11`。
    *   影像：依檔案修改時間排序，區分為 `1st`、`2st`、`3st`。

---

## 📂 預期資料夾結構

測試資料必須依照以下結構存放，程式方可正確讀取：

```text
[主資料夾]
├── lv1
│   ├── image_01.jpg (1st)
│   ├── image_02.jpg (2st)
│   └── image_03.jpg (3st)
├── lv2
│   └── ...
├── ...
└── lv11
    └── ...
```
* 每個子資料夾需包含 **3 張影像**
* 程式會自動偵測 **lv 開頭之資料夾** 並進行分析

---

## 🛠 判定標準與規範

### 亮度公式（BT.601）

```
Y = 0.299 * R + 0.587 * G + 0.114 * B
```

### 判定邏輯

* 計算每張照片與該 Level 平均值的 **誤差百分比（Difference %）**
* **Pass**：最大誤差值 ≤ 5%
* **Fail**：任一影像誤差 > 5%

---

## 📖 操作指南

### 1. 啟動工具

執行：

```
DQE AE Tool.exe
```

### 2. 執行分析

* 點擊「📂 選擇主資料夾」

### 3. 檢視結果

* 右側面板將列出所有 Level 的分析圖表
* 若影像誤差超標（> 5%），該影像卡片會以 **紅色標記** 提醒

### 4. 獲取報告

* **自動生成**：

  * 於主資料夾下建立 `Results/AE`
  * 內含數據與長圖

* **手動複製**：

  * 點擊「📋 複製 Excel 數據」
  * 可貼入既有 Excel 模板

### 5. 清空重置

* 點擊「🗑 清空結果」清除目前數據
* 可開始下一輪測試

---

## 📦 打包發佈（PyInstaller）

若需重新打包成執行檔，請於終端機執行：

```powershell
python -m PyInstaller --noconsole --onefile --icon=exposure.ico --add-data "exposure.ico;." AE2026.py
```

---

## 📋 版本資訊

* **版本名稱**：v2.0_20260317

### 主要更動

1. 新增 `Results/AE` 自動存檔機制
2. 優化 1st / 2nd / 3rd 標籤顯示
3. 加入圖標（Icon）封裝與視窗置中邏輯
4. 新增 UI 清空功能

---
