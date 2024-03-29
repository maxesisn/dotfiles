import json
import os
import logging
import re
import httpx
from datetime import datetime
from tomlkit import parse, dumps, table

from global_config import MEDIALIB_FOLDER_PATH, BGMI_FOLDER_PATH, BGMI_API_URL, BANGUMITV_API_TOKEN
from sendmail import send_mail


def extract_seson_number(episode_name):
    """Extract season number from episode name"""
    season_number = re.search(r".*S(\d+)E\d+.*", episode_name)
    if season_number:
        return int(season_number.group(1))
    else:
        return 0


def replace_season_number(episode_name, season_number):
    """Replace season number in episode name"""
    return re.sub(r"S\d+E", f"S{season_number:02d}E", episode_name)

def get_raw_name_from_bangumi_tv(bangumi_name):
    """Get raw name from bangumi.tv"""
    bangumitv_api_url = "https://api.bgm.tv/v0/search/subjects"
    payload = {
        "keyword": bangumi_name,
        "type": [2]
    }
    payload = json.dumps(payload, ensure_ascii=False)
    headers = {
        "User-Agent": "maxesisn/bgmi_syncer",
    }
    response = httpx.post(bangumitv_api_url, data=payload, headers=headers)
    if response.status_code == 200:
        try:
            return response.json()["data"][0]["name"]
        except:
            return None
    else:
        return None

log_pattern = re.compile(r"(.*)Skipped(.*)already exists(.*)")
NEED_RENAME_CONFIG = MEDIALIB_FOLDER_PATH+"RENAME_CONFIG.toml"

bgmi_index_data = httpx.get(BGMI_API_URL).json()
bgmi_bangumi_list = list()
for data in bgmi_index_data["data"]:
    bangumi_data = dict()
    bangumi_data["bangumi_name"]: str = data["bangumi_name"]
    bangumi_data["total_episodes"]: int = data["episode"]
    if bangumi_data["total_episodes"] == 0:
        continue
    bangumi_data["episode_list"]: list = data["player"]
    bgmi_bangumi_list.append(bangumi_data)

bgmi_bangumi_name_list = [x["bangumi_name"] for x in bgmi_bangumi_list]

logging.basicConfig(level=logging.DEBUG)
email_content = ""

bangumi_in_rename_config_list = list()

with open(NEED_RENAME_CONFIG) as f:
    config_str = f.read()
    config = parse(config_str)
    config_anime_list = config["Anime"]
    for anime in config_anime_list:
        bangumi_in_rename_config_list.append({
            "folder_name": anime.get("folder_name"),
            "raw_name": anime.get("raw_name") or anime.get("folder_name"),
            "season": anime.get("season") or 1,
            "first_episode_in_metadata_db": anime.get("first_episode_in_metadata_db") or 1,
        })


bangumi_missing_str = "警告：\n"

bangumi_foldername_list = [bangumi["folder_name"]
                           for bangumi in bangumi_in_rename_config_list]
bangumi_only_in_rename_config_list = [
    bgm for bgm in bangumi_foldername_list if bgm not in bgmi_bangumi_name_list]
bangumi_only_in_bgmi_web_list = [
    bgm for bgm in bgmi_bangumi_name_list if bgm not in bangumi_foldername_list]

if bangumi_only_in_rename_config_list:
    config_anime_list = [anime for anime in config_anime_list if not anime.get("folder_name") in bangumi_only_in_rename_config_list]
    config_table = table()
    config_table.add("Anime", config_anime_list)
    with open(NEED_RENAME_CONFIG, "w") as f:
        f.write(dumps(config_table))
    logging.info("Removed bangumi from config as it not exists in BGmi: %s", bangumi_only_in_rename_config_list)
    bangumi_missing_str += "以下番剧仅在RENAME_CONFIG.toml中记录，已自动移除："
    bangumi_missing_str += " ".join(bangumi_only_in_rename_config_list)
    bangumi_missing_str += "\n"
if bangumi_only_in_bgmi_web_list:
    config_table = table()
    for bgm in bangumi_only_in_bgmi_web_list:
        new_anime_table = table()
        new_anime_table.add("folder_name", bgm)
        raw_name_from_bgmtv = get_raw_name_from_bangumi_tv(bgm)
        if raw_name_from_bgmtv:
            new_anime_table.add("raw_name", raw_name_from_bgmtv)
        config_anime_list.append(new_anime_table)
    config_table.add("Anime", config_anime_list)
    with open(NEED_RENAME_CONFIG, "w") as f:
        new_config = dumps(config_table)
        if new_config:
            f.write(new_config)
        else:
            logging.warning("Failed to write new config to file as it appears to be empty")
    logging.info("Added bangumi to config as it only exists in BGmi: %s", bangumi_only_in_bgmi_web_list)
    bangumi_missing_str += "以下番剧在BGmi中有记录，但未存在于RENAME_CONFIG.toml，已自动添加："
    bangumi_missing_str += " ".join(bangumi_only_in_bgmi_web_list)
    bangumi_missing_str += "\n"
if not (bangumi_only_in_rename_config_list or bangumi_only_in_bgmi_web_list):
    bangumi_missing_str = ""

for bangumi in bangumi_in_rename_config_list:
    if bangumi["folder_name"] in bangumi_only_in_rename_config_list:
        continue
    bangumi_in_bgmi: list[dict] = bgmi_bangumi_list[bgmi_bangumi_name_list.index(
        bangumi["folder_name"])]
    folder_name = bangumi["folder_name"]
    raw_name_from_bgmtv = bangumi["raw_name"]
    start_episode = int(sorted(bangumi_in_bgmi["episode_list"])[0])
    if folder_name not in os.listdir(BGMI_FOLDER_PATH):
        logging.info("Bangumi not exist, skipped")
        continue
    if folder_name not in os.listdir(MEDIALIB_FOLDER_PATH):
        os.mkdir(MEDIALIB_FOLDER_PATH+folder_name)
    bangumi_in_medialib = os.listdir(MEDIALIB_FOLDER_PATH+folder_name)
    p = re.compile(r"(.*) - S([0-9][0-9])E([0-9][0-9]) - (.*)")
    bangumi_in_medialib_existed_episodes = list()
    for bgm in bangumi_in_medialib:
        ep_g = p.search(bgm)
        if ep_g is None:
            continue
        ep = ep_g.group(3)
        ses = ep_g.group(2)
        ep = int(ep)
        if bangumi["first_episode_in_metadata_db"] == 1:
            ep = ep+start_episode-1
        bangumi_in_medialib_existed_episodes.append(ep)

    bangumi_in_bgmi_folder_episodes = os.listdir(BGMI_FOLDER_PATH+folder_name)
    bangumi_in_bgmi_folder_episodes = [
        int(ep) for ep in bangumi_in_bgmi_folder_episodes]
    bangumi_all_available_episodes = bangumi_in_medialib_existed_episodes + \
        bangumi_in_bgmi_folder_episodes
    bangumi_all_available_episodes = set(bangumi_all_available_episodes)
    new_episodes_in_bgmi_folder = bangumi_all_available_episodes.difference(
        bangumi_in_medialib_existed_episodes)

    if not new_episodes_in_bgmi_folder:
        continue
    new_episodes_in_bgmi_folder = sorted(list(new_episodes_in_bgmi_folder))

    episodes_still_in_downloading_status = list()
    for ep in new_episodes_in_bgmi_folder:
        if not os.listdir(os.path.join(BGMI_FOLDER_PATH, folder_name, str(ep))):
            episodes_still_in_downloading_status.append(ep)
        else:
            for files in os.listdir(os.path.join(BGMI_FOLDER_PATH, folder_name, str(ep))):
                if files.endswith(".aria2"):
                    episodes_still_in_downloading_status.append(ep)

    for ep in episodes_still_in_downloading_status:
        new_episodes_in_bgmi_folder.remove(ep)
        logging.info("Episode "+str(ep)+" of " + folder_name +
                     " still in downloading status, skipped")

    if not new_episodes_in_bgmi_folder:
        continue

    if email_content == "":
        email_content += "已对下列新番完成处理:"
    email_content += "\n"+folder_name+": "
    episode_name_list = list()
    for episode in new_episodes_in_bgmi_folder:
        episode = str(episode)
        logging.info("ℹ Processing episode "+episode + " of "+folder_name)
        episode_name_list.append(f"第{episode}集")
        episode_ready_for_copy_path: str = bangumi_in_bgmi["episode_list"][episode]["path"]
        episode_ready_for_copy_path = BGMI_FOLDER_PATH + episode_ready_for_copy_path
        # for linux running rsync
        os.system(
            f"rsync -a '{episode_ready_for_copy_path}' '{os.path.join(MEDIALIB_FOLDER_PATH, folder_name)}'")
    episode_name = " ".join(episode_name_list)
    email_content += episode_name

    os.chdir(os.path.join(MEDIALIB_FOLDER_PATH, folder_name))
    rename_log = os.popen(f"/usr/local/bin/anirename '{raw_name_from_bgmtv}'").read()
    rename_log = rename_log.splitlines()
    new_rename_log = list()
    for log in rename_log:
        if not log_pattern.match(log):
            if not log.startswith("Stripping invalid characters"):
                new_rename_log.append(log)
    new_rename_log = "\n".join(new_rename_log)
    email_content += "\n重命名日志如下:\n"
    email_content += new_rename_log

    if bangumi["season"] != "1":
        season_replace_flag = False
        for file in os.listdir():
            season_number = extract_seson_number(file)
            if season_number != bangumi["season"]:
                os.rename(file, replace_season_number(file, bangumi["season"]))
                season_replace_flag = True
        if season_replace_flag:
            email_content += "\n检测到不正确的重命名结果，已将文件名中的季数替换为" + \
                str(bangumi["season"])+"\n\n"

if email_content == "" and bangumi_missing_str != "":
    email_content += bangumi_missing_str

if email_content != "":
    subject = f"新番复制重命名工作 {datetime.now().strftime('%m/%d/%Y, %H:%M')}"
    send_mail(subject, email_content)


scan_rename_log = ""
for bangumi_name in bangumi_in_rename_config_list:
    folder_name = bangumi_name["folder_name"]
    raw_name_from_bgmtv = bangumi_name["raw_name"]
    try:
        os.chdir(os.path.join(MEDIALIB_FOLDER_PATH, folder_name))
        rename_log = os.popen(f"/usr/local/bin/anirename '{raw_name_from_bgmtv}'").read()
        rename_log = rename_log.splitlines()
        new_rename_log = list()
        for log in rename_log:
            if not log_pattern.match(log):
                if not log.startswith("Stripping invalid characters"):
                    new_rename_log.append(log)
        new_rename_log = "\n".join(new_rename_log)
        if not any(x in rename_log for x in ["Processed 0 files", "No media files"]):
            logging.info(f"《{folder_name}》补全了重命名")
            scan_rename_log += f"对《{folder_name}》扫描时补全了重命名工作：\n"
            scan_rename_log += new_rename_log
            scan_rename_log += "\n"
    except FileNotFoundError:
        logging.warning("Bangumi not exist, skipped")
if scan_rename_log != "":
    subject = f"新番补充重命名工作 {datetime.now().strftime('%m/%d/%Y, %H:%M')}"
    send_mail(subject, scan_rename_log)

needed_add = 0
# make sure RENAME_CONFIG_FILE has 2 new lines at the end
with open(NEED_RENAME_CONFIG, "r") as f:
    lines = f.readlines()
    if lines[-2] in ['\n','\r\n']:
        exit()
    elif lines[-1] in ['\n','\r\n']:
        needed_add = 1
    else:
        needed_add = 2
with open(NEED_RENAME_CONFIG, "a") as f:
    for i in range(needed_add):
        f.write("\n")
exit()
