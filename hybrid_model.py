# -*- coding: utf-8 -*-
"""hybrid model.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1g24MZ6YWdPZFcMu4tM1BXpk7IA4Ai-M2
"""

import torch
import torch.nn as nn
from torchvision import datasets, transforms
from torchvision.models import efficientnet_b0
import timm
from torch.utils.data import DataLoader

# EfficientNet feature extractor
efficientnet = efficientnet_b0(pretrained=True)
efficientnet_feature_extractor = nn.Sequential(*list(efficientnet.children())[:-1])  # Remove the classification head

# Swin Transformer feature extractor
swin_transformer = timm.create_model('swin_tiny_patch4_window7_224', pretrained=True)
swin_feature_extractor = nn.Sequential(*list(swin_transformer.children())[:-1])  # Remove the classification head

from google.colab import drive

# Mount Google Drive
drive.mount('/content/drive')

from torchvision import datasets, transforms
from torch.utils.data import DataLoader

# Define paths
train_dir = '/content/drive/MyDrive/data/train'
val_dir = '/content/drive/MyDrive/data/test'

# Define image transformations
image_transforms = {
    'train': transforms.Compose([
        transforms.Resize((224, 224)),  # Resize images for EfficientNet and Swin
        transforms.RandomHorizontalFlip(),  # Data augmentation
        transforms.RandomRotation(10),     # Data augmentation
        transforms.ToTensor(),             # Convert to Tensor
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])  # Normalize
    ]),
    'val': transforms.Compose([
        transforms.Resize((224, 224)),  # Resize images
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
}

# Load datasets
train_dataset = datasets.ImageFolder(root=train_dir, transform=image_transforms['train'])
val_dataset = datasets.ImageFolder(root=val_dir, transform=image_transforms['val'])

# DataLoaders
batch_size = 32
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

# Print dataset sizes
print(f"Training samples: {len(train_dataset)}")
print(f"Validation samples: {len(val_dataset)}")

class HybridSkinCancerModel(nn.Module):
    def __init__(self, efficientnet, swin_transformer, num_classes):
        super(HybridSkinCancerModel, self).__init__()
        self.efficientnet = efficientnet
        self.swin_transformer = swin_transformer

        # Swin Transformer output adjustment
        self.swin_fc = nn.Linear(7 * 7 * 768, 768)  # Flatten and reduce Swin Transformer output

        # Fully connected layer for combined features
        self.fc = nn.Linear(1280 + 768, num_classes)  # Adjust dimensions accordingly

    def forward(self, x):
        # EfficientNet features
        eff_features = self.efficientnet(x)  # Shape: (batch_size, 1280, 1, 1)
        eff_features = eff_features.view(eff_features.size(0), -1)  # Flatten: (batch_size, 1280)

        # Swin Transformer features
        swin_features = self.swin_transformer(x)  # Shape: (batch_size, 768, 7, 7)
        swin_features = swin_features.view(swin_features.size(0), -1)  # Flatten: (batch_size, 768 * 7 * 7)
        swin_features = self.swin_fc(swin_features)  # Reduce: (batch_size, 768)

        # Concatenate features
        combined_features = torch.cat((eff_features, swin_features), dim=1)  # Shape: (batch_size, 1280 + 768)

        # Fully connected layer
        out = self.fc(combined_features)  # Shape: (batch_size, num_classes)
        return out

# Define image transformations
image_transforms = transforms.Compose([
    transforms.Resize((224, 224)),  # Resize images to 224x224 for both models
    transforms.ToTensor(),          # Convert images to tensors
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])  # Normalize based on ImageNet
])

# Load the dataset
train_dataset = datasets.ImageFolder(root='/content/drive/MyDrive/data/train', transform=image_transforms)

# DataLoader
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

# Instantiate the hybrid model
num_classes = 2  # Example: benign and malignant
hybrid_model = HybridSkinCancerModel(efficientnet_feature_extractor, swin_feature_extractor, num_classes)

# Loss function and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(hybrid_model.parameters(), lr=0.001)

# Training setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
hybrid_model.to(device)

# Training loop
epochs = 10
for epoch in range(epochs):
    hybrid_model.train()
    running_loss = 0.0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)

        # Zero gradients
        optimizer.zero_grad()

        # Forward pass
        outputs = hybrid_model(images)
        loss = criterion(outputs, labels)

        # Backward pass and optimization
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    # Log the epoch's average loss
    print(f"Epoch [{epoch + 1}/{epochs}], Loss: {running_loss / len(train_loader):.4f}")

# Save the trained model
torch.save(hybrid_model.state_dict(), "hybrid_skin_cancer_model.pth")

torch.save(hybrid_model.state_dict(), '/content/drive/MyDrive/hybrid_skin_cancer_model.pth')

from sklearn.metrics import confusion_matrix, classification_report, ConfusionMatrixDisplay
import numpy as np
import matplotlib.pyplot as plt

# Initialize placeholders for evaluation
all_labels = []
all_preds = []

# Validation Phase (with metrics collection)
hybrid_model.eval()
val_loss = 0.0
correct = 0
total = 0

with torch.no_grad():
    for images, labels in val_loader:
        images, labels = images.to(device), labels.to(device)
        outputs = hybrid_model(images)
        loss = criterion(outputs, labels)
        val_loss += loss.item()

        # Predictions and ground truth
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

        # Store labels for metrics
        all_labels.extend(labels.cpu().numpy())
        all_preds.extend(predicted.cpu().numpy())

# Calculate accuracy
accuracy = 100 * correct / total
print(f"Validation Accuracy: {accuracy:.2f}%")

# Calculate F1 score
from sklearn.metrics import f1_score
f1 = f1_score(all_labels, all_preds, average='weighted')
print(f"F1 Score: {f1:.4f}")

# Confusion Matrix
conf_matrix = confusion_matrix(all_labels, all_preds)
print("Confusion Matrix:")
print(conf_matrix)

# Classification Report
class_report = classification_report(all_labels, all_preds, target_names=train_dataset.classes)
print("Classification Report:")
print(class_report)

# Plot Confusion Matrix
disp = ConfusionMatrixDisplay(confusion_matrix=conf_matrix, display_labels=train_dataset.classes)
disp.plot(cmap=plt.cm.Blues)
plt.title("Confusion Matrix")
plt.show()

# Save metrics to a file
with open('/content/drive/MyDrive/metrics.txt', 'w') as f:
    f.write(f"Validation Accuracy: {accuracy:.2f}%\n")
    f.write(f"F1 Score: {f1:.4f}\n")
    f.write("Confusion Matrix:\n")
    f.write(np.array2string(conf_matrix))
    f.write("\nClassification Report:\n")
    f.write(class_report)

# Example lists to track loss
train_losses = []  # Populate with running_loss / len(train_loader) from each epoch
val_losses = []    # Populate with val_loss / len(val_loader) from each epoch

# Plot training vs validation loss
plt.plot(range(1, len(train_losses) + 1), train_losses, label='Training Loss')
plt.plot(range(1, len(val_losses) + 1), val_losses, label='Validation Loss')
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.title("Training and Validation Loss")
plt.legend()
plt.show()



import matplotlib.pyplot as plt

# Data (replace these values if needed)
epochs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # Example epochs
val_accuracies = [85.0, 86.5, 87.8, 89.0, 90.3, 90.0, 91.0, 91.5, 92.0, 92.5]  # Validation accuracy over epochs
f1_scores = [0.850, 0.865, 0.878, 0.890, 0.903, 0.900, 0.910, 0.915, 0.920, 0.925]  # F1 score over epochs

# Plotting the graph
plt.figure(figsize=(10, 6))

# Plot accuracy
plt.plot(epochs, val_accuracies, marker='o', label='Validation Accuracy', color='blue')

# Plot F1 Score
plt.plot(epochs, f1_scores, marker='x', label='F1 Score', color='green', linestyle='--')

# Graph details
plt.title('Model Performance Over Epochs')
plt.xlabel('Epochs')
plt.ylabel('Percentage')
plt.xticks(epochs)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.show()

import matplotlib.pyplot as plt

# Data (replace with your actual values if needed)
epochs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # epochs
val_accuracies = [85.0, 86.5, 87.8, 89.0, 90.3, 90.0, 91.0, 91.5, 92.0, 92.5]  # Validation Accuracy
f1_scores = [0.850, 0.865, 0.878, 0.890, 0.903, 0.900, 0.910, 0.915, 0.920, 0.925]  # F1 Score
precisions = [0.84, 0.85, 0.87, 0.89, 0.91, 0.90, 0.92, 0.93, 0.93, 0.94]  # Precision
losses = [0.45, 0.40, 0.38, 0.35, 0.30, 0.28, 0.26, 0.24, 0.22, 0.20]  # Loss values per epoch

# Plotting the graphs
plt.figure(figsize=(14, 8))

# Subplot 1: Accuracy
plt.subplot(2, 2, 1)
plt.plot(epochs, val_accuracies, marker='o', color='blue', label='Validation Accuracy')
plt.title('Validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy (%)')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()

# Subplot 2: F1 Score
plt.subplot(2, 2, 2)
plt.plot(epochs, f1_scores, marker='x', color='green', label='F1 Score')
plt.title('F1 Score')
plt.xlabel('Epochs')
plt.ylabel('Score')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()

# Subplot 3: Precision
plt.subplot(2, 2, 3)
plt.plot(epochs, precisions, marker='s', color='orange', label='Precision')
plt.title('Precision')
plt.xlabel('Epochs')
plt.ylabel('Score')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()

# Subplot 4: Loss
plt.subplot(2, 2, 4)
plt.plot(epochs, losses, marker='d', color='red', label='Loss')
plt.title('Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()

# Adjust layout and show
plt.tight_layout()
plt.show()