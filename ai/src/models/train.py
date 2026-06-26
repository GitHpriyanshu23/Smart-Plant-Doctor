import json
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models, transforms
from src.data.dataset import get_dataloaders


def build_classifier(num_classes: int, backbone: str = "efficientnet_b3"):
    if backbone == "efficientnet_b3":
        model = models.efficientnet_b3(weights=models.EfficientNet_B3_Weights.IMAGENET1K_V1)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.2, inplace=True),
            nn.Linear(in_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.2, inplace=True),
            nn.Linear(512, num_classes),
        )
        image_size = 300
    else:
        model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
        model.classifier = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(model.last_channel, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(512, num_classes),
        )
        image_size = 224
    return model, image_size


def temperature_scale(logits: torch.Tensor, temperature: float) -> torch.Tensor:
    return logits / max(temperature, 1e-6)


def fit_temperature(model, val_loader, device) -> float:
    model.eval()
    logits_list, labels_list = [], []
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            logits_list.append(outputs)
            labels_list.append(labels)
    logits = torch.cat(logits_list)
    labels = torch.cat(labels_list)
    temp = nn.Parameter(torch.ones(1, device=device) * 1.5)
    optimizer = optim.LBFGS([temp], lr=0.01, max_iter=50)
    nll = nn.CrossEntropyLoss()

    def closure():
        optimizer.zero_grad()
        loss = nll(temperature_scale(logits, temp.item()), labels.to(device))
        loss.backward()
        return loss

    optimizer.step(closure)
    return float(temp.item())


def train_model(
    data_dir="data",
    backbone="efficientnet_b3",
    batch_size=32,
    lr=1e-4,
    num_epochs=10,
    device=None,
    export_path="exports/smart_plant_doctor_model.pth",
):
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}, backbone: {backbone}")

    image_size = 300 if backbone == "efficientnet_b3" else 224
    train_loader, val_loader, class_names = get_dataloaders(data_dir, image_size, batch_size)
    num_classes = len(class_names)
    print(f"Found {num_classes} classes")
    model, image_size = build_classifier(num_classes, backbone)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    best_acc = 0.0
    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch + 1}/{num_epochs}")
        model.train()
        running_loss, running_corrects = 0.0, 0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            _, preds = torch.max(outputs, 1)
            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)

        train_acc = running_corrects.double() / len(train_loader.dataset)
        print(f"Train Acc: {train_acc:.4f}")

        model.eval()
        val_corrects = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                val_corrects += torch.sum(preds == labels.data)

        val_acc = val_corrects.double() / len(val_loader.dataset)
        print(f"Val Acc: {val_acc:.4f}")

        if val_acc > best_acc:
            best_acc = val_acc
            temperature = fit_temperature(model, val_loader, device)
            os.makedirs(os.path.dirname(export_path) or ".", exist_ok=True)
            bundle = {
                "state_dict": model.state_dict(),
                "classes": class_names,
                "backbone": backbone,
                "input_size": image_size,
                "best_val_acc": float(val_acc * 100),
                "temperature": temperature,
            }
            torch.save(bundle, export_path)
            print(f"Saved best model to {export_path} (temp={temperature:.3f})")

    print(f"\nTraining complete. Best Val Acc: {best_acc * 100:.2f}%")
    return model, class_names


if __name__ == "__main__":
    train_model()
