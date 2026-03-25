import cv2
import os
import sys
import numpy as np
import customtkinter as ctk
from tkinter import filedialog
import pyperclip
from PIL import Image, ImageDraw, ImageFont
import re
from datetime import datetime
import ctypes

# --- Windows 高解析度 DPI 處理 ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# --- UI 風格設定 ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

# --- 自定義縮放彈窗 ---
class CTkMessage(ctk.CTkToplevel):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        sw = self.winfo_screenwidth()
        w = int(sw * 0.2) if sw > 1920 else 400
        h = int(w * 0.5)
        self.title(title)
        self.geometry(f"{w}x{h}")
        self.attributes("-topmost", True)
        self.grab_set()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - (w // 2)
        py = parent.winfo_y() + (parent.winfo_height() // 2) - (h // 2)
        self.geometry(f"+{px}+{py}")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.label = ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=14), wraplength=w-40)
        self.label.grid(row=0, column=0, padx=20, pady=20)
        self.btn = ctk.CTkButton(self, text="確定", command=self.destroy, width=100)
        self.btn.grid(row=1, column=0, pady=(0, 20))

class AEPhotoDetail:
    def __init__(self, path):
        self.path = path
        self.filename = os.path.basename(path)
        img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None: raise ValueError(f"無法讀取影像: {self.filename}")
        self.h, self.w = img.shape[:2]
        cx, cy = self.w // 2, self.h // 2
        x1, y1, x2, y2 = cx-50, cy-50, cx+50, cy+50
        roi = img[max(0, y1):min(self.h, y2), max(0, x1):min(self.w, x2)]
        b_avg, g_avg, r_avg = cv2.mean(roi)[:3]
        self.rgb_avg = (round(r_avg, 2), round(g_avg, 2), round(b_avg, 2))
        self.y_avg = 0.299 * r_avg + 0.587 * g_avg + 0.114 * b_avg
        self.diff_from_avg = 0.0
        self.full_res_boxed = self.get_boxed_img(img, x1, y1, x2, y2)
        self.preview_tk = self.create_tk_img(self.full_res_boxed)

    def get_boxed_img(self, img, x1, y1, x2, y2):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        draw = ImageDraw.Draw(pil_img)
        draw.rectangle([x1, y1, x2, y2], outline="red", width=6)
        return pil_img

    def create_tk_img(self, pil_img):
        temp_img = pil_img.copy()
        temp_img.thumbnail((180, 180))
        return ctk.CTkImage(light_image=temp_img, dark_image=temp_img, size=(180, 135))

class ModernAEValidator(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DQE AE Tool")
        self.version = "DQE_20260317"
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        width, height = int(sw * 0.6), int(sh * 0.65)
        self.geometry(f"{width}x{height}+{int((sw-width)/2)}+{int((sh-height)/2)}")
        self.minsize(1024, 720)
        
        self.results_cache = [] 
        self.global_max_diff = 0.0
        self.global_max_lv_list = []

        icon_path = resource_path("exposure.ico")
        try:
            if os.path.exists(icon_path): self.iconbitmap(icon_path)
        except: pass
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        ctk.CTkLabel(self.sidebar, text="DQE AE Tool", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=30)
        ctk.CTkButton(self.sidebar, text="📂 選擇主資料夾", command=self.start_analysis, height=40).pack(pady=10, padx=20)
        self.btn_copy = ctk.CTkButton(self.sidebar, text="📋 複製 Excel 數據", command=self.copy_to_clipboard, state="disabled", height=40)
        self.btn_copy.pack(pady=10, padx=20)
        self.btn_clear = ctk.CTkButton(self.sidebar, text="🗑 清空結果", command=self.clear_results, fg_color="#A93226", hover_color="#CB4335", height=40)
        self.btn_clear.pack(pady=10, padx=20)
        self.status_lbl = ctk.CTkLabel(self.sidebar, text="Ready", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ABB2B9")
        self.status_lbl.pack(pady=(30, 5))
        self.max_stat_lbl = ctk.CTkLabel(self.sidebar, text="", font=ctk.CTkFont(size=14), text_color="#E67E22", wraplength=220)
        self.max_stat_lbl.pack(pady=5)
        self.ver_lbl = ctk.CTkLabel(self.sidebar, text=f"Version: {self.version}", font=ctk.CTkFont(size=11), text_color="#566573")
        self.ver_lbl.pack(side="bottom", pady=15)
        self.info_box = ctk.CTkLabel(self.sidebar, text="判定規範：\nDiff > 5% 為 Fail\nDiff <= 5% 為 Pass", font=ctk.CTkFont(size=12), justify="left")
        self.info_box.pack(side="bottom", pady=10)
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="AE 數據分析報告")
        self.scroll_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        def _on_mousewheel(event):
            self.scroll_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 120) * 120), "units")
        self.scroll_frame._parent_canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def clear_results(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        self.results_cache = []
        self.global_max_diff = 0.0
        self.global_max_lv_list = []
        self.status_lbl.configure(text="Ready", text_color="#ABB2B9")
        self.max_stat_lbl.configure(text="")
        self.btn_copy.configure(state="disabled", fg_color="gray")
        CTkMessage(self, "清空", "所有結果已清除。")

    def start_analysis(self):
        main_path = filedialog.askdirectory()
        if not main_path: return
        subfolders = sorted([d for d in os.listdir(main_path) if os.path.isdir(os.path.join(main_path, d))], key=natural_sort_key)
        
        # 排除 Results 資料夾
        subfolders = [d for d in subfolders if d.lower() != "results"]

        if not subfolders:
            CTkMessage(self, "錯誤", "找不到符合規範的子資料夾。")
            return

        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        self.results_cache, self.global_max_diff, self.global_max_lv_list = [], 0.0, []
        overall_pass, has_error = True, False
        valid_ext = ('.png', '.jpg', '.jpeg', '.bmp', '.tif')

        try:
            for folder_name in subfolders:
                folder_path = os.path.join(main_path, folder_name)
                files = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(valid_ext)], key=os.path.getmtime)
                
                # 檔案數量檢查
                if len(files) != 3:
                    CTkMessage(self, "檔案數量錯誤", f"資料夾 '{folder_name}' 偵測到 {len(files)} 張照片 (應為 3 張)。已跳過此階分析。")
                    res_data = {"level": folder_name, "status": "Skip", "error": f"Error: Found {len(files)} files, expected 3", "photos": []}
                    has_error = True
                else:
                    photo_details = [AEPhotoDetail(f) for f in files]
                    avg_y = sum(p.y_avg for p in photo_details) / 3
                    lv_max_diff = 0.0
                    for p in photo_details:
                        p.diff_from_avg = abs(p.y_avg - avg_y) / avg_y * 100 if avg_y != 0 else 0
                        if p.diff_from_avg > lv_max_diff: lv_max_diff = p.diff_from_avg

                    if round(lv_max_diff, 2) > round(self.global_max_diff, 2):
                        self.global_max_diff, self.global_max_lv_list = lv_max_diff, [folder_name]
                    elif round(lv_max_diff, 2) == round(self.global_max_diff, 2) and lv_max_diff > 0:
                        if folder_name not in self.global_max_lv_list: self.global_max_lv_list.append(folder_name)
                    
                    status = "Pass" if lv_max_diff <= 5.0 else "Fail"
                    if status == "Fail": overall_pass = False
                    res_data = {"level": folder_name, "y_list": [p.y_avg for p in photo_details], "avg": avg_y, "max_diff": lv_max_diff, "status": status, "photos": photo_details}
                
                self.results_cache.append(res_data)
                self.render_level_section(res_data)

            self.status_lbl.configure(text="OVERALL: PASS" if overall_pass and not has_error else "OVERALL: FAIL/WARN", text_color="#2ECC71" if overall_pass and not has_error else "#E67E22")
            self.max_stat_lbl.configure(text=f"Max Diff: {self.global_max_diff:.2f}% @ {', '.join(self.global_max_lv_list)}")
            self.btn_copy.configure(state="normal", fg_color="#1F538D")
            self.auto_save_results(main_path, overall_pass and not has_error)
            
        except Exception as e:
            CTkMessage(self, "錯誤", f"處理失敗：{str(e)}")

    def auto_save_results(self, main_path, overall_pass):
        save_dir = os.path.join(main_path, "Results", "AE")
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_path = os.path.join(save_dir, f"AE_Report_Data_{timestamp}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Level\t1st\t2nd\t3rd\tAvg\tMax Diff\tResult\n")
            for r in self.results_cache:
                if r["status"] == "Skip":
                    f.write(f"{r['level']}\t--\t--\t--\t--\t--\t{r['error']}\n")
                else:
                    f.write(f"{r['level']}\t{r['y_list'][0]:.2f}\t{r['y_list'][1]:.2f}\t{r['y_list'][2]:.2f}\t{r['avg']:.2f}\t{r['max_diff']:.2f}%\t{r['status']}\n")
            f.write(f"\n[Global Summary]\nGlobal Max Difference:\t{self.global_max_diff:.2f}%\tLocated in:\t{', '.join(self.global_max_lv_list)}\n")
        self.generate_long_report_image(os.path.join(save_dir, f"AE_Report_Image_{timestamp}.png"), overall_pass)
        CTkMessage(self, "自動存檔", f"數據與長圖已儲存至：\n{save_dir}")

    def generate_long_report_image(self, save_path, overall_pass):
            # 稍微增加 row_h 以確保文字不會超出底線 (360 -> 420)
            width, row_h, header_h = 1100, 420, 130
            img = Image.new('RGB', (width, header_h + (len(self.results_cache) * row_h) + 60), color=(25, 25, 25))
            draw = ImageDraw.Draw(img)
            
            # 標題與全局資訊
            draw.text((30, 20), f"AE Tool Version : {self.version}", fill=(255, 255, 255))
            draw.text((30, 50), f"Overall Result: {'PASS' if overall_pass else 'FAIL/WARN'} | Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fill=(46, 204, 113) if overall_pass else (231, 76, 60))
            draw.text((30, 80), f"Global Max Difference: {self.global_max_diff:.2f}% (Found in {', '.join(self.global_max_lv_list)})", fill=(230, 126, 34))
            
            curr_y = header_h
            ordinals = ["1st", "2nd", "3rd"] # 統一序數定義

            for res in self.results_cache:
                draw.line([(20, curr_y), (width-20, curr_y)], fill=(80, 80, 80), width=1)
                
                if res["status"] == "Skip":
                    draw.text((30, curr_y + 15), f"Level: {res['level']} | {res['error']}", fill=(241, 196, 15))
                else:
                    lv_color = (46, 204, 113) if res["status"] == "Pass" else (231, 76, 60)
                    draw.text((30, curr_y + 15), f"Level: {res['level']} | Avg Y: {res['avg']:.2f} | Max Diff: {res['max_diff']:.2f}% | Result: {res['status']}", fill=lv_color)
                    
                    # 處理三張一組的照片
                    for i, p in enumerate(res["photos"]):
                        # 縮放圖片並取得實際尺寸
                        thumb = p.full_res_boxed.copy()
                        thumb.thumbnail((280, 210))
                        tw, th = thumb.size # tw: 寬度, th: 高度
                        
                        # 計算圖片貼上座標
                        img_x = 30 + (i * 350)
                        img_y = curr_y + 50
                        img.paste(thumb, (img_x, img_y))
                        
                        # 核心修正：文字位置根據圖片實際高度 th 動態計算，並修正序數
                        text_y = img_y + th + 10 # 圖片底部下方 10 像素
                        ordinal_label = ordinals[i] if i < 3 else f"[{i+1}th]"
                        
                        text_content = (
                            f"[{ordinal_label}]\n"
                            f"Filename: {p.filename}\n"
                            f"Size: {p.w}x{p.h}\n"
                            f"RGB: {p.rgb_avg}\n"
                            f"Y: {p.y_avg:.2f}\n"
                            f"Diff: {p.diff_from_avg:.2f}%"
                        )
                        
                        draw.multiline_text(
                            (img_x, text_y), 
                            text_content, 
                            fill=(231, 76, 60) if p.diff_from_avg > 5.0 else (200, 200, 200), 
                            spacing=4
                        )
                
                curr_y += row_h
            
            img.save(save_path)

    def render_level_section(self, res):
        if res["status"] == "Skip":
            f = ctk.CTkFrame(self.scroll_frame, border_width=1, border_color="#F1C40F")
            f.pack(fill="x", pady=15, padx=10)
            ctk.CTkLabel(f, text=f"Level: {res['level']} | {res['error']}", text_color="#F1C40F", font=ctk.CTkFont(weight="bold")).pack(pady=20, padx=15)
        else:
            color = "#2ECC71" if res["status"] == "Pass" else "#E74C3C"
            f = ctk.CTkFrame(self.scroll_frame, border_width=1, border_color="#444444")
            f.pack(fill="x", pady=15, padx=10)
            ctk.CTkLabel(f, text=f"Level: {res['level']} | Avg Y: {res['avg']:.2f} | Max Diff: {res['max_diff']:.2f}% | {res['status']}", text_color=color, font=ctk.CTkFont(weight="bold")).pack(pady=10, padx=15, anchor="w")
            row_f = ctk.CTkFrame(f, fg_color="transparent"); row_f.pack(fill="x", padx=10, pady=5)
            for i, p in enumerate(res["photos"]):
                card = ctk.CTkFrame(row_f, fg_color="#2B2B2B", border_width=1 if p.diff_from_avg > 5.0 else 0, border_color="#E74C3C")
                card.pack(side="left", padx=10, pady=10, expand=True, fill="both")
                ctk.CTkLabel(card, image=p.preview_tk, text="").pack(pady=10)
                txt = f"【{['1st','2nd','3rd'][i]}】\n檔名: {p.filename}\n尺寸: {p.w}x{p.h}\nRGB Avg: {p.rgb_avg}\nY Avg: {p.y_avg:.2f}\nDiff: {p.diff_from_avg:.2f}%"
                ctk.CTkLabel(card, text=txt, justify="left", font=ctk.CTkFont(size=11), text_color="#E74C3C" if p.diff_from_avg > 5.0 else "#D5D8DC").pack(pady=8, padx=12)

    def copy_to_clipboard(self):
        h = "Level\t1st\t2nd\t3rd\tAvg\tMax Diff\tResult\n"
        rows = []
        for r in self.results_cache:
            if r["status"] == "Skip": rows.append(f"{r['level']}\t--\t--\t--\t--\t--\t{r['error']}")
            else: rows.append(f"{r['level']}\t{r['y_list'][0]:.2f}\t{r['y_list'][1]:.2f}\t{r['y_list'][2]:.2f}\t{r['avg']:.2f}\t{r['max_diff']:.2f}%\t{r['status']}")
        pyperclip.copy(h + "\n".join(rows) + f"\nGlobal Max Difference:\t{self.global_max_diff:.2f}%\t@ {', '.join(self.global_max_lv_list)}")
        CTkMessage(self, "成功", "數據已成功複製至剪貼簿。")

if __name__ == "__main__":
    app = ModernAEValidator(); app.mainloop()