"""
🤖 Nitro Proxy - Advanced 3-Bot Management System
Owner Bot | Admin Bot | User Bot
"""
import json, time, os, asyncio, re, hashlib, html as html_module
from datetime import datetime, timedelta
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, WebAppInfo
from telegram.constants import ParseMode
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, 
                          MessageHandler, filters, ContextTypes)

# Import config
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import *
from key_manager import create_pending_key, activate_license_key, load_license_keys, save_license_keys

# Import mod safety manager
try:
    from mod_safety_manager import load_mod_safety_status, save_mod_safety_status, update_mod_status
except ImportError:
    # Fallback if mod_safety_manager not found
    def load_mod_safety_status():
        return {}
    def save_mod_safety_status(data):
        pass
    def update_mod_status(port, status, updated_by):
        return False

# CONFIGURATION
KEYS_PER_PAGE = 8  # عدد المفاتيح في كل صفحة

# Language Strings
LANG = {
    "ar": {
        "owner_panel": "👑 لوحة المالك\n\n📊 إحصائيات النظام:\n├ 👨‍✈️ الموزعين: {admins}\n├ 🔑 المفاتيح: {keys}\n├ 👥 المستخدمين: {users}\n└ 💰 الإيرادات: ${revenue:.2f}\n\n🎯 اختر خياراً:",
        "admin_panel": "👨‍✈️ لوحة الموزع\n\nمرحباً {name}! 👋\n\n📊 إحصائياتك:\n├ 💰 المحفظة: ${wallet:.2f}\n├ 🔑 المفاتيح: {keys}\n└ ✅ النشطة: {active}\n\n💵 الأسعار:\n├ يوم: ${day:.2f}\n├ أسبوع: ${week:.2f}\n└ شهر: ${month:.2f}\n\n🎯 اختر خياراً:",
        "user_panel": "👋 أهلاً {name}!\n\n🎮 Nitro Proxy - لوحة المستخدم\n\n🎯 اختر خياراً:",
        "add_reseller": "➕ إضافة موزع",
        "manage_wallets": "💰 إدارة المحافظ",
        "ban_reseller": "🚫 حظر موزع",
        "withdraw_money": "💸 سحب أموال",
        "resellers_list": "📋 قائمة الموزعين",
        "statistics": "📊 الإحصائيات",
        "all_keys": "🔑 جميع المفاتيح",
        "freeze_all_keys": "❄️ تجميد المفاتيح",
        "unfreeze_all_keys": "✅ فك التجميد",
        "delete_all_keys": "🧹 حذف كل المفاتيح",
        "free_keys": "🎁 مفاتيح مجانية",
        "freeze_already": "⏸️ المفاتيح مجمّدة بالفعل.",
        "freeze_started": "⏸️ تم تجميد جميع المفاتيح. سيتم إيقاف الوقت مؤقتاً.",
        "unfreeze_not_active": "✅ لا يوجد تجميد حالياً.",
        "unfreeze_done": "✅ تم فك التجميد. تمت إضافة {seconds} ثانية مؤقتاً.",
        "confirm_delete_all_keys": "⚠️ تأكيد حذف كل المفاتيح! هذا سيحذف الأكواد والاشتراكات.",
        "yes_confirm": "✅ نعم",
        "no_cancel": "❌ لا",
        "delete_cancelled": "❌ تم إلغاء الحذف.",
        "delete_done": "🧹 تم حذف كل المفاتيح بنجاح.",
        "send_freekey_count": "🎁 أدخل عدد المفاتيح المجانية التي تريد توليدها:",
        "send_freekey_days": "⏰ أدخل المدة (بالأيام) لكل مفتاح مجاناً.\nعدد المفاتيح: {count}",
        "freekey_count_too_large": "❌ العدد كبير جداً. الحد 200.",
        "free_keys_done": "✅ تم توليد {count} مفتاح مجاناً لمدة {days} يوم.\nسيتم إرسالها كملف txt.",
        "add_key": "➕ إضافة مفتاح",
        "my_keys": "🔑 مفاتيحي",
        "extend_key": "⏰ تمديد مفتاح",
        "ban_key": "🚫 حظر مفتاح",
        "wallet_info": "💰 معلومات المحفظة",
        "language": "🌐 اللغة",
        "check_sub": "📊 حالة الاشتراك",
        "get_ip": "📖 كيف أعرف IP",
        "ip_tutorial": "📖 خطوات معرفة IP العام (IPv4):\n\n1) افتح Safari على الآيفون.\n2) ادخل الموقع:\n{url}\n3) انسخ الرقم الظاهر كـ IPv4 (مثل 12.34.56.78).\n4) لا تستخدم VPN أثناء النسخ.\n\n⚠️ استخدم نفس شبكة الـ Wi‑Fi التي ضبطت عليها البروكسي.",
        "ask_send_ip_sub": "📊 للتحقق من الاشتراك:\n\nاتبع الخطوات في الرسالة السابقة، ثم أرسل عنوان IPv4 هنا (رسالة واحدة فقط).",
        "ask_send_key_first": "✅ تفعيل المفتاح — الخطوة 1 من 2\n\nأرسل المفتاح بهذه الصيغة:\nXXXX-XXXX-XXXX",
        "ask_send_ip_activate": "✅ الخطوة 2 من 2\n\nأرسل IPv4 العام الذي نسخته من الموقع.",
        "invalid_ip": "❌ عنوان IP غير صحيح. أرسل IPv4 مثل: 1.2.3.4",
        "back": "🔙 رجوع",
        "support": "💬 الدعم",
        "unauthorized": "❌ غير مصرح لك بالوصول",
        "contact_support": "💬 تواصل مع: {support}",
        "send_admin_id": "📝 أرسل Telegram ID للموزع الجديد:",
        "admin_added": "✅ تم إضافة الموزع بنجاح!\n\nID: {aid}\nالمحفظة: $0.00",
        "admin_added_rich": "✅ تم إضافة الموزع\n\n🆔 <b>معرف Telegram (اضغط للنسخ):</b>\n<code>{aid}</code>\n\n🔗 <a href=\"tg://user?id={aid}\">فتح محادثة الموزع</a>\n\nاضغط الزر أدناه لإضافة رصيد مباشرة.",
        "wallet_quick": "💰 إضافة رصيد لهذا الموزع",
        "owner_section_codes": "📋 <b>أكواد الترخيص</b>",
        "owner_section_ips": "🌐 <b>اشتراكات IP النشطة</b>",
        "no_license_codes": "<i>لا توجد أكواد بعد</i>",
        "no_active_ips": "<i>لا توجد اشتراكات IP نشطة</i>",
        "send_amount": "💵 أرسل المبلغ المراد إضافته (بالدولار):",
        "wallet_added": "✅ تم إضافة ${amount:.2f} للمحفظة!\n\nالرصيد الجديد: ${balance:.2f}",
        "invalid_format": "❌ صيغة خاطئة! حاول مرة أخرى",
        "no_resellers": "❌ لا يوجد موزعين",
        "select_reseller_ban": "🚫 اختر موزع للحظر:",
        "reseller_banned": "🚫 تم حظر الموزع!\n\n👤 ID: {aid}\n\n✅ تم تعطيل الحساب",
        "insufficient_balance": "❌ رصيد غير كافٍ!\n\n💰 رصيدك: ${wallet:.2f}\n💵 المطلوب: ${required:.2f}\n\n💬 تواصل مع المالك: {support}",
        "send_ip": "📝 أرسل عنوان IP للمفتاح الجديد:",
        "select_duration": "⏰ اختر المدة\n\n🔑 IP: {ip}\n💰 رصيدك: ${wallet:.2f}\n\nاختر المدة:",
        "key_added": "✅ تم إضافة المفتاح!\n\n🔑 IP: {ip}\n📅 المدة: {days} يوم\n⏰ ينتهي: {date}\n💰 التكلفة: ${cost:.2f}\n💵 الرصيد الجديد: ${balance:.2f}",
        "no_keys": "❌ لا توجد مفاتيح",
        "select_key_extend": "🔑 اختر مفتاح للتمديد:",
        "select_key_ban": "🔑 اختر مفتاح للحظر:",
        "key_extended": "✅ تم تمديد المفتاح!\n\n🔑 IP: {ip}\n📅 المدة: {days} يوم\n⏰ ينتهي: {date}\n💰 التكلفة: ${cost:.2f}\n💵 الرصيد الجديد: ${balance:.2f}",
        "key_banned": "🚫 تم حظر المفتاح!\n\n🔑 IP: {ip}\n\n✅ تم تعطيل المفتاح",
        "sub_active": "✅ اشتراكك نشط!\n\n🔑 IP الخاص بك: {ip}\n⏰ ينتهي: {date}\n📅 المتبقي: {days}d {hours}h\n\n🎮 استمتع بـ Nitro Proxy!",
        "sub_frozen_notice": "❄️ النظام في وضع التجميد (Maintenance).\n\n⏸️ المفتاح متجمد مؤقتًا ولن يعمل الآن.\n✅ مدة اشتراكك محفوظة ولن تنقص أثناء التجميد.\n\n🔑 IP: {ip}",
        "sub_inactive": "❌ لا يوجد اشتراك نشط\n\n🔑 IP الخاص بك: {ip}\n\n💬 تواصل مع موزع لتفعيل اشتراكك",
        "your_ip": "🌐 عنوان IP الخاص بك\n\n🔑 IP: {ip}\n\n💡 أرسل هذا الـ IP للموزع لتفعيل اشتراكك",
        "day_btn": "📅 يوم (${price:.2f})",
        "week_btn": "📅 أسبوع (${price:.2f})",
        "month_btn": "📅 شهر (${price:.2f})",
        "cancel": "❌ إلغاء",
        "select_key_manage": "🔑 اختر مفتاح للإدارة:",
        "key_info": "🔑 معلومات المفتاح\n\n📍 IP: {ip}\n👤 الموزع: {admin}\n📅 ينتهي: {date}\n⏰ المتبقي: {days}d {hours}h\n\n🎯 اختر إجراء:",
        "delete_key": "🗑️ حذف",
        "extend_key_owner": "⏰ تمديد",
        "key_deleted": "🗑️ تم حذف المفتاح!\n\n🔑 IP: {ip}",
        "select_extend_duration": "⏰ اختر مدة التمديد\n\n🔑 IP: {ip}",
        "key_extended_owner": "✅ تم تمديد المفتاح!\n\n🔑 IP: {ip}\n📅 المدة المضافة: {days} يوم\n⏰ ينتهي الآن: {date}",
        "select_reseller_withdraw": "💸 اختر موزع لسحب الأموال:",
        "send_withdraw_amount": "💸 أرسل المبلغ المراد سحبه (بالدولار):",
        "money_withdrawn": "✅ تم سحب ${amount:.2f} من المحفظة!\n\nالرصيد الجديد: ${balance:.2f}",
        "insufficient_balance_withdraw": "❌ رصيد غير كافٍ للسحب!\n\n💰 رصيد الموزع: ${wallet:.2f}\n💵 المبلغ المطلوب: ${amount:.2f}",
        "gen_license_btn": "🎫 توليد مفتاح (كود)",
        "gen_select_duration": "⏰ اختر مدة المفتاح\n\n💰 رصيدك: ${wallet:.2f}",
        "gen_key_created": "✅ تم إنشاء المفتاح\n\n🔑 <b>انسخ الكود:</b>\n<code>{key}</code>\n\n📅 المدة: {days} يوم\n💰 التكلفة: ${cost:.2f}\n💵 رصيدك: ${balance:.2f}\n\n<i>اضغط على الكود أو انسخه لإرساله للمستخدم.</i>",
        "activate_btn": "✅ تفعيل مفتاح",
        "mini_app_btn": "🚀 Nitro Dashboard",
        "send_activation_key": "📝 التفعيل يدوي: أولاً المفتاح، ثم IPv4 من الموقع.",
        "license_activated_ok": "✅ تم التفعيل!\n\n🔑 IP المرتبط: {ip}\n⏰ ينتهي: {date}\n\n🎮 يمكنك اللعب الآن عبر البروكسي.",
        "license_err_not_found": "❌ المفتاح غير صحيح أو غير موجود.",
        "license_err_used": "❌ هذا المفتاح مُفعَّل مسبقاً.",
        "license_err_banned": "❌ هذا المفتاح موقوف.",
        "license_err_format": "❌ الصيغة خطأ. استخدم: XXXX-XXXX-XXXX",
        "license_err_expired": "❌ المفتاح منتهي الصلاحية.",
        "license_err_ip_in_use": "❌ هذا الـ IP مرتبط بمفتاح آخر نشط.",
        "license_err_frozen": "❄️ المفتاح متجمد مؤقتًا. حاول لاحقًا.",
        "mod_safety": "🛡️ حالة أمان التعديلات",
        "mod_safety_panel": "🛡️ إدارة حالة أمان التعديلات\n\nاختر التعديل لتغيير حالته:",
        "mod_status_updated": "✅ تم تحديث حالة {mod_name}!\n\nالحالة الجديدة: {status}",
        "mark_safe": "✅ آمن (Safe)",
        "mark_not_safe": "⚠️ غير آمن (Ban Risk)",
        "page_info": "📄 صفحة {current} من {total}",
        "next_page": "التالي ➡️",
        "prev_page": "⬅️ السابق",
        "no_more_pages": "لا توجد صفحات أخرى"
    },
    "en": {
        "owner_panel": "👑 OWNER CONTROL PANEL\n\n📊 System Statistics:\n├ 👨‍✈️ Resellers: {admins}\n├ 🔑 Keys: {keys}\n├ 👥 Users: {users}\n└ 💰 Revenue: ${revenue:.2f}\n\n🎯 Select an option:",
        "admin_panel": "👨‍✈️ RESELLER PANEL\n\nWelcome back, {name}! 👋\n\n📊 Your Statistics:\n├ 💰 Wallet: ${wallet:.2f}\n├ 🔑 Keys: {keys}\n└ ✅ Active: {active}\n\n💵 Pricing:\n├ Day: ${day:.2f}\n├ Week: ${week:.2f}\n└ Month: ${month:.2f}\n\n🎯 Select an option:",
        "user_panel": "👋 Welcome {name}!\n\n🎮 Nitro Proxy - User Panel\n\n🎯 Select an option:",
        "add_reseller": "➕ Add Reseller",
        "manage_wallets": "💰 Manage Wallets",
        "ban_reseller": "🚫 Ban Reseller",
        "withdraw_money": "💸 Withdraw Money",
        "resellers_list": "📋 Resellers List",
        "statistics": "📊 Statistics",
        "all_keys": "🔑 All Keys",
        "freeze_all_keys": "❄️ Freeze All Keys",
        "unfreeze_all_keys": "✅ Unfreeze",
        "delete_all_keys": "🧹 Delete All Keys",
        "free_keys": "🎁 Free Keys",
        "freeze_already": "⏸️ Keys are already frozen.",
        "freeze_started": "⏸️ All keys frozen. Time is paused until unfreeze.",
        "unfreeze_not_active": "✅ Not frozen right now.",
        "unfreeze_done": "✅ Unfrozen. Added {seconds} seconds.",
        "confirm_delete_all_keys": "⚠️ Confirm delete ALL keys! This removes codes and IP subscriptions.",
        "yes_confirm": "✅ Yes",
        "no_cancel": "❌ Cancel",
        "delete_cancelled": "❌ Delete cancelled.",
        "delete_done": "🧹 All keys deleted successfully.",
        "send_freekey_count": "🎁 Enter number of free keys to generate:",
        "send_freekey_days": "⏰ Enter duration (days) for each free key.\nKeys count: {count}",
        "freekey_count_too_large": "❌ Too many keys. Limit is 200.",
        "free_keys_done": "✅ Generated {count} free keys for {days} days. Sending txt file.",
        "add_key": "➕ Add Key",
        "my_keys": "🔑 My Keys",
        "extend_key": "⏰ Extend Key",
        "ban_key": "🚫 Ban Key",
        "wallet_info": "💰 Wallet Info",
        "language": "🌐 Language",
        "check_sub": "📊 Check Subscription",
        "get_ip": "📖 How to find my IP",
        "ip_tutorial": "📖 How to find your public IPv4:\n\n1) Open Safari on your iPhone.\n2) Visit:\n{url}\n3) Copy the IPv4 shown (e.g. 12.34.56.78).\n4) Don’t use VPN while copying.\n\n⚠️ Use the same Wi‑Fi where you set the proxy.",
        "ask_send_ip_sub": "📊 To check subscription:\n\nFollow the steps above, then send your IPv4 here as one message.",
        "ask_send_key_first": "✅ Activate key — step 1 of 2\n\nSend your key in this format:\nXXXX-XXXX-XXXX",
        "ask_send_ip_activate": "✅ Step 2 of 2\n\nSend the public IPv4 you copied from the site.",
        "invalid_ip": "❌ Invalid IP. Send IPv4 like: 1.2.3.4",
        "back": "🔙 Back",
        "support": "💬 Support",
        "unauthorized": "❌ Unauthorized access",
        "contact_support": "💬 Contact: {support}",
        "send_admin_id": "📝 Send the Telegram ID of the new reseller:",
        "admin_added": "✅ Reseller added successfully!\n\nID: {aid}\nWallet: $0.00",
        "admin_added_rich": "✅ Reseller added\n\n🆔 <b>Telegram ID (tap to copy):</b>\n<code>{aid}</code>\n\n🔗 <a href=\"tg://user?id={aid}\">Open chat with reseller</a>\n\nUse the button below to add balance.",
        "wallet_quick": "💰 Add balance for this reseller",
        "owner_section_codes": "📋 <b>License codes</b>",
        "owner_section_ips": "🌐 <b>Active IP subscriptions</b>",
        "no_license_codes": "<i>No codes yet</i>",
        "no_active_ips": "<i>No active IP subscriptions</i>",
        "send_amount": "💵 Send the amount to add (in USD):",
        "wallet_added": "✅ Added ${amount:.2f} to wallet!\n\nNew balance: ${balance:.2f}",
        "invalid_format": "❌ Invalid format! Try again",
        "no_resellers": "❌ No resellers found",
        "select_reseller_ban": "🚫 Select reseller to ban:",
        "reseller_banned": "🚫 RESELLER BANNED!\n\n👤 ID: {aid}\n\n✅ Account deactivated",
        "insufficient_balance": "❌ Insufficient balance!\n\n💰 Your wallet: ${wallet:.2f}\n💵 Required: ${required:.2f}\n\n💬 Contact owner: {support}",
        "send_ip": "📝 Send the IP address for the new key:",
        "select_duration": "⏰ SELECT DURATION\n\n🔑 IP: {ip}\n💰 Your wallet: ${wallet:.2f}\n\nSelect duration:",
        "key_added": "✅ KEY ADDED!\n\n🔑 IP: {ip}\n📅 Duration: {days} days\n⏰ Expires: {date}\n💰 Cost: ${cost:.2f}\n💵 New balance: ${balance:.2f}",
        "no_keys": "❌ No keys found",
        "select_key_extend": "🔑 Select key to extend:",
        "select_key_ban": "🔑 Select key to ban:",
        "key_extended": "✅ KEY EXTENDED!\n\n🔑 IP: {ip}\n📅 Duration: {days} days\n⏰ Expires: {date}\n💰 Cost: ${cost:.2f}\n💵 New balance: ${balance:.2f}",
        "key_banned": "🚫 KEY BANNED!\n\n🔑 IP: {ip}\n\n✅ Key deactivated",
        "sub_active": "✅ SUBSCRIPTION ACTIVE!\n\n🔑 Your IP: {ip}\n⏰ Expires: {date}\n📅 Remaining: {days}d {hours}h\n\n🎮 Enjoy Nitro Proxy!",
        "sub_frozen_notice": "❄️ SYSTEM IS FROZEN (MAINTENANCE MODE).\n\n⏸️ Your key is temporarily paused and cannot be used now.\n✅ Your subscription time is preserved and will not decrease during freeze.\n\n🔑 IP: {ip}",
        "sub_inactive": "❌ NO ACTIVE SUBSCRIPTION\n\n🔑 Your IP: {ip}\n\n💬 Contact a reseller to activate your subscription",
        "your_ip": "🌐 YOUR IP ADDRESS\n\n🔑 IP: {ip}\n\n💡 Send this IP to your reseller to activate your subscription",
        "day_btn": "📅 Day (${price:.2f})",
        "week_btn": "📅 Week (${price:.2f})",
        "month_btn": "📅 Month (${price:.2f})",
        "cancel": "❌ Cancel",
        "select_key_manage": "🔑 Select key to manage:",
        "key_info": "🔑 Key Information\n\n📍 IP: {ip}\n👤 Reseller: {admin}\n📅 Expires: {date}\n⏰ Remaining: {days}d {hours}h\n\n🎯 Select action:",
        "delete_key": "🗑️ Delete",
        "extend_key_owner": "⏰ Extend",
        "key_deleted": "🗑️ Key deleted!\n\n🔑 IP: {ip}",
        "select_extend_duration": "⏰ Select extension duration\n\n🔑 IP: {ip}",
        "key_extended_owner": "✅ Key extended!\n\n🔑 IP: {ip}\n📅 Added duration: {days} days\n⏰ Now expires: {date}",
        "select_reseller_withdraw": "💸 Select reseller to withdraw money:",
        "send_withdraw_amount": "💸 Send the amount to withdraw (in USD):",
        "money_withdrawn": "✅ Withdrawn ${amount:.2f} from wallet!\n\nNew balance: ${balance:.2f}",
        "insufficient_balance_withdraw": "❌ Insufficient balance to withdraw!\n\n💰 Reseller balance: ${wallet:.2f}\n💵 Requested amount: ${amount:.2f}",
        "gen_license_btn": "🎫 Generate license key",
        "gen_select_duration": "⏰ Choose key duration\n\n💰 Your wallet: ${wallet:.2f}",
        "gen_key_created": "✅ License key created\n\n🔑 <b>Copy this code:</b>\n<code>{key}</code>\n\n📅 Duration: {days} days\n💰 Cost: ${cost:.2f}\n💵 Your balance: ${balance:.2f}\n\n<i>Tap the code or copy to send to the user.</i>",
        "activate_btn": "✅ Activate key",
        "mini_app_btn": "🚀 Nitro Dashboard",
        "send_activation_key": "📝 Manual activation: key first, then IPv4 from the site.",
        "license_activated_ok": "✅ Activated!\n\n🔑 Bound IP: {ip}\n⏰ Expires: {date}\n\n🎮 You can use the proxy now.",
        "license_err_not_found": "❌ Invalid or unknown key.",
        "license_err_used": "❌ This key was already activated.",
        "license_err_banned": "❌ This key is disabled.",
        "license_err_format": "❌ Bad format. Use: XXXX-XXXX-XXXX",
        "license_err_expired": "❌ This key is expired.",
        "license_err_ip_in_use": "❌ This IP is already bound to another active key.",
        "license_err_frozen": "❄️ This key is frozen. Please try again later.",
        "mod_safety": "🛡️ Mod Safety Status",
        "mod_safety_panel": "🛡️ Manage Modification Safety Status\n\nSelect modification to change status:",
        "mod_status_updated": "✅ Updated {mod_name} status!\n\nNew status: {status}",
        "mark_safe": "✅ Safe",
        "mark_not_safe": "⚠️ Not Safe (Ban Risk)",
        "page_info": "📄 Page {current} of {total}",
        "next_page": "Next ➡️",
        "prev_page": "⬅️ Previous",
        "no_more_pages": "No more pages"
    },
    "ru": {
        "owner_panel": "👑 ПАНЕЛЬ ВЛАДЕЛЬЦА\n\n📊 Статистика системы:\n├ 👨‍✈️ Реселлеров: {admins}\n├ 🔑 Ключей: {keys}\n├ 👥 Пользователей: {users}\n└ 💰 Доход: ${revenue:.2f}\n\n🎯 Выберите опцию:",
        "admin_panel": "👨‍✈️ ПАНЕЛЬ РЕСЕЛЛЕРА\n\nДобро пожаловать, {name}! 👋\n\n📊 Ваша статистика:\n├ 💰 Кошелек: ${wallet:.2f}\n├ 🔑 Ключей: {keys}\n└ ✅ Активных: {active}\n\n💵 Цены:\n├ День: ${day:.2f}\n├ Неделя: ${week:.2f}\n└ Месяц: ${month:.2f}\n\n🎯 Выберите опцию:",
        "user_panel": "👋 Добро пожаловать, {name}!\n\n🎮 Nitro Proxy - Панель пользователя\n\n🎯 Выберите опцию:",
        "add_reseller": "➕ Добавить реселлера",
        "manage_wallets": "💰 Управление кошельками",
        "ban_reseller": "🚫 Заблокировать реселлера",
        "withdraw_money": "💸 Снять деньги",
        "resellers_list": "📋 Список реселлеров",
        "statistics": "📊 Статистика",
        "all_keys": "🔑 Все ключи",
        "freeze_all_keys": "❄️ Заморозить ключи",
        "unfreeze_all_keys": "✅ Разморозить",
        "delete_all_keys": "🧹 Удалить все ключи",
        "free_keys": "🎁 Бесплатные ключи",
        "freeze_already": "⏸️ Ключи уже заморожены.",
        "freeze_started": "⏸️ Все ключи заморожены. Время приостановлено до разморозки.",
        "unfreeze_not_active": "✅ Сейчас не заморожено.",
        "unfreeze_done": "✅ Разморозка выполнена. Добавлено {seconds} секунд.",
        "confirm_delete_all_keys": "⚠️ Подтвердите удаление ВСЕХ ключей! Это удалит коды и подписки IP.",
        "yes_confirm": "✅ Да",
        "no_cancel": "❌ Нет",
        "delete_cancelled": "❌ Удаление отменено.",
        "delete_done": "🧹 Все ключи удалены успешно.",
        "send_freekey_count": "🎁 Введите количество бесплатных ключей для генерации:",
        "send_freekey_days": "⏰ Введите срок (в днях) для каждого бесплатного ключа.\nКоличество ключей: {count}",
        "freekey_count_too_large": "❌ Слишком много ключей. Лимит 200.",
        "free_keys_done": "✅ Сгенерировано {count} бесплатных ключей на {days} дней. Отправляю txt файл.",
        "add_key": "➕ Добавить ключ",
        "my_keys": "🔑 Мои ключи",
        "extend_key": "⏰ Продлить ключ",
        "ban_key": "🚫 Заблокировать ключ",
        "wallet_info": "💰 Информация о кошельке",
        "language": "🌐 Язык",
        "check_sub": "📊 Проверить подписку",
        "get_ip": "📖 Как узнать IP",
        "ip_tutorial": "📖 Как узнать публичный IPv4:\n\n1) Откройте Safari на iPhone.\n2) Зайдите:\n{url}\n3) Скопируйте IPv4 (например 12.34.56.78).\n4) Без VPN при копировании.\n\n⚠️ Та же Wi‑Fi, где настроен прокси.",
        "ask_send_ip_sub": "📊 Проверка подписки:\n\nСледуйте шагам выше, затем отправьте IPv4 одним сообщением.",
        "ask_send_key_first": "✅ Активация ключа — шаг 1 из 2\n\nОтправьте ключ:\nXXXX-XXXX-XXXX",
        "ask_send_ip_activate": "✅ Шаг 2 из 2\n\nОтправьте публичный IPv4 с сайта.",
        "invalid_ip": "❌ Неверный IP. Формат: 1.2.3.4",
        "back": "🔙 Назад",
        "support": "💬 Поддержка",
        "unauthorized": "❌ Доступ запрещен",
        "contact_support": "💬 Контакт: {support}",
        "send_admin_id": "📝 Отправьте Telegram ID нового реселлера:",
        "admin_added": "✅ Реселлер успешно добавлен!\n\nID: {aid}\nКошелек: $0.00",
        "admin_added_rich": "✅ Реселлер добавлен\n\n🆔 <b>Telegram ID (копировать):</b>\n<code>{aid}</code>\n\n🔗 <a href=\"tg://user?id={aid}\">Открыть чат</a>\n\nКнопка ниже — пополнить баланс.",
        "wallet_quick": "💰 Пополнить баланс",
        "owner_section_codes": "📋 <b>Коды лицензий</b>",
        "owner_section_ips": "🌐 <b>Активные IP</b>",
        "no_license_codes": "<i>Кодов пока нет</i>",
        "no_active_ips": "<i>Нет активных IP</i>",
        "send_amount": "💵 Отправьте сумму для добавления (в USD):",
        "wallet_added": "✅ Добавлено ${amount:.2f} в кошелек!\n\nНовый баланс: ${balance:.2f}",
        "invalid_format": "❌ Неверный формат! Попробуйте снова",
        "no_resellers": "❌ Реселлеры не найдены",
        "select_reseller_ban": "🚫 Выберите реселлера для блокировки:",
        "reseller_banned": "🚫 РЕСЕЛЛЕР ЗАБЛОКИРОВАН!\n\n👤 ID: {aid}\n\n✅ Аккаунт деактивирован",
        "insufficient_balance": "❌ Недостаточно средств!\n\n💰 Ваш кошелек: ${wallet:.2f}\n💵 Требуется: ${required:.2f}\n\n💬 Свяжитесь с владельцем: {support}",
        "send_ip": "📝 Отправьте IP-адрес для нового ключа:",
        "select_duration": "⏰ ВЫБЕРИТЕ ДЛИТЕЛЬНОСТЬ\n\n🔑 IP: {ip}\n💰 Ваш кошелек: ${wallet:.2f}\n\nВыберите длительность:",
        "key_added": "✅ КЛЮЧ ДОБАВЛЕН!\n\n🔑 IP: {ip}\n📅 Длительность: {days} дней\n⏰ Истекает: {date}\n💰 Стоимость: ${cost:.2f}\n💵 Новый баланс: ${balance:.2f}",
        "no_keys": "❌ Ключи не найдены",
        "select_key_extend": "🔑 Выберите ключ для продления:",
        "select_key_ban": "🔑 Выберите ключ для блокировки:",
        "key_extended": "✅ КЛЮЧ ПРОДЛЕН!\n\n🔑 IP: {ip}\n📅 Длительность: {days} дней\n⏰ Истекает: {date}\n💰 Стоимость: ${cost:.2f}\n💵 Новый баланс: ${balance:.2f}",
        "key_banned": "🚫 КЛЮЧ ЗАБЛОКИРОВАН!\n\n🔑 IP: {ip}\n\n✅ Ключ деактивирован",
        "sub_active": "✅ ПОДПИСКА АКТИВНА!\n\n🔑 Ваш IP: {ip}\n⏰ Истекает: {date}\n📅 Осталось: {days}d {hours}h\n\n🎮 Наслаждайтесь Nitro Proxy!",
        "sub_frozen_notice": "❄️ СИСТЕМА ЗАМОРОЖЕНА (РЕЖИМ ОБСЛУЖИВАНИЯ).\n\n⏸️ Ключ временно приостановлен и сейчас не работает.\n✅ Время подписки сохранено и не уменьшается во время заморозки.\n\n🔑 IP: {ip}",
        "sub_inactive": "❌ НЕТ АКТИВНОЙ ПОДПИСКИ\n\n🔑 Ваш IP: {ip}\n\n💬 Свяжитесь с реселлером для активации подписки",
        "your_ip": "🌐 ВАШ IP-АДРЕС\n\n🔑 IP: {ip}\n\n💡 Отправьте этот IP реселлеру для активации подписки",
        "day_btn": "📅 День (${price:.2f})",
        "week_btn": "📅 Неделя (${price:.2f})",
        "month_btn": "📅 Месяц (${price:.2f})",
        "cancel": "❌ Отмена",
        "select_key_manage": "🔑 Выберите ключ для управления:",
        "key_info": "🔑 Информация о ключе\n\n📍 IP: {ip}\n👤 Реселлер: {admin}\n📅 Истекает: {date}\n⏰ Осталось: {days}d {hours}h\n\n🎯 Выберите действие:",
        "delete_key": "🗑️ Удалить",
        "extend_key_owner": "⏰ Продлить",
        "key_deleted": "🗑️ Ключ удален!\n\n🔑 IP: {ip}",
        "select_extend_duration": "⏰ Выберите длительность продления\n\n🔑 IP: {ip}",
        "key_extended_owner": "✅ Ключ продлен!\n\n🔑 IP: {ip}\n📅 Добавлено: {days} дней\n⏰ Теперь истекает: {date}",
        "select_reseller_withdraw": "💸 Выберите реселлера для снятия денег:",
        "send_withdraw_amount": "💸 Отправьте сумму для снятия (в USD):",
        "money_withdrawn": "✅ Снято ${amount:.2f} с кошелька!\n\nНовый баланс: ${balance:.2f}",
        "insufficient_balance_withdraw": "❌ Недостаточно средств для снятия!\n\n💰 Баланс реселлера: ${wallet:.2f}\n💵 Запрошенная сумма: ${amount:.2f}",
        "gen_license_btn": "🎫 Создать ключ",
        "gen_select_duration": "⏰ Выберите срок ключа\n\n💰 Кошелек: ${wallet:.2f}",
        "gen_key_created": "✅ Ключ создан\n\n🔑 <b>Скопируйте код:</b>\n<code>{key}</code>\n\n📅 Срок: {days} дн.\n💰 Стоимость: ${cost:.2f}\n💵 Баланс: ${balance:.2f}\n\n<i>Нажмите на код или скопируйте.</i>",
        "activate_btn": "✅ Активировать ключ",
        "mini_app_btn": "🚀 Nitro Dashboard",
        "send_activation_key": "📝 Активация вручную: сначала ключ, затем IPv4 с сайта.",
        "license_activated_ok": "✅ Активировано!\n\n🔑 IP: {ip}\n⏰ Истекает: {date}\n\n🎮 Можно играть через прокси.",
        "license_err_not_found": "❌ Неверный ключ.",
        "license_err_used": "❌ Ключ уже активирован.",
        "license_err_banned": "❌ Ключ отключен.",
        "license_err_format": "❌ Неверный формат. Нужно: XXXX-XXXX-XXXX",
        "license_err_expired": "❌ Срок действия ключа истек.",
        "license_err_ip_in_use": "❌ Этот IP уже привязан к другому активному ключу.",
        "license_err_frozen": "❄️ Ключ временно заморожен. Попробуйте позже.",
        "mod_safety": "🛡️ Статус безопасности модов",
        "mod_safety_panel": "🛡️ Управление статусом безопасности\n\nВыберите мод для изменения статуса:",
        "mod_status_updated": "✅ Статус {mod_name} обновлен!\n\nНовый статус: {status}",
        "mark_safe": "✅ Безопасно",
        "mark_not_safe": "⚠️ Небезопасно (риск бана)",
        "page_info": "📄 Страница {current} из {total}",
        "next_page": "Далее ➡️",
        "prev_page": "⬅️ Назад",
        "no_more_pages": "Больше нет страниц"
    }
}

# ═══════════════════════════════════════════════════════════════
# Helper Functions for Pagination
# ═══════════════════════════════════════════════════════════════

def paginate_list(items, page=1, per_page=KEYS_PER_PAGE):
    """Paginate a list of items"""
    total_items = len(items)
    total_pages = (total_items + per_page - 1) // per_page  # Ceiling division
    
    if page < 1:
        page = 1
    if page > total_pages and total_pages > 0:
        page = total_pages
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    return {
        'items': items[start_idx:end_idx],
        'page': page,
        'total_pages': total_pages,
        'total_items': total_items,
        'has_next': page < total_pages,
        'has_prev': page > 1
    }

def create_pagination_keyboard(callback_prefix, page, total_pages, back_callback, lang='en'):
    """Create pagination keyboard buttons"""
    kb = []
    
    # Navigation buttons
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(
            LANG[lang]["prev_page"],
            callback_data=f'{callback_prefix}_page_{page-1}'
        ))
    
    # Page info
    nav_row.append(InlineKeyboardButton(
        LANG[lang]["page_info"].format(current=page, total=total_pages),
        callback_data='page_info'
    ))
    
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(
            LANG[lang]["next_page"],
            callback_data=f'{callback_prefix}_page_{page+1}'
        ))
    
    if nav_row:
        kb.append(nav_row)
    
    # Back button
    kb.append([InlineKeyboardButton(LANG[lang]["back"], callback_data=back_callback)])
    
    return kb

# Database Management
def load_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    if not os.path.exists(DB_FILE):
        return {"admins": {str(OWNER_ID): {"role": "owner", "keys": [], "wallet": 0, "lang": "en", "banned": False}}, "keys": {}, "users": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_ips():
    if not os.path.exists(IPS_FILE):
        os.makedirs(os.path.dirname(IPS_FILE), exist_ok=True)
        return {}
    with open(IPS_FILE, "r") as f:
        return json.load(f)

def save_ips(data):
    with open(IPS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Freeze state (owner pause/resume for all keys)
FREEZE_STATE_FILE = os.path.join(os.path.dirname(IPS_FILE), "freeze_state.json")

def load_freeze_state():
    """
    Returns:
      {"frozen": bool, "frozen_at": float|None}
    """
    if not os.path.exists(FREEZE_STATE_FILE):
        return {"frozen": False, "frozen_at": None}
    try:
        with open(FREEZE_STATE_FILE, "r", encoding="utf-8") as f:
            st = json.load(f)
        if "frozen" not in st:
            st["frozen"] = False
        return st
    except Exception:
        # If state is corrupted, default to not frozen to avoid permanent lock.
        return {"frozen": False, "frozen_at": None}

def save_freeze_state(state: dict):
    os.makedirs(os.path.dirname(FREEZE_STATE_FILE), exist_ok=True)
    with open(FREEZE_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def parse_ipv4(s):
    """Validate and normalize IPv4 string; returns None if invalid."""
    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", (s or "").strip())
    if not m:
        return None
    parts = [int(m.group(i)) for i in range(1, 5)]
    if any(p > 255 for p in parts):
        return None
    return ".".join(str(p) for p in parts)

def _hash_ip(ip: str) -> str:
    return hashlib.md5((ip or "").encode("utf-8")).hexdigest()[:16]

def _ip_from_hash(h: str):
    for ip in load_ips().keys():
        if _hash_ip(ip) == h:
            return ip
    return None

def get_lang(user_id, db=None):
    if db is None:
        db = load_db()
    if str(user_id) in db.get('admins', {}):
        return db['admins'][str(user_id)].get('lang', 'en')
    if str(user_id) in db.get('users', {}):
        return db['users'][str(user_id)].get('lang', 'en')
    return 'en'

# ═══════════════════════════════════════════════════════════════
# 👑 OWNER BOT - Complete Control
# ═══════════════════════════════════════════════════════════════
async def owner_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text(LANG["en"]["unauthorized"])
        return
    
    db = load_db()
    lang = get_lang(OWNER_ID, db)
    admins = len([a for a in db['admins'].values() if a.get('role') == 'admin' and not a.get('banned', False)])
    keys = len(db['keys'])
    users = len(db['users'])
    revenue = sum(a.get('wallet', 0) for a in db['admins'].values() if a.get('role') == 'admin')
    freeze_state = load_freeze_state()
    
    msg = LANG[lang]["owner_panel"].format(admins=admins, keys=keys, users=users, revenue=revenue)
    
    kb = [
        [InlineKeyboardButton(LANG[lang]["add_reseller"], callback_data='o_add_admin')],
        [InlineKeyboardButton(LANG[lang]["manage_wallets"], callback_data='o_wallets'),
         InlineKeyboardButton(LANG[lang]["withdraw_money"], callback_data='o_withdraw')],
        [InlineKeyboardButton(LANG[lang]["ban_reseller"], callback_data='o_ban')],
        [InlineKeyboardButton(LANG[lang]["mod_safety"], callback_data='o_mod_safety')],
        [InlineKeyboardButton(LANG[lang]["all_keys"], callback_data='o_all_keys')],
        [InlineKeyboardButton(
            LANG[lang]["freeze_all_keys"] if not freeze_state.get("frozen", False) else LANG[lang]["unfreeze_all_keys"],
            callback_data='o_freeze_all' if not freeze_state.get("frozen", False) else 'o_unfreeze_all'
        )],
        [InlineKeyboardButton(LANG[lang]["delete_all_keys"], callback_data='o_delete_all_keys'),
         InlineKeyboardButton(LANG[lang]["free_keys"], callback_data='o_free_keys')],
        [InlineKeyboardButton(LANG[lang]["resellers_list"], callback_data='o_list'),
         InlineKeyboardButton(LANG[lang]["statistics"], callback_data='o_stats')],
        [InlineKeyboardButton(LANG[lang]["language"], callback_data='o_lang')]
    ]
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def owner_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = load_db()
    lang = get_lang(OWNER_ID, db)
    
    if q.data == 'o_add_admin':
        context.user_data['waiting_for'] = 'admin_id'
        await q.edit_message_text(LANG[lang]["send_admin_id"])
    
    elif q.data == 'o_wallets':
        admins = [(aid, info) for aid, info in db['admins'].items() if info.get('role') == 'admin' and not info.get('banned', False)]
        
        if not admins:
            msg = LANG[lang]["no_resellers"]
            kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')]]
        else:
            msg = "💰 " + ("إدارة المحافظ" if lang == "ar" else "WALLET MANAGEMENT" if lang == "en" else "УПРАВЛЕНИЕ КОШЕЛЬКАМИ") + "\n\n"
            kb = []
            for aid, info in admins:
                wallet = info.get('wallet', 0)
                name = info.get('name', f'Admin_{aid[:4]}')
                msg += f"├ {name}: ${wallet:.2f}\n"
                kb.append([InlineKeyboardButton(f"💵 {name}", callback_data=f'addw_{aid}')])
            kb.append([InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')])
        
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data.startswith('addw_'):
        aid = q.data[5:]
        context.user_data['wallet_admin'] = aid
        context.user_data['waiting_for'] = 'wallet_amount'
        await q.edit_message_text(LANG[lang]["send_amount"])
    
    elif q.data == 'o_withdraw':
        admins = [(aid, info) for aid, info in db['admins'].items() if info.get('role') == 'admin' and not info.get('banned', False)]
        
        if not admins:
            msg = LANG[lang]["no_resellers"]
            kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')]]
        else:
            msg = LANG[lang]["select_reseller_withdraw"]
            kb = [[InlineKeyboardButton(f"{info.get('name', f'Admin_{aid[:4]}')} - ${info.get('wallet', 0):.2f}", callback_data=f'withd_{aid}')] for aid, info in admins[:10]]
            kb.append([InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')])
        
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data.startswith('withd_'):
        aid = q.data[6:]
        context.user_data['withdraw_admin'] = aid
        context.user_data['waiting_for'] = 'withdraw_amount'
        await q.edit_message_text(LANG[lang]["send_withdraw_amount"])
    
    elif q.data == 'o_ban':
        admins = [(aid, info) for aid, info in db['admins'].items() if info.get('role') == 'admin' and not info.get('banned', False)]
        
        if not admins:
            msg = LANG[lang]["no_resellers"]
            kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')]]
        else:
            msg = LANG[lang]["select_reseller_ban"]
            kb = [[InlineKeyboardButton(f"{info.get('name', f'Admin_{aid[:4]}')} - {aid[:8]}", callback_data=f'banadm_{aid}')] for aid, info in admins[:10]]
            kb.append([InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')])
        
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data.startswith('banadm_'):
        aid = q.data[7:]
        if aid in db['admins']:
            db['admins'][aid]['banned'] = True
            save_db(db)
        
        msg = LANG[lang]["reseller_banned"].format(aid=aid)
        kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'o_list':
        admins = [(aid, info) for aid, info in db['admins'].items() if info.get('role') == 'admin']
        
        if not admins:
            msg = LANG[lang]["no_resellers"]
        else:
            msg = "📋 " + ("قائمة الموزعين" if lang == "ar" else "RESELLERS LIST" if lang == "en" else "СПИСОК РЕСЕЛЛЕРОВ") + "\n\n"
            for aid, info in admins:
                name = info.get('name', f'Admin_{aid[:4]}')
                keys = len(info.get('keys', []))
                wallet = info.get('wallet', 0)
                status = "🚫" if info.get('banned', False) else "✅"
                msg += f"{status} {name}\n├ ID: {aid}\n├ Keys: {keys}\n└ Wallet: ${wallet:.2f}\n\n"
        
        kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'o_freeze_all':
        st = load_freeze_state()
        if st.get("frozen", False):
            msg = LANG[lang]["freeze_already"]
        else:
            st["frozen"] = True
            st["frozen_at"] = time.time()
            save_freeze_state(st)
            msg = LANG[lang]["freeze_started"]
        kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'o_unfreeze_all':
        st = load_freeze_state()
        if not st.get("frozen", False):
            msg = LANG[lang]["unfreeze_not_active"]
        else:
            frozen_at = st.get("frozen_at") or time.time()
            elapsed = max(0, time.time() - float(frozen_at))
            ips = load_ips()
            # Pause time: extend all subscriptions that were active at freeze start.
            for ip, rec in ips.items():
                exp = rec.get("expires_at", 0)
                if exp and exp > frozen_at:
                    rec["expires_at"] = exp + elapsed
            save_ips(ips)
            st["frozen"] = False
            st["frozen_at"] = None
            save_freeze_state(st)
            msg = LANG[lang]["unfreeze_done"].format(seconds=int(elapsed))
        kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'o_delete_all_keys':
        kb = [[
            InlineKeyboardButton(LANG[lang]["yes_confirm"], callback_data='o_delete_all_confirm'),
            InlineKeyboardButton(LANG[lang]["no_cancel"], callback_data='o_delete_all_cancel')
        ]]
        await q.edit_message_text(LANG[lang]["confirm_delete_all_keys"], reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'o_delete_all_cancel':
        await q.edit_message_text(LANG[lang]["delete_cancelled"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')]]))
    
    elif q.data == 'o_delete_all_confirm':
        # Destructive operation: remove all license codes + all active IP subscriptions.
        save_license_keys({})
        save_ips({})
        db = load_db()
        for aid, info in db.get("admins", {}).items():
            if isinstance(info, dict):
                info["keys"] = []
        save_db(db)
        # Reset freeze state as well.
        save_freeze_state({"frozen": False, "frozen_at": None})
        await q.edit_message_text(LANG[lang]["delete_done"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')]]))
    
    elif q.data == 'o_free_keys':
        context.user_data["waiting_for"] = "freekey_count"
        await q.edit_message_text(LANG[lang]["send_freekey_count"])
    
    elif q.data == 'o_mod_safety':
        mods = load_mod_safety_status()
        msg = LANG[lang]["mod_safety_panel"]
        kb = []
        
        for port in sorted(mods.keys(), reverse=True):
            mod = mods[port]
            status_emoji = "✅" if mod["status"] == "safe" else "⚠️"
            kb.append([InlineKeyboardButton(
                f"{status_emoji} {mod['name']} (Port {port})",
                callback_data=f'mod_{port}'
            )])
        
        kb.append([InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')])
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data.startswith('mod_') and not q.data.startswith('modset_'):
        port = q.data[4:]
        mods = load_mod_safety_status()
        
        if port in mods:
            mod = mods[port]
            current_status = "✅ Safe" if mod["status"] == "safe" else "⚠️ Not Safe"
            msg = f"🛡️ {mod['name']} (Port {port})\n\n"
            msg += f"Current Status: {current_status}\n\n"
            msg += "Select new status:"
            
            kb = [
                [InlineKeyboardButton(LANG[lang]["mark_safe"], callback_data=f'modset_{port}_safe')],
                [InlineKeyboardButton(LANG[lang]["mark_not_safe"], callback_data=f'modset_{port}_not_safe')],
                [InlineKeyboardButton(LANG[lang]["back"], callback_data='o_mod_safety')]
            ]
            await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data.startswith('modset_'):
        parts = q.data.split('_')
        port = parts[1]
        new_status = parts[2]
        
        mods = load_mod_safety_status()
        if port in mods:
            update_mod_status(port, new_status, OWNER_ID)
            mods = load_mod_safety_status()
            mod = mods[port]
            
            status_text = "✅ Safe" if new_status == "safe" else "⚠️ Not Safe (Ban Risk)"
            msg = LANG[lang]["mod_status_updated"].format(
                mod_name=mod["name"],
                status=status_text
            )
            
            kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_mod_safety')]]
            await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'o_all_keys' or q.data.startswith('o_all_keys_page_'):
        # Extract page number
        page = 1
        if q.data.startswith('o_all_keys_page_'):
            try:
                page = int(q.data.split('_')[-1])
            except:
                page = 1
        
        lkeys = load_license_keys()
        all_keys = [(k, rec) for k, rec in lkeys.items() if rec.get("status") in ("pending", "active")]
        
        if not all_keys:
            msg = LANG[lang]["no_keys"]
            kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')]]
            await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
            return
        
        # Paginate keys
        paginated = paginate_list(all_keys, page, KEYS_PER_PAGE)
        
        msg = "🔑 " + ("جميع المفاتيح" if lang == "ar" else "ALL KEYS" if lang == "en" else "ВСЕ КЛЮЧИ") + "\n\n"
        msg += LANG[lang]["page_info"].format(current=paginated['page'], total=paginated['total_pages']) + "\n"
        msg += f"📊 Total: {paginated['total_items']} keys\n\n"
        
        for key, rec in paginated['items']:
            status_emoji = "✅" if rec.get("status") == "active" else "⏳"
            admin_id = rec.get("admin", "Unknown")
            
            if rec.get("status") == "active":
                ip = rec.get("activated_ip", "N/A")
                exp = rec.get("expires_at", 0)
                if exp > time.time():
                    days = int((exp - time.time()) / 86400)
                    msg += f"{status_emoji} <code>{key}</code>\n"
                    msg += f"   IP: {ip} | Admin: {admin_id}\n"
                    msg += f"   Expires: {days}d\n\n"
                else:
                    msg += f"❌ <code>{key}</code> (Expired)\n\n"
            else:
                msg += f"{status_emoji} <code>{key}</code> (Pending)\n"
                msg += f"   Admin: {admin_id}\n\n"
        
        # Create keyboard with pagination
        kb = []
        for key, rec in paginated['items']:
            kb.append([InlineKeyboardButton(
                f"🔑 {key[:13]}...",
                callback_data=f'okey_{key}'
            )])
        
        # Add pagination buttons
        kb.extend(create_pagination_keyboard('o_all_keys', paginated['page'], paginated['total_pages'], 'o_back', lang))
        
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    
    elif q.data.startswith('okey_'):
        key = q.data[5:]
        lkeys = load_license_keys()
        if key in lkeys:
            rec = lkeys[key]
            admin_id = rec.get("admin", "Unknown")
            admin_name = db['admins'].get(str(admin_id), {}).get('name', f'Admin_{str(admin_id)[:4]}')
            
            if rec.get("status") == "active":
                ip = rec.get("activated_ip", "N/A")
                exp = rec.get("expires_at", 0)
                days = int((exp - time.time()) / 86400)
                hours = int(((exp - time.time()) % 86400) / 3600)
                date_str = datetime.fromtimestamp(exp).strftime('%Y-%m-%d %H:%M')
                msg = f"🔑 Key: <code>{key}</code>\n\n"
                msg += f"📍 IP: {ip}\n"
                msg += f"👤 Admin: {admin_name}\n"
                msg += f"📅 Expires: {date_str}\n"
                msg += f"⏰ Remaining: {days}d {hours}h\n"
            else:
                msg = f"🔑 Key: <code>{key}</code>\n\n"
                msg += f"Status: Pending\n"
                msg += f"👤 Admin: {admin_name}\n"
            
            kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_all_keys')]]
            await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        else:
            await q.edit_message_text(LANG[lang]["no_keys"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_all_keys')]]))
    
    elif q.data == 'page_info':
        await q.answer(LANG[lang].get("page_info", "Page info"), show_alert=False)
    
    elif q.data.startswith('oip_'):
        h = q.data[4:]
        ip = _ip_from_hash(h)
        ips = load_ips()
        if ip and ip in ips:
            data = ips[ip]
            admin_id = data.get('admin', 'Unknown')
            admin_name = db['admins'].get(str(admin_id), {}).get('name', f'Admin_{str(admin_id)[:4]}')
            exp = data.get('expires_at', 0)
            days = int((exp - time.time()) / 86400)
            hours = int(((exp - time.time()) % 86400) / 3600)
            date_str = datetime.fromtimestamp(exp).strftime('%Y-%m-%d %H:%M')
            msg = LANG[lang]["key_info"].format(ip=ip, admin=admin_name, date=date_str, days=days, hours=hours)
            kb = [
                [InlineKeyboardButton(LANG[lang]["extend_key_owner"], callback_data=f'oext_{h}')],
                [InlineKeyboardButton(LANG[lang]["delete_key"], callback_data=f'odel_{h}')],
                [InlineKeyboardButton(LANG[lang]["back"], callback_data='o_all_keys')]
            ]
            await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await q.edit_message_text(LANG[lang]["no_keys"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_all_keys')]]))
    
    elif q.data.startswith('oext_'):
        h = q.data[5:]
        ip = _ip_from_hash(h)
        if not ip:
            await q.edit_message_text(LANG[lang]["no_keys"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_all_keys')]]))
            return
        context.user_data['owner_extend_ip'] = ip
        msg = LANG[lang]["select_extend_duration"].format(ip=ip)
        kb = [
            [InlineKeyboardButton(LANG[lang]["day_btn"].format(price=PRICING['day']), callback_data='odur_day')],
            [InlineKeyboardButton(LANG[lang]["week_btn"].format(price=PRICING['week']), callback_data='odur_week')],
            [InlineKeyboardButton(LANG[lang]["month_btn"].format(price=PRICING['month']), callback_data='odur_month')],
            [InlineKeyboardButton(LANG[lang]["back"], callback_data=f'oip_{h}')]
        ]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data.startswith('odur_'):
        duration_type = q.data[5:]
        ip = context.user_data.get('owner_extend_ip')
        days = DURATIONS[duration_type]
        
        ips = load_ips()
        if ip in ips:
            ips[ip]['expires_at'] += days * 86400
            save_ips(ips)
            
            exp_date = datetime.fromtimestamp(ips[ip]['expires_at']).strftime('%Y-%m-%d %H:%M')
            
            msg = LANG[lang]["key_extended_owner"].format(ip=ip, days=days, date=exp_date)
            kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_all_keys')]]
            await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await q.edit_message_text(LANG[lang]["no_keys"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_all_keys')]]))
    
    elif q.data.startswith('odel_'):
        h = q.data[5:]
        ip = _ip_from_hash(h)
        ips = load_ips()
        if ip and ip in ips:
            del ips[ip]
            save_ips(ips)
            msg = LANG[lang]["key_deleted"].format(ip=ip)
            kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_all_keys')]]
            await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await q.edit_message_text(LANG[lang]["no_keys"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_all_keys')]]))
    
    elif q.data == 'o_stats':
        ips = load_ips()
        active = sum(1 for ip in ips.values() if ip.get('expires_at', 0) > time.time())
        revenue = sum(a.get('wallet', 0) for a in db['admins'].values() if a.get('role') == 'admin')
        
        msg = "📊 " + ("إحصائيات مفصلة" if lang == "ar" else "DETAILED STATISTICS" if lang == "en" else "ПОДРОБНАЯ СТАТИСТИКА") + "\n\n"
        msg += f"├ 👨‍✈️ " + ("الموزعين" if lang == "ar" else "Resellers" if lang == "en" else "Реселлеров") + f": {len([a for a in db['admins'].values() if a.get('role')=='admin'])}\n"
        msg += f"├ 🔑 " + ("المفاتيح" if lang == "ar" else "Keys" if lang == "en" else "Ключей") + f": {len(db['keys'])}\n"
        msg += f"├ ✅ " + ("نشطة" if lang == "ar" else "Active" if lang == "en" else "Активных") + f": {active}\n"
        msg += f"├ ❌ " + ("منتهية" if lang == "ar" else "Expired" if lang == "en" else "Истекших") + f": {len(ips) - active}\n"
        msg += f"├ 👥 " + ("المستخدمين" if lang == "ar" else "Users" if lang == "en" else "Пользователей") + f": {len(db['users'])}\n"
        msg += f"└ 💰 " + ("الإيرادات" if lang == "ar" else "Revenue" if lang == "en" else "Доход") + f": ${revenue:.2f}\n"
        
        kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'o_lang':
        msg = LANG[lang]["language"]
        kb = [
            [InlineKeyboardButton("العربية 🇸🇦", callback_data='olang_ar')],
            [InlineKeyboardButton("English 🇺🇸", callback_data='olang_en')],
            [InlineKeyboardButton("Русский 🇷🇺", callback_data='olang_ru')],
            [InlineKeyboardButton(LANG[lang]["back"], callback_data='o_back')]
        ]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data.startswith('olang_'):
        new_lang = q.data[6:]
        db['admins'][str(OWNER_ID)]['lang'] = new_lang
        save_db(db)
        
        # Recreate the main panel with new language
        admins = len([a for a in db['admins'].values() if a.get('role') == 'admin' and not a.get('banned', False)])
        keys = len(db['keys'])
        users = len(db['users'])
        revenue = sum(a.get('wallet', 0) for a in db['admins'].values() if a.get('role') == 'admin')
        
        msg = LANG[new_lang]["owner_panel"].format(admins=admins, keys=keys, users=users, revenue=revenue)
        
        freeze_state = load_freeze_state()
        kb = [
            [InlineKeyboardButton(LANG[new_lang]["add_reseller"], callback_data='o_add_admin')],
            [InlineKeyboardButton(LANG[new_lang]["manage_wallets"], callback_data='o_wallets'),
             InlineKeyboardButton(LANG[new_lang]["withdraw_money"], callback_data='o_withdraw')],
            [InlineKeyboardButton(LANG[new_lang]["ban_reseller"], callback_data='o_ban')],
            [InlineKeyboardButton(LANG[new_lang]["mod_safety"], callback_data='o_mod_safety')],
            [InlineKeyboardButton(LANG[new_lang]["all_keys"], callback_data='o_all_keys')],
            [InlineKeyboardButton(
                LANG[new_lang]["freeze_all_keys"] if not freeze_state.get("frozen", False) else LANG[new_lang]["unfreeze_all_keys"],
                callback_data='o_freeze_all' if not freeze_state.get("frozen", False) else 'o_unfreeze_all'
            )],
            [InlineKeyboardButton(LANG[new_lang]["delete_all_keys"], callback_data='o_delete_all_keys'),
             InlineKeyboardButton(LANG[new_lang]["free_keys"], callback_data='o_free_keys')],
            [InlineKeyboardButton(LANG[new_lang]["resellers_list"], callback_data='o_list'),
             InlineKeyboardButton(LANG[new_lang]["statistics"], callback_data='o_stats')],
            [InlineKeyboardButton(LANG[new_lang]["language"], callback_data='o_lang')]
        ]
        
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'o_back':
        # Recreate main panel
        admins = len([a for a in db['admins'].values() if a.get('role') == 'admin' and not a.get('banned', False)])
        keys = len(db['keys'])
        users = len(db['users'])
        revenue = sum(a.get('wallet', 0) for a in db['admins'].values() if a.get('role') == 'admin')
        
        msg = LANG[lang]["owner_panel"].format(admins=admins, keys=keys, users=users, revenue=revenue)
        
        freeze_state = load_freeze_state()
        kb = [
            [InlineKeyboardButton(LANG[lang]["add_reseller"], callback_data='o_add_admin')],
            [InlineKeyboardButton(LANG[lang]["manage_wallets"], callback_data='o_wallets'),
             InlineKeyboardButton(LANG[lang]["withdraw_money"], callback_data='o_withdraw')],
            [InlineKeyboardButton(LANG[lang]["ban_reseller"], callback_data='o_ban')],
            [InlineKeyboardButton(LANG[lang]["mod_safety"], callback_data='o_mod_safety')],
            [InlineKeyboardButton(LANG[lang]["all_keys"], callback_data='o_all_keys')],
            [InlineKeyboardButton(
                LANG[lang]["freeze_all_keys"] if not freeze_state.get("frozen", False) else LANG[lang]["unfreeze_all_keys"],
                callback_data='o_freeze_all' if not freeze_state.get("frozen", False) else 'o_unfreeze_all'
            )],
            [InlineKeyboardButton(LANG[lang]["delete_all_keys"], callback_data='o_delete_all_keys'),
             InlineKeyboardButton(LANG[lang]["free_keys"], callback_data='o_free_keys')],
            [InlineKeyboardButton(LANG[lang]["resellers_list"], callback_data='o_list'),
             InlineKeyboardButton(LANG[lang]["statistics"], callback_data='o_stats')],
            [InlineKeyboardButton(LANG[lang]["language"], callback_data='o_lang')]
        ]
        
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def owner_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for') != 'admin_id':
        return
    
    try:
        aid = str(int(update.message.text.strip()))
        db = load_db()
        lang = get_lang(OWNER_ID, db)
        db['admins'][aid] = {"role": "admin", "keys": [], "wallet": 0.0, "name": f"Admin_{aid[:4]}", "lang": "en", "banned": False}
        save_db(db)
        msg = LANG[lang]["admin_added_rich"].format(aid=aid)
        kb = [[InlineKeyboardButton(LANG[lang]["wallet_quick"], callback_data=f"addw_{aid}")]]
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))
        context.user_data['waiting_for'] = None
    except:
        db = load_db()
        lang = get_lang(OWNER_ID, db)
        await update.message.reply_text(LANG[lang]["invalid_format"])

async def owner_add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for') != 'wallet_amount':
        return
    
    try:
        amount = float(update.message.text.strip())
        aid = context.user_data.get('wallet_admin')
        db = load_db()
        lang = get_lang(OWNER_ID, db)
        
        if aid in db['admins']:
            old_balance = db['admins'][aid].get('wallet', 0)
            new_balance = old_balance + amount
            db['admins'][aid]['wallet'] = new_balance
            save_db(db)
            
            # إرسال رسالة للأونر
            await update.message.reply_text(LANG[lang]["wallet_added"].format(amount=amount, balance=new_balance))
            
            # إرسال إشعار للموزع
            try:
                admin_lang = db['admins'][aid].get('lang', 'en')
                admin_name = db['admins'][aid].get('name', f'Admin_{aid[:4]}')
                
                notification_msg = {
                    'ar': f"💰 تم إضافة رصيد لحسابك!\n\n✅ المبلغ المضاف: ${amount:.2f}\n📊 الرصيد السابق: ${old_balance:.2f}\n💵 الرصيد الجديد: ${new_balance:.2f}\n\n🎉 يمكنك الآن إضافة المزيد من المفاتيح!",
                    'en': f"💰 Balance added to your account!\n\n✅ Amount added: ${amount:.2f}\n📊 Previous balance: ${old_balance:.2f}\n💵 New balance: ${new_balance:.2f}\n\n🎉 You can now add more keys!",
                    'ru': f"💰 Баланс добавлен на ваш счет!\n\n✅ Добавлено: ${amount:.2f}\n📊 Предыдущий баланс: ${old_balance:.2f}\n💵 Новый баланс: ${new_balance:.2f}\n\n🎉 Теперь вы можете добавить больше ключей!"
                }
                
                await context.bot.send_message(
                    chat_id=int(aid),
                    text=notification_msg.get(admin_lang, notification_msg['en'])
                )
            except Exception as e:
                print(f"Failed to send notification to admin {aid}: {e}")
        else:
            await update.message.reply_text(LANG[lang]["no_resellers"])
        
        context.user_data['waiting_for'] = None
    except:
        db = load_db()
        lang = get_lang(OWNER_ID, db)
        await update.message.reply_text(LANG[lang]["invalid_format"])

async def owner_withdraw_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for') != 'withdraw_amount':
        return
    
    try:
        amount = float(update.message.text.strip())
        aid = context.user_data.get('withdraw_admin')
        db = load_db()
        lang = get_lang(OWNER_ID, db)
        
        if aid in db['admins']:
            current_balance = db['admins'][aid].get('wallet', 0)
            
            if current_balance < amount:
                await update.message.reply_text(LANG[lang]["insufficient_balance_withdraw"].format(wallet=current_balance, amount=amount))
            else:
                new_balance = current_balance - amount
                db['admins'][aid]['wallet'] = new_balance
                save_db(db)
                
                # إرسال رسالة للأونر
                await update.message.reply_text(LANG[lang]["money_withdrawn"].format(amount=amount, balance=new_balance))
                
                # إرسال إشعار للموزع
                try:
                    admin_lang = db['admins'][aid].get('lang', 'en')
                    
                    notification_msg = {
                        'ar': f"💸 تم سحب أموال من حسابك!\n\n❌ المبلغ المسحوب: ${amount:.2f}\n📊 الرصيد السابق: ${current_balance:.2f}\n💵 الرصيد الجديد: ${new_balance:.2f}\n\n⚠️ تم السحب بواسطة المالك",
                        'en': f"💸 Money withdrawn from your account!\n\n❌ Amount withdrawn: ${amount:.2f}\n📊 Previous balance: ${current_balance:.2f}\n💵 New balance: ${new_balance:.2f}\n\n⚠️ Withdrawn by owner",
                        'ru': f"💸 Деньги сняты с вашего счета!\n\n❌ Снято: ${amount:.2f}\n📊 Предыдущий баланс: ${current_balance:.2f}\n💵 Новый баланс: ${new_balance:.2f}\n\n⚠️ Снято владельцем"
                    }
                    
                    await context.bot.send_message(
                        chat_id=int(aid),
                        text=notification_msg.get(admin_lang, notification_msg['en'])
                    )
                except Exception as e:
                    print(f"Failed to send notification to admin {aid}: {e}")
        else:
            await update.message.reply_text(LANG[lang]["no_resellers"])
        
        context.user_data['waiting_for'] = None
    except:
        db = load_db()
        lang = get_lang(OWNER_ID, db)
        await update.message.reply_text(LANG[lang]["invalid_format"])

# ═══════════════════════════════════════════════════════════════
# 👨‍✈️ ADMIN BOT - Reseller Panel with Wallet
# ═══════════════════════════════════════════════════════════════
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    aid = str(update.effective_user.id)
    
    if aid not in db['admins'] or db['admins'][aid].get('role') != 'admin':
        await update.message.reply_text(LANG["en"]["unauthorized"] + f"\n\n{LANG['en']['contact_support'].format(support=SUPPORT_USERNAME)}")
        return
    
    if db['admins'][aid].get('banned', False):
        await update.message.reply_text("🚫 ACCOUNT BANNED\n\nYour account has been deactivated.\n\n💬 Contact: " + SUPPORT_USERNAME)
        return
    
    lang = get_lang(aid, db)
    name = update.effective_user.first_name
    wallet = db['admins'][aid].get('wallet', 0)
    keys = len(db['admins'][aid].get('keys', []))
    ips = load_ips()
    active = sum(1 for k in db['admins'][aid].get('keys', []) 
                 if k in ips and ips[k].get('expires_at', 0) > time.time())
    
    msg = LANG[lang]["admin_panel"].format(
        name=name, wallet=wallet, keys=keys, active=active,
        day=PRICING['day'], week=PRICING['week'], month=PRICING['month']
    )
    
    kb = [
        [InlineKeyboardButton(LANG[lang]["gen_license_btn"], callback_data='a_gen')],
        [InlineKeyboardButton(LANG[lang]["my_keys"], callback_data='a_keys'),
         InlineKeyboardButton(LANG[lang]["ban_key"], callback_data='a_ban')],
        [InlineKeyboardButton(LANG[lang]["wallet_info"], callback_data='a_wallet'),
         InlineKeyboardButton(LANG[lang]["language"], callback_data='a_lang')],
        [InlineKeyboardButton(LANG[lang]["support"], url=f"https://t.me/{SUPPORT_USERNAME[1:]}")]
    ]
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def admin_gen_duration_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    aid = str(q.from_user.id)
    db = load_db()
    lang = get_lang(aid, db)
    if q.data == "gen_cancel":
        await q.edit_message_text(LANG[lang]["cancel"])
        return
    duration_type = q.data[4:]
    if duration_type not in DURATIONS:
        return
    cost = PRICING[duration_type]
    days = DURATIONS[duration_type]
    wallet = db["admins"][aid].get("wallet", 0)
    if wallet < cost:
        await q.edit_message_text(
            LANG[lang]["insufficient_balance"].format(wallet=wallet, required=cost, support=SUPPORT_USERNAME)
        )
        return
    db["admins"][aid]["wallet"] -= cost
    save_db(db)
    key = create_pending_key(aid, duration_type, days, cost)
    new_wallet = db["admins"][aid]["wallet"]
    msg = LANG[lang]["gen_key_created"].format(key=key, days=days, cost=cost, balance=new_wallet)
    await q.edit_message_text(msg, parse_mode=ParseMode.HTML)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    aid = str(q.from_user.id)
    db = load_db()
    lang = get_lang(aid, db)
    
    # Safety guard: some callbacks may arrive for an admin id
    # that doesn't exist in db['admins'] (KeyError -> bot handler crashes).
    admins = db.get("admins", {})
    if aid not in admins or admins[aid].get("role") != "admin":
        await q.edit_message_text(LANG[lang]["unauthorized"])
        return
    
    if q.data == 'a_gen':
        wallet = db['admins'][aid].get('wallet', 0)
        if wallet < PRICING['day']:
            msg = LANG[lang]["insufficient_balance"].format(wallet=wallet, required=PRICING['day'], support=SUPPORT_USERNAME)
            kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='a_back')]]
            await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
            return
        msg = LANG[lang]["gen_select_duration"].format(wallet=wallet)
        kb = []
        if wallet >= PRICING['day']:
            kb.append([InlineKeyboardButton(LANG[lang]["day_btn"].format(price=PRICING['day']), callback_data='gen_day')])
        if wallet >= PRICING['week']:
            kb.append([InlineKeyboardButton(LANG[lang]["week_btn"].format(price=PRICING['week']), callback_data='gen_week')])
        if wallet >= PRICING['month']:
            kb.append([InlineKeyboardButton(LANG[lang]["month_btn"].format(price=PRICING['month']), callback_data='gen_month')])
        kb.append([InlineKeyboardButton(LANG[lang]["cancel"], callback_data='gen_cancel')])
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'a_keys' or q.data.startswith('a_keys_page_'):
        # Extract page number
        page = 1
        if q.data.startswith('a_keys_page_'):
            try:
                page = int(q.data.split('_')[-1])
            except:
                page = 1
        
        lkeys = load_license_keys()
        admin_keys = [(k, rec) for k, rec in lkeys.items() 
                      if str(rec.get("admin", "")) == aid and rec.get("status") in ("pending", "active")]
        
        if not admin_keys:
            msg = LANG[lang]["no_keys"]
            kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='a_back')]]
            await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
            return
        
        # Paginate keys
        paginated = paginate_list(admin_keys, page, KEYS_PER_PAGE)
        
        msg = "🔑 " + ("مفاتيحي" if lang == "ar" else "MY KEYS" if lang == "en" else "МОИ КЛЮЧИ") + "\n\n"
        msg += LANG[lang]["page_info"].format(current=paginated['page'], total=paginated['total_pages']) + "\n"
        msg += f"📊 Total: {paginated['total_items']} keys\n\n"
        
        for key, rec in paginated['items']:
            status_emoji = "✅" if rec.get("status") == "active" else "⏳"
            
            if rec.get("status") == "active":
                ip = rec.get("activated_ip", "N/A")
                exp = rec.get("expires_at", 0)
                if exp > time.time():
                    days = int((exp - time.time()) / 86400)
                    date_str = datetime.fromtimestamp(exp).strftime('%Y-%m-%d')
                    msg += f"{status_emoji} <code>{key}</code>\n"
                    msg += f"   IP: {ip}\n"
                    msg += f"   Expires: {days}d ({date_str})\n\n"
                else:
                    msg += f"❌ <code>{key}</code> (Expired)\n\n"
            else:
                msg += f"{status_emoji} <code>{key}</code> (Pending)\n\n"
        
        # Create keyboard with pagination
        kb = create_pagination_keyboard('a_keys', paginated['page'], paginated['total_pages'], 'a_back', lang)
        
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    
    
    elif q.data == 'a_ban' or q.data.startswith('a_ban_page_'):
        # Extract page number
        page = 1
        if q.data.startswith('a_ban_page_'):
            try:
                page = int(q.data.split('_')[-1])
            except:
                page = 1
        
        lkeys = load_license_keys()
        admin_keys = [k for k, rec in lkeys.items() 
                      if str(rec.get("admin", "")) == aid and rec.get("status") in ("pending", "active") and not rec.get("banned", False)]
        
        if not admin_keys:
            msg = LANG[lang]["no_keys"]
            kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='a_back')]]
            await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
            return
        
        # Paginate keys
        paginated = paginate_list(admin_keys, page, KEYS_PER_PAGE)
        
        msg = LANG[lang]["select_key_ban"] + "\n\n"
        msg += LANG[lang]["page_info"].format(current=paginated['page'], total=paginated['total_pages'])
        
        kb = []
        for key in paginated['items']:
            kb.append([InlineKeyboardButton(key, callback_data=f'ban_{key}')])
        
        # Add pagination buttons
        kb.extend(create_pagination_keyboard('a_ban', paginated['page'], paginated['total_pages'], 'a_back', lang))
        
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data.startswith('ban_'):
        key_id = q.data[4:]
        lkeys = load_license_keys()
        rec = lkeys.get(key_id)
        if rec and str(rec.get("admin", "")) == aid:
            rec["banned"] = True
            old_ip = rec.get("activated_ip")
            rec["status"] = "banned"
            lkeys[key_id] = rec
            save_license_keys(lkeys)

            if old_ip:
                ips = load_ips()
                if old_ip in ips and ips[old_ip].get("license_key") == key_id:
                    ips.pop(old_ip, None)
                    save_ips(ips)

                db = load_db()
                if aid in db.get("admins", {}) and isinstance(db["admins"][aid].get("keys", []), list):
                    db["admins"][aid]["keys"] = [x for x in db["admins"][aid]["keys"] if x != old_ip]
                if old_ip in db.get("keys", {}):
                    db["keys"].pop(old_ip, None)
                save_db(db)
        
        msg = LANG[lang]["key_banned"].format(ip=key_id)
        kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='a_back')]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'a_wallet':
        wallet = db['admins'][aid].get('wallet', 0)
        keys = len(db['admins'][aid].get('keys', []))
        
        msg = "💰 " + ("معلومات المحفظة" if lang == "ar" else "WALLET INFO" if lang == "en" else "ИНФОРМАЦИЯ О КОШЕЛЬКЕ") + "\n\n"
        msg += f"├ " + ("الرصيد" if lang == "ar" else "Balance" if lang == "en" else "Баланс") + f": ${wallet:.2f}\n"
        msg += f"└ " + ("المفاتيح" if lang == "ar" else "Keys" if lang == "en" else "Ключей") + f": {keys}\n\n"
        msg += "💵 " + ("الأسعار" if lang == "ar" else "PRICING" if lang == "en" else "ЦЕНЫ") + ":\n"
        msg += f"├ " + ("يوم" if lang == "ar" else "Day" if lang == "en" else "День") + f": ${PRICING['day']:.2f}\n"
        msg += f"├ " + ("أسبوع" if lang == "ar" else "Week" if lang == "en" else "Неделя") + f": ${PRICING['week']:.2f}\n"
        msg += f"└ " + ("شهر" if lang == "ar" else "Month" if lang == "en" else "Месяц") + f": ${PRICING['month']:.2f}\n\n"
        msg += LANG[lang]["contact_support"].format(support=SUPPORT_USERNAME)
        
        kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='a_back')]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'a_lang':
        msg = LANG[lang]["language"]
        kb = [
            [InlineKeyboardButton("العربية 🇸🇦", callback_data='alang_ar')],
            [InlineKeyboardButton("English 🇺🇸", callback_data='alang_en')],
            [InlineKeyboardButton("Русский 🇷🇺", callback_data='alang_ru')],
            [InlineKeyboardButton(LANG[lang]["back"], callback_data='a_back')]
        ]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data.startswith('alang_'):
        new_lang = q.data[6:]
        db['admins'][aid]['lang'] = new_lang
        save_db(db)
        
        # Recreate main panel with new language
        name = q.from_user.first_name
        wallet = db['admins'][aid].get('wallet', 0)
        keys = len(db['admins'][aid].get('keys', []))
        ips = load_ips()
        active = sum(1 for k in db['admins'][aid].get('keys', []) 
                     if k in ips and ips[k].get('expires_at', 0) > time.time())
        
        msg = LANG[new_lang]["admin_panel"].format(
            name=name, wallet=wallet, keys=keys, active=active,
            day=PRICING['day'], week=PRICING['week'], month=PRICING['month']
        )
        
        kb = [
            [InlineKeyboardButton(LANG[new_lang]["gen_license_btn"], callback_data='a_gen')],
            [InlineKeyboardButton(LANG[new_lang]["my_keys"], callback_data='a_keys'),
             InlineKeyboardButton(LANG[new_lang]["ban_key"], callback_data='a_ban')],
            [InlineKeyboardButton(LANG[new_lang]["wallet_info"], callback_data='a_wallet'),
             InlineKeyboardButton(LANG[new_lang]["language"], callback_data='a_lang')],
            [InlineKeyboardButton(LANG[new_lang]["support"], url=f"https://t.me/{SUPPORT_USERNAME[1:]}")]
        ]
        
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'a_back':
        # Recreate main panel
        name = q.from_user.first_name
        wallet = db['admins'][aid].get('wallet', 0)
        keys = len(db['admins'][aid].get('keys', []))
        ips = load_ips()
        active = sum(1 for k in db['admins'][aid].get('keys', []) 
                     if k in ips and ips[k].get('expires_at', 0) > time.time())
        
        msg = LANG[lang]["admin_panel"].format(
            name=name, wallet=wallet, keys=keys, active=active,
            day=PRICING['day'], week=PRICING['week'], month=PRICING['month']
        )
        
        kb = [
            [InlineKeyboardButton(LANG[lang]["gen_license_btn"], callback_data='a_gen')],
            [InlineKeyboardButton(LANG[lang]["my_keys"], callback_data='a_keys'),
             InlineKeyboardButton(LANG[lang]["ban_key"], callback_data='a_ban')],
            [InlineKeyboardButton(LANG[lang]["wallet_info"], callback_data='a_wallet'),
             InlineKeyboardButton(LANG[lang]["language"], callback_data='a_lang')],
            [InlineKeyboardButton(LANG[lang]["support"], url=f"https://t.me/{SUPPORT_USERNAME[1:]}")]
        ]
        
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))

# ═══════════════════════════════════════════════════════════════
# 👤 USER BOT - End User Interface (No Support Contact)
# ═══════════════════════════════════════════════════════════════
async def user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_db()
    
    if uid not in db['users']:
        db['users'][uid] = {'lang': 'en'}
        save_db(db)
    
    lang = get_lang(uid, db)
    name = update.effective_user.first_name
    
    msg = LANG[lang]["user_panel"].format(name=name)
    
    kb = [
        [InlineKeyboardButton(LANG[lang]["mini_app_btn"], web_app=WebAppInfo(url=MINI_APP_URL))]
    ]
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = str(q.from_user.id)
    db = load_db()
    lang = get_lang(uid, db)
    
    if q.data == 'u_status':
        context.user_data['waiting_for'] = 'check_sub_ip'
        msg = LANG[lang]["ip_tutorial"].format(url=IP_LOOKUP_URL) + "\n\n" + LANG[lang]["ask_send_ip_sub"]
        kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='u_back')]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'u_ip':
        msg = LANG[lang]["ip_tutorial"].format(url=IP_LOOKUP_URL)
        kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='u_back')]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'u_activate':
        context.user_data['waiting_for'] = 'activate_step_key'
        context.user_data.pop('pending_license_key', None)
        msg = LANG[lang]["ip_tutorial"].format(url=IP_LOOKUP_URL) + "\n\n" + LANG[lang]["ask_send_key_first"]
        kb = [[InlineKeyboardButton(LANG[lang]["back"], callback_data='u_back')]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'u_lang':
        msg = LANG[lang]["language"]
        kb = [
            [InlineKeyboardButton("العربية 🇸🇦", callback_data='ulang_ar')],
            [InlineKeyboardButton("English 🇺🇸", callback_data='ulang_en')],
            [InlineKeyboardButton("Русский 🇷🇺", callback_data='ulang_ru')],
            [InlineKeyboardButton(LANG[lang]["back"], callback_data='u_back')]
        ]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data.startswith('ulang_'):
        new_lang = q.data[6:]
        db['users'][uid]['lang'] = new_lang
        save_db(db)
        
        # Recreate main panel with new language
        name = q.from_user.first_name
        msg = LANG[new_lang]["user_panel"].format(name=name)
        
        kb = [
            [InlineKeyboardButton(LANG[new_lang]["mini_app_btn"], web_app=WebAppInfo(url=MINI_APP_URL))]
        ]
        
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    
    elif q.data == 'u_back':
        context.user_data['waiting_for'] = None
        context.user_data.pop('pending_license_key', None)
        name = q.from_user.first_name
        msg = LANG[lang]["user_panel"].format(name=name)
        
        kb = [
            [InlineKeyboardButton(LANG[lang]["mini_app_btn"], web_app=WebAppInfo(url=MINI_APP_URL))]
        ]
        
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def user_activate_step_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for') != 'activate_step_key':
        return
    text = (update.message.text or "").strip()
    uid = str(update.effective_user.id)
    db = load_db()
    lang = get_lang(uid, db)
    context.user_data['pending_license_key'] = text
    context.user_data['waiting_for'] = 'activate_step_ip'
    await update.message.reply_text(LANG[lang]["ask_send_ip_activate"])

async def user_activate_step_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for') != 'activate_step_ip':
        return
    uid = str(update.effective_user.id)
    db = load_db()
    lang = get_lang(uid, db)
    ip = parse_ipv4((update.message.text or "").strip())
    key_text = context.user_data.get('pending_license_key', '')
    if not ip:
        await update.message.reply_text(LANG[lang]["invalid_ip"])
        return
    ok, err = activate_license_key(key_text, ip, uid)
    context.user_data['waiting_for'] = None
    context.user_data.pop('pending_license_key', None)
    if ok:
        ips = load_ips()
        exp = ips.get(ip, {}).get('expires_at', 0)
        date_str = datetime.fromtimestamp(exp).strftime('%Y-%m-%d %H:%M')
        await update.message.reply_text(LANG[lang]["license_activated_ok"].format(ip=ip, date=date_str))
        return
    err_map = {
        "bad_format": LANG[lang]["license_err_format"],
        "not_found": LANG[lang]["license_err_not_found"],
        "already_used": LANG[lang]["license_err_used"],
        "banned": LANG[lang]["license_err_banned"],
        "expired": LANG[lang]["license_err_expired"],
        "ip_in_use": LANG[lang]["license_err_ip_in_use"],
        "frozen": LANG[lang]["license_err_frozen"],
    }
    await update.message.reply_text(err_map.get(err, LANG[lang]["license_err_not_found"]))

async def user_check_sub_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for') != 'check_sub_ip':
        return
    uid = str(update.effective_user.id)
    db = load_db()
    lang = get_lang(uid, db)
    ip = parse_ipv4((update.message.text or "").strip())
    if not ip:
        await update.message.reply_text(LANG[lang]["invalid_ip"])
        return
    context.user_data['waiting_for'] = None
    ips = load_ips()
    freeze_state = load_freeze_state()
    is_frozen = bool(freeze_state.get("frozen", False))
    if ip in ips and ips[ip].get('expires_at', 0) > time.time():
        if is_frozen:
            msg = LANG[lang]["sub_frozen_notice"].format(ip=ip)
            await update.message.reply_text(msg)
            return
        exp = ips[ip]['expires_at']
        days = int((exp - time.time()) / 86400)
        hours = int(((exp - time.time()) % 86400) / 3600)
        date_str = datetime.fromtimestamp(exp).strftime('%Y-%m-%d %H:%M')
        msg = LANG[lang]["sub_active"].format(ip=ip, date=date_str, days=days, hours=hours)
    else:
        msg = LANG[lang]["sub_inactive"].format(ip=ip)
    await update.message.reply_text(msg)

# ═══════════════════════════════════════════════════════════════
# 🚀 MAIN ENGINE - Run All Bots
# ═══════════════════════════════════════════════════════════════
async def run_all_bots():
    print("\n" + "="*60)
    print("🤖 Nitro Proxy - Advanced 3-Bot System")
    print("="*60)
    
    # Create applications
    owner_app = Application.builder().token(TOKENS['owner']).build()
    admin_app = Application.builder().token(TOKENS['admin']).build()
    user_app = Application.builder().token(TOKENS['user']).build()
    
    # ═══ Owner Bot Handlers ═══
    async def owner_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        waiting_for = context.user_data.get('waiting_for')
        db = load_db()
        lang = get_lang(OWNER_ID, db)
        if waiting_for == 'admin_id':
            await owner_add_admin(update, context)
        elif waiting_for == 'wallet_amount':
            await owner_add_wallet(update, context)
        elif waiting_for == 'withdraw_amount':
            await owner_withdraw_money(update, context)
        elif waiting_for == 'freekey_count':
            try:
                count = int((update.message.text or "").strip())
                if count <= 0:
                    raise ValueError("count<=0")
                if count > 200:
                    await update.message.reply_text(LANG[lang]["freekey_count_too_large"])
                    return
                context.user_data["freekey_count"] = count
                context.user_data["waiting_for"] = "freekey_days"
                await update.message.reply_text(LANG[lang]["send_freekey_days"].format(count=count))
            except:
                await update.message.reply_text(LANG[lang]["invalid_format"])
        elif waiting_for == 'freekey_days':
            try:
                days = int((update.message.text or "").strip())
                count = int(context.user_data.get("freekey_count", 0))
                if count <= 0 or days <= 0:
                    raise ValueError("bad count/days")
                
                keys = []
                for _ in range(count):
                    key = create_pending_key(OWNER_ID, "custom", days, 0.0)
                    keys.append(key)
                
                content = "\n".join(keys)
                bio = BytesIO(content.encode("utf-8"))
                bio.name = "free_keys.txt"
                
                await context.bot.send_document(
                    chat_id=int(OWNER_ID),
                    document=InputFile(bio),
                    caption=LANG[lang]["free_keys_done"].format(count=count, days=days)
                )
                
                context.user_data["waiting_for"] = None
                context.user_data["freekey_count"] = None
            except:
                context.user_data["waiting_for"] = None
                await update.message.reply_text(LANG[lang]["invalid_format"])
    
    owner_app.add_handler(CommandHandler("start", owner_start))
    owner_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, owner_message_handler))
    owner_app.add_handler(CallbackQueryHandler(owner_callback))
    
    # ═══ Admin Bot Handlers ═══
    admin_app.add_handler(CommandHandler("start", admin_start))
    admin_app.add_handler(CallbackQueryHandler(admin_gen_duration_callback, pattern='^gen_'))
    admin_app.add_handler(CallbackQueryHandler(admin_callback))
    
    # ═══ User Bot Handlers ═══
    async def user_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        wf = context.user_data.get('waiting_for')
        if wf == 'activate_step_key':
            await user_activate_step_key(update, context)
        elif wf == 'activate_step_ip':
            await user_activate_step_ip(update, context)
        elif wf == 'check_sub_ip':
            await user_check_sub_ip(update, context)
    
    user_app.add_handler(CommandHandler("start", user_start))
    user_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_message_handler))
    user_app.add_handler(CallbackQueryHandler(user_callback))
    
    # Initialize
    await owner_app.initialize()
    await admin_app.initialize()
    await user_app.initialize()
    
    # Start
    await owner_app.start()
    await admin_app.start()
    await user_app.start()
    
    print("✅ 1. Owner Bot   : ACTIVE (@OwnersNitroBot)")
    print("✅ 2. Admin Bot   : ACTIVE (@NitroAdminsBot)")
    print("✅ 3. User Bot    : ACTIVE (@NitroUsersBot)")
    print("="*60 + "\n")
    
    # Start polling
    await asyncio.gather(
        owner_app.updater.start_polling(drop_pending_updates=True),
        admin_app.updater.start_polling(drop_pending_updates=True),
        user_app.updater.start_polling(drop_pending_updates=True)
    )
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print("\n⚠️  Stopping bots...")
        await owner_app.stop()
        await admin_app.stop()
        await user_app.stop()
        print("✅ Stopped successfully")

if __name__ == "__main__":
    try:
        asyncio.run(run_all_bots())
    except KeyboardInterrupt:
        print("\n[!] Stopped")
