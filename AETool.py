import cv2
import os
import sys
import numpy as np
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pyperclip
from PIL import Image, ImageDraw, ImageFont
import re
from datetime import datetime

# --- UI 風格設定 ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def resource_path(relative_path):
    """ 取得資源絕對路徑，相容 PyInstaller 打包後的環境 """
    try:
        # PyInstaller 建立的臨時資料夾路徑存放在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def natural_sort_key(s):
    """ 自然排序：確保 lv1, lv2... lv11 順序正確 """
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

class AEPhotoDetail:
    """ 處理單張照片數據與影像處理 """
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
        self.geometry("1300x640")
        self.version = "v2.0_20260317"
        self.results_cache = [] 

        # --- 設定 Icon ---
        icon_path = resource_path("exposure.ico")
        try:
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icon loading failed: {e}")

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 左側側邊欄 ---
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="DQE AE Tool", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=30)
        
        ctk.CTkButton(self.sidebar, text="📂 選擇主資料夾", command=self.start_analysis, height=40).pack(pady=10, padx=20)
        
        self.btn_copy = ctk.CTkButton(self.sidebar, text="📋 複製 Excel 數據", command=self.copy_to_clipboard, state="disabled", height=40)
        self.btn_copy.pack(pady=10, padx=20)

        self.btn_clear = ctk.CTkButton(self.sidebar, text="🗑 清空結果", command=self.clear_results, fg_color="#A93226", hover_color="#CB4335", height=40)
        self.btn_clear.pack(pady=10, padx=20)

        self.status_lbl = ctk.CTkLabel(self.sidebar, text="Ready", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ABB2B9")
        self.status_lbl.pack(pady=30)

        self.ver_lbl = ctk.CTkLabel(self.sidebar, text=f"Version: {self.version}", font=ctk.CTkFont(size=11), text_color="#566573")
        self.ver_lbl.pack(side="bottom", pady=15)

        self.info_box = ctk.CTkLabel(self.sidebar, text="判定規範：\nDiff > 5% 為 Fail\nDiff <= 5% 為 Pass", font=ctk.CTkFont(size=12), justify="left")
        self.info_box.pack(side="bottom", pady=10)

        # --- 右側顯示區 ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="AE 數據分析報告")
        self.scroll_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

    def clear_results(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.results_cache = []
        self.status_lbl.configure(text="Ready", text_color="#ABB2B9")
        self.btn_copy.configure(state="disabled", fg_color="gray")
        messagebox.showinfo("清空", "所有結果已清除。")

    def start_analysis(self):
        main_path = filedialog.askdirectory()
        if not main_path: return

        subfolders = sorted([d for d in os.listdir(main_path) if os.path.isdir(os.path.join(main_path, d))], key=natural_sort_key)
        
        if not subfolders:
            messagebox.showerror("錯誤", "找不到符合規範的子資料夾。")
            return

        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        self.results_cache = []
        overall_pass = True
        valid_ext = ('.png', '.jpg', '.jpeg', '.bmp', '.tif')

        try:
            for folder_name in subfolders:
                folder_path = os.path.join(main_path, folder_name)
                files = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                                if f.lower().endswith(valid_ext)], key=os.path.getmtime)
                
                if len(files) != 3: continue 

                photo_details = [AEPhotoDetail(f) for f in files]
                y_vals = [p.y_avg for p in photo_details]
                avg_y = sum(y_vals) / 3
                
                diffs = []
                for p in photo_details:
                    d = abs(p.y_avg - avg_y) / avg_y * 100 if avg_y != 0 else 0
                    p.diff_from_avg = d
                    diffs.append(d)
                
                max_diff = max(diffs)
                status = "Pass" if max_diff <= 5.0 else "Fail"
                if status == "Fail": overall_pass = False

                res_data = {
                    "level": folder_name, "y_list": y_vals, "avg": avg_y, 
                    "max_diff": max_diff, "status": status, "photos": photo_details
                }
                self.results_cache.append(res_data)
                self.render_level_section(res_data)

            self.status_lbl.configure(text="OVERALL: PASS" if overall_pass else "OVERALL: FAIL", 
                                      text_color="#2ECC71" if overall_pass else "#E74C3C")
            self.btn_copy.configure(state="normal", fg_color="#1F538D")
            self.auto_save_results(main_path, overall_pass)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"處理失敗：{str(e)}")

    def auto_save_results(self, main_path, overall_pass):
        save_dir = os.path.join(main_path, "Results", "AE")
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        txt_path = os.path.join(save_dir, f"AE_Report_Data_{timestamp}.txt")
        header = "Level\t1st\t2st\t3st\tAvg\tMax Diff\tResult\n"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(header)
            for r in self.results_cache:
                line = f"{r['level']}\t{r['y_list'][0]:.2f}\t{r['y_list'][1]:.2f}\t{r['y_list'][2]:.2f}\t{r['avg']:.2f}\t{r['max_diff']:.2f}%\t{r['status']}\n"
                f.write(line)
        
        png_path = os.path.join(save_dir, f"AE_Report_Image_{timestamp}.png")
        self.generate_long_report_image(png_path, overall_pass)
        messagebox.showinfo("自動存檔", f"數據與長圖已儲存至：\n{save_dir}")

    def generate_long_report_image(self, save_path, overall_pass):
        width = 1100
        row_h = 360
        header_h = 100
        total_h = header_h + (len(self.results_cache) * row_h) + 60
        img = Image.new('RGB', (width, total_h), color=(25, 25, 25))
        draw = ImageDraw.Draw(img)
        
        # 繪製標題 (符合規範)
        header_text = f"AE Tool Version : {self.version}"
        total_status = "PASS" if overall_pass else "FAIL"
        draw.text((30, 25), header_text, fill=(255, 255, 255))
        draw.text((30, 55), f"Overall Result: {total_status} | Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                  fill=(46, 204, 113) if overall_pass else (231, 76, 60))

        curr_y = header_h
        for res in self.results_cache:
            draw.line([(20, curr_y), (width-20, curr_y)], fill=(80, 80, 80), width=1)
            lv_color = (46, 204, 113) if res["status"] == "Pass" else (231, 76, 60)
            lv_text = f"Folder: {res['level']} | Avg Y: {res['avg']:.2f} | Max Diff: {res['max_diff']:.2f}% | Result: {res['status']}"
            draw.text((30, curr_y + 15), lv_text, fill=lv_color)

            labels = ["1st", "2st", "3st"]
            for i, p in enumerate(res["photos"]):
                thumb = p.full_res_boxed.copy()
                thumb.thumbnail((280, 210))
                x_pos = 30 + (i * 350)
                img.paste(thumb, (x_pos, curr_y + 50))
                info = (f"[{labels[i]}]\nFilename: {p.filename}\nSize: {p.w}x{p.h}\nRGB: {p.rgb_avg}\nY: {p.y_avg:.2f}\nDiff: {p.diff_from_avg:.2f}%")
                text_color = (231, 76, 60) if p.diff_from_avg > 5.0 else (200, 200, 200)
                draw.multiline_text((x_pos, curr_y + 250), info, fill=text_color, spacing=4)
            curr_y += row_h
        img.save(save_path)

    def render_level_section(self, res):
        color = "#2ECC71" if res["status"] == "Pass" else "#E74C3C"
        f = ctk.CTkFrame(self.scroll_frame, border_width=1, border_color="#444444")
        f.pack(fill="x", pady=15, padx=10)
        ctk.CTkLabel(f, text=f"Level: {res['level']} | Avg Y: {res['avg']:.2f} | Max Diff: {res['max_diff']:.2f}% | {res['status']}", 
                     text_color=color, font=ctk.CTkFont(weight="bold")).pack(pady=10, padx=15, anchor="w")
        row_f = ctk.CTkFrame(f, fg_color="transparent")
        row_f.pack(fill="x", padx=10, pady=5)
        labels = ["1st", "2st", "3st"]
        for i, p in enumerate(res["photos"]):
            card = ctk.CTkFrame(row_f, fg_color="#2B2B2B", border_width=1 if p.diff_from_avg > 5.0 else 0, border_color="#E74C3C")
            card.pack(side="left", padx=10, pady=10, expand=True, fill="both")
            ctk.CTkLabel(card, image=p.preview_tk, text="").pack(pady=10)
            txt = f"【{labels[i]}】\n檔名: {p.filename}\n尺寸: {p.w}x{p.h}\nRGB Avg: {p.rgb_avg}\nY Avg: {p.y_avg:.2f}\nDiff: {p.diff_from_avg:.2f}%"
            ctk.CTkLabel(card, text=txt, justify="left", font=ctk.CTkFont(size=11), 
                         text_color="#E74C3C" if p.diff_from_avg > 5.0 else "#D5D8DC").pack(pady=8, padx=12)

    def copy_to_clipboard(self):
        h = "Level\t1st\t2st\t3st\tAvg\tMax Diff\tResult\n"
        rows = [f"{r['level']}\t{r['y_list'][0]:.2f}\t{r['y_list'][1]:.2f}\t{r['y_list'][2]:.2f}\t{r['avg']:.2f}\t{r['max_diff']:.2f}%\t{r['status']}" for r in self.results_cache]
        pyperclip.copy(h + "\n".join(rows))
        messagebox.showinfo("成功", "數據已成功複製至剪貼簿。")

if __name__ == "__main__":
    app = ModernAEValidator()
    app.mainloop()