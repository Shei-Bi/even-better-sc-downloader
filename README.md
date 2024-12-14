<p>
<h1 align="center" style="font-size: 32px;"> <sub><sup>(better)</sup></sub> SC Downloader</h1>
</p>

### Description
File downloader for all  <sub><sup>(probably)</sup></sub> games from Supercell. It directly receives all the latest data from the server and downloads it.  
[This sc-downloader by vorono4ka was used as a base](https://github.com/Vorono4ka/sc-downloader), some code from it is still here. But it has been greatly improved:
- Added support for latest game servers iterations
- Added threading to improve downloading speed
- Added file patching feature
- Added file verify feature

### HOW TO USE
You need to have at least Python 3.9 for this to work.  
If you want to run script for the first time, then install all modules with this command in cmd
```
pip install -r requirements.txt
```
Basic usage is very simple, just run script with a command like
```
py main.py
```
After that, select the game server you need. All assets will begin downloading into ```assets/{Server name}/```

## In case if you need more
There are additional flags here too. 

- ```--hash``` You can download assets directly using the version hash. Assets will be downloaded to a folder with the same name as hash. Example ```py main.py --hash=SomeVersionHash```

- ```--repair-mode``` and ```--strict-repair-mode``` is just flags.  
Normal mode checks if files exist and if not, downloads them. Useful if: You have downloaded apk or ipa of the game, you already have almost all the assets. You can unpack these assets into the folder of the desired server and run script with this flag, it will download all files that may not be in your assets like background textures or music.  
Strict mode checks all files based on their content and this can be a bit long. Useful if: You accidentally somehow replaced a file or its content. Run script with this flag and its contents will be restored.

## Patches
Patches are a very useful feature if you just need to get new files from the latest update.  
It compares previous version and current one, and copies all new or changed files to ```patches/{Server name}/{old version name} {new version name}/```  
If detailed patches are enabled in the config, then the patch will be divided into 3 parts, new files, changed files and deleted files.
To enable or disable this feature, you can look in ```config.json```.

## Config
```config.json``` contains all settings for managing servers, threading and patches.
- ```servers``` are stored in a dictionary, key of which means name and value of key means address of the game server. You can easily add your own server.  
- ```auto_update``` means whether files should be updated automatically. Otherwise, every time there is an optional update, script will ask about files updating. 
- ```make_patches``` and ```make_detailed_patches``` explained in patches description
- ```max_workers``` or maximum count of threads. Each thread downloads its own list of files and this parameter sets maximum number of threads that can work at one time. Be careful, a large number of threads can either speed up or slow down process, for the most part it all depends on your PC. A large number of threads is not recommended on weak PCs.  
- ```worker_max_items``` sets the number of how many files one worker can process. This is made for large folders like folders with 3d graphics or sounds. This folders will be divided into pieces whose size depends on this value, and each piece will be processed by a new worker.
- ```save_dump``` mostly needed for debugging messages from server. just don't touch it.

