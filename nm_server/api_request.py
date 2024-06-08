import os, json, base64
import requests
from Crypto import PublicKey
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5, AES

apiHost = 'https://api.tilko.net/'
# apiKey  = 'bcdb5762c50341e9b42cff6e15aa0c2d'
apiKey = '8913ef8fd48e4d5daf1d38aaf9209400'

def aesEncrypt(key, iv, plainText):
    def pad(text):
        text_length     = len(text)
        amount_to_pad   = AES.block_size - (text_length % AES.block_size)

        if amount_to_pad == 0:
            amount_to_pad = AES.block_size
            
        pad     = chr(amount_to_pad)

        result  = None
        try:
            result  = text + str(pad * amount_to_pad).encode('utf-8')
        except Exception as e:
            result  = text + str(pad * amount_to_pad)

        return result
    
    if type(plainText) == str:
        plainText = plainText.encode('utf-8')
    
    plainText   = pad(plainText)
    cipher      = AES.new(key, AES.MODE_CBC, iv)
    
    if(type(plainText) == bytes):
        return base64.b64encode(cipher.encrypt(plainText)).decode('utf-8')
    else:
        return base64.b64encode(cipher.encrypt(plainText.encode('utf-8'))).decode('utf-8')

def rsaEncrypt(publicKey, aesKey):
    rsa             = RSA.importKey(base64.b64decode(publicKey))
    cipher          = PKCS1_v1_5.new(rsa.publickey())
    aesCipherKey	= cipher.encrypt(aesKey)
    return aesCipherKey


def getPublicKey():
    headers = {'Content-Type': 'application/json'}
    response = requests.get(apiHost + "/api/Auth/GetPublicKey?APIkey=" + apiKey, headers=headers)
    return response.json()['PublicKey']


def request_auth(data):
    rsaPublicKey    = getPublicKey()

    aesKey          = os.urandom(16)
    aesIv           = ('\x00' * 16).encode('utf-8')

    aesCipherKey    = base64.b64encode(rsaEncrypt(rsaPublicKey, aesKey))


    url         = apiHost + "api/v1.0/hirasimpleauth/simpleauthrequest";

    name = data["name"]

    birth_date = birth(data["rrn"])
    number = data["phone"].replace('-','')
    id_num = data["rrn"]

    options     = {
        "headers": {
            "Content-Type"          : "application/json",
            "API-KEY"               : apiKey,
            "ENC-KEY"               : aesCipherKey
        },
        
        "json": {
            "PrivateAuthType"       : "0",
            "UserName"              : aesEncrypt(aesKey, aesIv, name),
            "BirthDate"             : aesEncrypt(aesKey, aesIv, birth_date),
            "UserCellphoneNumber"   : aesEncrypt(aesKey, aesIv, number),
            "IdentityNumber"        : aesEncrypt(aesKey, aesIv, id_num),
        },
    }

    res         = requests.post(url, headers=options['headers'], json=options['json'])
    return res.json()

def med_info(reqData,rrn):
    rsaPublicKey    = getPublicKey()

    aesKey          = os.urandom(16)
    aesIv           = ('\x00' * 16).encode('utf-8')

    aesCipherKey    = base64.b64encode(rsaEncrypt(rsaPublicKey, aesKey))
    birth_date = birth(rrn)
    options     = {
        "headers": {
            "Content-Type"          : "application/json",
            "API-KEY"               : apiKey,
            "ENC-KEY"               : aesCipherKey
        },
        
        "json": {
            "IdentityNumber"        : aesEncrypt(aesKey, aesIv, rrn),
            "StartDate"             : "20230630",
            "EndDate"               : "20240518",
            "CxId"                  : reqData["CxId"],
            "PrivateAuthType"       : reqData["PrivateAuthType"],
            "ReqTxId"               : reqData["ReqTxId"],
            "Token"                 : reqData["Token"],
            "TxId"                  : reqData["TxId"],
            "UserName"              : aesEncrypt(aesKey, aesIv, reqData["UserName"]),
            "BirthDate"             : aesEncrypt(aesKey, aesIv, birth_date),
            "UserCellphoneNumber"   : aesEncrypt(aesKey, aesIv, reqData["UserCellphoneNumber"]),
        },
        }

    url = apiHost+"api/v1.0/hirasimpleauth/hiraa050300000100";
    res         = requests.post(url, headers=options['headers'], json=options['json'])
    return res.json()



def birth(rrn):
    if int(rrn[:2]) < 21 and int(rrn[6]) in (3, 4) :
        biryear = 2000 + int(rrn[:2])
    else:
        biryear = 1900 + int(rrn[:2])
    birmonth = int(rrn[2:4])
    birmonth = format(birmonth,'02d')
    birday = int(rrn[4:6])
    return str(biryear) + str(birmonth) + str(birday)


