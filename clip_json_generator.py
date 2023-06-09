# -*- coding: utf-8 -*-
"""Clip_Json_Generator.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1sI6jMccCziRlcDp50Bu2QIs9Q0uzn4kH

# Clip Json Generator
"""

#%pip install pillow torch openai-clip

import os
import zipfile
import hashlib
import json
from PIL import Image
import requests
from io import BytesIO
import clip
import torch
import argparse

model_name = "ViT-L/14"

def clip_json_generator(input_directory, output_directory):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load(model_name, device=device)

    def get_file_hash(file):
        hasher = hashlib.md5()
        with open(file, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def get_clip_vector(image_path):
        try:
            image = Image.open(image_path)
            image_input = preprocess(image).unsqueeze(0).to(device)
            with torch.no_grad():
                features = model.encode_image(image_input)
            normalized_features = features / features.norm(dim=-1, keepdim=True)
            clip_vector = normalized_features.cpu().numpy().tolist()
            return clip_vector
        except FileNotFoundError:
            print(f"Image file not found at {image_path}. Skipping...")
            return None

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.endswith('.zip'):
                zip_file_path = os.path.join(root, file)
                image_data = []

                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    for member in zip_ref.infolist():
                        if member.filename.lower().endswith(('.png', '.jpg')):
                            # Extract image from the zip file
                            with zip_ref.open(member) as img_file:
                                img_data = img_file.read()
                                img = Image.open(BytesIO(img_data))
                                img.save(f'extracted_{os.path.basename(member.filename)}')

                            # Calculate file hash
                            file_hash = get_file_hash(f'extracted_{os.path.basename(member.filename)}')

                            # Generate CLIP vector
                            clip_vector = get_clip_vector(f'extracted_{os.path.basename(member.filename)}')

                            # Add the data to the list (if the CLIP vector is not None)
                            if clip_vector is not None:
                                image_data.append({
                                    'zip_file': zip_file_path,
                                    'filename': member.filename,
                                    'file_hash': file_hash,
                                    'clip_model': model_name,
                                    'clip_vector': clip_vector,
                                })
                            else:
                                print(f"Skipping image {member.filename} due to missing file.")

                            # Clean up the extracted image
                            os.remove(f'extracted_{os.path.basename(member.filename)}')

                # Write the image_data list to a separate JSON file for each zip file
                output_json_file = os.path.join(output_directory, f"{os.path.splitext(file)[0]}_clip_vectors.json")
                with open(output_json_file, 'w') as f:
                    json.dump(image_data, f, indent=4)

#Change input_directory and output_directory paths with Correct paths

if __name__ == "__main__":
    input_directory = '/path/to/input/directory'
    output_directory = '/path/to/output/directory'
    clip_json_generator(input_directory, output_directory)

# Also, you can run the script using the command:
#python clip_json_generator.py /path/to/input/directory /path/to/output/directory

