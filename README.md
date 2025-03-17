# RGB Controler by Temp for Asus Aura with liquidctl in Linux

## Running the project

- Install `requirements.txt`

    > pip install -r requirements.txt

- Install sensors

    > sudo apt-get install lm-sensors

- Download openRGB.AppImage from official site and copy it in this dir. Change name to <openRGB.AppImage>

- Add execute permissions to the AppImage file

    > chmod +x openRGB.AppImage

- Download openrgb-udev.rules from official site and copy it in this dir.

- Add execute permissions to the udev install file.

    > chmod +x openrgb-udev-install.sh

- Run the udev rules install script

    > sudo ./openrgb-udev-install.sh

- Change parameters u see fit

## Creating the service

- Make the script executable

    > chmod +x rgb_controller.py

- Create a service file in /etc/systemd/system/

    > sudo nano /etc/systemd/system/rgb_controller.service

- Add the following content to the service file:

    ```
    [Unit]
    Description=RGB Controller Service
    After=network.target
    
    [Service]
    ExecStart=/usr/bin/python3 /path/to/rgb_controller.py
    WorkingDirectory=/path/to/directory
    Restart=always
    User=YOUR_USERNAME
    Group=YOUR_GROUP
    Environment=DISPLAY=:0
    
    [Install]
    WantedBy=multi-user.target
    ```

- Enable and start the service

    > sudo systemctl enable rgb-controller.service
    > sudo systemctl start rgb-controller.service

- Check the status of the service

    > sudo systemctl status rgb-controller.service

TL;DR: This was a program implemented for MY Motherboard and MY Mouse, it should not work with your build if u have different specs. 