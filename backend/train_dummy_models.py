import os
import shutil
import glob
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {DEVICE}")

# Find all images in the project directory
project_dir = os.path.dirname(os.path.abspath(__file__))
image_extensions = ('*.png', '*.jpg', '*.jpeg')
all_images = []
for ext in image_extensions:
    all_images.extend(glob.glob(os.path.join(project_dir, '**', ext), recursive=True))

# Filter out non-relevant images or too small ones just to be safe, but we'll use most of them
valid_images = [img for img in all_images if '.git' not in img and 'venv' not in img and 'cam_' not in img.lower()]

print(f"Found {len(valid_images)} valid images to use as dataset.")

# --- Setup Dataset Structure ---
dataset_dir = os.path.join(project_dir, 'dataset')
os.makedirs(dataset_dir, exist_ok=True)

# App3: 5 classes
app3_dir = os.path.join(dataset_dir, 'app3')
app3_classes = ["Colon Adenocarcinoma", "Colon Benign Tissue", "Lung Adenocarcinoma", "Lung Benign Tissue", "Lung Squamous Cell Carcinoma"]

# App4: 2 classes
app4_dir = os.path.join(dataset_dir, 'app4')
app4_classes = ['IDC_minus', 'IDC_plus']

# App5: 2 classes
app5_dir = os.path.join(dataset_dir, 'app5')
app5_classes = ['Cancer_minus', 'Cancer_plus']

# Create folders and distribute images
for d, classes in [(app3_dir, app3_classes), (app4_dir, app4_classes), (app5_dir, app5_classes)]:
    os.makedirs(d, exist_ok=True)
    for c in classes:
        os.makedirs(os.path.join(d, c), exist_ok=True)
        
    # Just distribute all images evenly across the classes to act as a dummy dataset
    if len(valid_images) == 0:
        continue
    
    imgs_per_class = max(1, len(valid_images) // len(classes))
    for i, img_path in enumerate(valid_images):
        class_idx = (i // imgs_per_class) % len(classes)
        class_name = classes[class_idx]
        dest_path = os.path.join(d, class_name, f"img_{i}.png")
        shutil.copy(img_path, dest_path)

# --- Define Training Routine ---
def train_model(data_dir, model, num_epochs=1, save_path='', is_app5=False):
    print(f"\nTraining model for {save_path}...")
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    dataset = datasets.ImageFolder(data_dir, transform=transform)
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    model = model.to(DEVICE)
    model.train()
    
    for epoch in range(num_epochs):
        running_loss = 0.0
        for inputs, labels in dataloader:
            inputs = inputs.to(DEVICE)
            labels = labels.to(DEVICE)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * inputs.size(0)
            
        epoch_loss = running_loss / len(dataset)
        print(f"Epoch {epoch+1}/{num_epochs} Loss: {epoch_loss:.4f}")
        
    # Save model
    if is_app5:
        # App5 expects 'model_state_dict' key
        torch.save({'model_state_dict': model.state_dict()}, save_path)
    else:
        torch.save(model.state_dict(), save_path)
    print(f"Model saved to {save_path}")

# --- Train App3 Model ---
model3 = models.resnet18(weights=None)
model3.fc = nn.Linear(model3.fc.in_features, 5)
train_model(app3_dir, model3, num_epochs=2, save_path=os.path.join(project_dir, 'app3', 'resnet18_model_001.pth'))

# --- Train App4 Model ---
# App4 uses ResNetModel which wraps resnet18
class ResNetModel(nn.Module):
    def __init__(self, num_classes=2):
        super(ResNetModel, self).__init__()
        self.resnet = models.resnet18(weights=None)
        num_ftrs = self.resnet.fc.in_features
        self.resnet.fc = nn.Linear(num_ftrs, num_classes)

    def forward(self, x):
        return self.resnet(x)

model4 = ResNetModel(num_classes=2)
train_model(app4_dir, model4, num_epochs=2, save_path=os.path.join(project_dir, 'app4', 'breast_cancer_cnn_model_updated.pth'))

# --- Train App5 Model ---
model5 = models.resnet18(weights=None)
in_features = model5.fc.in_features
model5.fc = nn.Sequential(
    nn.Dropout(0.3),
    nn.Linear(in_features, 256),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(256, len(app5_classes))
)
train_model(app5_dir, model5, num_epochs=2, save_path=os.path.join(project_dir, 'app5', 'lung_cancer_prediction_20250821_150505.pth'), is_app5=True)

# ════════════════════════════════════════════════════
# NEW MODULES — Skin Cancer, Chest X-Ray, Diabetic Retinopathy
# ════════════════════════════════════════════════════

# App8: Skin Cancer — 2 classes
app8_dir = os.path.join(dataset_dir, 'app8')
app8_classes = ['Benign', 'Malignant']
for c in app8_classes:
    os.makedirs(os.path.join(app8_dir, c), exist_ok=True)
if valid_images:
    ipc = max(1, len(valid_images) // len(app8_classes))
    for i, img in enumerate(valid_images):
        ci = (i // ipc) % len(app8_classes)
        shutil.copy(img, os.path.join(app8_dir, app8_classes[ci], f"img_{i}.png"))

model8 = models.resnet18(weights=None)
model8.fc = nn.Linear(model8.fc.in_features, 2)
train_model(app8_dir, model8, num_epochs=2,
            save_path=os.path.join(project_dir, 'app8', 'skin_cancer_resnet18.pth'),
            is_app5=True)

# App9: Chest X-Ray — 4 classes
app9_dir = os.path.join(dataset_dir, 'app9')
app9_classes = ['Normal', 'Pneumonia', 'COVID-19', 'Tuberculosis']
for c in app9_classes:
    os.makedirs(os.path.join(app9_dir, c), exist_ok=True)
if valid_images:
    ipc = max(1, len(valid_images) // len(app9_classes))
    for i, img in enumerate(valid_images):
        ci = (i // ipc) % len(app9_classes)
        shutil.copy(img, os.path.join(app9_dir, app9_classes[ci], f"img_{i}.png"))

model9 = models.resnet18(weights=None)
model9.fc = nn.Linear(model9.fc.in_features, 4)
train_model(app9_dir, model9, num_epochs=2,
            save_path=os.path.join(project_dir, 'app9', 'chest_xray_resnet18.pth'),
            is_app5=True)

# App10: Diabetic Retinopathy — 5 classes
app10_dir = os.path.join(dataset_dir, 'app10')
app10_classes = ['No DR', 'Mild', 'Moderate', 'Severe', 'Proliferative DR']
for c in app10_classes:
    os.makedirs(os.path.join(app10_dir, c), exist_ok=True)
if valid_images:
    ipc = max(1, len(valid_images) // len(app10_classes))
    for i, img in enumerate(valid_images):
        ci = (i // ipc) % len(app10_classes)
        shutil.copy(img, os.path.join(app10_dir, app10_classes[ci], f"img_{i}.png"))

model10 = models.resnet18(weights=None)
model10.fc = nn.Linear(model10.fc.in_features, 5)
train_model(app10_dir, model10, num_epochs=2,
            save_path=os.path.join(project_dir, 'app10', 'diabetic_retinopathy_resnet18.pth'),
            is_app5=True)

print("\nAll models (including new modules) trained and saved successfully!")
