
import os
import hashlib
from PIL import Image
from collections import defaultdict

def calculate_image_hash(image_path):
    """
    Calculate a hash for an image file.
    """
    with open(image_path, 'rb') as f:
        image_data = f.read()
        return hashlib.md5(image_data).hexdigest()

def find_duplicate_images_with_size(root_dir):
    """
    Find duplicate images with the exact same size in the given directory and its subdirectories.
    """
    image_hashes = defaultdict(list)
    image_sizes = defaultdict(list)

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                image_path = os.path.join(root, file)
                with Image.open(image_path) as img:
                    image_size = img.size
                image_hash = calculate_image_hash(image_path)
                image_hashes[image_hash].append(image_path)
                image_sizes[image_hash].append(image_size)

    duplicate_images = {hash: paths for hash, paths in image_hashes.items() if len(paths) > 1 and len(set(image_sizes[hash])) == 1}
    return duplicate_images

def generate_html_for_duplicates(duplicate_images):
    """
    Generate an HTML file to display duplicate images for comparison.
    """
    html_content = "<html><head><style>table {border-collapse: collapse;} table, th, td {border: 1px solid black; padding: 10px;} img {max-width: 200px;}</style></head><body>"

    for image_hashes, image_paths in duplicate_images.items():
        html_content += f"<h3>Duplicate Images (Hash: {image_hashes})</h3>"
        html_content += "<table><tr><th>Image</th><th>Location</th></tr>"
        for image_path in image_paths:
            html_content += f"<tr><td><img src='{image_path}'></td><td>{image_path}</td></tr>"
        html_content += "</table><br>"

    html_content += "</body></html>"

    with open("duplicate_images.html", "w") as html_file:
        html_file.write(html_content)

if __name__ == "__main__":
    project_location = input("Enter the project location: ")

    if os.path.isdir(project_location):
        duplicate_images = find_duplicate_images_with_size(project_location)

        if duplicate_images:
            generate_html_for_duplicates(duplicate_images)
            print("Duplicate images found. Open 'duplicate_images.html' in your web browser to compare.")
        else:
            print("No duplicate images with the exact same size found in the specified directory.")
    else:
        print("Invalid directory. Please provide a valid project location.")
