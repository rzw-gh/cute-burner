# configuration file for Cute Burner Script

import os

FONT = {
    'fonts_dir': os.path.abspath("assets"),
    'font_path': os.path.abspath("assets/Vazir Black.ttf")
}

video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.mpeg', '.mpg', '.m4v']
leading_zero = 2  # appends one 0 before video index name e.g: 01

copy_right = [
    "AniFox.site",  # website
    r".:: ارائه شده توسط وبسایت انی فاکس ::.\N.:: AniFox.site ::.",  # start of video
    r"وبسایت انی فاکس با افتخار تقدیم میکند\NAniFox.site",  # middle of video
    r"انیمه های بیشتر در\Nt.me/AniFoxIR | AniFox.site",  # end of video
]

# include words you want to remove from text of extracted soft subtitle
words_to_remove_from_subtitle = [
    "nightmovie", "digimovie", "digimoviez", "avamovie", "aniplus", "animelist", "animlist", "Anime Khor", "AnimWorld", "Forums.AnimWorld.Net",
    "اوا مووی", "دیجی مووی", "دیجی موویز", "نایت مووی", "انیمه لیست", "انی پلاس", "انیمه ورلد", "انیم ورلد",
    "شبکه های اجتماعی",
    "شبکه اجتماعی",
    "تلگرام", "اینستاگرام", "telegram", "instagram", "پیج", "کانال تلگرام", "تلگرامی", "t.me", "@",
    "وب سایت",
    "زیرنویس",
    ":زیرنویس",
    "زیرنویس:",
    "زیر نویس",
    ":زیر نویس",
    "زیر نویس:",
    "با افتخار تقدیم میکند",
    "ترجمه و تنظیم",
    ":ترجمه و تنظیم",
    "ترجمه و تنظیم:",
    "تنظیم و ترجمه",
    ":تنظیم و ترجمه",
    "تنظیم و ترجمه:",
    "ترجمه و زیرنویس",
    "ترجمه و زیرنویس:",
    ":ترجمه و زیرنویس",
    "ترجمه و زیر نویس",
    "ترجمه و زیر نویس:",
    ":ترجمه و زیر نویس",
    "کاری از تیم",
    "انکود",
    "ارائه ای از",
    "ارائه شده",
    "ارائه‌شده",
    "ترجمه‌از",
    "ترجمه‌و‌تنظیم",
    "تنظیم‌و‌ترجمه",
    "کاری‌از",
    "تیم‌ترجمه",
    "وب‌سایت",
    "زیر‌نویس",
    "تقدیم‌میکند",
    "انکود‌توسط",
    "انکود‌اختصاصی",
    "تیم ترجمه",
    "ترجمه اختصاصی",
    "انکودر", "encode", "encoder", "translate", "translator", "translated",
    ".com", ".ir", ".org", ".shop", ".site", ".fun", ".me", ".top", ".tv",
    "ترجمه از", "مترجم", "مترجمین",
    "》", "《", ">", "<", "~", ".::", "::.",
    "m 151 9 l 155 14 l"
]