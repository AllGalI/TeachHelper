import redis
import os 
from dotenv import load_dotenv
load_dotenv()

red_client = redis.Redis(
  host=os.getenv("REDIS_HOST"),
  port=int(os.getenv("REDIS_PORT")),
  # username=os.getenv("REDIS_USER"),
  # password=os.getenv("REDIS_PASS"),
  decode_responses=True
)