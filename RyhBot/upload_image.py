improt requests

def upload_image(image_path, image_filename, yh_token):
    upload_url = f"https://chat-go.jwzhd.com/open-apis/v1/image/upload?token={yh_token}"
    with open(image_path, "rb") as image_file:
        response = requests.post(upload_url, files={'image': (image_filename, image_file)})
        if response.status_code == 200 and response.json()['msg'] == "success":
            return response.json()['data']['imageKey']
        else:
            print(f"上传图片失败: {response.status_code if response.status_code != 200 else response.json()['msg']}")
            return None
