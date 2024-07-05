# Image AE Tool 使用說明  
簡介  
這個工具旨在處理指定資料夾中的圖片，計算其亮度和顏色的平均值，並展示圖片的詳細信息，包括中心區域的亮度和色彩平均值。  
  
使用步驟  
選擇資料夾: 點選 "Select" 按鈕以選擇包含圖片的資料夾。  
查看結果: 程式會顯示每張圖片的原始檔案名稱、尺寸、中心區域的大小、亮度平均值及顏色平均值。  
評估結果: 程式會計算所有圖片的平均亮度及其範圍，並判斷是否通過給定的範圍。  
主要功能  
圖片選擇: 可從指定資料夾中選擇包含圖片的資料夾進行處理。  
亮度計算: 自動計算每張圖片中心區域(Frame size/3)的亮度平均值。  
色彩分析: 計算每張圖片的顏色平均值（RGB）。  
結果顯示: 將結果即時顯示於視窗中，並提供文字框以查看詳細信息。  
程式碼版本  
目前版本：v1.1_20240705    
  
注意事項  
程式假定所有處理的圖片具有相同的框架大小。  
支持的圖片格式包括：jpg、jpeg、png、bmp 和 tiff。  
