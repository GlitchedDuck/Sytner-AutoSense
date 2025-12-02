# helpers/ocr.py
# Simple helper to preprocess images for OCR (binarization/resize/contrast)
from PIL import Image, ImageOps, ImageFilter, ImageEnhance

def preprocess_for_ocr(pil_img, target_width=1200):
    # Auto-rotate & convert to RGB
    img = ImageOps.exif_transpose(pil_img).convert("RGB")
    # Resize while keeping aspect ratio
    w, h = img.size
    if w < target_width:
        ratio = target_width / float(w)
        img = img.resize((int(w*ratio), int(h*ratio)), Image.LANCZOS)
    # Increase contrast and sharpen slightly
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    img = img.filter(ImageFilter.SHARPEN)
    # Convert to grayscale
    img = img.convert("L")
    return img
