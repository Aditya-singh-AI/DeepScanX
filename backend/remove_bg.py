import cv2
import numpy as np
import sys

input_path = r'c:\Users\Hp\Downloads\DeepScanX AI\DeepScanX AI\frontend\public\logo.png'
output_path = r'c:\Users\Hp\Downloads\DeepScanX AI\DeepScanX AI\frontend\public\logo.png'

# Read image
img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
if img is None:
    print("Could not read image.")
    sys.exit(1)

# Ensure it has an alpha channel
if img.shape[2] == 3:
    img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

# Convert to grayscale to evaluate brightness
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# The background is a dark textured gray. The logo is bright orange and blue.
# Create a mask where pixels are darker than a certain threshold.
_, mask = cv2.threshold(gray, 70, 255, cv2.THRESH_BINARY)

# To remove the rough edges, we can apply morphological operations
kernel = np.ones((3, 3), np.uint8)
# opening removes small noise in the background
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
# dilate the background mask slightly to eat into the edges, or erode the foreground mask
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

# Optional GrabCut for better edge detection
# Since it's a textured background, GrabCut is usually much better.
# Let's use GrabCut with a bounding box covering the entire inner area,
# telling it the border 5 pixels are DEFINITELY background.
bgdModel = np.zeros((1,65),np.float64)
fgdModel = np.zeros((1,65),np.float64)

rect = (5, 5, img.shape[1]-10, img.shape[0]-10)
# convert to BGR for grabcut
bgr = img[:,:,:3]

# Create initial mask: 0=bg, 1=fg, 2=pr_bg, 3=pr_fg
# We use the threshold mask as an initial guess
gc_mask = np.where(mask > 0, cv2.GC_PR_FGD, cv2.GC_PR_BGD).astype('uint8')
# Set the very edges to definitely background
gc_mask[0:5, :] = cv2.GC_BGD
gc_mask[-5:, :] = cv2.GC_BGD
gc_mask[:, 0:5] = cv2.GC_BGD
gc_mask[:, -5:] = cv2.GC_BGD

cv2.grabCut(bgr, gc_mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_MASK)

# The final mask is where gc_mask is fg (1) or pr_fg (3)
final_mask = np.where((gc_mask==1)|(gc_mask==3), 255, 0).astype('uint8')

# Apply some smoothing to the mask edges to avoid jagged pixelation
final_mask = cv2.GaussianBlur(final_mask, (5, 5), 0)
_, final_mask = cv2.threshold(final_mask, 127, 255, cv2.THRESH_BINARY)

# Set the alpha channel
img[:, :, 3] = final_mask

# Save the transparency out
cv2.imwrite(output_path, img)
print("Background removed successfully.")
