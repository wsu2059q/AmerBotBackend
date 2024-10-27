import uvicorn
from config import (server_host, server_port, yh_webhook_path)
from aiocqhttp import CQHttp, Event, MessageSegment
from quart import request,jsonify
from RyhBot.handler import handler as YH_handler
from RqqBot.handler import msg_handler as QQ_msg_handler
qqBot = CQHttp(__name__)

# qqBotHander - 接收消息
@qqBot.on_message
async def handle_msg(event: Event):
    if event:
        await QQ_msg_handler(event,qqBot)
    else:
        return {'reply': "我的机体出错了喵,快联系我的机体主人修好我! - 2694611137", 'at_sender': False}
# qqBotHanderForIncrease - 接收通知事件
@qqBot.on_notice('group_increase')
async def handle_group_increase(event: Event):
    info = await qqBot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
    nickname = info['nickname']
    name = nickname if nickname else '新人'
    await qqBot.send(event,
                     message=f'欢迎{name}～',
                     at_sender=True,
                     auto_escape=True)
# yhBotHandlerWebhook - 云湖订阅消息
@qqBot.server_app.route(yh_webhook_path, methods=['POST'])
async def webhook():
    if await request.get_json():
        await YH_handler(await request.get_json(), qqBot)
        return jsonify({"status": "success"}),200
    return jsonify({"status": "error"}),200

# WebServer - 启动!
if __name__ == "__main__":
    uvicorn.run("main:qqBot.asgi", host=server_host, port=server_port, reload=True)