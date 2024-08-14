import os
from tkinter import Tk, filedialog, Button, Label, Text, Scrollbar
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import time

# 版本名稱
VERSION_NAME = "v1.3_20240814"

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

def process_images(folder, text_box, log_file=None):
    """處理指定資料夾中的所有圖片，並將結果寫入文字框（如果提供）和 LOG 檔案。"""
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

    brightness_list = []
    fail_images = []

    # 先計算所有圖片的亮度，然後計算總平均亮度和範圍
    for idx, (image_file, image) in enumerate(zip(image_files, images)):
        central_region = image.crop((x_start, y_start, x_start + region_width, y_start + region_height))
        brightness, mean_color = calculate_mean_brightness_and_color(central_region)
        brightness_list.append(brightness)
    
    # 計算總平均亮度及其範圍
    ae_brightness_avg = np.mean(brightness_list)
    ae_range = [ae_brightness_avg - 0.3, ae_brightness_avg + 0.3]

    # 確定 AE 結果是否通過
    ae_result = all(ae_range[0] <= b <= ae_range[1] for b in brightness_list)

    # 然後再遍歷每張圖片進行檢查
    for idx, (image_file, image) in enumerate(zip(image_files, images)):
        row = idx // IMAGES_PER_ROW
        col = idx % IMAGES_PER_ROW
        
        brightness = brightness_list[idx]
        mean_color = calculate_mean_brightness_and_color(image)[1]

        plt.subplot(num_rows, IMAGES_PER_ROW, idx + 1)
        plt.imshow(image)
        plt.xlim([0, width])
        plt.ylim([height, 0])
        plt.gca().add_patch(plt.Rectangle((x_start, y_start), region_width, region_height, edgecolor='red', facecolor='none', lw=2))
        
        # 檢查是否在允許的亮度範圍內
        is_fail = brightness < ae_range[0] or brightness > ae_range[1]
        
        # 設置標題的文字顏色
        title_color = 'red' if is_fail else 'black'

        # 顯示圖片的標題信息
        title_text = f"{os.path.basename(image_file)}\n" \
                     f"Size: {width}x{height}\n" \
                     f"Region Size: {region_width}x{region_height}\n" \
                     f"Brightness Avg.: {brightness:.2f}\n" \
                     f"Color Avg.(RGB): {mean_color.astype(int)}"
        plt.title(title_text, fontsize=12, color=title_color)

        # 保存詳細信息到 log 文件
        log_info = f"{os.path.basename(image_file)}\n" \
                   f"Size: {width}x{height}\n" \
                   f"Region Size: {region_width}x{region_height}\n" \
                   f"Brightness Avg.: {brightness:.2f}\n" \
                   f"Color Avg.(RGB): {mean_color.astype(int)}\n" \
                   f"----------------------------\n\n"
        if text_box is not None:
            text_box.insert('end', log_info)
        if log_file is not None:
            log_file.write(log_info)

        # 如果該圖片失敗，添加到 fail_images 列表中
        if is_fail:
            fail_image = f"FAIL: {os.path.basename(image_file)} - Brightness Avg.: {brightness:.2f}\n"
            fail_images.append(fail_image)

    # 如果有 Fail，記錄到 log 並顯示在 text_box 中
    if fail_images:
        for fail_image in fail_images:
            if text_box is not None:
                text_box.insert('end', fail_image, 'fail')
            if log_file is not None:
                log_file.write(fail_image)

    # 計算並顯示總結果
    summary_info = "----------------------------\n\n" \
                   f"AE Brightness Avg.: {ae_brightness_avg:.2f}\n" \
                   f"AE Range: [{ae_range[0]:.2f}, {ae_range[1]:.2f}]\n" \
                   f"AE Result: {'PASS' if ae_result else 'FAIL'}\n"
    if text_box is not None:
        text_box.insert('end', summary_info)
    if log_file is not None:
        log_file.write(summary_info)

    # 如果有 Fail，使用紅字標示
    if fail_images and text_box is not None:
        text_box.tag_config('fail', foreground='red')

    # 設置視窗的標題名稱
    plt.gcf().canvas.manager.set_window_title("Image Analysis Results")  # 替換成你想要的標題

    # 顯示結果並返回結果截圖
    plt.show(block=False)  # 不阻塞主線程，確保視窗可以完全顯示
    screenshot_path = save_screenshot(folder)

    return screenshot_path

def save_screenshot(folder):
    """保存結果視窗的截圖到指定資料夾的result/AE資料夾中。"""
    # 創建目標資料夾
    result_folder = os.path.join(folder, "result", "AE")
    os.makedirs(result_folder, exist_ok=True)
    
    # 生成截圖文件名，前綴加上日期
    date_prefix = time.strftime("%Y%m%d_%H%M%S")
    screenshot_file = os.path.join(result_folder, f"{date_prefix}_AE_screenshot.png")
    
    # 保存當前figure的截圖
    plt.pause(0.5)  # 暫停以確保圖片完全顯示
    plt.savefig(screenshot_file, dpi=300, bbox_inches='tight')
    
    return screenshot_file

def select_folder():
    """選擇資料夾並處理其中的圖片。"""
    folder_path = filedialog.askdirectory()
    if folder_path:
        try:
            # 在成功運行前清除錯誤訊息
            error_label.config(text="")

            # 開始處理圖片
            show_image_details(folder_path)

        except ValueError as e:
            # 捕捉ValueError，顯示錯誤訊息但不存LOG和截圖
            error_label.config(text=str(e))
        except Exception as e:
            # 捕捉一般性錯誤，顯示通用錯誤訊息
            error_label.config(text="Error processing images")
    else:
        error_label.config(text="No folder selected")

def show_image_details(folder):
    """顯示圖片詳細信息並處理指定資料夾中的所有圖片。"""
    try:
        # 創建 result/AE 資料夾並創建 log 文件名
        result_folder = os.path.join(folder, "result", "AE")
        os.makedirs(result_folder, exist_ok=True)
        
        date_prefix = time.strftime("%Y%m%d_%H%M%S")
        log_file_path = os.path.join(result_folder, f"{date_prefix}_AE_log.txt")
        
        # 打開 log 文件
        with open(log_file_path, 'w') as log_file:
            # 處理圖片並將信息寫入 log 文件
            screenshot_path = process_images(folder, text_box=None, log_file=log_file)
            log_file.write(f"Screenshot saved at: {screenshot_path}\n")

        # 創建並顯示新窗口來顯示圖片詳細信息
        details_window = Tk()
        details_window.title(f"Image Details")
        details_window.geometry("600x500")

        # 創建文字框和捲動條
        text_box = Text(details_window, wrap='word', height=30, width=80)
        text_box.pack(padx=10, pady=10, fill='both', expand=True)

        scrollbar = Scrollbar(details_window, orient='vertical', command=text_box.yview)
        scrollbar.pack(side='right', fill='y')

        text_box.config(yscrollcommand=scrollbar.set)

        # 將 LOG 文件中的內容讀取並顯示在文字框中
        with open(log_file_path, 'r') as log_file:
            text_box.insert('end', log_file.read())

        details_window.mainloop()

    except Exception as e:
        # 捕捉所有錯誤，不創建視窗，不保存 LOG 和截圖，只顯示錯誤訊息
        error_label.config(text="Error: " + str(e))


# 創建主窗口
root = Tk()
root.title(f"IQ AE Tool")
root.geometry("300x150")

# 創建和放置小部件
Label(root, text="Select a folder to calculate AE:").pack(pady=10)
Button(root, text="Select", command=select_folder).pack(pady=10)
error_label = Label(root, text="", fg="red")
error_label.pack(pady=10)

# 在左下角顯示版本名稱，並稍微往上調整位置
version_label = Label(root, text=f"Version: {VERSION_NAME}", anchor="w")
# 使用 pack 將標籤放置在窗口的底部，使用 pady 來稍微抬高
version_label.pack(side="bottom", anchor="sw", pady=3, padx=10)

# 啟動 GUI 事件循環
root.mainloop()
