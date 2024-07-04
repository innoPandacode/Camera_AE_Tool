import os
from tkinter import Tk, filedialog, Button, Label, Text, Scrollbar
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
# v1.0_20240704

# 提取矩陣大小相關的變數
MATRIX_DIVISOR = 3

# 每行顯示的圖片數量
IMAGES_PER_ROW = 3

def get_image_files(folder):
    """從指定資料夾中獲取所有圖片檔案的路徑列表。"""
    return [os.path.join(folder, file) for file in os.listdir(folder) if file.endswith(('jpg', 'jpeg', 'png', 'bmp', 'tiff'))]

def calculate_mean_brightness_and_color(image):
    """計算給定圖片的平均亮度和色彩。"""
    image_np = np.array(image)
    if image_np.shape[-1] == 4:
        image_np = image_np[:, :, :3]
    brightness = np.mean(image_np.mean(axis=2))
    mean_color = image_np.mean(axis=(0, 1))
    return brightness, mean_color

def process_images(folder, text_box):
    """處理指定資料夾中的所有圖片。"""
    # 设置全局字体为宋体
    plt.rcParams['font.family'] = 'SimSun'

    image_files = get_image_files(folder)
    images = [Image.open(image_file) for image_file in image_files]

    frame_sizes = [image.size for image in images]
    if len(set(frame_sizes)) != 1:
        raise ValueError("Not all images have the same frame size")
    
    width, height = frame_sizes[0]
    region_width = width // MATRIX_DIVISOR
    region_height = height // MATRIX_DIVISOR
    x_start = (width - region_width) // 2
    y_start = (height - region_height) // 2

    num_images = len(images)
    num_rows = (num_images + IMAGES_PER_ROW - 1) // IMAGES_PER_ROW
    plt.figure(figsize=(10, 8))
    
    for idx, (image_file, image) in enumerate(zip(image_files, images)):
        row = idx // IMAGES_PER_ROW
        col = idx % IMAGES_PER_ROW
        
        central_region = image.crop((x_start, y_start, x_start + region_width, y_start + region_height))
        brightness, mean_color = calculate_mean_brightness_and_color(central_region)
        
        plt.subplot(num_rows, IMAGES_PER_ROW, idx + 1)
        plt.imshow(image)
        plt.xlim([0, width])
        plt.ylim([height, 0])
        plt.gca().add_patch(plt.Rectangle((x_start, y_start), region_width, region_height, edgecolor='red', facecolor='none', lw=2))
        
        # 顯示原始圖片及其中心框選區域的信息
        plt.title(f"{os.path.basename(image_file)}\n"
                  f"Size: {width}x{height}\n"
                  f"Region Size: {region_width}x{region_height}\n"
                  f"Brightness Avg.: {brightness:.2f}\n"
                  f"Color Avg.: {mean_color.astype(int)}", fontsize=12)

        # 將圖片信息添加到文字框中
        text_box.insert('end', f"{os.path.basename(image_file)}\n"
                              f"Size: {width}x{height}\n"
                              f"Region Size: {region_width}x{region_height}\n"
                              f"Brightness Avg.: {brightness:.2f}\n"
                              f"Color Avg.: {mean_color.astype(int)}\n"
                              f"----------------------------\n\n")
    
    pad = max(3.0 - 0.1 * num_rows, 0.3)
    plt.tight_layout(pad=pad, h_pad=1.0, w_pad=1.0)
    plt.gcf().canvas.manager.set_window_title("Image AE Results")
    plt.show()

def select_folder():
    """選擇資料夾並處理其中的圖片。"""
    folder_path = filedialog.askdirectory()
    if folder_path:
        try:
            show_image_details(folder_path)
            error_label.config(text="")  # 清除錯誤訊息
        except ValueError as e:
            error_label.config(text=str(e))
        except Exception as e:
            error_label.config(text="Error processing images")
    else:
        error_label.config(text="No folder selected")

def show_image_details(folder):
    """顯示圖片詳細信息並處理指定資料夾中的所有圖片。"""
    # 創建新的窗口來顯示圖片詳細信息
    details_window = Tk()
    details_window.title("Image Details")
    details_window.geometry("600x500")

    # 創建文字框和捲動條
    text_box = Text(details_window, wrap='word', height=30, width=80)
    text_box.pack(padx=10, pady=10, fill='both', expand=True)

    scrollbar = Scrollbar(details_window, orient='vertical', command=text_box.yview)
    scrollbar.pack(side='right', fill='y')

    text_box.config(yscrollcommand=scrollbar.set)

    # 處理圖片並將信息添加到文字框中
    process_images(folder, text_box)

    details_window.mainloop()

# 創建主窗口
root = Tk()
root.title("Image AE Tool")
root.geometry("300x130")

# 創建和放置小部件
Label(root, text="Select a folder to calculate AE:").pack(pady=10)
Button(root, text="Select", command=select_folder).pack(pady=10)
error_label = Label(root, text="", fg="red")
error_label.pack(pady=10)

# 啟動 GUI 事件循環
root.mainloop()
