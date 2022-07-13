import os
import shutil
import logging
import re
from ics import Calendar
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime


from global_config import mail_pass, mail_user, sender, receivers, sender_name, smtp_server
from global_config import PLEX_ANIME_PATH, BGMI_BANGUMI_PATH, calender_url

log_pattern = re.compile(r"(.*)Skipped(.*)already exists(.*)")
NEED_RENAME_CONFIG = PLEX_ANIME_PATH+"NEED_RENAME.txt"


c = Calendar(requests.get(calender_url).text)
act_recorded_bangumi = list()
for recorded_bangumi in c:
    if recorded_bangumi.startswith("SUMMARY:"):
        act_recorded_bangumi.append(
            str(recorded_bangumi).strip().removeprefix("SUMMARY:").replace(":", ""))

logging.basicConfig(level=logging.DEBUG)
email_content = ""

new_bangumi_list = list()

with open(NEED_RENAME_CONFIG) as f:
    while True:
        temp_dict = dict()
        temp_dict["folder_name"] = f.readline().rstrip("\n")
        if temp_dict["folder_name"].startswith("+"):
            temp_dict["start_ep"] = temp_dict["folder_name"][1:3]
            temp_dict["folder_name"] = temp_dict["folder_name"][3:]
        else:
            temp_dict["start_ep"] = "0"
        temp_dict["raw_name"] = f.readline().rstrip("\n")
        if not (temp_dict["folder_name"] or temp_dict["raw_name"]):
            break
        new_bangumi_list.append(temp_dict)

print(new_bangumi_list)
bangumi_missing_str = "警告：\n"

bangumi_foldername_list = [bangumi["folder_name"]
                           for bangumi in new_bangumi_list]
bangumi_only_in_record_list = [
    bgm for bgm in bangumi_foldername_list if bgm not in act_recorded_bangumi]
bangumi_only_in_bgmi_list = [
    bgm for bgm in act_recorded_bangumi if bgm not in bangumi_foldername_list]

if bangumi_only_in_record_list:
    bangumi_missing_str += "以下番剧仅在NEED_RENAME.txt中记录："
    bangumi_missing_str += " ".join(bangumi_only_in_record_list)
    bangumi_missing_str += "\n"
if bangumi_only_in_bgmi_list:
    bangumi_missing_str += "以下番剧在BGmi中有记录，但未存在于NEED_RENAME.txt："
    bangumi_missing_str += " ".join(bangumi_only_in_bgmi_list)
    bangumi_missing_str += "\n"
if not (bangumi_only_in_record_list or bangumi_only_in_bgmi_list):
    bangumi_missing_str = str()

print(bangumi_missing_str)

for bangumi_name in new_bangumi_list:
    folder_name = bangumi_name["folder_name"]
    raw_name = bangumi_name["raw_name"]
    logging.info("Processing "+folder_name)
    if folder_name not in os.listdir(BGMI_BANGUMI_PATH):
        logging.info("Bangumi not exist, skipped")
        continue
    if folder_name not in os.listdir(PLEX_ANIME_PATH):
        os.mkdir(os.path.join(PLEX_ANIME_PATH, folder_name))
    bangumi_in_plex = os.listdir(PLEX_ANIME_PATH+folder_name)
    p = re.compile(r"(.*) - S([0-9][0-9])E([0-9][0-9]) - (.*)")
    bangumi_in_plex_digit = list()
    start_ep = int(bangumi_name["start_ep"])
    for bgm in bangumi_in_plex:
        ep_g = p.search(bgm)
        if ep_g is None:
            continue
        ep = ep_g.group(3)
        ses = ep_g.group(2)
        ep = int(ep)

        bangumi_in_plex_digit.append(str(ep+start_ep))
    bangumi_in_bgmi = os.listdir(BGMI_BANGUMI_PATH+folder_name)
    bangumi_all_available = bangumi_in_plex_digit + bangumi_in_bgmi
    bangumi_all_available = set(bangumi_all_available)
    new_episodes = bangumi_all_available.difference(bangumi_in_plex_digit)

    if not new_episodes:
        logging.info("Already newest")
        continue
    new_episodes = list(new_episodes)
    new_episodes.sort()

    non_finished_eps = list()
    for episode in new_episodes:
        if not os.listdir(os.path.join(BGMI_BANGUMI_PATH, folder_name, str(episode))):
            non_finished_eps.append(episode)
        else:
            for files in os.listdir(os.path.join(BGMI_BANGUMI_PATH, folder_name, str(episode))):
                if files.endswith(".!qB"):
                    non_finished_eps.append(episode)
    for ep in non_finished_eps:
        new_episodes.remove(ep)
    if not new_episodes:
        logging.info("Already newest")
        continue

    if email_content == "":
        email_content += bangumi_missing_str
        email_content += "已对下列新番完成处理:\n"
    email_content += folder_name+": "
    episode_name_list = list()
    for episode in new_episodes:
        episode = str(episode)
        logging.info("Processing episode "+episode)
        episode_name_list.append(f"第{episode}集")
        episode_path = os.path.join(folder_name, episode)
        print(os.path.join(BGMI_BANGUMI_PATH, episode_path),
              os.path.join(PLEX_ANIME_PATH, folder_name))
        # for linux running rsync
        os.system(
            f"rsync -a --info=progress2 '{os.path.join(BGMI_BANGUMI_PATH, episode_path)}' '{os.path.join(PLEX_ANIME_PATH, folder_name)}'")
    episode_name = " ".join(episode_name_list)
    email_content += episode_name
    os.chdir(os.path.join(PLEX_ANIME_PATH, folder_name))
    dirlist = os.listdir()
    for dir in dirlist:
        if os.path.isdir(dir):
            filelist = os.listdir(dir)
        else:
            continue
        for file in filelist:
            try:
                shutil.move(os.path.join("./", dir, file), os.path.join("./"))
            except shutil.Error:
                pass
        if dir.isdigit():
            shutil.rmtree(dir)
    rename_log = os.popen(f"/usr/local/bin/anirename '{raw_name}'").read()
    rename_log = rename_log.splitlines()
    new_rename_log = list()
    for log in rename_log:
        if not log_pattern.match(log):
            if not log.startswith("Stripping invalid characters"):
                new_rename_log.append(log)
    new_rename_log = "\n".join(new_rename_log)
    email_content += "\n重命名日志如下:\n"
    email_content += new_rename_log
    email_content += "\n\n"

if email_content != "":
    message = MIMEText(email_content, 'plain', 'utf-8')
    message['From'] = str(Header(f"{sender_name} <{sender}>"))
    message['To'] = ", ".join(receivers)

    subject = f"新番复制重命名工作 {datetime.now().strftime('%m/%d/%Y, %H:%M')}"
    message['Subject'] = Header(subject, 'utf-8')

    smtpObj = smtplib.SMTP_SSL(f"{smtp_server}:465")
    smtpObj.login(mail_user, mail_pass)
    smtpObj.sendmail(sender, receivers, message.as_string())

# sleep(10)
logging.info("开始二次扫描")
scan_rename_log = ""
for bangumi_name in new_bangumi_list:
    folder_name = bangumi_name["folder_name"]
    raw_name = bangumi_name["raw_name"]
    try:
        logging.info(f"Processing {folder_name}")
        os.chdir(os.path.join(PLEX_ANIME_PATH, folder_name))
        rename_log = os.popen(f"/usr/local/bin/anirename '{raw_name}'").read()
        rename_log = rename_log.splitlines()
        new_rename_log = list()
        for log in rename_log:
            if not log_pattern.match(log):
                if not log.startswith("Stripping invalid characters"):
                    new_rename_log.append(log)
        new_rename_log = "\n".join(new_rename_log)
        print(new_rename_log)
        if not any(x in rename_log for x in ["Processed 0 files", "No media files"]):
            logging.info(f"《{folder_name}》补全了重命名")
            scan_rename_log += f"对《{folder_name}》扫描时补全了重命名工作：\n"
            scan_rename_log += new_rename_log
            scan_rename_log += "\n"
    except FileNotFoundError:
        logging.warning("Bangumi not exist, skipped")
if scan_rename_log != "":
    message = MIMEText(scan_rename_log, 'plain', 'utf-8')
    message['From'] = str(Header(f"{sender_name} <{sender}>"))
    message['To'] = ", ".join(receivers)

    subject = f"新番补充重命名工作 {datetime.now().strftime('%m/%d/%Y, %H:%M')}"
    message['Subject'] = Header(subject, 'utf-8')

    smtpObj = smtplib.SMTP_SSL(f"{smtp_server}:465")
    smtpObj.login(mail_user, mail_pass)
    smtpObj.sendmail(sender, receivers, message.as_string())
    exit()
