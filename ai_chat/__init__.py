import json
from ai_chat import FunctionCalling
from openai import OpenAI
from datetime import datetime
import os
import logging
import redis
import asyncio
import json
from config import (redis_host, redis_port, redis_db, redis_password, openai_base_url, openai_api_key)

redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, password=redis_password)
client = OpenAI(base_url=openai_base_url, api_key=openai_api_key)

async def send_to_ai(messages):
    response = await asyncio.to_thread(client.chat.completions.create, model="deepseek-chat", messages=messages)
    return response.choices[0].message

def save_conversation(id, messages):
    filtered_messages = [msg for msg in messages if msg.get("role") != "system"]
    redis_client.set(f'conversation:{id}', json.dumps(filtered_messages))
def load_conversation(id):
    messages = redis_client.get(f'conversation:{id}')
    if messages:
        messages = json.loads(messages)
        messages = [msg for msg in messages if msg.get("role") != "system"]
        return messages
    return []

async def send_message(new_message, sender_id, sender_name, type=None, group_id=False, timenow=datetime.now()):
    id = group_id if group_id else sender_id
    messages = [
        {"role": "system", "content": f"""
            角色设定： 你是聪明、可爱并且喜欢与用户互动的猫娘助手，名字为{bot_name}
            特别设定：
            QQ将传入一些数据，它们是json格式，请理解并正确处理它们。
            请参考之前的对话，以便更好地回答当前问题。
            请你直接回复内容，不要以任何格式
            你需要保持可爱、友善但逻辑清晰，务必提供准确、可靠的回答。
        """}
    ]
    
    messages.extend(load_conversation(id))

    new_message_dict = {
        "sender_id": sender_id,
        "sender_name": sender_name,
        "content": new_message,
        "type": type,
        "group_id": group_id if group_id else None,
        "timestamp": timenow.isoformat()
    }
    messages.append({"role": "user", "content": json.dumps(new_message_dict)})

    message = await send_to_ai(messages)
    messages.append({"role": "assistant", "content": message.content})

    save_conversation(id, messages)
    return message.content


async def add_RoleMessage(content, sender_id, sender_name, group_id, max_length=None):
    # 使用群号作为 ID
    record_id = group_id

    # 检查隐私开关
    privacy_switch = redis_client.get(f"privacy_switch:{record_id}")
    if privacy_switch and privacy_switch.decode("utf-8") == "开":
        return
    
    # 构建 JSON 消息
    new_message = {
        "sender_id": sender_id,
        "sender_name": sender_name,
        "content": content,
        "type": "group",
        "group_id": group_id,
        "timestamp": datetime.now().isoformat()
    }

    # 加载现有对话消息
    messages = load_conversation(record_id)
    messages.append({"role": "user", "content": json.dumps(new_message)})

    # 计算用户消息数量
    user_messages_count = sum(1 for msg in messages if msg.get("role") == "user")
    if messages and messages[-1].get("role") == "assistant":
        user_messages_count -= 1

    # 从 Redis 获取最大上下文数量
    if max_length is None:
        max_length = redis_client.get(f"max_context_count:{record_id}")
        max_length = int(max_length) if max_length else 5  # 默认值为 5

    # 根据指定的最大长度修剪消息
    while user_messages_count > max_length:
        messages.pop(0)
        user_messages_count -= 1

    save_conversation(record_id, messages)

