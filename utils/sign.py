from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

message = 'To be signed'
key = RSA.importKey(open('.mysensorsPrivKey.pem').read())
h = SHA256.new(message)
signer = PKCS1_v1_5.new(key)
signature = signer.sign(h)
print 'hello'