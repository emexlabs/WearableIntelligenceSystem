1. Do not change the AES key, just retain the default during initial setup. You can change it later if needed in key.py and <another place>
2. In Android Studio, Preferences->Build,Execution,Deployment->Build Tools->Gradle->set Gradle JDK to Java 11
3. Make sure to change IP address to that of your own GL Box in AudioService.java and GlboxClientSocket.java
4. Make sure to enable Developer Mode and USB debugging on the Blade. Instructions to do this can be found in official Vuzix Developer documentation

