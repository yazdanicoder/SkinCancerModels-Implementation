# -*- coding: utf-8 -*-
"""VGG16.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1E5mATHjH8YjhZZxz3w58FvuGC-YaW-sD
"""

from google.colab import drive
drive.mount('/content/drive')

from tensorflow.keras.applications import VGG16
from tensorflow.keras import layers, models
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Define image size
IMG_SIZE = (224, 224)  # Required input size for VGG16

# Load the VGG16 model pre-trained on ImageNet, without the top layers
base_model = VGG16(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

# Freeze the convolutional layers
for layer in base_model.layers:
    layer.trainable = False

# Create a new model on top of VGG16 base
model = models.Sequential([
    base_model,                # VGG16 base model
    layers.Flatten(),          # Flatten the output of the convolutional layers
    layers.Dense(256, activation='relu'),  # Fully connected layer
    layers.Dropout(0.5),       # Dropout for regularization
    layers.Dense(1, activation='sigmoid')  # Output layer for binary classification
])

# Compile the model
model.compile(optimizer=Adam(learning_rate=0.0001),
              loss='binary_crossentropy',
              metrics=['accuracy'])

# Prepare the data generators

# Data augmentation and rescaling for the training set
train_datagen = ImageDataGenerator(
    rescale=1./255,           # Rescale pixel values to [0, 1]
    shear_range=0.2,          # Random shear
    zoom_range=0.2,           # Random zoom
    horizontal_flip=True      # Randomly flip images
)

# Only rescaling for the validation set (no augmentation needed)
val_datagen = ImageDataGenerator(rescale=1./255)

# Load and preprocess the training images
train_generator = train_datagen.flow_from_directory(
    '/content/drive/MyDrive/data/train',              # Path to training data
    target_size=IMG_SIZE,       # Resize all images to 224x224 pixels
    batch_size=32,              # Number of images to be fed in each batch
    class_mode='binary'         # Binary classification (benign or malignant)
)

# Load and preprocess the validation images
validation_generator = val_datagen.flow_from_directory(
    '/content/drive/MyDrive/data/test',          # Path to validation data
    target_size=IMG_SIZE,       # Resize all images to 224x224 pixels
    batch_size=32,              # Number of images in each batch
    class_mode='binary'         # Binary classification
)

# Train the model using the data generators
history = model.fit(
    train_generator,
    epochs=10,                  # Number of epochs to train
)

# Evaluate the model on the validation set
val_loss, val_acc = model.evaluate(validation_generator)
print(f'Validation Accuracy: {val_acc:.4f}')
print(f'Validation Loss: {val_loss:.4f}')

import matplotlib.pyplot as plt

# Plot training & validation accuracy values
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('Model accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.show()

# Plot training & validation loss values
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.show()

# Save the model
model.save('skin_cancer_vgg16_model.h5')

import numpy as np
from tensorflow.keras.preprocessing import image

# Load and preprocess a single image
img_path = '/content/drive/MyDrive/data/test/benign/1006.jpg'
img = image.load_img(img_path, target_size=IMG_SIZE)
img_array = image.img_to_array(img)
img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
img_array /= 255.  # Rescale like during training

# Predict the class
prediction = model.predict(img_array)
if prediction[0] > 0.5:
    print('Malignant')
else:
    print('Benign')

# Using model.save()
model.save('my_model.keras')

# Or using keras.saving.save_model()
import keras.saving
keras.saving.save_model(model, 'my_model.keras')

from sklearn.metrics import f1_score

# Assuming 'model' is your trained model
import numpy as np

# Make predictions on the validation set
y_pred = model.predict(validation_generator)

# Convert predictions to class labels (0 or 1)
y_pred_classes = np.argmax(y_pred, axis=1)

# Get the true labels from the validation generator
y_true_classes = validation_generator.classes

from sklearn.metrics import f1_score

# Calculate F1 score
f1 = f1_score(y_true_classes, y_pred_classes, average='binary')  # For binary classification
print(f'F1 Score: {f1:.4f}')

print("True Classes:", y_true_classes)
print("Predicted Classes:", y_pred_classes)

from sklearn.metrics import classification_report

print(classification_report(y_true_classes, y_pred_classes))

# Unfreeze the last few layers of VGG16
for layer in base_model.layers[-4:]:
    layer.trainable = True

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=40,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

from sklearn.utils import class_weight
import numpy as np

# Get the classes from the generator
class_indices = train_generator.class_indices  # Get class indices
num_classes = len(class_indices)  # Get number of classes
y_train_classes = train_generator.classes  # Get the classes from the generator

# Calculate class weights
class_weights = class_weight.compute_class_weight(
    class_weight='balanced',
    classes=np.array(list(class_indices.values())),  # The class labels
    y=y_train_classes  # The actual labels from the generator
)

# Convert to a dictionary for use in model fitting
class_weight_dict = dict(enumerate(class_weights))

print("Class weights:", class_weight_dict)

history = model.fit(
    train_generator,
    validation_data=validation_generator,
    epochs=30,
    class_weight=class_weight_dict,  # Pass the class weights
)

# Evaluate the model on the validation set
val_loss, val_accuracy = model.evaluate(validation_generator)

print(f'Validation Loss: {val_loss:.4f}')
print(f'Validation Accuracy: {val_accuracy:.4f}')

# Generate predictions
y_pred = model.predict(validation_generator)
y_pred_classes = (y_pred > 0.5).astype(int)  # Convert probabilities to binary predictions

from sklearn.metrics import classification_report

# Get the true classes from the validation generator
y_true_classes = validation_generator.classes

# Generate a classification report
report = classification_report(y_true_classes, y_pred_classes, target_names=validation_generator.class_indices.keys())
print(report)

from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# Compute confusion matrix
cm = confusion_matrix(y_true_classes, y_pred_classes)

# Plot confusion matrix
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=validation_generator.class_indices.keys())
disp.plot(cmap=plt.cm.Blues)
plt.title('Confusion Matrix')
plt.show()

# Plot training & validation accuracy and loss values
plt.figure(figsize=(12, 5))

# Accuracy
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend()

# Loss
plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Model Loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend()

plt.show()

from sklearn.metrics import f1_score

# Get the true classes from the validation generator
y_true_classes = validation_generator.classes

# Calculate F1 score
f1 = f1_score(y_true_classes, y_pred_classes, average='binary')  # Use 'macro' or 'weighted' for multi-class
print(f'F1 Score: {f1:.4f}')

from sklearn.metrics import accuracy_score

# Get the true classes from the validation generator
y_true_classes = validation_generator.classes

# Calculate accuracy
accuracy = accuracy_score(y_true_classes, y_pred_classes)
print(f'Accuracy: {accuracy:.4f}')

from tensorflow.keras.preprocessing.image import ImageDataGenerator

datagen = ImageDataGenerator(
    rotation_range=40,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

for layer in base_model.layers[-4:]:
    layer.trainable = True

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

from sklearn.metrics import accuracy_score, f1_score

# Generate predictions
y_pred = model.predict(validation_generator)
y_pred_classes = (y_pred > 0.5).astype(int)  # Convert probabilities to binary predictions

from sklearn.metrics import f1_score

# Get the true classes from the validation generator
y_true_classes = validation_generator.classes

# Calculate F1 score
f1 = f1_score(y_true_classes, y_pred_classes, average='binary')  # Use 'macro' or 'weighted' for multi-class
print(f'F1 Score: {f1:.4f}')

from sklearn.metrics import accuracy_score

# Get the true classes from the validation generator
y_true_classes = validation_generator.classes

# Calculate accuracy
accuracy = accuracy_score(y_true_classes, y_pred_classes)
print(f'Accuracy: {accuracy:.4f}')

# For multi-class classification
y_pred_classes = y_pred.argmax(axis=-1)

# Get the true classes from the validation generator
y_true_classes = validation_generator.classes

from sklearn.metrics import accuracy_score

# Calculate accuracy
accuracy = accuracy_score(y_true_classes, y_pred_classes)
print(f'Accuracy: {accuracy:.4f}')

# Using model.save()
model.save('my_model.keras')

# Or using keras.saving.save_model()
import keras.saving
keras.saving.save_model(model, 'my_model.keras')