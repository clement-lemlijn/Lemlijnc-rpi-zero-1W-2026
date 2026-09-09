```
# 1. Nettoyer les verrous éventuels
sudo rm -f /var/lib/dpkg/lock*
sudo rm -f /var/lib/apt/lists/lock
sudo rm -f /var/cache/apt/archives/lock
# 2. Forcer la configuration
sudo dpkg --configure -a

# 3. Réparer les paquets cassés
sudo apt --fix-broken install -y

# 4. Mettre à jour
sudo apt update
```

```
sudo dpkg --configure -a
```

```
sudo apt update
sudo apt install -y python3-picamera2
```
