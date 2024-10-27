import re
import os
import requests
import RyhBot.bind as bind
import RyhBot.send as yhBot
import ai_chat
import redis
from config import (ban_ai_id, bot_name, bot_qq, redis_host, redis_port, redis_db, redis_password, yh_token)
from typing import Dict, Any

class MessageData:
    def __init__(self, data: Dict[str, Any]):
        self.self_id = data.get('self_id', "")
        self.user_id = data.get('user_id', "")
        self.time = data.get('time', "")
        self.message_id = data.get('message_id', "")
        self.message_seq = data.get('message_seq', "")
        self.real_id = data.get('real_id', "")
        self.message_type = data.get('message_type', "")
        self.raw_message = data.get('raw_message', "")
        self.font = data.get('font', "")
        self.sub_type = data.get('sub_type', "")
        self.message_format = data.get('message_format', "")
        self.post_type = data.get('post_type', "")
        self.group_id = data.get('group_id', "")
        
        sender_info = data.get('sender', {})
        self.sender_user_id = sender_info.get('user_id', "")
        self.sender_nickname = sender_info.get('nickname', "")
        self.sender_card = sender_info.get('card', "")
        self.sender_role = sender_info.get('role', "")

async def msg_handler(data: Dict[str, Any], qqBot):
    message_data = MessageData(data)

    if message_data.message_type == "private":
        airesp = await ai_chat.send_message(message_data.raw_message, message_data.sender_user_id, message_data.sender_nickname)
        await qqBot.send_private_msg(user_id=message_data.sender_user_id, message=airesp)
    elif message_data.message_type == "group":
        if message_data.raw_message.startswith('/'):
            await handle_command(message_data, qqBot)
            return
        elif (bot_name in message_data.raw_message or bot_qq in message_data.raw_message):
            if message_data.sender_nickname:
                sender_name = message_data.sender_nickname
            else:
                sender_name = "未知用户"
            airesp = await ai_chat.send_message(message_data.raw_message, message_data.sender_user_id, sender_name, type = "qq_group", group_id = message_data.group_id)
            await qqBot.send_group_msg(group_id=message_data.group_id, message=airesp)
            return
        else:
            await ai_chat.add_RoleMessage(message_data.raw_message,message_data.sender_user_id,message_data.sender_nickname,message_data.group_id)
        
        sync_mode = bind.get_sync_mode(message_data.group_id, "QQ")
        if sync_mode == "AllSync" or sync_mode == "QQToYH":
            YH_group_ids = bind.get_bind(message_data.group_id, "QQ")
            if YH_group_ids:
                cq_codes = extract_cq_codes(message_data.raw_message)
                for cq_code in cq_codes:
                    print(cq_code)
                    processed_cq_code = await process_cq_code(cq_code)
                    if processed_cq_code[0]:
                        for YH_group_id in YH_group_ids:
                            yhBot.send(recvId=YH_group_id, recvType="group", contentType="text", content=f"来自 {message_data.sender_nickname}:")
                            yhBot.send(recvId=YH_group_id, recvType="group", contentType=processed_cq_code[1], url=processed_cq_code[0])
                cleaned_message = remove_cq_codes(message_data.raw_message)
                cleaned_message = cleaned_message.strip()
                if cleaned_message:
                    for YH_group_id in YH_group_ids:
                        yhBot.send(recvId=YH_group_id, recvType="group", contentType="text", content=f"[{message_data.sender_nickname}]:{cleaned_message}")

async def handle_command(message_data: MessageData, qqBot):
    command = message_data.raw_message[1:]
    if command == "帮助":
        await qqBot.send_group_msg(group_id=message_data.group_id, message=
"""📌 指令指南 📌

1. 隐私模式 开/关：
    🔒 当隐私模式开启时：
      - Amer除了指定消息外将不会记录或处理任何信息
    🔑 当隐私模式关闭时：
      - Amer 将会记录和处理设置的最大消息历史，无论它们是以何种形式发送的

2.隐私模式 最大上文提示 <数量>
    🔒 你可以通过设置最大上文提示数来设置 Amer 记录的最大消息历史,默认为5""")
    elif command.startswith("隐私模式"):
        parts = command.split()
        if len(parts) > 1:
            if parts[1] in ["开", "关"]:
                switch_status = parts[1]
                redis.Redis(host=redis_host, port=redis_port, db=redis_db, password=redis_password).set(f"privacy_switch:{message_data.group_id}", switch_status)
                await qqBot.send_group_msg(group_id=message_data.group_id, message=f"隐私模式已设置为 {switch_status}")
            elif parts[1] == "最大上文提示":
                if len(parts) > 2:
                    try:
                        max_context_count = int(parts[2])
                        redis.Redis(host=redis_host, port=redis_port, db=redis_db, password=redis_password).set(f"max_context_count:{message_data.group_id}", max_context_count)
                        await qqBot.send_group_msg(group_id=message_data.group_id, message=f"最大上文提示数已设置为 {max_context_count}")
                    except ValueError:
                        await qqBot.send_group_msg(group_id=message_data.group_id, message="无效的数量，请输入一个整数")
                else:
                    await qqBot.send_group_msg(group_id=message_data.group_id, message="缺少数量参数，请输入一个整数")
            else:
                await qqBot.send_group_msg(group_id=message_data.group_id, message="无效的子指令，请使用 '开'、'关' 或 '最大上文提示'")
        else:
            await qqBot.send_group_msg(group_id=message_data.group_id, message="缺少子指令，请使用 '开'、'关' 或 '最大上文提示'")
    else:
        await qqBot.send_group_msg(group_id=message_data.group_id, message=f"未知指令: {command}")

# 定义CQ码的正则表达式
cq_code_pattern = re.compile(r'\[CQ:(.*?)\]')

# 获取CQ码的函数
def extract_cq_codes(raw_message):
    return cq_code_pattern.findall(raw_message)

# 处理CQ码的函数
async def process_cq_code(cq_code):
    if cq_code.startswith("image"):
        # 提取图片的URL
        image_url_match = re.search(r'url=(.*?)(?:,|$)', cq_code)
        if image_url_match:
            image_url = image_url_match.group(1)
            # 替换URL中的&amp;为&
            image_url = image_url.replace("&amp;", "&")
            
            # 提取图片的原始文件名
            image_filename_match = re.search(r'file=(.*?)(?:,|$)', cq_code)
            if image_filename_match:
                image_filename = image_filename_match.group(1)
                # 添加.png后缀
                if not image_filename.lower().endswith('.png'):
                    image_filename += '.png'
            else:
                image_filename = os.path.basename(image_url)
                # 添加.png后缀
                if not image_filename.lower().endswith('.png'):
                    image_filename += '.png'
            
            # 下载图片
            image_data = requests.get(image_url).content
            
            # 创建Temp文件夹（如果不存在）
            temp_folder = "Temp"
            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)
            
            # 保存图片到Temp文件夹，以原始文件名命名并添加.png后缀
            image_path = os.path.join(temp_folder, image_filename)
            with open(image_path, "wb") as image_file:
                image_file.write(image_data)
            
            # 上传图片到云湖，指定文件名为原始文件名并添加.png后缀
            upload_url = f"https://chat-go.jwzhd.com/open-apis/v1/image/upload?token={yh_token}"
            with open(image_path, "rb") as image_file:
                files = {'image': (image_filename, image_file)}
                response = requests.post(upload_url, files=files)
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data['msg'] == "success":
                        image_key = response_data['data']['imageKey']
                        return image_key, "image"
                    else:
                        print(f"上传图片失败: {response_data['msg']}")
                        return None, None
                else:
                    print(f"上传图片失败: {response.status_code}")
                    return None, None
    return None, None

# 删除CQ码的函数
def remove_cq_codes(raw_message):
    return cq_code_pattern.sub('', raw_message)