import concurrent.futures
import io
import os
import re
import sys
import time
import socket
import requests
import yaml
import subprocess
import platform
import gzip
import shutil
import zipfile
import urllib.request
from urllib.parse import quote_plus, urlparse

# ===================== 配置区 =====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BLACKLIST_DOMAINS = [
    "github.com", "google.com", "baidu.com", "w3.org", "cloudflare.com", 
    "microsoft.com", "apple.com", "github.io", "gitlab.com", "wikipedia.org", 
    "example.com", "127.0.0.1", "localhost", "t.me", "sub.xeton.dev", "api.telegram.org",
    "jsdelivr.net", "raw.githubusercontent.com", "t.me/s/"
]

# 🚀 狂飙配置：缩短超时，不惯着慢节点
TCP_TIMEOUT = 1.0        # TCP预筛超时(秒)
REAL_TEST_TIMEOUT = 1200 # 内核真实请求超时(毫秒)

# 🌍 国家代码与 Emoji 国旗映射字典
COUNTRY_EMOJIS = {
    "US": "🇺🇸", "HK": "🇭🇰", "SG": "🇸🇬", "JP": "🇯🇵", "TW": "🇹🇼",
    "KR": "🇰🇷", "GB": "🇬🇧", "DE": "🇩🇪", "FR": "🇫🇷", "NL": "🇳🇱",
    "RU": "🇷🇺", "IN": "🇮🇳", "CA": "🇨🇦", "AU": "🇦🇺", "CN": "🇨🇳",
    "MO": "🇲🇴", "MY": "🇲🇾", "PH": "🇵🇭", "TH": "🇹🇭", "VN": "🇻🇳",
    "BR": "🇧🇷", "ZA": "🇿🇦", "TR": "🇹🇷", "IT": "🇮🇹", "ES": "🇪🇸",
    "AE": "🇦🇪", "CH": "🇨🇭", "SE": "🇸🇪", "NO": "🇳🇴", "FI": "🇫🇮"
}

# ===================== 🎯 TG 频道弹药库 =====================
# 你可以直接把含有 https://t.me/xxx 的文本贴在这里，代码会自动解析去重！
_RAW_CHANNELS = """
- https://t.me/ARv2ray
- https://t.me/Alfred_Config
- https://t.me/Baraye_azadi_Info
- https://t.me/BmFt1
- https://t.me/Capital_NET
- https://t.me/Capoit
- https://t.me/CloudCityy
- https://t.me/ConfigV2rayNG
- https://t.me/Configforvpn01
- https://t.me/ConfigsHUB2
- https://t.me/DailyV2RY
- https://t.me/DigiV2ray
- https://t.me/DirectVPN
- https://t.me/Easy_Free_VPN
- https://t.me/Eleven_vpn
- https://t.me/EliV2ray
- https://t.me/EuServer
- https://t.me/EzNett
- https://t.me/FOXNT
- https://t.me/FProxies
- https://t.me/FalconPolV2rayNG
- https://t.me/FreakConfig
- https://t.me/Free166
- https://t.me/FreeV2rays
- https://t.me/FreeVlessVpn
- https://t.me/Free_HTTPCustom
- https://t.me/Helix_Servers
- https://t.me/Hope_Net
- https://t.me/IBV2RAY
- https://t.me/IRANVPNNET
- https://t.me/JiedianSsr
- https://t.me/Jsnzk
- https://t.me/Lockey_vpn
- https://t.me/MTConfig
- https://t.me/MrV2Ray
- https://t.me/MsV2ray
- https://t.me/NIM_VPN_ir
- https://t.me/Napsternetvirani
- https://t.me/NetAccount
- https://t.me/OKAB3_Script_Channel
- https://t.me/OutlineVpnOfficial
- https://t.me/Outline_Vpn
- https://t.me/Powerful1VPN
- https://t.me/PrivateVPNs
- https://t.me/ProxyFn
- https://t.me/Qv2rayDONATED
- https://t.me/Qv2raychannel
- https://t.me/SSRSUB
- https://t.me/ServerNett
- https://t.me/ShadowProxy66
- https://t.me/ShadowsocksRssr
- https://t.me/ShareCentre
- https://t.me/ShareCentrePro
- https://t.me/Shh_Proxy
- https://t.me/TGxChina
- https://t.me/TLS_v2ray
- https://t.me/TVCminer
- https://t.me/UnlimitedDev
- https://t.me/V2RayTz
- https://t.me/V2Ray_FreedomIran
- https://t.me/V2pedia
- https://t.me/V2rayCollectorDonate
- https://t.me/V2rayNG3
- https://t.me/V2rayNGn
- https://t.me/V2ray_Alpha
- https://t.me/V2rayng_Fast
- https://t.me/VPNCUSTOMIZE
- https://t.me/V_2rayngVpn
- https://t.me/ViPVpn_v2ray
- https://t.me/VlessConfig
- https://t.me/VmessProtocol
- https://t.me/WeePeeN
- https://t.me/WomanLifeFreedomVPN
- https://t.me/YtTe3la
- https://t.me/ZDYZ2
- https://t.me/abra_vpn
- https://t.me/academi_vpn
- https://t.me/accountplanetir
- https://t.me/adamak_vpn
- https://t.me/afv2ray
- https://t.me/ahe_vpn
- https://t.me/aifenxiang2020
- https://t.me/ailumao
- https://t.me/airproxies
- https://t.me/aiuvpn
- https://t.me/alfred_config
- https://t.me/alienvpn402
- https://t.me/alismartvpn
- https://t.me/aliyosgraphy
- https://t.me/allporter
- https://t.me/alo_v2rayng
- https://t.me/alpha_v2ray_fazayi
- https://t.me/alphaomegavpn
- https://t.me/alsheykhvpn
- https://t.me/amir_rooman
- https://t.me/amirinventor2010
- https://t.me/amironetwork
- https://t.me/an0nymousteam
- https://t.me/android_best
- https://t.me/angus_vpn
- https://t.me/angus_vpn3
- https://t.me/anix_v2ray
- https://t.me/antifilterjadid
- https://t.me/antifilterjadid3
- https://t.me/antifilterservice
- https://t.me/apkgold
- https://t.me/apkprogramming
- https://t.me/app_jiedian
- https://t.me/apple_x1
- https://t.me/appsooner
- https://t.me/archive_android
- https://t.me/argooo_vpn
- https://t.me/aries_init
- https://t.me/armod_iran
- https://t.me/arouxping
- https://t.me/artemis_vpn_free
- https://t.me/artemisvpn1
- https://t.me/arv2ra
- https://t.me/arv2ray
- https://t.me/asak_vpn
- https://t.me/asgard_config
- https://t.me/asintech
- https://t.me/asjdxm
- https://t.me/asliveepn
- https://t.me/asr_proxy
- https://t.me/astrovpn_ir
- https://t.me/astrovpn_official
- https://t.me/av2drup
- https://t.me/axv2ray
- https://t.me/azad_intrnet
- https://t.me/azadneit
- https://t.me/badsha_mohammad
- https://t.me/baipiao01
- https://t.me/baipiaob
- https://t.me/baipiaojiedian
- https://t.me/bakvpns
- https://t.me/bamboo_vpn
- https://t.me/bargovpn
- https://t.me/bemolatext
- https://t.me/berice_v2
- https://t.me/bestvpn4030
- https://t.me/betv2ray
- https://t.me/bigsmoke_config
- https://t.me/bimnetvpn
- https://t.me/birdserver
- https://t.me/bitnetvpn
- https://t.me/black8rose
- https://t.me/blueberrynetwork
- https://t.me/bluev2rayng
- https://t.me/bluevpn_v2ray
- https://t.me/bolbolvpn
- https://t.me/bored_vpn
- https://t.me/bpjzx2
- https://t.me/bright_vpn
- https://t.me/buffalo_vpn
- https://t.me/bug_vpn
- https://t.me/bypass_filter
- https://t.me/caa_chanel
- https://t.me/caa_v2ray
- https://t.me/canguro_english
- https://t.me/capital_net
- https://t.me/capoit
- https://t.me/castom_v2ray
- https://t.me/catvpns
- https://t.me/cav2ray
- https://t.me/cephalon_ala
- https://t.me/ch_a2l
- https://t.me/chanel_config
- https://t.me/changfengchannel
- https://t.me/chatbuzzteam
- https://t.me/circle_vpn
- https://t.me/cisco_acc
- https://t.me/click_vpnn
- https://t.me/cloudcityy
- https://t.me/club_vpn9
- https://t.me/clubvpn443
- https://t.me/cnfg_v2ray
- https://t.me/cnfings
- https://t.me/cod_arshiya0
- https://t.me/configV2rayForFree
- https://t.me/configV2rayNG
- https://t.me/config_station
- https://t.me/configforvpn
- https://t.me/configforvpn01
- https://t.me/configms
- https://t.me/configpluse
- https://t.me/configpositive
- https://t.me/configscenter
- https://t.me/configshub2
- https://t.me/configsstore
- https://t.me/configt
- https://t.me/configv2rayforfree
- https://t.me/configv2rayng
- https://t.me/confing_costume
- https://t.me/confing_problems
- https://t.me/confingv2raayng
- https://t.me/connectix
- https://t.me/cpuvpn
- https://t.me/croownvpn
- https://t.me/custom_14
- https://t.me/custom_config
- https://t.me/customizev2ray
- https://t.me/customv2ray
- https://t.me/customvpnserver
- https://t.me/dailyv2ray
- https://t.me/dailyv2ry
- https://t.me/damonconfig
- https://t.me/daredevill_404
- https://t.me/dark_telecom
- https://t.me/darkma3ter24
- https://t.me/darknightvpn
- https://t.me/darksectora
- https://t.me/darktunnelvip1
- https://t.me/daryaye_sorkhh
- https://t.me/dataworld_ir
- https://t.me/dav2ray
- https://t.me/deli_servers
- https://t.me/deragv2ray
- https://t.me/diamondproxytm
- https://t.me/digigard_vpn
- https://t.me/digiv2ray
- https://t.me/dingyue_Center
- https://t.me/directvpn
- https://t.me/disvpn
- https://t.me/dns68
- https://t.me/donald_config
- https://t.me/dr_v2ray
- https://t.me/dribble7
- https://t.me/eaglevps
- https://t.me/easy_free_vpn
- https://t.me/editorvpn
- https://t.me/ehsawn8
- https://t.me/eiiim
- https://t.me/elitevpnv2
- https://t.me/eliv2ray
- https://t.me/energybigger_1
- https://t.me/esetsecuritylicense
- https://t.me/euserver
- https://t.me/ev2rayy
- https://t.me/evay_vpn
- https://t.me/everyday_vpn
- https://t.me/expreset
- https://t.me/express_v2ray
- https://t.me/expresspace
- https://t.me/expressvpn_420
- https://t.me/falconpolv2rayng
- https://t.me/falcunargo
- https://t.me/farahvpn
- https://t.me/fasst_vpn
- https://t.me/fast_2ray
- https://t.me/fastfilterr
- https://t.me/fastgozar
- https://t.me/fazevpn
- https://t.me/feri_v2ray_proxy
- https://t.me/fffffx2
- https://t.me/filter_vpn2
- https://t.me/filterintl
- https://t.me/filteroghortbede
- https://t.me/filtershekan_channel
- https://t.me/filtershekanssh1
- https://t.me/filterzapata
- https://t.me/fire_vpn_channel
- https://t.me/firewallvpn
- https://t.me/fix_proxy
- https://t.me/flash_proxies
- https://t.me/flystoreir
- https://t.me/flyv2ray
- https://t.me/forwardv2ray
- https://t.me/foxnt
- https://t.me/frav2ray
- https://t.me/freakconfig
- https://t.me/free4allVPN
- https://t.me/free4allvpn
- https://t.me/freeVPNjd
- https://t.me/free_httpcustom
- https://t.me/free_proxy_001
- https://t.me/free_shekan
- https://t.me/free_v2
- https://t.me/free_v2rayyy
- https://t.me/free_vpn02
- https://t.me/free_worlld
- https://t.me/freeconfing
- https://t.me/freeinir
- https://t.me/freeiranet
- https://t.me/freeiranweb
- https://t.me/freekankan
- https://t.me/freeland8
- https://t.me/freenapsternetv
- https://t.me/freenet_for_everyone
- https://t.me/freenetpro99
- https://t.me/freeownvpn
- https://t.me/freeshadowsock
- https://t.me/freestrongvpn
- https://t.me/freev2flyng
- https://t.me/freev2rayi
- https://t.me/freev2raym
- https://t.me/freev2rays
- https://t.me/freev2rayssr
- https://t.me/freevlessvpn
- https://t.me/freevpn3327
- https://t.me/freevpnchina
- https://t.me/freevpnhomesconfigs
- https://t.me/frev2ray
- https://t.me/frev2rayng
- https://t.me/fsv2ray
- https://t.me/funix_shope
- https://t.me/fv2ray
- https://t.me/game_file2020
- https://t.me/gh_v2rayng
- https://t.me/ghalagyann
- https://t.me/ghalagyann2
- https://t.me/global_net_vpn
- https://t.me/go4sharing
- https://t.me/goldd_v2ray
- https://t.me/golestan_vpn
- https://t.me/golf_vpn
- https://t.me/good_v2rayy
- https://t.me/gozargahvpn
- https://t.me/gp_proxy_vpn
- https://t.me/grizzlyvpn
- https://t.me/gulaiguq_baipiao2
- https://t.me/hajimamadvpn
- https://t.me/hajvpn
- https://t.me/hatunnel_vpn
- https://t.me/heinuhome
- https://t.me/helix_servers
- https://t.me/hennessypro
- https://t.me/hermanosvpn
- https://t.me/hhi_vpn222
- https://t.me/hilynet
- https://t.me/hkaa0
- https://t.me/holderproxy
- https://t.me/hologate6
- https://t.me/hooshang_vpn1
- https://t.me/hope_net
- https://t.me/hopev2ray
- https://t.me/hopevpn
- https://t.me/hosseinstore_za
- https://t.me/hpv2ray_official
- https://t.me/hpv2rayng
- https://t.me/hypervpn6
- https://t.me/hypervpns
- https://t.me/i3v2ray
- https://t.me/ibv2ray
- https://t.me/icloudyshop
- https://t.me/icocoon
- https://t.me/icv2ray
- https://t.me/igrsdet
- https://t.me/internet4iran
- https://t.me/internet_nor
- https://t.me/iosfulishare
- https://t.me/ipV2Ray
- https://t.me/ip_cf_config
- https://t.me/iphonebax
- https://t.me/ipv2ray
- https://t.me/ipv2rayng
- https://t.me/ir_config_an
- https://t.me/ir_nekobox
- https://t.me/iran_access
- https://t.me/iran_v2ray1
- https://t.me/iranbaxvpn
- https://t.me/iranbfilter
- https://t.me/iraniv2ray
- https://t.me/iranmedicalvpn
- https://t.me/iranproxypro
- https://t.me/iranray_vpn
- https://t.me/iranv2raynng
- https://t.me/iranvipnet
- https://t.me/iranvpnnet
- https://t.me/irn_vpn
- https://t.me/irnhackers
- https://t.me/iroazadi
- https://t.me/irov2rayn
- https://t.me/irvpnify
- https://t.me/iunsw
- https://t.me/jcvpn
- https://t.me/jetupnet
- https://t.me/jiedian24
- https://t.me/jiedian_share
- https://t.me/jiedianf
- https://t.me/jiedianssr
- https://t.me/jiujied
- https://t.me/jokersfantastichome
- https://t.me/jokerv2ray
- https://t.me/justkingoo
- https://t.me/juzibaipiao
- https://t.me/kafing_2
- https://t.me/kesslervpn
- https://t.me/khadamat_sadra
- https://t.me/khalaa_vpn
- https://t.me/kiava
- https://t.me/kilid_stor
- https://t.me/kingoclubs
- https://t.me/kingofilter
- https://t.me/kingofv2ray
- https://t.me/kingspeedchanel
- https://t.me/kralvpn
- https://t.me/kurd_v2ray
- https://t.me/kurdistan_vpn_perfectt
- https://t.me/kurdvpn1
- https://t.me/kuto_proxy
- https://t.me/kuto_proxy1
- https://t.me/kuto_proxy2
- https://t.me/kxswa
- https://t.me/lakvpn1
- https://t.me/lax_vpn
- https://t.me/legendery_server
- https://t.me/lepingshop
- https://t.me/lepingvpn
- https://t.me/lexa_vpn
- https://t.me/lightning6
- https://t.me/lightv2ray
- https://t.me/likearzonpanell
- https://t.me/limootuursh
- https://t.me/lion_channel_vpn2
- https://t.me/liq_vpn
- https://t.me/lockey_vpn
- https://t.me/lrnbymaa
- https://t.me/ltscxk
- https://t.me/m_buy
- https://t.me/m_vipv2ray
- https://t.me/mahanvpn
- https://t.me/mahdiserver
- https://t.me/mahxray
- https://t.me/mainv2ray
- https://t.me/marketvpni
- https://t.me/mater_1345
- https://t.me/matrixnetvvork
- https://t.me/maxshare
- https://t.me/maznet
- https://t.me/mdvpnsec
- https://t.me/mehrosaboran
- https://t.me/meli_prooxy
- https://t.me/meli_proxyy
- https://t.me/meli_v2rayng
- https://t.me/melov2ray
- https://t.me/mester_v2ray
- https://t.me/mftizi
- https://t.me/mi_pn_official
- https://t.me/miaomua
- https://t.me/migping
- https://t.me/mikasavpn
- https://t.me/mimitdl
- https://t.me/miyanbor_vpn
- https://t.me/mizbanv2ray
- https://t.me/mobilinternet
- https://t.me/mobsec
- https://t.me/moein_insta
- https://t.me/moft_vpn
- https://t.me/moftinet
- https://t.me/mr_vpn123
- https://t.me/mrv2raay
- https://t.me/mrv2ray
- https://t.me/mrvpn1403
- https://t.me/mso_666_baz
- https://t.me/msv2flyng
- https://t.me/msv2ray
- https://t.me/msv2raynp
- https://t.me/mt_team_iran
- https://t.me/mtconfig
- https://t.me/mtpproxy0098
- https://t.me/mtproxy22_v2ray
- https://t.me/mtpv2ray
- https://t.me/murandepindao
- https://t.me/mxv2ray
- https://t.me/my_proxii
- https://t.me/n2vpn
- https://t.me/nameless255
- https://t.me/napsternetvirani
- https://t.me/nepo_v2ray
- https://t.me/netaccount
- https://t.me/netmaask
- https://t.me/netmellianti
- https://t.me/netspeedservice
- https://t.me/network_cfz
- https://t.me/networknim
- https://t.me/new_mtproxi2
- https://t.me/nicolv2ray
- https://t.me/nim_vpn_ir
- https://t.me/nitrovpne
- https://t.me/nofilter_v2rayng
- https://t.me/nofiltering2
- https://t.me/noori_93
- https://t.me/nordaccount1
- https://t.me/novavpn1984
- https://t.me/novinology
- https://t.me/npv_v2ray
- https://t.me/nt_safe
- https://t.me/ntconfig
- https://t.me/nufilter
- https://t.me/nufilter2
- https://t.me/oceanproo
- https://t.me/ohvpn
- https://t.me/oneclickvpnkeys
- https://t.me/onessr
- https://t.me/optvpn
- https://t.me/orb_daily
- https://t.me/orb_irancell
- https://t.me/orb_mci
- https://t.me/orb_rightel
- https://t.me/orb_vpn
- https://t.me/outlineOpenKey
- https://t.me/outline_ir
- https://t.me/outline_oneclick1
- https://t.me/outline_vpn
- https://t.me/outlineiran
- https://t.me/outlinev2rayng
- https://t.me/outlinevpnofficial
- https://t.me/ovpn2
- https://t.me/oxidvip
- https://t.me/oxir_vpn
- https://t.me/oxnet_ir
- https://t.me/pak4you
- https://t.me/pardazeshvpn
- https://t.me/parsashonam
- https://t.me/payam_nsi
- https://t.me/persian_proxy6
- https://t.me/persianv2rayng
- https://t.me/ph_onex
- https://t.me/phiilshekn
- https://t.me/piavpngo
- https://t.me/pin_proxy
- https://t.me/ping01pro
- https://t.me/polproxy
- https://t.me/ponv2ray
- https://t.me/pov2ray
- https://t.me/powerful1vpn
- https://t.me/ppal03
- https://t.me/premiumaccshoop
- https://t.me/prim_vpn
- https://t.me/private_access_guard_vpn
- https://t.me/privatevpnn
- https://t.me/privatevpns
- https://t.me/pro_chaneel
- https://t.me/programmer_best
- https://t.me/proprojec
- https://t.me/proxie
- https://t.me/proxiiraniii
- https://t.me/proxiteiegramm
- https://t.me/proxy48
- https://t.me/proxy_iranv2
- https://t.me/proxy_mtm
- https://t.me/proxy_mtproto_vpns_free
- https://t.me/proxy_n1
- https://t.me/proxy_speed
- https://t.me/proxycityiran
- https://t.me/proxydaemioutline
- https://t.me/proxyfn
- https://t.me/proxyforopeta
- https://t.me/proxyirancel
- https://t.me/proxystore11
- https://t.me/proxysudo
- https://t.me/proxyymeliii
- https://t.me/prrofile_purple
- https://t.me/public504
- https://t.me/puni_shop_v2rayng
- https://t.me/pydriclub
- https://t.me/qeshmserver
- https://t.me/qrv2ray
- https://t.me/qv2raychannel
- https://t.me/qwjhfx
- https://t.me/radiofarex
- https://t.me/rayanconf
- https://t.me/raze_vpn
- https://t.me/realvpnmaster
- https://t.me/relaxv2ray
- https://t.me/renetvpn
- https://t.me/repairms
- https://t.me/rez1vpn
- https://t.me/rk_filtershekan
- https://t.me/rk_filtershking
- https://t.me/rnrifci
- https://t.me/romax_vpn
- https://t.me/royalping_ir
- https://t.me/rxv2ray
- https://t.me/s0013_Official
- https://t.me/s0013_official
- https://t.me/sabz_v2ray
- https://t.me/saferoadnet
- https://t.me/sajad_titan_s_t_n_v2ray
- https://t.me/samiv2ray
- https://t.me/satellitenewspersian
- https://t.me/satoshivpn
- https://t.me/savagev2ray
- https://t.me/sayco_proxy
- https://t.me/selinc
- https://t.me/sellvpniran1
- https://t.me/server444
- https://t.me/server_nekobox
- https://t.me/servermomo
- https://t.me/servernett
- https://t.me/serversiran11
- https://t.me/serverv2ray00
- https://t.me/set_v2ray
- https://t.me/seven_ping
- https://t.me/shadow_v2ray
- https://t.me/shadowproxy66
- https://t.me/shadowsockskeys
- https://t.me/shadowsocksm
- https://t.me/shadowsocksshop
- https://t.me/share_nodes
- https://t.me/sharecentrepro
- https://t.me/shconfig
- https://t.me/shh_proxy
- https://t.me/shopingv2ray
- https://t.me/sinabigo
- https://t.me/sitefilter
- https://t.me/skivpn
- https://t.me/snowguardvpn
- https://t.me/sobi_vpn
- https://t.me/sockcs_http
- https://t.me/sockshttp_vpn
- https://t.me/sourcefreefilter
- https://t.me/spcware
- https://t.me/speed_vpn70
- https://t.me/speedconfig00
- https://t.me/speedent_net
- https://t.me/spikevpn
- https://t.me/srcvpn
- https://t.me/ssrList
- https://t.me/ssrshares
- https://t.me/suddaehi
- https://t.me/superpinghub
- https://t.me/svnteam
- https://t.me/tc_v2ray
- https://t.me/teamvpnpro
- https://t.me/tehranargo
- https://t.me/tehranargo1
- https://t.me/teiknovpn
- https://t.me/telmavpn
- https://t.me/tenzovpn
- https://t.me/thunderv2ray
- https://t.me/tiktok_proxy
- https://t.me/timingvpn
- https://t.me/tiny_vpn_official
- https://t.me/titan_v2rayvpn
- https://t.me/tls_v2ray
- https://t.me/tmv2ray
- https://t.me/top_vpn_chanel
- https://t.me/topvpn02
- https://t.me/torang_vpn
- https://t.me/toyota_proxy
- https://t.me/toyota_proxyyyy
- https://t.me/trand_farsi
- https://t.me/tunssh
- https://t.me/turboo_server
- https://t.me/tv2rayrr
- https://t.me/tv_v2ray
- https://t.me/u3ervpn
- https://t.me/u_confingvpn
- https://t.me/ultravpn_v2ray
- https://t.me/univstar
- https://t.me/unlimiteddev
- https://t.me/uraniumvpn
- https://t.me/v20reyng
- https://t.me/v2Line
- https://t.me/v2_Hub
- https://t.me/v2_hub
- https://t.me/v2_r_ayng
- https://t.me/v2_team
- https://t.me/v2ang
- https://t.me/v2aryng_vpn
- https://t.me/v2bamdad
- https://t.me/v2boxng74
- https://t.me/v2dotcom
- https://t.me/v2fast100
- https://t.me/v2fetch
- https://t.me/v2fox_config
- https://t.me/v2gng
- https://t.me/v2graphy
- https://t.me/v2hamid
- https://t.me/v2icy
- https://t.me/v2line
- https://t.me/v2list
- https://t.me/v2logy
- https://t.me/v2maxx
- https://t.me/v2meowcf
- https://t.me/v2mod
- https://t.me/v2mystery
- https://t.me/v2naptv
- https://t.me/v2net_iran
- https://t.me/v2org
- https://t.me/v2pedia
- https://t.me/v2ra2
- https://t.me/v2raa_server
- https://t.me/v2raand
- https://t.me/v2raayngconfig
- https://t.me/v2rabot
- https://t.me/v2rang_255
- https://t.me/v2range
- https://t.me/v2rangkanal
- https://t.me/v2raxx
- https://t.me/v2ray009
- https://t.me/v2ray03
- https://t.me/v2ray16
- https://t.me/v2ray1_ng
- https://t.me/v2ray313
- https://t.me/v2ray4free
- https://t.me/v2ray851403
- https://t.me/v2ray8x
- https://t.me/v2ray96
- https://t.me/v2rayNG_VPN
- https://t.me/v2rayNG_VPNN
- https://t.me/v2ray_8
- https://t.me/v2ray_83
- https://t.me/v2ray_alpha
- https://t.me/v2ray_best_iran
- https://t.me/v2ray_cartel
- https://t.me/v2ray_configs_pool
- https://t.me/v2ray_custom
- https://t.me/v2ray_donya
- https://t.me/v2ray_fark
- https://t.me/v2ray_fd
- https://t.me/v2ray_for_free
- https://t.me/v2ray_freedomiran
- https://t.me/v2ray_god
- https://t.me/v2ray_inter
- https://t.me/v2ray_ng
- https://t.me/v2ray_nonoal
- https://t.me/v2ray_official
- https://t.me/v2ray_one1
- https://t.me/v2ray_onli
- https://t.me/v2ray_outlinee
- https://t.me/v2ray_outlineir
- https://t.me/v2ray_phoenix
- https://t.me/v2ray_raha
- https://t.me/v2ray_reality_new
- https://t.me/v2ray_rh
- https://t.me/v2ray_rolly
- https://t.me/v2ray_string
- https://t.me/v2ray_swhil
- https://t.me/v2ray_tunnel_plus
- https://t.me/v2ray_txshop
- https://t.me/v2ray_ty
- https://t.me/v2ray_vme
- https://t.me/v2ray_vmes
- https://t.me/v2ray_vpnalfa
- https://t.me/v2ray_youtube
- https://t.me/v2rayan
- https://t.me/v2rayargon
- https://t.me/v2rayarmy
- https://t.me/v2rayaz
- https://t.me/v2raybe
- https://t.me/v2raybold
- https://t.me/v2raybx
- https://t.me/v2raycactus
- https://t.me/v2raycollectordonate
- https://t.me/v2raycrow
- https://t.me/v2raycustomize
- https://t.me/v2raydiyako
- https://t.me/v2rayeservers
- https://t.me/v2rayfa
- https://t.me/v2rayfast
- https://t.me/v2rayfast_7
- https://t.me/v2rayfr
- https://t.me/v2rayfree
- https://t.me/v2rayfree1
- https://t.me/v2rayhubvip
- https://t.me/v2rayi_net
- https://t.me/v2raying
- https://t.me/v2rayip1
- https://t.me/v2rayir1
- https://t.me/v2rayland02
- https://t.me/v2rayn_openavpn
- https://t.me/v2rayn_red
- https://t.me/v2rayn_store
- https://t.me/v2rayng110n
- https://t.me/v2rayng12023
- https://t.me/v2rayng20000000
- https://t.me/v2rayng3
- https://t.me/v2rayng8833
- https://t.me/v2rayng_81
- https://t.me/v2rayng_channel_vpn
- https://t.me/v2rayng_fast
- https://t.me/v2rayng_ip
- https://t.me/v2rayng_lion
- https://t.me/v2rayng_my2
- https://t.me/v2rayng_nv
- https://t.me/v2rayng_ribvar
- https://t.me/v2rayng_v
- https://t.me/v2rayng_v2_ray
- https://t.me/v2rayng_vpn
- https://t.me/v2rayng_vpnn
- https://t.me/v2rayng_vpnrog
- https://t.me/v2rayngchaannel
- https://t.me/v2rayngchannelll
- https://t.me/v2rayngcloud
- https://t.me/v2rayngco0
- https://t.me/v2rayngconfiig
- https://t.me/v2rayngconfings
- https://t.me/v2rayngfast
- https://t.me/v2rayngfreee
- https://t.me/v2rayngg_iran
- https://t.me/v2rayngim
- https://t.me/v2rayngmat
- https://t.me/v2rayngn
- https://t.me/v2rayngninja
- https://t.me/v2rayngprivate
- https://t.me/v2rayngraisi
- https://t.me/v2rayngrit
- https://t.me/v2rayngrr13
- https://t.me/v2rayngseven
- https://t.me/v2rayngte
- https://t.me/v2rayngtime
- https://t.me/v2rayngup
- https://t.me/v2rayngupp
- https://t.me/v2rayngvpn
- https://t.me/v2rayngvpn_1
- https://t.me/v2rayngvpnn
- https://t.me/v2rayngvvpn
- https://t.me/v2raynplus
- https://t.me/v2raynz
- https://t.me/v2rayopen
- https://t.me/v2raypanelhub
- https://t.me/v2rayprooo
- https://t.me/v2rayprotocol
- https://t.me/v2raysaznv
- https://t.me/v2rayshop_m
- https://t.me/v2raytg
- https://t.me/v2raytork
- https://t.me/v2raytz
- https://t.me/v2rayvmess
- https://t.me/v2rayvpn009
- https://t.me/v2rayvpn2
- https://t.me/v2rayvpnchannel
- https://t.me/v2rayvpnclub
- https://t.me/v2rayvpnking0
- https://t.me/v2rayweb
- https://t.me/v2rayy_ir
- https://t.me/v2rayy_vpn13
- https://t.me/v2rayyngvpn
- https://t.me/v2rayza
- https://t.me/v2raz
- https://t.me/v2rey_free_for_all
- https://t.me/v2reyy
- https://t.me/v2rez
- https://t.me/v2roay
- https://t.me/v2rplus
- https://t.me/v2rray1_ng
- https://t.me/v2rray_ng
- https://t.me/v2ry_proxy
- https://t.me/v2ryng01
- https://t.me/v2ryorg
- https://t.me/v2ryvip
- https://t.me/v2safe
- https://t.me/v2safee
- https://t.me/v2sezar
- https://t.me/v2shop2
- https://t.me/v2vipchannel
- https://t.me/v3410ray
- https://t.me/v5ray_ng
- https://t.me/v_2ray1
- https://t.me/v_2rayngvpn
- https://t.me/v_2rey
- https://t.me/vboxpanel
- https://t.me/vip_free_vpn02
- https://t.me/vipnetmeli
- https://t.me/vipserverstm
- https://t.me/vipufovpn
- https://t.me/vipv2rayngnp
- https://t.me/vipv2rayngvip
- https://t.me/vipv2rayvip
- https://t.me/vipv2rey
- https://t.me/vipvpn_v2ray
- https://t.me/virapn
- https://t.me/virav2ray
- https://t.me/vistav2ray
- https://t.me/vlees_v2rayng
- https://t.me/vless_vmess
- https://t.me/vlessconfig
- https://t.me/vmess_ir
- https://t.me/vmess_iran
- https://t.me/vmess_tg
- https://t.me/vmessiran
- https://t.me/vmesskhodam
- https://t.me/vmesskhodam_vip
- https://t.me/vmessorg
- https://t.me/vmessprotocol
- https://t.me/vp22ray
- https://t.me/vpidiamond
- https://t.me/vplusvpn_free
- https://t.me/vpn11_v2
- https://t.me/vpn4ir_1
- https://t.me/vpn_098
- https://t.me/vpn_315
- https://t.me/vpn_Nv1
- https://t.me/vpn_amo
- https://t.me/vpn_arta
- https://t.me/vpn_azadi_2024
- https://t.me/vpn_bal0uch
- https://t.me/vpn_booth
- https://t.me/vpn_connect
- https://t.me/vpn_famous
- https://t.me/vpn_gaming
- https://t.me/vpn_gold_free_1
- https://t.me/vpn_ioss
- https://t.me/vpn_kanfik
- https://t.me/vpn_mafia
- https://t.me/vpn_mikey
- https://t.me/vpn_nafas
- https://t.me/vpn_ocean
- https://t.me/vpn_room
- https://t.me/vpn_shop_v1
- https://t.me/vpn_storm
- https://t.me/vpn_tehran
- https://t.me/vpn_v2ra_ng
- https://t.me/vpn_v2rang_box
- https://t.me/vpn_v2rayng_gap
- https://t.me/vpn_v2rayng_iran
- https://t.me/vpn_vetiver
- https://t.me/vpn_vip_nor
- https://t.me/vpn_wedbaz2
- https://t.me/vpn_whal
- https://t.me/vpn_xw
- https://t.me/vpn_zvpn
- https://t.me/vpnafra
- https://t.me/vpnaiden
- https://t.me/vpnandroid2
- https://t.me/vpnbigbang
- https://t.me/vpnchina
- https://t.me/vpnclick
- https://t.me/vpncostume
- https://t.me/vpncostumer
- https://t.me/vpncustomize
- https://t.me/vpned
- https://t.me/vpnepic
- https://t.me/vpnfail_v2ray
- https://t.me/vpnfastservice
- https://t.me/vpnfree
- https://t.me/vpnfreeaccounts
- https://t.me/vpnfreeramoo
- https://t.me/vpngate_config
- https://t.me/vpnhat
- https://t.me/vpnhouse_official
- https://t.me/vpnhub69
- https://t.me/vpnkanfik
- https://t.me/vpnkar
- https://t.me/vpnkaro
- https://t.me/vpnmasi
- https://t.me/vpnmk1
- https://t.me/vpnowl
- https://t.me/vpnpacket
- https://t.me/vpnplus100
- https://t.me/vpnplusee_free
- https://t.me/vpnpopular2023
- https://t.me/vpnsal
- https://t.me/vpnserver_tel
- https://t.me/vpnserverrr
- https://t.me/vpnshecan
- https://t.me/vpnskyy
- https://t.me/vpnsshocean
- https://t.me/vpnstorefast
- https://t.me/vpntrt
- https://t.me/vpntwitt
- https://t.me/vpnv2rayonline
- https://t.me/vpnv2raytop
- https://t.me/vpnvg
- https://t.me/vpnwedbaz
- https://t.me/vpnwlf
- https://t.me/vpnworldone
- https://t.me/vpnxyam_ir
- https://t.me/vpnyes
- https://t.me/vpray3
- https://t.me/vtechno_vpn
- https://t.me/vtworay_wolf
- https://t.me/wancloudfa
- https://t.me/warphiddify
- https://t.me/wbnet
- https://t.me/wbrovers
- https://t.me/wearestand
- https://t.me/webhube
- https://t.me/webovpn
- https://t.me/webrovers
- https://t.me/webshecan
- https://t.me/weepeen
- https://t.me/white_servers_turkmenistan
- https://t.me/wizyvpn
- https://t.me/womanlifefreedom13
- https://t.me/womanlifefreedomvpn
- https://t.me/world_vmess
- https://t.me/wsbvpn
- https://t.me/wxdy666
- https://t.me/wxgmrjdcc
- https://t.me/x4azadi
- https://t.me/xiaobaicaifx
- https://t.me/xiaoxinv
- https://t.me/xiv2ray
- https://t.me/xivpn
- https://t.me/xnxv2ray
- https://t.me/xray_vpn_pro
- https://t.me/xrayzxn
- https://t.me/xvproxy
- https://t.me/yaney_01
- https://t.me/yangcun68
- https://t.me/yasv2ray
- https://t.me/yekoyekvpn
- https://t.me/ys_v2ray
- https://t.me/ytte3la
- https://t.me/yuproxytelegram
- https://t.me/yxjnode
- https://t.me/zabuza_shop
- https://t.me/zar_vpn
- https://t.me/zdyz2
- https://t.me/zede_filteri
- https://t.me/zedmodeonvpn
- https://t.me/zedping
- https://t.me/zen_cloud
- https://t.me/zerobaipiao
- https://t.me/zeynabghatee
- https://t.me/zibanabz
- https://t.me/zilatvpn
- https://t.me/zqfxpd
- https://t.me/zvpnn
- https://t.me/zyfxlnn
- https://t.me/wxdy666
- https://t.me/jcvpn
- https://t.me/allv2board
- https://t.me/v2raydailyupdate
- https://t.me/freeVPNjd
- https://t.me/baipiaowansui
- https://t.me/juzibaipiao
- https://t.me/zyfxlnn
- https://t.me/ShareCentrePro
- https://t.me/murandepindao
- https://t.me/aries_init
- https://t.me/forwardv2ray
- https://t.me/xiaoxinv
- https://t.me/bpjzx2
- https://t.me/qwjhfx
- https://t.me/ltscxk
- https://t.me/jiedian24
- https://t.me/Free166
- https://t.me/baipiaojiedian
- https://t.me/changfengchannel
- https://t.me/freeshadowsock
- https://t.me/onessr
- https://t.me/ShadowsocksRssr
- https://t.me/ShareCentre
- https://t.me/ssrshares
- https://t.me/SSRSUB
- https://t.me/suyucom
- https://t.me/vpn880
- https://t.me/ZDYZ2
- https://t.me/sdffnkl
- https://t.me/linux_do_channel
"""

# ===================== 解析与提取频道 =====================
TG_CHANNELS = []
for line in _RAW_CHANNELS.split('\n'):
    match = re.search(r't\.me/([a-zA-Z0-9_]+)', line)
    if match:
        TG_CHANNELS.append(match.group(1))
# 自动去重
TG_CHANNELS = list(set(TG_CHANNELS))
# =================================================

# ----------------- ⚙️ 内核与解析模块 -----------------
def setup_clash_core():
    sys_os = platform.system().lower()
    if sys_os == 'windows':
        core_name, dl_url = 'mihomo.exe', "https://github.com/MetaCubeX/mihomo/releases/download/v1.18.3/mihomo-windows-amd64-v1.18.3.zip"
    else:
        core_name, dl_url = 'mihomo', "https://github.com/MetaCubeX/mihomo/releases/download/v1.18.3/mihomo-linux-amd64-v1.18.3.gz"

    if os.path.exists(core_name): return f"./{core_name}" if sys_os != 'windows' else core_name
    print(f"\n[*] 正在下载测速内核: {core_name} ...")
    try:
        if dl_url.endswith('.gz'):
            urllib.request.urlretrieve(dl_url, 'mihomo.gz')
            with gzip.open('mihomo.gz', 'rb') as f_in, open(core_name, 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
            os.remove('mihomo.gz')
            os.chmod(core_name, 0o755)
        elif dl_url.endswith('.zip'):
            urllib.request.urlretrieve(dl_url, 'mihomo.zip')
            with zipfile.ZipFile('mihomo.zip', 'r') as zip_ref:
                exe_name = [n for n in zip_ref.namelist() if n.endswith('.exe')][0]
                zip_ref.extract(exe_name)
                os.rename(exe_name, core_name)
            os.remove('mihomo.zip')
    except Exception as e:
        print(f"  ✗ 下载失败: {e}")
        sys.exit(1)
    return f"./{core_name}" if sys_os != 'windows' else core_name

def search_telegram(channels, pass_name="TG频道抓取"):
    """通过 Telegram 网页预览版 (t.me/s/) 抓取最新的订阅链接"""
    raw_urls = set()
    print(f"\n[*] 开始【{pass_name}】，去重后真实目标频道数量: {len(channels)}")
    
    # 伪装成普通浏览器
    tg_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }

    for idx, channel in enumerate(channels, 1):
        print(f"  [{idx}/{len(channels)}] 正在扫荡: @{channel}")
        
        url = f"https://t.me/s/{channel}"
        try:
            r = requests.get(url, headers=tg_headers, timeout=15)
            if r.status_code != 200:
                continue

            # 正则提取链接
            found_links = re.findall(r'https?://[^\s\'"<>\]\)]+', r.text)
            
            for link in found_links:
                link = link.rstrip('.,;\'\")]}>\\')
                lower_link = link.lower()
                
                # 排除黑名单域名
                if any(b in lower_link for b in BLACKLIST_DOMAINS):
                    continue
                    
                # 命中可能是订阅源的特征
                if any(kw in lower_link for kw in ['sub', 'yaml', 'txt', 'pastebin', 'gist', 'api', 'share', 'proxies', 'v2ray']):
                    raw_urls.add(link)

        except Exception as e:
            pass
            
        # 停顿 1.5 秒，保护 GitHub IP 不被 TG 拉黑
        time.sleep(1.5)
        
    return list(raw_urls)

def fetch_and_parse_nodes(url):
    proxies = []
    try:
        r = requests.get(url, headers={"User-Agent": "ClashforWindows/0.20.39"}, timeout=8)
        if r.status_code == 200:
            content = r.text.strip()
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict) and 'proxies' in data: return data['proxies']
            except: pass
        sub_api = f"https://sub.xeton.dev/sub?target=clash&insert=false&url={quote_plus(url)}"
        r_sub = requests.get(sub_api, headers={"User-Agent": "ClashforWindows/0.20.39"}, timeout=12)
        if r_sub.status_code == 200:
            data = yaml.safe_load(r_sub.text)
            if isinstance(data, dict) and 'proxies' in data: return data['proxies']
    except: pass
    return proxies

# ----------------- 🛡️ 安全与漏斗模块 -----------------
def is_valid_proxy(p):
    """Python层强洗数据，防止 YAML 转换引发内核致命错误"""
    try:
        if not p.get('type') or not p.get('server') or not p.get('port'): return False
        port = int(p['port'])
        if port < 1 or port > 65535: return False
        p['port'] = port 
        ptype = str(p['type']).lower()
        p['type'] = ptype
        if ptype in ['vmess', 'vless']:
            uuid_val = str(p.get('uuid', ''))
            if not re.match(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', uuid_val): return False
        if ptype in ['trojan', 'ss'] and not p.get('password'): return False
        return True
    except: return False

def tcp_ping(proxy_dict):
    host, port = proxy_dict.get('server'), proxy_dict.get('port')
    try:
        with socket.create_connection((host, int(port)), timeout=TCP_TIMEOUT): return proxy_dict
    except: return None

def get_geo_info(servers):
    """🌍 批量获取节点IP所属国家代码"""
    location_map = {}
    unique_servers = list(set(servers))
    for i in range(0, len(unique_servers), 100):
        batch = unique_servers[i:i+100]
        payload = [{"query": s, "fields": "countryCode,query"} for s in batch]
        try:
            r = requests.post("http://ip-api.com/batch", json=payload, timeout=10)
            if r.status_code == 200:
                for res in r.json():
                    if res.get('countryCode'): location_map[res['query']] = res['countryCode']
        except: pass
        time.sleep(1.5) 
    return location_map

def core_rest_ping(node):
    name = quote_plus(node['name'])
    api_url = f"http://127.0.0.1:9090/proxies/{name}/delay?timeout={REAL_TEST_TIMEOUT}&url=http://www.gstatic.com/generate_204"
    try:
        r = requests.get(api_url, timeout=(REAL_TEST_TIMEOUT / 1000) + 1)
        data = r.json()
        if 'delay' in data and data['delay'] > 0:
            node['delay'] = data['delay'] 
            return node
    except: pass
    return None

def generate_clash_yaml(alive_proxies):
    alive_proxies.sort(key=lambda x: x.get('delay', 9999))
    for p in alive_proxies: p.pop('delay', None)
    config = {
        'port': 7890, 'socks-port': 7891, 'allow-lan': True, 'mode': 'rule', 'log-level': 'info',
        'proxies': alive_proxies,
        'proxy-groups': [
            {'name': '🚀 节点选择', 'type': 'select', 'proxies': ['♻️ 自动测速', 'DIRECT'] + [p['name'] for p in alive_proxies]},
            {'name': '♻️ 自动测速', 'type': 'url-test', 'url': 'http://www.gstatic.com/generate_204', 'interval': 300, 'proxies': [p['name'] for p in alive_proxies]}
        ],
        'rules': ['MATCH,🚀 节点选择']
    }
    return yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)

# ===================== 🚀 主函数入口 =====================
def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("错误: 缺少 Telegram 环境变量"); sys.exit(1)

    print("="*60)
    print(f" 👑 启动 [Telegram] 终极兵器: 扫荡 {len(TG_CHANNELS)} 个频道")
    print("="*60)

    # 1. 扫荡 TG 频道获取原始订阅链接
    all_links = set(search_telegram(TG_CHANNELS, "TG 频道极速扫荡"))
    if not all_links: 
        print("[!] 没有抓到任何有效链接，提早下班。")
        sys.exit(1)

    # 2. 解析重组与强校验 (漏斗0)
    print(f"\n[*] 降维解析节点，发现 {len(all_links)} 个潜在订阅源...")
    raw_proxies = []
    # 🚀 加大解析并发到 40
    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        for proxies in executor.map(fetch_and_parse_nodes, all_links):
            if proxies: raw_proxies.extend(proxies)

    unique_proxies = {}
    for p in raw_proxies:
        if isinstance(p, dict) and is_valid_proxy(p):
            key = f"{p['server']}:{p['port']}"
            if key not in unique_proxies:
                p['name'] = f"TempNode-{len(unique_proxies)}"
                unique_proxies[key] = p
    nodes_to_test = list(unique_proxies.values())
    print(f"    - 结构完好且去重后，共 {len(nodes_to_test)} 个节点。")
    if not nodes_to_test: sys.exit(1)

    # 3. 极速 TCP 预筛 (漏斗1)
    print("\n[*] [漏斗一] TCP 极速端口预筛...")
    tcp_alive_nodes = []
    # 🚀 瞬间拉满 TCP 并发到 150，极速扫盘
    with concurrent.futures.ThreadPoolExecutor(max_workers=150) as executor:
        for result in executor.map(tcp_ping, nodes_to_test):
            if result: tcp_alive_nodes.append(result)
    print(f"    - 预筛存活: {len(tcp_alive_nodes)} / {len(nodes_to_test)}")
    if not tcp_alive_nodes: sys.exit(1)

    # 4. 🌍 批量获取国家标识并重命名
    print("\n[*] 正在批量查询存活节点的地理位置归属 (IP-API)...")
    servers_to_query = [p.get('server') for p in tcp_alive_nodes if p.get('server')]
    geo_map = get_geo_info(servers_to_query)
    for idx, p in enumerate(tcp_alive_nodes):
        cc = geo_map.get(p.get('server'), "UN")
        emoji = COUNTRY_EMOJIS.get(cc, "🏳️‍🌈")
        p_type = str(p.get('type', 'node')).upper()
        p['name'] = f"{emoji}-{cc}-{p_type}-{idx+1:03d}"

    # 5. 内核排雷预检 (漏斗2)
    core_path = setup_clash_core()
    print("\n[*] [漏斗二] 内核级语法强校验 (Mihomo -t 预检排雷)...")
    safe_nodes = []
    chunk_size = 200
    temp_check_file = 'core_check_temp.yaml'
    
    for i in range(0, len(tcp_alive_nodes), chunk_size):
        chunk = tcp_alive_nodes[i:i+chunk_size]
        with open(temp_check_file, 'w', encoding='utf-8') as f: yaml.dump({'proxies': chunk}, f, allow_unicode=True)
        res = subprocess.run([core_path, '-t', '-f', temp_check_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            safe_nodes.extend(chunk) 
        else:
            # 揪出致死节点
            for node in chunk:
                with open(temp_check_file, 'w', encoding='utf-8') as f: yaml.dump({'proxies': [node]}, f, allow_unicode=True)
                s_res = subprocess.run([core_path, '-t', '-f', temp_check_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if s_res.returncode == 0: safe_nodes.append(node)
                    
    if os.path.exists(temp_check_file): os.remove(temp_check_file)
    print(f"    - 排雷完毕！获得纯净防崩节点: {len(safe_nodes)} / {len(tcp_alive_nodes)}")
    if not safe_nodes: sys.exit(1)

    # ==================== 🚀 新增环节：发送【测速前全量包】 ====================
    print("\n[*] [阶段汇报] 正在向 Telegram 推送【测速前全量防崩节点】...")
    pre_nodes = [p.copy() for p in safe_nodes]
    pre_yaml_content = generate_clash_yaml(pre_nodes)
    pre_file_obj = io.BytesIO(pre_yaml_content.encode("utf-8"))
    pre_file_obj.name = f"PreTest_TG_GeoNodes_{len(safe_nodes)}.yaml"

    pre_payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": f"🚀 <b>[测速前全量包] 待测节点档案</b>\n\n🎯 <b>节点总数:</b> {len(safe_nodes)} 个\n🛡 <b>当前进度:</b> 已通过 TCP预筛 & 语法校验\n🌍 <b>节点名称:</b> 已注入 GeoIP 归属地\n⏳ <b>下一步:</b> 即将启动耗时 Mihomo 真机测速...",
        "parse_mode": "HTML"
    }
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument", data=pre_payload, files={"document": pre_file_obj}, timeout=60)
        print("  ✓ 测速前全量包推送成功！")
    except Exception as e:
        print(f"  ✗ 测速前全量包推送异常: {e}")
    # =======================================================================

    # 6. Mihomo 真机验证 (漏斗3) - 全量分批测试汇总版
    print("\n[*] [漏斗三] 启动 Mihomo 内核进行底层真机 HTTP 验证 (智能分批测速)...")
    
    alive_proxies = []
    BATCH_SIZE = 2000 # 每次安全吞吐量 2000 个
    total_batches = (len(safe_nodes) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(total_batches):
        batch_nodes = safe_nodes[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
        print(f"\n    >> 正在处理批次 {i+1}/{total_batches} (包含 {len(batch_nodes)} 个节点) ...")
        
        with open('core_temp.yaml', 'w', encoding='utf-8') as f:
            yaml.dump({'port': 7890, 'external-controller': '127.0.0.1:9090', 'proxies': batch_nodes}, f, allow_unicode=True)

        clash_process = subprocess.Popen([core_path, '-f', 'core_temp.yaml'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 探测API是否启动
        api_ready = False
        for _ in range(15):
            try:
                if requests.get("http://127.0.0.1:9090/", timeout=1).status_code == 200:
                    api_ready = True
                    break
            except: pass
            time.sleep(1)
            
        if not api_ready:
            print(f"    [!] 批次 {i+1} 内核 API 启动超时，跳过本批次。")
            clash_process.terminate(); clash_process.wait()
            continue

        if clash_process.poll() is not None:
            print(f"    [!] 批次 {i+1} 内核崩溃，跳过。")
            continue

        try:
            # 内核测速保持稳健并发 (30) 保护免费 2核 CPU
            with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
                for result in executor.map(core_rest_ping, batch_nodes):
                    if result:
                        alive_proxies.append(result)
                        print(f"      ✓ {result['name']} (延迟: {result['delay']}ms)")
        finally:
            clash_process.terminate(); clash_process.wait()
            if os.path.exists('core_temp.yaml'): os.remove('core_temp.yaml')

    if not alive_proxies: 
        print("\n[!] 灾难级情况：所有批次测速完毕，没有发现任何存活节点！")
        sys.exit(1)

    # 7. 生成报告 (最终极品测速包)
    print("\n[*] 推送【测速后极品包】至 Telegram...")
    yaml_content = generate_clash_yaml(alive_proxies)
    file_obj = io.BytesIO(yaml_content.encode("utf-8"))
    file_obj.name = f"Ultimate_TG_GeoNodes_{len(alive_proxies)}.yaml"

    payload_final = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": f"👑 <b>[Telegram 极品专属配置]</b>\n\n🎯 <b>测速后存活:</b> {len(alive_proxies)} 个\n📡 <b>侦察频道:</b> {len(TG_CHANNELS)} 个\n🛡 <b>验证引擎:</b> 极速并发预筛 + 分批真机测速\n🌍 <b>命名优化:</b> GeoIP归属地解析\n🕒 <b>时间:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "parse_mode": "HTML"
    }
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument", data=payload_final, files={"document": file_obj}, timeout=60)
        print("  ✓ 最终极品包推送成功！")
    except Exception as e:
        print(f"  ✗ 推送异常: {e}")

if __name__ == "__main__":
    main()
