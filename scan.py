#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from pathlib import Path

# ==================== 配置 ====================
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

NUM_RESULTS = 100
SLEEP_BETWEEN_KEYWORDS = 1.5
MAX_WORKERS = 30
FETCH_WORKERS = 30
TEST_TIMEOUT = 12

SEEDS_FILE = "seeds_domains.txt"

# ==================== Google Dorks 专属挖掘词（SERPER 安全防错版） ====================
KEYWORDS = [
    'api/v1/client/subscribe',
    'osubscribe.php?sid',
    'sub?target=clash',
    'subscribe?token',
    'type: hysteria2',
    'site:pastebin.com subscribe',
    'site:telegra.ph 免费节点 订阅',
    'site:rentry.co clash节点',
    'site:t.me/s/ subscribe',
    '免费机场 订阅 2026',
    '白嫖机场 订阅 clash',
    '机场面板 订阅 v2board',
    '机场 订阅链接 bit.ly'
]

# ==================== 真实订阅域名最终完整种子 (500+ 去重全量版) ====================
INITIAL_SEEDS = [
    "088ea81a-3547-85e0-4af6-dfcb3c6674aa.372372.xyz", "1.kongcheng777.dpdns.org", "1.mjjclub.top", "123.ziqiyun.xyz",
    "1349701107-files.gitbook.io", "1bbbaf.one", "1e3y2.no-mad-world.club", "2.342242.icu", "2.juanwangjc.top", "22na.cn",
    "2983839.xyz", "3.mjjspeed.top", "316.sub987.top", "33147899awhlop6658.hssl8088.icu", "342242.icu", "38.175.196.72",
    "47.242.128.61", "47.76.155.27", "4ofkc.no-mad-sub.one", "523qaweg246.pandafly.site", "52daishu.uk", "66ds.dishujichang.xyz",
    "7m8tk.no-mad-world.club", "8088.hssl8088.icu", "9770f00d98e.bigbigwatermelon.com", "a.jiedianxielou.workers.dev", "a335.sbs",
    "aa.dabai.in", "aaaa.gay", "ab.dabai.in", "abc.xhonor.top:9066", "ableton.com", "act.oxfam.org", "activemelody.com", "activemesa.com",
    "acyunsa.sbs", "ad.rd06.com", "afun-waf.trafficmanager.net", "airtable.com", "alipromo.com", "aliyun.com", "allets.com",
    "alzheimers.org.uk", "amatrixap.com", "amazon.ae", "amazon.com", "amazon.es", "anrdoezrs.net", "apa.dyljstar.sbs",
    "api-bigbear-v2-sub.sodtool.com", "api-goodtek.loliloli.live", "api.1vpn.sbs", "api.aca.best", "api.fast.com", "api.flowercloud.xyz",
    "api.immtel.me", "api.kuke-sub.com", "api.ktmcloud.id", "api.liangxin.xyz", "api.oxycontinon.com", "api.sanfennetwork.com",
    "api.scyu.xyz", "api.star-history.com", "api.suying666.info", "api.weibo.cn", "api.ytoo.xyz", "api.yuyan.vin", "api2.52tb.xyz",
    "api3.52tb.xyz", "apollographql.com", "app.bitrise.io", "app.deepsource.com", "app.denza.xyz", "app.hellothematic.com",
    "app.paymento.io", "app.tline.website", "apple.slashdot.org", "applink.feishu.cn", "apps.webofknowledge.com", "appurl.ppacc.cc",
    "area.chinadevelop21.org", "astropix.org", "auto.daum.net", "autolackaffen-shop.de", "avanquest.com", "avon.qualtrics.com",
    "b.jiedianxielou.workers.dev", "b.zodacc2.com", "b3b0549e-160e-495a-a528-cccf5148bc48.372372.xyz", "bac-l.net", "bafang",
    "bajie.info", "bajie.pw", "bakapie", "bakapie.cf", "barnyardtheatre.co.za", "bazarhorizonte.com.br", "bbs2.ruliweb.daum.net",
    "beifengyuns", "beifengyuns.top", "bestanime.co.kr", "bestfriends.org", "bh.jiedianxielou.workers.dev", "bigairport.icu",
    "bigbasket.com", "biteb.club", "blanco-germany.com", "blog.zzounds.com", "blogger.com", "bnsubservdom", "books.slashdot.org",
    "boost1", "boost1.shop", "bp-toys.com", "bpjc.lol", "brighamandwomens.org", "broadcom.com", "btxst.eu.cc", "buahfancha.com",
    "bujidao302.com", "by.xbygood.xyz", "bypassgo.com", "byte11", "byte11.com", "byte33.com", "byte77", "byte77.com", "c.sdm.lat",
    "c0d97821eafa5.nydy.cc", "cameta.com", "camp-fire.jp", "canadadrives.ca", "canva.com", "car-plus.com.tw", "carpetpacific",
    "carpetpacific.com", "cb.dabai.in", "cc.dabai.in", "ccsub", "ccsub.org", "ccwu.cc", "cdc502", "cdc502.online", "cdn.1454250.xyz",
    "cdn.huojian999.xyz", "cdn.plaid.com", "cdn.tlsa.top", "cf-workers-sub-16w.pages.dev", "cf-workers-sub-6g0.pages.dev", "cf.chesszyh.xyz",
    "chaoxi.fun", "chaozhuowang.com", "chefsteps.com", "chromatic.com", "chrome.zzzmh.cn", "cigna.com", "clash2sfa.xmdhs.com",
    "classic.yarnpkg.com", "clickserve.dartsearch.net", "clickserve.eu.dartsearch.net", "clickserve.us2.dartsearch.net", "cloud.anyijc.top",
    "cloudupup.com", "cococloud.online", "cocoduck", "codecov.io", "conf1.hokkaido-toyoni.com", "config-sync", "config-sync.com",
    "config.huojian111.com", "constitutionalhealth.com", "contentatscale.ai", "cpdd.one", "cryptosquare.org", "customs.go.kr",
    "cutleryandmore.com", "d7b12d59-21aa-9561-087f-89c834ac7fe8.372372.xyz", "dabai.in", "daijob.com", "dash.djjc.cfd", "dash.harry.lv",
    "dash.knjc.cfd", "dash.pqjc.site", "dash.xn--cp3a08l.com", "dash.yfjc.xyz", "dashboard.plaid.com", "davidcantone.com",
    "dddddddddddddd.cc", "demo.wuqb2i4f.workers.dev", "developers.redhat.com", "developers.slashdot.org", "developers.weixin.qq.com",
    "devshive.tech", "diamondresorts.com", "digitalrev4u.com", "dishujichang.xyz", "disk.pku.edu.cn", "disk.pku.edu.cn:443",
    "divide.jd.com", "djjc", "djjc.cfd", "dmp.citiservi.es", "dobrerowery.pl", "dogvacay.com", "doubledou.win", "download.8886698.xyz",
    "download.edius.de", "downloads.onelighter.site", "dp3.config-sync.com", "dpbolvw.net", "dy.2983839.xyz", "dy.588511.xyz",
    "dy.boost1.shop", "dy.pmy666.xyz", "dy.shandiandog.com", "dy.tntv2.xyz", "dy.ucat.live", "dy.wenliansub.com", "dy.xyyjc.top",
    "dyljstar", "dyljstar.sbs", "dyzk.020318.xyz", "dzpd.jiedianxielou.workers.dev", "e-liquidwinkel.securearea.eu", "e.db01.in",
    "e7yr5.no-mad-world.club", "ec.europa.eu", "ec.wjkc.xyz", "edaily.co.kr", "edmunds.com", "edu.dianping.men", "efanyunapi",
    "efanyunapi.com", "efcloud.bio", "efcloud.cc", "egovframe.go.kr", "elamanecer.org", "elephant", "elibrary.ru", "encinal.org",
    "endless.com", "energyonline.com", "entertainment.slashdot.org", "era.int", "ereplacementparts.com", "erf.de", "ericsaade.com",
    "ermao", "es.aliexpress.com", "eservicepayments.com", "eshop.wurth.pl", "ethicalrevolution.co.uk", "eur-lex.europa.eu", "eurocamp.nl",
    "eventbrite.com", "evermart.dk", "evo-lution.ru", "extrememetalproducts.com", "f2vip", "f2vip.net", "falabella.com",
    "falabella.com.co", "falcocloud.730894.xyz", "fastestcloud.xyz", "fb.22na.cn", "fba01.fbsubcn01.cc", "fbsubcn", "fbsubcn01.cc",
    "fcapp", "fcapp.run", "feiniaoyun.org", "feiniaoyun11.life", "fitbit.com", "fku-ppg.co.uk", "flow.cl", "flowercloud",
    "flowercloud.xyz", "flybarurl.com", "flybit", "flynb.site", "fm-sub-mainpanel-vygijfogpm.cn-shanghai.fcapp.run", "fn0618",
    "fn0618.xyz", "forever.fordham.edu", "forum.ableton.com", "fractal-design.com", "fratellikarida.com", "fredrik-vogt.de",
    "freetochoose.tv", "front.fishport.cloud", "fsxdz.us.kg", "fu-sen.in", "funabashi.mypl.net", "fundrazr.com", "g.luxury",
    "ga-sub", "ga-sub.hair", "gates.djjc.cfd", "genome-euro.ucsc.edu", "genome.ucsc.edu", "get.affiliatescn.net", "ggbong",
    "ggbong.xyz", "ginfem.com", "gitlab.com", "glados", "glados-config.com", "globalsources.com", "gofundme.com", "gogofp.com",
    "gpbikes.com", "greatdeal.life", "guolicheng.cfd", "gy.205266.xyz", "gy.lzj520hxw.dpdns.org", "gy.lzjbaby.com", "gy.lzjjjjjjj.pp.ua",
    "gy.xiaozi.ggff.net", "gy.xiaozi.us.kg", "hankookilbo.com", "hellot.net", "henet.icu", "hgwdev-max.gi.ucsc.edu", "hh.haibucuo.xyz",
    "hifix.co.uk", "hk.xmm1993.top", "hokkaido-toyoni", "hokkaido-toyoni.com", "homecenter.com.co", "honda.co.jp", "hvpn.xyz",
    "i.stga.cn", "i.v2xo.com", "ieeexplore.ieee.org", "ierboryt.spphhnhg.top", "igromania.ru", "ikuuu", "ilead.itrack.it",
    "images.zsxq.com", "img.shields.io", "indarnb.ru", "iphone-tricks.com", "issue.media.daum.net", "it.slashdot.org", "itjustasub.icu",
    "jaloucity.de", "jehsd.ssu.ac.ir", "jerome-jdmp.fr", "jh7yd.no-mad-sub.one", "jichang.123417.xyz", "jindouyun88.life",
    "jkun.waimaosass.icu", "jp.xmm1993.top", "jsjc", "jsjc.cfd", "jstor.org", "kabum.com.br", "kats.go.kr", "kawashima-ya.jp",
    "kfccloud.com", "kin.naver.com", "kingsroadmerch.com", "kirmizikep.com", "knjc", "knjc.cfd", "knoxops.app", "knrpc.olark.com",
    "korea.kr", "ktmcloud", "ktmcloud.id", "kuaidog", "kuaidog005.top", "kuaigou.life", "kuaiqiangshou.xyz", "kuaivpn", "kuaivpn.app",
    "kuke-sub", "kuke-sub.com", "l.dabai.in", "l.db-link01.top", "l1wn2.no-mad-world.club", "lanebryant.com", "laoyao", "laoyao.ltd",
    "latiaocloud.net", "law.go.kr", "ldgb.pages.dev", "lds.qualtrics.com", "legavolleyfemminile.it", "leonromer.nl", "let.bnsubservdom.com",
    "lexaloffle.com", "liangxin", "liangxin.xyz", "liangyuandian.vip", "lifes.nchu.edu.tw", "liftkits4less.com", "lilys.ai",
    "link.dingyueapi.net", "link.onesy.link", "link.springer.com", "link.suying666.info", "link123.52pokemon66.cc", "linkedin.com",
    "linksc.laoyao.ltd", "lmlla.lmscunb.pro", "lmscunb", "lmscunb.pro", "lnithefedhwadf2qhhald5l23zdadzci.skygo0527.top", "login.djjc.cfd",
    "login.yfjc.xyz", "lojapescaalternativa.com.br", "louwangzhiyu", "louwangzhiyu.org", "lp.landing-page.mobi", "lp.opteck.com",
    "lscluster.hockeytech.com", "luronn.com", "m11.spwvpn.com", "ma.ecsdl.org", "mall.shopee.tw", "mangapolo.com", "maplesoft.com",
    "maps.googleapis.com", "mar.bbc.xx.kg", "marathon.jd.com", "marinedepot.com", "marktplaats.nl", "maskent.com", "matrixap.com",
    "mc.jiedianxielou.workers.dev", "media.daum.net", "melectronics.ch", "mercurycommerce.com", "mfbot.tcip.top", "microsoft-update-daily.com",
    "midpen-housing.org", "ml.azure.com", "mlshu.com", "mobile-harddisk.nl", "mobile.gmarket.co.kr", "moef.go.kr", "mois.go.kr",
    "mojie", "mojie.link", "mp.weixin.qq.com", "msub.xn--m7r52rosihxm.com", "murmashilive.ru", "mycolor.space", "mydaily.co.kr",
    "myfloridalicense.com", "mzyglc", "mzyglc.xyz", "n.news.naver.com", "nanbei.cloud", "navy.com", "navyreserve.com", "nded.com",
    "nded.fr", "ndy.fn0618.xyz", "nervixapp", "nervixapp.top", "netbooknavigator.com", "neteasegames", "neteasegames.site",
    "network.ayucloud.nl", "new.gfw.news", "news.sbs.co.kr", "news.slashdot.org", "nextport", "nextport.top", "ng.69hub.cc",
    "nginx-proxy-123.69hub.cc", "niaodi.top", "ninjasub.com", "nintendo.com", "nlpcenter.ru", "no1-svip.urlapi-dodo.sbs",
    "no7-svip.urlapi-dodo", "note.youdao.com", "novc.f6net.net", "nts.go.kr", "nydy", "nydy.cc", "obdesign.com.tw", "occto.or.jp",
    "omi.cdn-go.cn", "onedrive.live.com", "onetime.com", "onlineweb.work", "onlysub", "onlysub.mjurl.com", "openads.co.kr",
    "opensource.adobe.com", "order.investorplace.com", "osubscribe.flowercloud.xyz", "osubscribe.ytoo.xyz", "ourtime.com",
    "oxycontinon", "oxycontinon.com", "oymr1a9aua.todust.cc", "page.kakao.com", "pakash.co.il", "panel.nextnet.one", "paolu.pics",
    "payeasy.com.tw", "paypal.com", "pcq7y.no-mad-world.club", "pdda.me", "peace.mimon.cc", "peakauto.com", "permire-fabrica.ch",
    "pfjc.im", "pilor.net", "pilot.datatrans.biz", "pineapple.uk.com", "pinterest.com", "pioneer-twn.com.tw", "pipc.go.kr",
    "pixel.everesttech.net", "plaid.com", "plasti-dip.es", "platform.djjc.cfd", "pokelink", "pokelink.xn--4gsvmh74cwxi.cn",
    "poolpowershop.de", "portal.nextport.top", "ppacc", "ppacc.cc", "pqjc", "pqjc.site", "pravda.ru", "priceline.com.au",
    "primcast.com", "prjcm.itr.lol", "processon.com", "profile.zjurl.cn", "projectorpeople.com", "prourl.ru", "pubchem.ncbi.nlm.nih.gov",
    "public.tableau.com", "pvsmi.no-mad-sub.one", "pwac.gzi8998-ddns0721.eu", "qijiavpn.salnc.kuaivpn.app", "qualitygurus.com",
    "qyapi.weixin.qq.com", "r2-c11-dd.0-w.ccwu.cc", "ratchada.terminal69.win", "redacted.sbs", "renzhesub.com", "rest.genome.jp",
    "rest.kegg.jp", "rifiv.no-mad-world.club", "rightstuf.com", "ripleys.com", "rogers.com", "rss.csgfw.top", "rss.epon.cloud",
    "rss.getfree.win", "rss.msclm.net", "rsslinghun1.xyz", "ru.wargaming.net", "run-s2.jiedianxielou.workers.dev", "s.fb.22na.cn",
    "s.juzicloud.vip", "s.sdncimcin.xyz", "s.suying666.info", "s.youyun666.site", "s1.byte11.com", "s1.byte16.com", "s1.byte33.com",
    "s1.byte77.com", "s716i.no-mad-sub.one", "samsungpop.com", "sandbox.paypal.com", "sanfen003.xyz", "savoirmaigrir.fr",
    "sb.swiftnet.cloud", "scholarshipexperts.com", "sealosgzg.site", "sears.com", "searshomeservices.com", "searspartsdirect.com",
    "sebi.gov.in", "secure.imodules.com", "secure2.convio.net", "securelb.imodules.com", "seiseki-up.info",
    "serverstodaslasverciones.blogspot.com", "service-jaz4ivuy-1313667892.gz.apigw.tencentcs.com", "session.de", "setn.com",
    "sf.342242.icu", "sfsub.gonghailin.xin", "sg.xmm1993.top", "sh.zucks.net", "shan-cloud.xyz", "simcom.eu", "sir.com.tw",
    "site.com", "skyfd.chuna.nulaiha.aasxuan.yfftftf.shop", "skygo", "skygo0527.top", "slashdot.org", "slides.com", "smallstrawberry",
    "smallstrawberry.com", "smjcdh", "smjcdh.top", "snangua.com", "so.com", "sodimac.cl", "solidot.org", "somarecords.com",
    "sonatural.co.kr", "sp.senac.br", "space.bilibili.com", "spphhnhg", "spphhnhg.top", "sports.media.daum.net", "spwvpn",
    "spwvpn.com", "ss.suyunti.cc", "ss88.beifengyuns.top", "sso.yuetoto.com", "ssr.sh", "sss.xlajiao.xyz", "ssubb.erwandingyue.net",
    "starlinkcloud.club", "starlinkcloud.xyz", "starlinkstatic", "starlinkstatic.cc", "stitcher.com", "store.grimey.es",
    "store.kakocloud.pro", "strangemusicinc.net", "streamlabs.com", "stressnomore.co.uk", "sub-1.smjcdh.top", "sub-gfwairport2.cyou",
    "sub.342242.icu", "sub.372372.xyz", "sub.54unique.com", "sub.boost1.shop", "sub.byte11.com", "sub.carpetpacific.com",
    "sub.ccpc.de5.net", "sub.ccsub.org", "sub.cocoduck.cc", "sub.config-sync.com", "sub.djjc.cfd", "sub.domiw.com", "sub.easyinternet.one",
    "sub.efanyunapi.com", "sub.fbsubcn01.cc", "sub.fcapp.run", "sub.flowercloud.xyz", "sub.fnf.one", "sub.ggbong.xyz",
    "sub.glados-config.com", "sub.hktix.net", "sub.hokkaido-toyoni.com", "sub.jsjc.cfd", "sub.kccikk.top", "sub.knjc.cfd",
    "sub.ktmcloud.id", "sub.laoyao.ltd", "sub.liangxin.xyz", "sub.liger.solutions", "sub.lmscunb.pro", "sub.love-coffee.one",
    "sub.miaopu.cf", "sub.mogufan.com", "sub.mojie.app", "sub.mojie.co", "sub.mojie.me", "sub.nervixapp.top", "sub.nvi.cc.cd",
    "sub.onlysub.mjurl.com", "sub.oxycontinon.com", "sub.pianyi.info", "sub.pigeon-sub.one", "sub.pqjc.site", "sub.sanfen017.xyz",
    "sub.smallstrawberry.com", "sub.smjcdh.top", "sub.spphhnhg.top", "sub.ssr.sh", "sub.starlinkstatic.cc", "sub.suying666.info",
    "sub.terminal69.win", "sub.todust.cc", "sub.urlapi-dodo.sbs", "sub.wdyserver.com", "sub.xjhsub", "sub.xjhsub1.top",
    "sub.xn--54qu5qypuo1o.xn--fiqs8s", "sub.xnyun.wiki", "sub.xunlian.site", "sub.xz61.cn", "sub.yfjc.xyz", "sub.ymjc.cfd",
    "sub.yuetoto.com", "sub.zyfx6.xyz", "sub0530.wdyserver.com", "sub1.efshop.cc", "sub1.elkcloud.top", "sub1.smallstrawberry.com",
    "sub1.xn--mesv7f5toqlp.com", "sub2.smallstrawberry.com", "sub3.kelecloud.xyz", "sub3.smallstrawberry.com", "suba.f2vip.net",
    "subb3xq6b.skyvpn.bond", "submit.xz61.cn", "subs.doubao.one", "subs1001.apolloxi.art", "subscr.easyinternet.one",
    "subscribe.famint.net", "subscribe511295.fengqun.info", "subscription-shortlink.pages.dev", "subscription.sukiaira.com",
    "subsub.surge.sh", "subtangniu", "subxiandan", "support.savethechildren.org", "support.zte.com.cn", "sux.lol", "suying666",
    "suying666.info", "svip.ttyun.eu.org", "talk.hackers.com", "target.com", "targetpublications.org", "tbsss.xn--xhqy01cv5qjky.com",
    "tchibo-ideas.de", "tcxf.hssl8088.icu", "techtutor.pl", "teespring.com", "terminal69", "terminal69.win", "tfhub.dev",
    "thaiticketmajor.com", "tiktokcn.xyz", "tkqlhce.com", "tline.website", "to.runba.cyou", "todust", "todust.cc", "topspeedgolf.com",
    "torysamochodowe.pl", "toutiao.com", "tracker.marinsm.com", "trains.ctrip.com", "tripmama.com", "ttyun", "ttyun.eu.org",
    "tw-elements.com", "tyutgs.wjx.cn", "u.fast6.xyz", "uecrt.no-mad-sub.one", "uefa.com", "undeadly.org", "update.glados-config.com",
    "ure.best", "url.ktmcloud01.cc", "urlapi-dodo", "urlapi-dodo.sbs", "us.elsevierhealth.com", "us.freecat.cloud", "usaknifemaker.com",
    "user.1vpn.sbs", "user.bafang.vip", "v1.efshop.cc", "v1.tlsa.top", "v2board 订阅", "v2ny", "v2ray 机场 订阅", "victoriara.com",
    "vidaron.pl", "visitjeju.net", "vlab.amrita.edu", "vliz.be", "vodafone.eu.qualtrics.com", "voot.com", "w.12.kg", "w.jiesuo.link",
    "watt24.com", "wdyserver", "wdyserver.com", "web.archive.org", "web.budgetbakers.com", "web.tline.website", "webget.yfjc.xyz",
    "wenlian", "wenliansub.com", "widgets.pinterest.com", "windowsv1", "windowsv1.com", "wjkc", "woggdingyueyuming.top",
    "woodworkersjournal.com", "work.chma.ccwu.cc", "wperfolg.de", "wsa.roe.ac.uk:8080", "wumaojichang.com", "www.ccsub.org",
    "www.elephant223.com", "www.ermao.net", "www.kuaidog005.top", "www.neteasegames.site", "www1.sunrise.ch",
    "www18.bigairport-thirteenth-sub.com", "www7th.ga-sub.hair", "wwws-staging.moneytree.jp", "wx.qq.com", "wykop.pl", "xnyun",
    "xnyun.wiki", "xgis.maaamet.ee", "xiaohongshu.com", "xlajiao", "xlajiao.xyz", "xn--30rs3bu7r87f.com", "xn--9kqs1lo79d.cc",
    "xn--ihqu10cn4cf3cfv5a.com", "xq666.xn--9iqv4mb85adml.xn--fiqs8s", "xsj520.top", "xsus.buzz", "xz61", "xz61.cn",
    "xzjb8.no-mad-world.club", "yfjc", "yfjc.xyz", "yiyolink.xyz", "ymjc", "ymjc.cfd", "ymzx.jiedianxielou.workers.dev", "ytoo",
    "ytoo.xyz", "yun.139.com", "yuetoto", "yuetoto.com", "yz6on.no-mad-world.club", "zero.76898102.xyz", "zhs.futbol"
]

INITIAL_SEEDS_LOWER = [s.lower() for s in INITIAL_SEEDS]

# ==================== 工具函数 ====================

def get_headers():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    return headers

def load_seeds() -> list[str]:
    path = Path(SEEDS_FILE)
    if path.exists():
        seeds = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        print(f"📂 已加载 {len(seeds)} 个动态种子域名（来自 {SEEDS_FILE}）")
        return seeds
    else:
        print(f"📂 种子文件不存在，写入初始 {len(INITIAL_SEEDS)} 个域名")
        path.write_text("\n".join(INITIAL_SEEDS) + "\n", encoding="utf-8")
        return INITIAL_SEEDS.copy()

def save_seeds(seeds: list[str]):
    unique = sorted(set(s.strip().lower() for s in seeds if s.strip()))
    Path(SEEDS_FILE).write_text("\n".join(unique) + "\n", encoding="utf-8")
    print(f"💾 已保存 {len(unique)} 个种子域名到 {SEEDS_FILE}")

def search_serper(query: str, num: int = 100) -> list[dict]:
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    clean_query = query.strip()
    payload = {"q": clean_query, "num": num}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 400:
            print(f"    [ERROR] 400 → {clean_query[:70]}")
            return []
        resp.raise_for_status()
        return resp.json().get("organic", [])
    except Exception as e:
        print(f"    [ERROR] 搜索失败: {e}")
        return []

def is_potential_sub_link(url: str) -> bool:
    if not url.startswith("http"):
        return False
    url_lower = url.lower()

    exclude = [
        "google.", "youtube.", "facebook.", "twitter.", "x.com", "github.com",
        "stackoverflow", "wikipedia.", "microsoft.", "apple.com", "amazon.",
        "baidu.com", "zhihu.com", "bilibili.", "weixin.", "qq.com", "taobao.",
        "reddit.com", "medium.com", "csdn.net", "juejin.", "cnblogs.",
        "gitlab.com", "bitbucket.org"
    ]
    if any(x in url_lower for x in exclude):
        return False

    strong = [
        "token=", "sid=", "/api/v1/client/subscribe", "osubscribe.php",
        "/link/", "/s?", "sub?token", "subscribe?token"
    ]
    if not any(s in url_lower for s in strong):
        if len(url) < 80:
            return False
        if not any(ext in url_lower for ext in [".cc/", ".top/", ".xyz/", ".cfd", ".sbs", ".run/", ".icu", ".info/", ".ltd", ".win/", ".shop/", ".online/", ".site/"]):
            return False

    return True

def extract_links_from_results(results: list[dict]) -> set[str]:
    links = set()
    url_pattern = re.compile(r'https?://[^\s<>"\'\)\]\}\{\|,\\\\]{15,600}')

    for item in results:
        link = item.get("link", "").strip()
        if link:
            clean = link.rstrip('.,;:!?)\'\"')
            if is_potential_sub_link(clean):
                links.add(clean)

        text = " ".join([
            item.get("title", ""),
            item.get("snippet", ""),
            item.get("link", "")
        ])
        for m in url_pattern.findall(text):
            clean = m.rstrip('.,;:!?)\'\"')
            if is_potential_sub_link(clean):
                links.add(clean)

    return links

def fetch_and_extract(url: str) -> set[str]:
    try:
        r = requests.get(url, headers=get_headers(), timeout=15)
        if r.status_code == 200:
            found = set()
            url_pattern = re.compile(r'https?://[^\s<>"\'\)\]\}\{\|,\\\\]{15,600}')
            for m in url_pattern.findall(r.text):
                clean = m.rstrip('.,;:!?)\'\"')
                if is_potential_sub_link(clean):
                    found.add(clean)
            return found
    except:
        pass
    return set()

def batch_extract_links(html_urls: set[str]) -> set[str]:
    all_found = set(html_urls)
    print(f"\n⚡ 开始多线程并发深度提取（从 {len(html_urls)} 个初筛链接中找直链）...")
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as executor:
        futures = {executor.submit(fetch_and_extract, u): u for u in html_urls}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 100 == 0:
                print(f"    ...已深度提取 {completed}/{len(html_urls)} 个来源")
            try:
                res = future.result()
                all_found.update(res)
            except:
                pass
    
    final_direct_links = {link for link in all_found if is_potential_sub_link(link)}
    return final_direct_links

def is_alive(url: str) -> tuple[str, bool, str, int]:
    headers = {
        "User-Agent": "ClashforWindows/0.20.39",
        "Accept": "*/*",
    }
    try:
        r = requests.get(url, headers=headers, timeout=TEST_TIMEOUT, allow_redirects=True, stream=True)
        if r.status_code != 200:
            return url, False, f"HTTP {r.status_code}", 0

        content = b""
        for chunk in r.iter_content(1024):
            content += chunk
            if len(content) >= 8192:
                break

        text = content.decode("utf-8", errors="ignore").lower()
        length = len(text)

        signs = [
            "proxies:", "proxy-groups:", "rules:", "port:", "socks-port:",
            "vmess://", "vless://", "trojan://", "ss://", "ssr://", "hysteria",
            "uuid", "cipher:", "password:", "network:", "ws-opts", "grpc-opts",
            "server:", "tls:", "reality", "flow:", "client-fingerprint"
        ]
        if any(s in text for s in signs):
            return url, True, "存活", length
        if length > 150 and "error" not in text[:500] and "not found" not in text[:500]:
            return url, True, "可能存活", length
        return url, False, "内容不像订阅", length

    except requests.exceptions.Timeout:
        return url, False, "超时", 0
    except Exception as e:
        return url, False, str(e)[:40], 0

def batch_test(urls: list[str]) -> list[tuple[str, int]]:
    results = []
    print(f"\n  开始测活，共 {len(urls)} 个链接...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(is_alive, u): u for u in urls}
        for future in as_completed(futures):
            url, ok, reason, length = future.result()
            if ok:
                results.append((url, length))
                print(f"    ✅ {url}  (len={length})")
            else:
                print(f"    ❌ {url[:70]}... ({reason})")
    results.sort(key=lambda x: x[1], reverse=True)
    return results

def extract_domains_from_urls(urls: list[str]) -> set[str]:
    domains = set()
    for u in urls:
        try:
            parsed = urlparse(u)
            host = parsed.netloc.lower()
            if not host:
                continue
            if host.startswith("www."):
                host = host[4:]
            if re.match(r"^\d+\.\d+\.\d+\.\d+", host):
                continue
            if len(host) > 5 and "." in host:
                domains.add(host)
        except:
            pass
    return domains

def send_txt_file(file_path: str, caption: str = "") -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[WARN] 未配置 Telegram")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            files = {"document": (os.path.basename(file_path), f)}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1000]}
            r = requests.post(url, data=data, files=files, timeout=60)
            if r.status_code == 200:
                print(f"✅ 已发送: {os.path.basename(file_path)}")
                return True
            print(f"[ERROR] 发送失败: {r.text}")
            return False
    except Exception as e:
        print(f"[ERROR] 发送异常: {e}")
        return False

def save_and_send(links: list[str], filename: str, caption: str):
    with open(filename, "w", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")
    send_txt_file(filename, caption)

# ==================== 主逻辑 ====================

def main():
    if not SERPER_API_KEY:
        print("❌ 缺少 SERPER_API_KEY 环境变量")
        return

    print("🚀 真实订阅域名最终完整版 + SERPER 安全词防错启动")
    beijing = timezone(timedelta(hours=8))
    now = datetime.now(beijing).strftime("%Y-%m-%d %H:%M:%S")
    time_tag = datetime.now().strftime("%Y%m%d_%H%M")

    seeds = load_seeds()

    before_merge = set(s.lower() for s in seeds)
    added_from_initial = []
    for d in INITIAL_SEEDS:
        d_low = d.lower().strip()
        if d_low and d_low not in before_merge:
            seeds.append(d_low)
            added_from_initial.append(d_low)
    if added_from_initial:
        print(f"🔄 从 INITIAL_SEEDS 补充了 {len(added_from_initial)} 个缺失域名")
        save_seeds(seeds)

    all_candidates = set()

    # ========== 1. 关键词搜索 (SERPER 安全词) ==========
    print(f"\n{'='*60}")
    print(f"===== ① 关键词搜索（安全词捕获公开泄露）=====")
    print(f"{'='*60}")
    for idx, kw in enumerate(KEYWORDS, 1):
        print(f"\n[{idx}/{len(KEYWORDS)}] 执行关键词: {kw}")
        
        results = search_serper(kw, NUM_RESULTS)
        found = extract_links_from_results(results)
        all_candidates.update(found)
        time.sleep(0.4)
        
        print(f"  当前累计初步候选: {len(all_candidates)}")
        time.sleep(SLEEP_BETWEEN_KEYWORDS)

    print(f"\n✅ 关键词搜索完成，当前候选链接: {len(all_candidates)}")

    # ========== 2. 真实订阅域名定向搜索（套路一：纯链接精准榨取版） ==========
    print(f"\n{'='*60}")
    print(f"===== ② 真实订阅域名定向搜索（共 {len(seeds)} 个种子）=====")
    print(f"{'='*60}")
    for idx, domain in enumerate(seeds, 1):
        print(f"  [{idx}/{len(seeds)}] → {domain}")
        
        query = f'"{domain}" token sid clash sub'
        
        results = search_serper(query, 60)
        found = extract_links_from_results(results)
        all_candidates.update(found)
        
        time.sleep(0.8)

    # ========== 3. 深度提取（从网页/分享贴中扒出直链） ==========
    all_direct_links = batch_extract_links(all_candidates)
    all_direct_links = sorted(list(all_direct_links))
    print(f"\n📦 深度提取完成，最终锁定 {len(all_direct_links)} 个纯直链候选")

    if not all_direct_links:
        print("没有提取到直链候选，结束")
        return
        
    full_filename = f"full_direct_candidates_{time_tag}.txt"
    save_and_send(all_direct_links, full_filename,
                  f"📋 完整纯直链候选列表（安全词精准提取版）\n时间: {now}\n数量: {len(all_direct_links)}")

    # ========== 4. 测活 ==========
    alive_with_score = batch_test(all_direct_links)
    alive_links = [u for u, _ in alive_with_score]
    print(f"\n✅ 测活完成：存活 {len(alive_links)} / {len(all_direct_links)}")

    if not alive_links:
        print("没有测试到存活的链接。")
        return

    alive_filename = f"alive_subs_{time_tag}.txt"
    save_and_send(alive_links, alive_filename,
                  f"✅ 存活机场纯直链（已按质量排序）\n时间: {now}\n候选: {len(all_direct_links)} | 存活: {len(alive_links)}")

    # ========== 5. 提取新域名并升级种子库 ==========
    new_domains = extract_domains_from_urls(alive_links)
    print(f"\n🧬 本次发现 {len(new_domains)} 个存活特征域名")

    before = set(s.lower() for s in seeds)
    added = []
    for d in sorted(new_domains):
        if d not in before:
            seeds.append(d)
            added.append(d)

    if added:
        print(f"✨ 新增 {len(added)} 个种子域名")
        for a in added[:30]:
            print(f"    + {a}")
        if len(added) > 30:
            print(f"    ... 还有 {len(added)-30} 个")
        save_seeds(seeds)
    else:
        print("没有新域名需要追加")

    if new_domains:
        domain_file = f"new_domains_{time_tag}.txt"
        with open(domain_file, "w", encoding="utf-8") as f:
            for d in sorted(new_domains):
                f.write(d + "\n")
        send_txt_file(domain_file, f"🧬 本次有效提取域名归档\n时间: {now}\n数量: {len(new_domains)}")

    print("\n🎉 全部完成！安全词搜索 + 深度测活均已完美执行。")

if __name__ == "__main__":
    main()
