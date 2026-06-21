from itsdangerous import URLSafeTimedSerializer
secret_key='kaleem4352'
def endata(data):
    serilizer=URLSafeTimedSerializer(secret_key)
    return serilizer.dumps(data,salt='aqthar@4352')
def dndata(data):
    serilizer=URLSafeTimedSerializer(secret_key)
    return serilizer.loads(data,salt='aqthar@4352',max_age=60)