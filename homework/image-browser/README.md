# Image Browser

GUI duyệt ảnh — bài tập môn Xử lý ảnh số.

**Student:** Nguyen Vu Bao — 23110079

## Tính năng

- **Folder tree** (panel trái): cây thư mục để điều hướng nhanh.
- **Thumbnail grid** (panel giữa): lưới thumbnail của ảnh trong folder đang chọn.
- **Preview** (panel phải): xem ảnh lớn, scale theo cửa sổ; hiển thị `NO IMAGE AVAILABLE` khi chưa có ảnh.
- **Toolbar**: `Folder selection` (Ctrl+O) mở dialog chọn folder gốc; `Close` (Ctrl+Q) đóng app.
- **Status bar**: hiển thị folder hiện tại + số ảnh.
- Hỗ trợ định dạng: `.jpg .jpeg .png .bmp .tif .tiff .webp`.

## Cấu trúc

```
image-browser/
├── main.py                    # entry point
├── run.py                     # (tuỳ chọn) wrapper script xử lý env
├── requirements.txt
├── README.md
└── app/
    ├── main_window.py         # MainWindow + toolbar + 3-panel splitter
    ├── widgets/
    │   ├── folder_tree.py     # QTreeView + QFileSystemModel
    │   ├── thumbnail_grid.py  # QListView IconMode
    │   └── preview_panel.py   # QLabel + placeholder
    ├── core/
    │   ├── constants.py
    │   ├── image_loader.py    # list/load/scale (Qt + cv2 fallback)
    │   └── thumbnail_worker.py# (deprecated) QThread template
    └── processors/            # chỗ trống cho HW3+ (filter/rotate/crop…)
        └── __init__.py
```

## Cài đặt

### Dùng conda env `dipr` (khuyến nghị)

```bash
conda activate dipr
# Gỡ opencv-python GUI version, cài headless
pip uninstall opencv-python -y && pip install opencv-python-headless
# Cài PyQt5
pip install PyQt5
```

### Hoặc cài from `requirements.txt`

```bash
cd homework/image-browser
pip install -r requirements.txt
```

## Chạy

```bash
conda activate dipr  # nếu dùng conda
python main.py
```

Nếu gặp lỗi Qt plugin, thử:
```bash
# Đặt QT_QPA_PLATFORM thành wayland (GNOME modern)
QT_QPA_PLATFORM=wayland python main.py
```

## Smoke test checklist

- [ ] App mở → 3 panel + toolbar; preview hiện `NO IMAGE AVAILABLE`.
- [ ] `Folder selection` → chọn `../c1/images/` → tree hiện danh sách folder.
- [ ] Click `jpg` folder → grid load 10 thumbnail.
- [ ] Click 1 thumbnail → preview hiển thị ảnh lớn, scale đúng tỷ lệ.
- [ ] Resize cửa sổ → preview rescale mượt mà.
- [ ] Đổi folder `png` / `bmp` → grid update danh sách.
- [ ] Hotkey: Ctrl+O = Folder selection, Ctrl+Q = Close.
- [ ] Click Close button → app đóng sạch.

## Phát triển tiếp (HW3+)

Thêm processor mới:

1. Tạo `app/processors/<name>.py` với class:
   ```python
   class MyProcessor:
       def apply(self, image: np.ndarray, **params) -> np.ndarray:
           # ...process...
           return result_image
   ```

2. Reuse logic từ [../c1/hw2.ipynb](../c1/hw2.ipynb):
   - Split RGB: `cv2.split()`
   - Grayscale: `cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)`
   - Rotate: `cv2.getRotationMatrix2D()` + `cv2.warpAffine()`
   - Crop: array slicing `img[y1:y2, x1:x2]`

3. (Optional) Thêm `app/widgets/processor_panel.py` để chỉnh parameter realtime.

4. Thêm menu `Process` ở `main_window.py` để chạy processor lên preview.
