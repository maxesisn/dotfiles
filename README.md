# 杂碎文件合集

## 0x00 新番半自动重命名
* 所需文件：
    * `global_config.py`
    * `anirename`
    * `plex_syncer.py`

* 前置需求：
    1. 完善global_config相关配置:
        * `BGMI_API_URL`: BGmi的接口地址，修改IP与端口即可
        * `MEDIALIB_FOLDER_PATH`: 冻鳗媒体库关联的文件夹路径
        * `BGMI_FOLDER_PATH`: BGmi下载目录
    2. 需要拥有正常运行的[BGmi](https://github.com/BGmi/bgmi-docker-all-in-one)实例
    3. 需要安装[filebot](https://www.filebot.net/)并购买授权
    4. 需要将`anirename`脚本拷贝或链接至 `/usr/local/bin/`
  
* 使用方法：
    1. 在(Plex/Emby/Jellyfin之类的)媒体库文件夹下创建`NEED_RENAME.txt`
    2. 按如下格式修改该配置文件：
        ```
        番剧1中文译名
        番剧1原名
        番剧2中文译名
        番剧2原名
        ...
        ```
    3. 运行`python3 plex_syncer.py`，或添加定时运行配置

## 0x01 ZFS阵列状态告警
* 所需文件：
    * `global_config.py`
    * `chkzpool.py`

* 前置需求：
    1. 完善global_config相关配置:
        * `zpool_name`: 存储池名称

* 使用方法：
    1. 运行`python3 chkzpool.py`，或添加定时运行配置

## 0x02 S.M.A.R.T状态告警
* 所需文件：
    * `global_config.py`
    * `smartmon.py`

* 使用方法：
    1. 运行`python3 smartmon.py`，或添加定时运行配置

## 0xFF 其它文件
自己看代码参悟一下
