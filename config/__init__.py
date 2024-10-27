import json

# 初始化字典
config = {}
# 读取配置
with open('config/config.json', 'r') as f:
    config = json.load(f)
# 全局变量
server_host = config['server']['host']
server_port = config['server']['port']

bot_name = config['qq']['bot_name']
bot_qq = config['qq']['bot_qq']

yh_token = config['yh']['token']
yh_webhook_path = config['yh']['webhook']['path']

weather_api_url = config['WeatherApi']['url']
weather_api_token = config['WeatherApi']['token']

openai_base_url = config['OpenAI']['base_url']
openai_api_key = config['OpenAI']['api_key']

redis_host = config['Redis']['host']
redis_port = config['Redis']['port']
redis_db = config['Redis']['db']
redis_password = config['Redis']['password']

sqlite_db_path = config['SQLite']['db_path']

message_yh = config['Message']['message-YH']
message_yh_followed = config['Message']['message-YH-followed']
ban_ai_id = config['Ban']['ban_ai_id']

# 验证
# print("Server Host:", server_host)
# print("Server Port:", server_port)
# print("Bot Name:", bot_name)
# print("Bot QQ:", bot_qq)
# print("YH Token:", yh_token)
# print("YH Webhook Path:", yh_webhook_path)
# print("Weather API URL:", weather_api_url)
# print("Weather API Token:", weather_api_token)
# print("OpenAI Base URL:", openai_base_url)
# print("OpenAI API Key:", openai_api_key)
# print("Redis Host:", redis_host)
# print("Redis Port:", redis_port)
# print("Redis DB:", redis_db)
# print("Redis Password:", redis_password)
# print("SQLite DB Path:", sqlite_db_path)
# print("Message YH:", message_yh)