import redis

def create_redis_connection(app):
    return redis.Redis(host='REDIS_HOST', port='REDIS_PORT', db='REDIS_DB')
