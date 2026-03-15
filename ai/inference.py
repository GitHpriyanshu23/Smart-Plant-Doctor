#!/usr/bin/env python3
"""
Smart Plant Doctor - Disease Prediction Model with Treatment Recommendations
Trained MobileNetV2 model for plant disease recognition with home remedies
"""

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import json
import os
import sys
import argparse
from pathlib import Path

class SmartPlantDoctor:
    def __init__(self, model_path="exports/smart_plant_doctor_model.pth", device=None):
        """
        Initialize the Smart Plant Doctor model
        
        Args:
            model_path (str): Path to the trained model file
            device (str): Device to run inference on ('cuda', 'cpu', or None for auto)
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"🌱 Initializing Smart Plant Doctor...")
        print(f"📂 Loading model from: {model_path}")
        
        # Check if model file exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Load model bundle
        self.bundle = torch.load(model_path, map_location=self.device)
        self.classes = self.bundle['classes']
        self.num_classes = len(self.classes)
        
        print(f"🏷️ Found {self.num_classes} disease classes")
        
        # Rebuild model architecture (matching training architecture)
        self.model = models.mobilenet_v2(pretrained=False)
        self.model.classifier = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(self.model.last_channel, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(512, self.num_classes)
        )
        
        # Load trained weights
        self.model.load_state_dict(self.bundle['state_dict'])
        self.model = self.model.to(self.device).eval()
        
        # Setup image preprocessing (matching training transforms)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        # Initialize treatment database
        self.treatments = self._load_treatments()
        
        print(f"✅ Smart Plant Doctor loaded successfully!")
        print(f"🖥️ Device: {self.device}")
        print(f"🏆 Model accuracy: {self.bundle.get('best_val_acc', 0):.2f}%")
        print(f"📊 Input size: {self.bundle.get('input_size', 224)}x{self.bundle.get('input_size', 224)}")

    def _load_treatments(self):
        """Load treatment recommendations for each disease"""
        treatments = {
            # Aloe Vera Diseases
            "Aloe Vera_Aloe_Anthracnose": {
                "name": "Anthracnose",
                "symptoms": "Dark, sunken lesions on leaves and stems",
                "home_remedies": [
                    "Remove infected leaves immediately",
                    "Apply neem oil spray (2 tbsp neem oil + 1 gallon water)",
                    "Improve air circulation around the plant",
                    "Avoid overhead watering",
                    "Apply baking soda solution (1 tsp baking soda + 1 quart water)"
                ],
                "prevention": "Keep leaves dry, ensure good drainage, avoid overcrowding"
            },
            "Aloe Vera_Aloe_Healthy": {
                "name": "Healthy Aloe Vera",
                "symptoms": "No disease detected",
                "home_remedies": [
                    "Continue current care routine",
                    "Ensure adequate sunlight (6-8 hours daily)",
                    "Water only when soil is dry",
                    "Use well-draining soil mix",
                    "Fertilize monthly during growing season"
                ],
                "prevention": "Maintain consistent care, monitor for early signs of disease"
            },
            "Aloe Vera_Aloe_Leaf_Spot": {
                "name": "Leaf Spot",
                "symptoms": "Brown or black spots on leaves",
                "home_remedies": [
                    "Remove affected leaves",
                    "Apply copper fungicide spray",
                    "Improve air circulation",
                    "Water at soil level only",
                    "Apply chamomile tea spray (cooled tea)"
                ],
                "prevention": "Avoid wetting leaves, ensure proper spacing"
            },
            "Aloe Vera_Aloe_Rust": {
                "name": "Rust Disease",
                "symptoms": "Orange or reddish-brown pustules on leaves",
                "home_remedies": [
                    "Remove infected leaves",
                    "Apply sulfur-based fungicide",
                    "Improve air circulation",
                    "Reduce humidity around plant",
                    "Apply milk spray (1 part milk + 9 parts water)"
                ],
                "prevention": "Keep leaves dry, ensure good air flow"
            },
            "Aloe Vera_Aloe_Sunburn": {
                "name": "Sunburn",
                "symptoms": "Brown or white patches on leaves",
                "home_remedies": [
                    "Move to partial shade",
                    "Gradually acclimate to sunlight",
                    "Trim severely damaged leaves",
                    "Increase watering frequency",
                    "Apply aloe gel to damaged areas"
                ],
                "prevention": "Gradual sun exposure, provide afternoon shade"
            },
            
            # Chrysanthemum Diseases
            "Chrysanthemum_Chrysanthemum_Bacterial_Leaf_Spot": {
                "name": "Bacterial Leaf Spot",
                "symptoms": "Dark spots with yellow halos on leaves",
                "home_remedies": [
                    "Remove infected leaves",
                    "Apply copper-based fungicide",
                    "Improve air circulation",
                    "Water at soil level",
                    "Apply hydrogen peroxide solution (1:10 ratio)"
                ],
                "prevention": "Avoid overhead watering, ensure good drainage"
            },
            "Chrysanthemum_Chrysanthemum_Healthy": {
                "name": "Healthy Chrysanthemum",
                "symptoms": "No disease detected",
                "home_remedies": [
                    "Continue current care routine",
                    "Provide bright, indirect light",
                    "Water when top inch of soil is dry",
                    "Deadhead spent flowers",
                    "Fertilize every 2-3 weeks during growing season"
                ],
                "prevention": "Regular monitoring, proper spacing, good hygiene"
            },
            "Chrysanthemum_Chrysanthemum_Septoria_Leaf_Spot": {
                "name": "Septoria Leaf Spot",
                "symptoms": "Small, dark spots with yellow margins",
                "home_remedies": [
                    "Remove infected leaves",
                    "Apply baking soda spray (1 tsp + 1 quart water)",
                    "Improve air circulation",
                    "Water early in the day",
                    "Apply neem oil treatment"
                ],
                "prevention": "Avoid wetting foliage, ensure proper spacing"
            },
            
            # Hibiscus Diseases
            "Hibiscus_Hibiscus_Blight": {
                "name": "Blight Disease",
                "symptoms": "Rapid wilting and browning of leaves",
                "home_remedies": [
                    "Remove infected plant parts",
                    "Apply copper fungicide",
                    "Improve soil drainage",
                    "Reduce watering frequency",
                    "Apply cinnamon powder to cuts"
                ],
                "prevention": "Good drainage, avoid overwatering, proper spacing"
            },
            "Hibiscus_Hibiscus_Healthy": {
                "name": "Healthy Hibiscus",
                "symptoms": "No disease detected",
                "home_remedies": [
                    "Continue current care routine",
                    "Provide full sun (6+ hours daily)",
                    "Water deeply but infrequently",
                    "Fertilize monthly with balanced fertilizer",
                    "Prune to maintain shape"
                ],
                "prevention": "Consistent care, regular monitoring"
            },
            "Hibiscus_Hibiscus_Necrosis": {
                "name": "Necrosis",
                "symptoms": "Dead tissue areas on leaves and stems",
                "home_remedies": [
                    "Prune affected areas",
                    "Apply fungicide treatment",
                    "Improve air circulation",
                    "Check for pest damage",
                    "Apply honey to cuts for healing"
                ],
                "prevention": "Regular inspection, proper nutrition"
            },
            "Hibiscus_Hibiscus_Scorch": {
                "name": "Leaf Scorch",
                "symptoms": "Brown, crispy leaf edges",
                "home_remedies": [
                    "Increase watering frequency",
                    "Provide afternoon shade",
                    "Apply mulch to retain moisture",
                    "Mist leaves in early morning",
                    "Check soil pH and adjust if needed"
                ],
                "prevention": "Consistent moisture, protection from hot sun"
            },
            
            # Money Plant Diseases
            "Money Plant_Money_Plant_Bacterial_Wilt": {
                "name": "Bacterial Wilt",
                "symptoms": "Wilting and yellowing of leaves",
                "home_remedies": [
                    "Remove infected parts",
                    "Improve drainage",
                    "Apply copper fungicide",
                    "Reduce watering",
                    "Apply cinnamon to soil surface"
                ],
                "prevention": "Good drainage, avoid overwatering"
            },
            "Money Plant_Money_Plant_Chlorosis": {
                "name": "Chlorosis",
                "symptoms": "Yellowing leaves with green veins",
                "home_remedies": [
                    "Apply iron chelate",
                    "Check soil pH (should be 6.0-7.0)",
                    "Add compost to soil",
                    "Apply Epsom salt solution",
                    "Ensure proper drainage"
                ],
                "prevention": "Regular soil testing, balanced fertilization"
            },
            "Money Plant_Money_Plant_Healthy": {
                "name": "Healthy Money Plant",
                "symptoms": "No disease detected",
                "home_remedies": [
                    "Continue current care routine",
                    "Provide bright, indirect light",
                    "Water when soil is dry to touch",
                    "Wipe leaves monthly",
                    "Fertilize monthly during growing season"
                ],
                "prevention": "Consistent care, regular monitoring"
            },
            "Money Plant_Money_Plant_Manganese_Toxicity": {
                "name": "Manganese Toxicity",
                "symptoms": "Dark spots and leaf distortion",
                "home_remedies": [
                    "Flush soil with clean water",
                    "Check soil pH and adjust",
                    "Reduce fertilizer application",
                    "Repot with fresh soil",
                    "Apply chelated iron if needed"
                ],
                "prevention": "Regular soil testing, balanced fertilization"
            },
            
            # Rose Diseases
            "Rose_Rose_Black_Spot": {
                "name": "Black Spot",
                "symptoms": "Black spots with yellow halos on leaves",
                "home_remedies": [
                    "Remove infected leaves",
                    "Apply baking soda spray (1 tsp + 1 quart water)",
                    "Improve air circulation",
                    "Water at soil level only",
                    "Apply neem oil treatment"
                ],
                "prevention": "Morning watering, good air circulation, resistant varieties"
            },
            "Rose_Rose_Downy_Mildew": {
                "name": "Downy Mildew",
                "symptoms": "Yellow patches on upper leaves, white growth underneath",
                "home_remedies": [
                    "Remove infected leaves",
                    "Improve air circulation",
                    "Apply copper fungicide",
                    "Water early in the day",
                    "Apply milk spray (1:10 ratio)"
                ],
                "prevention": "Good air flow, avoid overhead watering"
            },
            "Rose_Rose_Healthy": {
                "name": "Healthy Rose",
                "symptoms": "No disease detected",
                "home_remedies": [
                    "Continue current care routine",
                    "Provide full sun (6+ hours daily)",
                    "Water deeply 2-3 times per week",
                    "Fertilize monthly during growing season",
                    "Prune in late winter"
                ],
                "prevention": "Regular care, disease-resistant varieties"
            },
            "Rose_Rose_Insect_Damage": {
                "name": "Insect Damage",
                "symptoms": "Holes, chewed edges, or distorted leaves",
                "home_remedies": [
                    "Hand-pick visible insects",
                    "Apply insecticidal soap",
                    "Use neem oil spray",
                    "Introduce beneficial insects",
                    "Apply diatomaceous earth"
                ],
                "prevention": "Regular inspection, companion planting"
            },
            "Rose_Rose_Mosaic_Virus": {
                "name": "Mosaic Virus",
                "symptoms": "Yellow mottling or patterns on leaves",
                "home_remedies": [
                    "Remove infected plants",
                    "Disinfect tools between plants",
                    "Control aphid populations",
                    "Improve plant nutrition",
                    "Apply seaweed extract"
                ],
                "prevention": "Virus-free plants, aphid control"
            },
            "Rose_Rose_Powdery_Mildew": {
                "name": "Powdery Mildew",
                "symptoms": "White powdery coating on leaves",
                "home_remedies": [
                    "Remove infected leaves",
                    "Apply baking soda spray",
                    "Improve air circulation",
                    "Apply milk spray (1:10 ratio)",
                    "Use sulfur-based fungicide"
                ],
                "prevention": "Good air flow, morning sun, resistant varieties"
            },
            "Rose_Rose_Rust": {
                "name": "Rose Rust",
                "symptoms": "Orange or reddish pustules on leaves",
                "home_remedies": [
                    "Remove infected leaves",
                    "Apply copper fungicide",
                    "Improve air circulation",
                    "Water at soil level",
                    "Apply sulfur treatment"
                ],
                "prevention": "Good air flow, avoid wetting foliage"
            },
            "Rose_Rose_Yellow_Mosaic_Virus": {
                "name": "Yellow Mosaic Virus",
                "symptoms": "Yellow patterns or streaks on leaves",
                "home_remedies": [
                    "Remove infected plants",
                    "Control aphid populations",
                    "Disinfect all tools",
                    "Improve plant nutrition",
                    "Apply antiviral treatments"
                ],
                "prevention": "Virus-free plants, aphid control"
            },
            
            # Turmeric Diseases
            "Turmeric_Turmeric_Aphid_Infestation": {
                "name": "Aphid Infestation",
                "symptoms": "Small insects on leaves, sticky residue",
                "home_remedies": [
                    "Spray with water to dislodge aphids",
                    "Apply insecticidal soap",
                    "Use neem oil spray",
                    "Introduce ladybugs",
                    "Apply garlic spray"
                ],
                "prevention": "Regular inspection, beneficial insects"
            },
            "Turmeric_Turmeric_Blotch": {
                "name": "Leaf Blotch",
                "symptoms": "Irregular brown or black spots on leaves",
                "home_remedies": [
                    "Remove infected leaves",
                    "Apply copper fungicide",
                    "Improve air circulation",
                    "Water at soil level",
                    "Apply baking soda solution"
                ],
                "prevention": "Good air flow, avoid overhead watering"
            },
            "Turmeric_Turmeric_Healthy": {
                "name": "Healthy Turmeric",
                "symptoms": "No disease detected",
                "home_remedies": [
                    "Continue current care routine",
                    "Provide partial shade",
                    "Keep soil consistently moist",
                    "Fertilize monthly with organic matter",
                    "Mulch around plants"
                ],
                "prevention": "Consistent moisture, good drainage"
            },
            "Turmeric_Turmeric_Leaf_Necrosis": {
                "name": "Leaf Necrosis",
                "symptoms": "Dead tissue areas on leaves",
                "home_remedies": [
                    "Remove affected leaves",
                    "Check for nutrient deficiencies",
                    "Improve soil drainage",
                    "Apply balanced fertilizer",
                    "Check for pest damage"
                ],
                "prevention": "Regular feeding, proper drainage"
            },
            "Turmeric_Turmeric_Leaf_Spot": {
                "name": "Leaf Spot",
                "symptoms": "Small, dark spots on leaves",
                "home_remedies": [
                    "Remove infected leaves",
                    "Apply copper fungicide",
                    "Improve air circulation",
                    "Water early in the day",
                    "Apply neem oil treatment"
                ],
                "prevention": "Good air flow, avoid wetting foliage"
            }
        }
        return treatments

    @torch.no_grad()
    def predict(self, image_path):
        """
        Predict plant disease from image with treatment recommendations
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Prediction results with plant, disease, confidence, and treatments
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # Predict
            output = self.model(image_tensor)
            probabilities = torch.softmax(output, dim=1)[0]  # shape: [num_classes]

            # Aggregate probabilities by plant, then pick top disease within best plant
            plant_to_indices = {}
            for idx, cname in enumerate(self.classes):
                if '_' in cname:
                    plant_name = cname.split('_', 1)[0]
                else:
                    plant_name = cname
                if plant_name not in plant_to_indices:
                    plant_to_indices[plant_name] = []
                plant_to_indices[plant_name].append(idx)

            plant_scores = {}
            for plant_name, idxs in plant_to_indices.items():
                plant_scores[plant_name] = float(probabilities[idxs].sum().item())

            best_plant = max(plant_scores.items(), key=lambda x: x[1])[0]

            plant_idxs = plant_to_indices[best_plant]
            plant_subprobs = probabilities[plant_idxs]
            submax_idx = int(torch.argmax(plant_subprobs).item())
            predicted_class = plant_idxs[submax_idx]
            confidence = float(plant_subprobs[submax_idx].item())

            # Get prediction details
            class_name = self.classes[predicted_class]
            if '_' in class_name:
                plant, disease = class_name.split('_', 1)
            else:
                plant, disease = class_name, "Unknown"

            # Get treatment information
            # Use the full class name as the treatment key since our database uses model class names
            treatment_key = class_name

            treatment_info = self.treatments.get(treatment_key, {
                "name": disease,
                "symptoms": "Unknown symptoms",
                "home_remedies": ["Consult a plant expert for specific treatment"],
                "prevention": "General plant care practices"
            })
            
            
            return {
                'plant': plant,
                'disease': disease,
                'confidence': confidence * 100,
                'class_name': class_name,
                'output_format': f"Plant is {plant} and have this {disease} disease",
                'treatment': treatment_info
            }
            
        except Exception as e:
            return {
                'error': f"Failed to process image: {str(e)}",
                'plant': None,
                'disease': None,
                'confidence': 0,
                'output_format': "Error processing image",
                'treatment': None
            }

    def list_classes(self):
        """List all available plant and disease classes"""
        print(f"\n🌱 Available Plant Disease Classes ({self.num_classes}):")
        print("=" * 60)
        
        plants = {}
        for i, class_name in enumerate(self.classes):
            if '_' in class_name:
                plant, disease = class_name.split('_', 1)
                if plant not in plants:
                    plants[plant] = []
                plants[plant].append(disease)
        
        for plant, diseases in plants.items():
            print(f"\n🌿 {plant}:")
            for disease in diseases:
                print(f"   • {disease}")

def main():
    """Command line interface for Smart Plant Doctor"""
    parser = argparse.ArgumentParser(description='Smart Plant Doctor - Disease Prediction with Treatment')
    parser.add_argument('image_path', nargs='?', help='Path to the plant image')
    parser.add_argument('--model', default='exports/smart_plant_doctor_model.pth', 
                       help='Path to model file')
    parser.add_argument('--device', choices=['cpu', 'cuda'], 
                       help='Device to use (auto-detect if not specified)')
    parser.add_argument('--list-classes', action='store_true',
                       help='List all available plant disease classes')
    
    args = parser.parse_args()
    
    try:
        # Initialize model
        doctor = SmartPlantDoctor(model_path=args.model, device=args.device)
        
        if args.list_classes:
            doctor.list_classes()
            return
        
        # Check if image path is provided
        if not args.image_path:
            print("❌ Error: Please provide an image path or use --list-classes")
            parser.print_help()
            sys.exit(1)
        
        # Check if image exists
        if not os.path.exists(args.image_path):
            print(f"❌ Error: Image file not found: {args.image_path}")
            sys.exit(1)
        
        print(f"\n🔍 Analyzing image: {args.image_path}")
        print("=" * 60)
        
        # Make prediction
        result = doctor.predict(args.image_path)
        
        if 'error' in result:
            print(f"❌ {result['error']}")
            sys.exit(1)
        
        # Display results - SIMPLIFIED OUTPUT (Top 1 only)
        print(f"🎯 {result['output_format']}")
        print(f"📊 Confidence: {result['confidence']:.2f}%")
        print(f"🏷️ Class: {result['class_name']}")
        
        # Display treatment information
        if result['treatment']:
            treatment = result['treatment']
            print(f"\n🩺 TREATMENT RECOMMENDATIONS:")
            print("=" * 50)
            print(f"📋 Disease: {treatment['name']}")
            print(f"🔍 Symptoms: {treatment['symptoms']}")
            
            print(f"\n💊 HOME REMEDIES:")
            for i, remedy in enumerate(treatment['home_remedies'], 1):
                print(f"   {i}. {remedy}")
            
            print(f"\n🛡️ PREVENTION:")
            print(f"   • {treatment['prevention']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()