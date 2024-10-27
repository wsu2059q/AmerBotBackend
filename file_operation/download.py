import os

def download_image(image_url, temp_folder="Temp"):
    # 下载图片
    image_data = requests.get(image_url).content
    
    # 创建Temp文件夹（如果不存在）
    os.makedirs(temp_folder, exist_ok=True)
    
    # 保存图片到Temp文件夹
    image_filename = os.path.basename(image_url)
    if not image_filename.lower().endswith('.png'):
        image_filename += '.png'
    
    image_path = os.path.join(temp_folder, image_filename)
    with open(image_path, "wb") as image_file:
        image_file.write(image_data)
    
    return image_path, image_filename