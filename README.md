![Lines of code](https://img.shields.io/tokei/lines/github/vertyco/ArkCSM?style=plastic)

# ArkCSM

Ark Crossplay Server Manager

This script auto-reboots crossplay ark servers downloaded from the microsoft store on Windows 10. It also checks for
updates and can send webhooks to the discord when one is detected.

I am not currently providing support for this script.


# How To Setup
To use ArkCSM, you will need python installed on your computer.
```ini
1. download this repo as a zip, extract wherever you like
2. open command prompt (as administrator) and cd into the directory where you extracted the files
3. run 'pip install -r requirements.txt'
4. run 'python arkcsm.py'
5. Done. You can configure the app how you like and it will generate a config.json file

Alternatively you can run the 'start.bat' script to execute it(remember to run as administrator)
```

This script is just to make it a little easier to host crossplay ark servers.