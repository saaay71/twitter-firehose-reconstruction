from datetime import datetime

def decodeSnowflake(snowflake):
    """ Returns unix timestamp """
    snowflake = int(snowflake)
    timestamp = (int(bin(snowflake)[2:-22], 2) + 1288834974657) / 1000
    datacenterID = int(bin(snowflake)[-22:-17], 2)
    serverID = int(bin(snowflake)[-17:-12], 2)
    sequenceNumber = int(bin(snowflake)[-12:], 2)
    return timestamp, datacenterID, serverID, sequenceNumber

def getSnowflake(timestamp, datacenterID, serverID, sequenceNumber):
    """ Expects twitter timestamp """
    return timestamp * 2**22 + datacenterID * 2**17 + serverID * 2**12 + sequenceNumber

def decodeTimestamp(timestamp: int):
    time = datetime.utcfromtimestamp(timestamp)
    return daysSinceEpoch(timestamp), time.hour, time.minute, time.second*1000 + time.microsecond // 1000

def daysSinceEpoch(timestamp: int) -> int:
    return int(timestamp // 86400)
