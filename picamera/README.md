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


## Service 

```
sudo nano /etc/systemd/system/stream-server.service
```

```
[Unit]
Description=Stream Server Python Script
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=lemlijnc
WorkingDirectory=/home/lemlijnc
ExecStart=/usr/bin/python3 /home/lemlijnc/stream_server.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl daemon-reload
sudo systemctl enable stream-server.service
sudo systemctl start stream-server.service
sudo systemctl status stream-server.service
journalctl -u stream-server.service -f
```




