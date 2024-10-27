import logging
from typing import Dict, Any
import RyhBot.bind as bind
import RyhBot.send as yhBot
from config import(message_yh, message_yh_followed, bot_qq)

logging.basicConfig(level=logging.INFO)
qqBot = None
class MessageData:
    def __init__(self, data: Dict[str, Any]):
        self.version = data.get("version", "")
        self.header_event_id = data.get("header", {}).get("eventId", "")
        self.header_event_type = data.get("header", {}).get("eventType", "")
        self.header_event_time = data.get("header", {}).get("eventTime", "")

        event_info = data.get("event", {})
        sender_info = event_info.get("sender", {})
        self.userid = event_info.get("userId", "")
        self.sender_id = sender_info.get("senderId", "")
        self.sender_type = sender_info.get("senderType", "")
        self.sender_user_level = sender_info.get("senderUserLevel", "")
        self.sender_nickname = sender_info.get("senderNickname", "")

        message_info = event_info.get("message", {})
        self.msg_id = message_info.get("msgId", "")
        self.parent_id = message_info.get("parentId", "")
        self.send_time = message_info.get("sendTime", "")
        self.message_chat_id = message_info.get("chatId", "")
        self.message_chat_type = message_info.get("chatType", "")
        self.content_type = message_info.get("contentType", "")
        self.message_content = message_info.get("content", {}).get("text", "")
        self.message_content_base = message_info.get("content", {})
        self.instruction_id = message_info.get("instructionId", "")
        self.instruction_name = message_info.get("instructionName", "")
        self.command_id = message_info.get("commandId", "")
        self.command_name = message_info.get("commandName", "")

async def handler(data: Dict[str, Any],qBot):
    global qqBot
    qqBot = qBot
    message_data = MessageData(data)

    event_handlers = {
        "message.receive.normal": handle_normal_message,
        "message.receive.instruction": handle_instruction_message,
        "bot.followed": handle_bot_followed,
        "bot.unfollowed": handle_bot_unfollowed,
        "group.join": handle_group_join,
        "group.leave": handle_group_leave,
        "button.report.inline": handle_button_event,
    }

    handler = event_handlers.get(message_data.header_event_type)
    if handler:
        await handler(message_data)
    else:
        logging.warning(f"未知事件类型: {message_data.header_event_type}")

async def handle_normal_message(message_data: MessageData):
    global qqBot
    logging.info(f"收到来自 {message_data.sender_nickname} 的普通消息: {message_data.message_content}")
    
    # 获取当前的同步模式
    sync_mode = bind.get_sync_mode(message_data.message_chat_id, "云湖")
    binding_info = bind.get_bind(message_data.message_chat_id, "云湖")
    if binding_info:
        QQ_group_id = binding_info[0]
        if sync_mode == "AllSync" or sync_mode == "YHToQQ":
            await qqBot.send_group_msg(group_id=QQ_group_id, message=f"[{message_data.sender_nickname}]:{message_data.message_content}")
        else:
            logging.info(f"当前同步模式为 {sync_mode}，消息未发送到QQ群。")

async def handle_instruction_message(message_data: MessageData):
    if message_data.message_chat_type == "group":
        if message_data.command_name == "帮助":
            yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "markdown", content=message_yh)
        if message_data.sender_user_level == "owner" or message_data.sender_user_level == "administrator":
            if message_data.command_name == "绑定":
                # 获取QQ群号
                qq_group_id = message_data.message_content
                
                # 获取机器人所在的QQ群列表
                member_info = await qqBot.get_group_list(self_id=bot_qq)
                logging.info(f"获取到用户信息: {member_info}")
                
                # 检查机器人是否在指定的QQ群里
                is_in_group = False
                for group in member_info:
                    if group['group_id'] == int(qq_group_id):
                        is_in_group = True
                        break
                
                if not is_in_group:
                    yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=f"绑定失败, 机器人不在QQ群{qq_group_id}中")
                    return

                # 绑定QQ群
                bind_status = bind.bind_qq_group(qq_group_id, message_data.message_chat_id, message_data.sender_id)

                if bind_status == "Success":
                    await qqBot.send_group_msg(group_id=qq_group_id, message=f"此群已通过Amer和云湖群聊{message_data.message_chat_id}成功绑定,同步模式为双向同步.请测试同步功能是否正常!")
                    yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=f"云湖群已经绑定到了QQ群{qq_group_id},请检查QQ群是否有提醒")
                elif bind_status == "Failed":
                    yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=f"绑定失败,系统错误")
                elif bind_status == "Repeat":
                    yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=f"云湖群{message_data.message_chat_id}已经绑定过了")
                elif bind_status == "NotDigit":
                    yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=f"{qq_group_id} 不是一个有效的QQ群号")

            elif message_data.command_name == "取消绑定":
                if message_data.message_content == "确定":
                    unbind_status = bind.unbind_qq_group(message_data.message_chat_id)
                    if unbind_status == "Success":
                        yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content="QQ群已经取消绑定")
                    elif unbind_status == "Failed":
                        yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content="取消绑定失败,系统错误")
                    elif unbind_status == "NotBind":
                        yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content="该云湖群还未绑定任何QQ群")

            elif message_data.command_name == "同步模式":
                if message_data.message_content == "双向":
                    set_sync_mode = bind.set_sync(message_data.message_chat_id, "AllSync")
                elif message_data.message_content == "停止":
                    set_sync_mode = bind.set_sync(message_data.message_chat_id, "NoSync")
                elif message_data.message_content == "QQ到云湖":
                    set_sync_mode = bind.set_sync(message_data.message_chat_id, "QQToYH")
                elif message_data.message_content == "云湖到QQ":
                    set_sync_mode = bind.set_sync(message_data.message_chat_id, "YHToQQ")
                else:
                    yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=f"同步模式 {message_data.message_content} 设置失败,请检查模式")
                if set_sync_mode == "Success":
                    yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=f"同步模式已设置为 {message_data.message_content}")
                elif set_sync_mode == "Failed":
                    yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=f"同步模式设置失败,系统错误")
                elif set_sync_mode == "NotBind":
                    yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=f"该云湖群还未绑定任何QQ群")
        else:
            yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=f"只有群主和管理员才能使用此指令")
    else:
        if message_data.command_name == "帮助":
            yhBot.send(message_data.sender_id, "user", "markdown", content=message_yh_followed)
    