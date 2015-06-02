/*
Kasun De Zoysa @ UCSC
Compile:
javac -cp ../BC/bcprov-jdk16-146.jar RSAEncryption.java 
Execute:
java -cp ../BC/bcprov-jdk16-146.jar:. RSAEncryption
*/

import java.security.Security;
import java.security.Key;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.SecureRandom;

import javax.crypto.Cipher;
import java.util.Formatter;
import java.util.Base64;
import java.math.BigInteger;
import java.security.KeyFactory;

import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.RSAPrivateKeySpec;
import java.security.spec.RSAPublicKeySpec;


//import org.bouncycastle.jce.provider.BouncyCastleProvider;

public class RSAEncryption {

  public static void main(String[]    args) throws Exception    {

  //Security.addProvider(new BouncyCastleProvider());

  String        input = "Hello Kasun ..";
  Cipher cipher = Cipher.getInstance("RSA/None/OAEPWithSHA1AndMGF1Padding");

/*
  // create the keys
  KeyPairGenerator generator = KeyPairGenerator.getInstance("RSA");
  generator.initialize(1024,new SecureRandom());


  KeyPair          pair = generator.generateKeyPair();
  Key              pubKey = pair.getPublic();
  Key              privKey = pair.getPrivate();

*/
String pubStr=new String("MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCyFwg3JilTgwvXQvdqidarrN7X"
+"llgLU132sMA6QXTalFonXNLB2tmJf9LRALpdEaXB368REEKCsxKGm9zt0ayhmGjg"
+"x5DI8s1bCRb7J5FCySoWJ9uYss06/2dFvfsc0oQ3FAVAJej/gCLbBamGwaO0md1Y"
+"2gQk75c0Mv8oS+OeiQIDAQAB");

byte[] decoded1 = Base64.getDecoder().decode(pubStr);

String privkeyS= new String("MIICXAIBAAKBgQCyFwg3JilTgwvXQvdqidarrN7XllgLU132sMA6QXTalFonXNLB"
+"2tmJf9LRALpdEaXB368REEKCsxKGm9zt0ayhmGjgx5DI8s1bCRb7J5FCySoWJ9uY"
+"ss06/2dFvfsc0oQ3FAVAJej/gCLbBamGwaO0md1Y2gQk75c0Mv8oS+OeiQIDAQAB"
+"AoGBAKTL5WFLIfDSklF2+YaP2KNyS5/J0t1gHtJZyvfdfGmL4EUOg0S55JV1QDsB"
+"ZnMbEnzuJY0vs6xIUvtXHcDARvKSUP/s2Rt3b1Ex6wjCrm3vAT57sOiWQs8z8WM6"
+"LJ2NckF1vCt+i6HoK4jQaWOx7NH6t0LehsFCKLfrDiIVaSNRAkEAyeOx97UghedC"
+"SmSv+dm26Cy4uzGv/YAILy4Jvlq/Uk/r/v1kHumof8S6Ca6WqlUv3Ood/b4EGYAg"
+"lhzPMi0J7QJBAOHSYGRAyCESnsHT41YKyaBDkkM51BP7vhiHC24lBkr+6UmhJ5Kc"
+"nEcfgHuThA7666ew0XKFBJZ5tf1mRFVo440CQBCTjng9Ofdkno/HJp/IHXmAuoY8"
+"NSwGSCW/jPNBNjZG86STH5ZeLwSWnYPP/vTrW6uy2VWNNX72gzZwFR8UjZ0CQG0S"
+"93oVDFVlMAeBN/JsXX0qhjAwc25/jw8701qNSZ/ZxobI71tSh+2WmrGVzBiMPF0P"
+"++qrs06XVT8jMWhrtFUCQCq6F8Ex5IF8EFqSOaa9FjBGYRer5564qmGlDba2qHVf"
+"TPaKn5GfJtjNK3DK7iKn4DZ2Ltn3dc2D2CShVoi/nCU=");
byte[] decoded2 = Base64.getDecoder().decode(privkeyS);

String exponentBase64 = "65537";

RSAPublicKeySpec publicKeySpec = new RSAPublicKeySpec(new BigInteger(1024,decoded1),new BigInteger(1024,exponentBase64.getBytes()));
RSAPrivateKeySpec privKeySpec = new RSAPrivateKeySpec(new BigInteger(1024,decoded2), new BigInteger(1024,exponentBase64.getBytes()));

KeyFactory publicKeyFactory = KeyFactory.getInstance("RSA");
KeyFactory privateKeyFactory = KeyFactory.getInstance("RSA");

Key pubKey = publicKeyFactory.generatePublic(publicKeySpec);
Key privKey = privateKeyFactory.generatePrivate(privKeySpec);

 
  // encryption step
  cipher.init(Cipher.ENCRYPT_MODE,pubKey);
  byte[] cipherText = cipher.doFinal(input.getBytes());
  System.out.println("Cipher : " +byteArray2Hex(cipherText));
  
  //decryption step
  cipher.init(Cipher.DECRYPT_MODE,privKey);
  byte[] plainText = cipher.doFinal(cipherText);
  System.out.println("Plain : " +new String(plainText));

 }

 private static String byteArray2Hex(byte[] hash) {
     Formatter formatter = new Formatter();
     for (byte b : hash) formatter.format("%02x", b);
     return formatter.toString();
  }

}

