# -*- coding: utf-8 -*-
"""novayag.com için SEO ve yapay zekâ (GEO) dosyalarını üretir.

Üretilenler:
  oyunlar/<slug>/index.html   her oyuna ayrı açılış sayfası (JSON-LD: MobileApplication + FAQPage + BreadcrumbList)
  oyunlar/index.html          tüm oyunlar listesi
  sitemap.xml, robots.txt, llms.txt
  media/og/*.png              paylaşım görselleri (1200x630)

Oyun bilgisi TEK YERDE: aşağıdaki OYUNLAR listesi. Ana sayfa (index.html) elle düzenlenir; oradaki JSON-LD de bu
listeden üretilen bloğa göre güncellenir (<!-- seo:jsonld --> işaretleri arası).

Kural (kullanıcı kararı 2026-09-25): bölüm/bulmaca/kelime SAYISI yazılmaz. Paket adları sayfada görünmez.
Çalıştırma: python tools/seo_uret.py   (site kökünde)
"""
import html
import json
import os
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SITE = "https://novayag.com"
PLAY_DEV = "https://play.google.com/store/apps/developer?id=Novayag"
EPOSTA = "yagizaydinli@novayag.com"
GUNCEL = "2026-09-27"

# En yeni üstte (ana sayfadaki sıra). yayinda=False → Play'de herkese açık değil ("yakında").
OYUNLAR = [
    dict(slug="kelime-esle", ad="Kelime Eşle", magaza_adi="Kelime Eşle: Kelime Oyunu", pkg="com.novayag.kelimeesle",
         yayinda=False, renk="#2f8fe0", video=True, tur="Kelime · Bulmaca", cevrimdisi=True, online=False,
         slogan="Balonlardaki kelimeleri doğru gruba topla.",
         ozet="Kelime Eşle, balonlara dağılmış kelimeleri kategorilerine göre birleştirdiğin Türkçe bir kelime gruplama oyunu. "
              "Grup tamamlanınca kategori ortaya çıkar ve balon patlar; her birleştirme bir hamle harcar.",
         nasil=["Bir balonu sürükle, aynı gruptaki bir kelimenin üstüne bırak.",
                "Doğru eşleşmede balonlar birleşir ve büyür; grubun bütün kelimeleri toplanınca kategori ortaya çıkar.",
                "Her birleştirme bir hamle harcar; yanlış gruba bırakmak da hamle yer. Hamlen bitmeden tahtayı temizle.",
                "İlerledikçe birbirine yakın kategoriler (örneğin ülkeler ve tahıllar: \"Mısır\") aynı tahtaya gelir."],
         ozellik=["Kolaydan zora giden bölümler, ilerledikçe birbirine yakın kategoriler",
                  "Büyüteç (gizli bir grubu gösterir), Mıknatıs (iki eşi hamlesiz birleştirir) ve +2 Yer güçlendiricileri",
                  "Günlük hediye ve sandık ödülleri",
                  "İnternetsiz oynanır; hesap ya da kayıt gerekmez",
                  "Canlı renkler, patlama efektleri, ses ve titreşim ayarları"],
         sss=[("Kelime Eşle nasıl oynanır?", "Aynı kategorideki kelimeleri taşıyan balonları sürükleyip birbirinin üstüne bırakırsın. Grubun tüm kelimeleri birleşince kategori ortaya çıkar ve balon patlar. Hamlelerin bitmeden bütün grupları tamamlaman gerekir."),
              ("Kelime Eşle internetsiz oynanır mı?", "Evet. Bütün bölümler telefona yüklü gelir; internet yalnızca isteğe bağlı reklamlar için kullanılır."),
              ("Takıldığımda ne yapabilirim?", "Büyüteç bir grubun kelimelerini ve adını gösterir, Mıknatıs aynı gruptan iki kelimeyi hamle harcamadan birleştirir, +2 Yer tahtada sıkıştığında yer açar. Hamlen bitince ek hamleyle devam edebilirsin.")],
         anahtar=["kelime gruplama oyunu", "kategori bulmaca", "kelime eşleştirme", "internetsiz kelime oyunu"]),
    dict(slug="kare-bulmaca", ad="Kare Bulmaca", magaza_adi="Kare Bulmaca: Çapraz Bulmaca", pkg="com.novayag.capraz",
         yayinda=False, renk="#f0702e", video=True, tur="Bulmaca", cevrimdisi=True, online=False,
         slogan="Gazetedeki çapraz bulmaca, telefonunda.",
         ozet="Kare Bulmaca, Türkçe hazırlanmış çapraz (kare) bulmaca uygulaması. Mini 5×5'ten büyük 9×9'a üç boyutta, "
              "kolaydan zora sıralanmış bulmacalar ve takıldığında yol gösteren ipuçları sunar.",
         nasil=["Bir kareye dokun; kelimenin tanımı üstte görünür. Aynı kareye tekrar dokunarak yatay ve dikey arasında geç.",
                "Türkçe klavyeyle harfleri yaz; doğru cevaplar kilitlenir, hatalar istersen anında gösterilir.",
                "Takılırsan kelimenin örnek cümlesini gör, bir harf ya da bütün kelimeyi aç veya bulmacayı kontrol et."],
         ozellik=["Üç boyut: Mini 5×5, Orta 7×7, Büyük 9×9",
                  "Kolay, Orta ve Zor ciltler",
                  "Tanım, örnek cümle, harf aç, kelime aç ve kontrol et ipuçları",
                  "Ç, Ğ, İ, Ö, Ş, Ü tek dokunuşla; süre tutma; göz yormayan koyu tema",
                  "İnternetsiz oynanır; hesap ya da kayıt gerekmez"],
         sss=[("Kare Bulmaca ile çengel bulmaca arasındaki fark ne?", "Kare (çapraz) bulmacada tanımlar ızgaranın dışında, numaralı listededir; çengel bulmacada tanımlar ızgaranın içindeki karelerde yazar. Novayag'ın ikisi için de ayrı oyunu var: Kare Bulmaca ve Çengel Bulmaca."),
              ("Kare Bulmaca internetsiz çalışır mı?", "Evet. Bulmacalar ve ipuçları telefonda bulunur; internet gerekmez."),
              ("Bulmacalar Türkçe mi, çeviri mi?", "Hepsi Türkçe hazırlandı; tanımlar bu oyun için yazıldı, çeviri bulmaca yok.")],
         anahtar=["kare bulmaca", "çapraz bulmaca", "Türkçe bulmaca uygulaması", "internetsiz bulmaca"]),
    dict(slug="petek", ad="Petek", magaza_adi="Petek: Günlük Kelime Oyunu", pkg="com.novayag.petek",
         yayinda=False, renk="#b07a0c", video=True, tur="Kelime · Günlük", cevrimdisi=True, online=False,
         slogan="Yedi harf, her gün yeni bir petek.",
         ozet="Petek, her gün yeni bir bulmaca sunan Türkçe bir kelime türetme oyunu. Yedi harfli peteğin ortasındaki harfi "
              "kullanarak bulabildiğin kadar kelime türetirsin; günün peteği herkes için aynıdır.",
         nasil=["Petekte yedi harf var; ortadaki sarı harf her kelimede geçmek zorunda.",
                "Diğer harfleri istediğin sırayla ve istediğin kadar tekrar ederek en az dört harfli kelimeler kur.",
                "Yedi harfin hepsini kullanan kelime pangramdır ve fazladan puan kazandırır.",
                "Buldukça rütbe atlarsın: Yavru Arı'dan Kraliçe Arı'ya."],
         ozellik=["Her gün gece yarısı yenilenen, herkes için aynı bulmaca",
                  "Rütbeler, rozet koleksiyonu ve gün serisi",
                  "Takvim: geçmiş günlerin kaçırılan kelimelerini öğren",
                  "Cevabı vermeyen ipucu tablosu (baş harf ve uzunluk dağılımı)",
                  "TDK kök kelimeleri; açık ve koyu tema; internetsiz oynanır"],
         sss=[("Petek, Spelling Bee'nin Türkçesi mi?", "Benzer bir fikirle çalışır: yedi harf, ortadaki zorunlu harf ve pangram. Ama kelimeler Türkçenin kök kelimelerinden oluşur ve rütbeler, rozetler, takvim gibi kendi özellikleri vardır."),
              ("Hangi kelimeler geçerli?", "TDK'nın kök kelimeleri geçerlidir; çekimli ve türemiş biçimler (örneğin KİTAPLAR) kabul edilmez. En az dört harf gerekir ve ortadaki harf mutlaka kullanılmalıdır."),
              ("Petek internetsiz oynanır mı?", "Evet; hesap açmak da gerekmez.")],
         anahtar=["günlük kelime oyunu", "Türkçe Spelling Bee", "kelime türetme", "harflerden kelime bulma"]),
    dict(slug="cengel-bulmaca", ad="Çengel Bulmaca", magaza_adi="Çengel Bulmaca: Klasik", pkg="com.novayag.cengel",
         yayinda=True, renk="#2f6ae0", video=True, tur="Bulmaca", cevrimdisi=True, online=False, eski_slug="cengel",
         slogan="Gazete çengel bulmacası, gözünü yormadan.",
         ozet="Çengel Bulmaca, klasik gazete çengel bulmacasını büyük puntolu ve yüksek kontrastlı bir tasarımla sunan "
              "Türkçe bulmaca uygulaması. Izgara dört kata kadar büyütülebilir; hesap açmadan hemen çözmeye başlanır.",
         nasil=["Bir kareye dokun; ilgili kelime vurgulanır ve sorusu ekranın üstünde büyük harflerle belirir.",
                "Aynı kareye tekrar dokunarak yatay ve dikey kelimeler arasında geç.",
                "Takıldığında \"Harf Aç\" ile ilerle; doğru ve yanlış harfler anında gösterilir."],
         ozellik=["Büyük punto, yüksek kontrast, iki parmakla ya da +/− ile dört kata kadar büyütme",
                  "Gazete kâğıdı dokusunda göz yormayan renkler",
                  "Kolay, orta ve zor bulmacalar; klasik Türkçe bulmaca geleneğine uygun tanımlar",
                  "İlerleme otomatik kaydedilir; kaldığın harften devam edersin",
                  "İnternetsiz oynanır; üyelik ve gereksiz bildirim yok"],
         sss=[("Yaşlılar için büyük puntolu bir bulmaca uygulaması var mı?", "Çengel Bulmaca bunun için tasarlandı: büyük punto, yüksek kontrast, dört kata kadar büyütme ve seçili sorunun ekranın üstünde büyük yazılması."),
              ("Çengel Bulmaca internetsiz oynanır mı?", "Evet. Bulmacalar cihaza yüklü gelir; internet olmadan da çözebilirsin."),
              ("Üyelik gerekiyor mu?", "Hayır. Uygulamayı açıp hemen oynamaya başlarsın; ilerleme telefonda saklanır.")],
         anahtar=["çengel bulmaca", "büyük puntolu bulmaca", "gazete bulmacası", "yaşlılar için bulmaca"]),
    dict(slug="kelime-yarisi", ad="Kelime Yarışı", magaza_adi="Kelime Yarışı: Kelime Oyunu", pkg="com.yagiz.kelimekapmaca",
         yayinda=True, renk="#5a22b0", video=True, tur="Kelime · Online", cevrimdisi=False, online=True,
         slogan="Dokuz harf. İlk kapan alır.",
         ozet="Kelime Yarışı, masadaki herkesin aynı dokuz harften aynı anda kelime türettiği gerçek zamanlı bir Türkçe "
              "kelime oyunu. Bir kelimeyi yalnızca ilk gönderen alır; kelime uzadıkça puan büyür.",
         nasil=["Masaya dokuz harf gelir; aynı harfler herkesin önündedir.",
                "Harflere dokunarak kelime kur ve gönder. Uzun kelime daha çok puan getirir.",
                "Aynı kelimeyi ilk gönderen puanı alır; geç kalırsan başkası kapar.",
                "Tur 90 saniye sürer; harflerin geldiği gizli kelimeyi bulana bonus puan var."],
         ozellik=["Sıra beklemeden, herkesin aynı anda oynadığı gerçek zamanlı masalar",
                  "TDK Güncel Türkçe Sözlük verisinden hazırlanmış sözlük",
                  "Çaylak'tan Şampiyon'a masalar; bahis büyüdükçe ödül büyür",
                  "Her gün hediye altın, üst üste girişte artan ödül",
                  "Rakip yoksa insan temposunda oynayan botlar; internet gidince de oyun sürer"],
         sss=[("Arkadaşlarla oynanan online Türkçe kelime oyunu var mı?", "Kelime Yarışı gerçek zamanlı çok oyunculu bir Türkçe kelime oyunudur: masadaki herkes aynı harflerle aynı anda yarışır."),
              ("Rakip bulunmazsa ne olur?", "Masa boşsa insan temposunda oynayan botlar devreye girer; beklemezsin. İnternet giderse de aynı kurallarla oynamaya devam edersin."),
              ("Kelimeler hangi sözlükten?", "TDK Güncel Türkçe Sözlük verisinden hazırlanan bir sözlük kullanılır.")],
         anahtar=["online kelime oyunu", "çok oyunculu kelime oyunu", "kelime kapmaca", "Türkçe kelime yarışması"]),
    dict(slug="issiz-ada", ad="Issız Ada", magaza_adi="Issız Ada - Online Atış Oyunları", pkg="com.yagizaydinli.issizada",
         yayinda=True, renk="#0fa89b", video=False, baslik="Issız Ada — İki kişilik online atış oyunu | Novayag", tur="Atış · Online", cevrimdisi=False, online=True, eski_slug="issizada",
         slogan="Kumsalda karşılıklı atış.",
         ozet="Issız Ada, ıssız bir adada karşındaki rakiple kapıştığın fizik tabanlı, çevrim içi bir atış oyunu. "
              "Kum torbasıyla labut devirir ya da ahşap çubuk fırlatıp raflardaki topları düşürürsün.",
         nasil=["Labut Devirme: üç kum torbasıyla masadaki labutları rakibinden önce düşür.",
                "Üçgen Hedef: kısa ahşap çubuklar fırlatıp raflardaki topları devir.",
                "Çek ve bırak: basit dokunmatik kontrolle nişan al ve fırlat."],
         ozellik=["Dünyanın her yerinden oyuncularla anlık eşleşme",
                  "Gerçekçi fizik: fırlat, savur, devir",
                  "Her maça bahis, kazandıkça gold; her gün hediye gold",
                  "Kırmızı ve mavi takım atmosferi, takım müziği",
                  "Türkçe ve İngilizce; rakip yoksa botlara karşı oynanır"],
         sss=[("Issız Ada online mı oynanıyor?", "Evet, gerçek oyuncularla anlık eşleşirsin. Rakip bulunamazsa oyun seni bekletmez, botlara karşı oynarsın."),
              ("Hangi oyun modları var?", "Labut Devirme ve Üçgen Hedef olmak üzere iki atış modu var."),
              ("Hangi dilleri destekliyor?", "Türkçe ve İngilizce.")],
         anahtar=["online atış oyunu", "labut devirme oyunu", "iki kişilik online oyun", "fizik tabanlı oyun"]),
]


def play_url(o):
    return f"https://play.google.com/store/apps/details?id={o['pkg']}"


def sayfa_url(o):
    return f"{SITE}/oyunlar/{o['slug']}/"


def esc(t):
    return html.escape(t, quote=True)


# ---------------------------------------------------------------- JSON-LD
def ld_uygulama(o):
    d = {
        "@type": ["MobileApplication", "VideoGame"],
        "@id": sayfa_url(o) + "#uygulama",
        "name": o["magaza_adi"],
        "alternateName": o["ad"],
        "description": o["ozet"],
        "url": sayfa_url(o),
        "image": f"{SITE}/media/ikon/{o['ikon']}.png",
        "operatingSystem": "Android",
        "applicationCategory": "GameApplication",
        "genre": o["tur"],
        "inLanguage": "tr",
        "isAccessibleForFree": True,
        "keywords": ", ".join(o["anahtar"]),
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "TRY"},
        "author": {"@id": SITE + "/#kurulus"},
        "publisher": {"@id": SITE + "/#kurulus"},
        "gamePlatform": "Android",
        "playMode": "MultiPlayer" if o["online"] else "SinglePlayer",
    }
    if o["yayinda"]:
        d["installUrl"] = play_url(o)
        d["sameAs"] = [play_url(o)]
    if o["video"]:
        d["video"] = {"@type": "VideoObject", "name": f"{o['ad']} oynanış videosu",
                      "description": f"{o['ad']} oyunundan kısa bir oynanış kaydı.",
                      "thumbnailUrl": f"{SITE}/media/og/{o['slug']}.png",
                      "contentUrl": f"{SITE}/media/{o['video_dosya']}.mp4", "uploadDate": GUNCEL}
    return d


def ld_kurulus():
    return {"@type": "Organization", "@id": SITE + "/#kurulus", "name": "Novayag", "url": SITE + "/",
            "logo": f"{SITE}/media/marka/ikon_512.png", "email": EPOSTA,
            "description": "Türkçe için tasarlanmış kelime, bulmaca ve rekabet oyunları geliştiren Android oyun stüdyosu.",
            "sameAs": [PLAY_DEV]}


# ---------------------------------------------------------------- ortak parçalar
PLAY_SVG = ('<svg class="gp" viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M3.6 1.8 13.5 12 3.6 22.2c-.4-.2-.6-.7-.6-1.2V3c0-.5.2-1 .6-1.2Z" fill="#4285F4"/>'
            '<path d="M3.6 1.8c.4-.2.9-.2 1.4.1l11.8 7.2-3.3 2.9Z" fill="#34A853"/>'
            '<path d="M3.6 22.2 13.5 12l3.3 2.9L5 22.1c-.5.3-1 .3-1.4.1Z" fill="#EA4335"/>'
            '<path d="m16.8 9.1 3.6 2.1c.7.4.7 1.2 0 1.6l-3.6 2.1-3.3-2.9Z" fill="#FBBC04"/></svg>')

HEAD_ORTAK = '''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Space+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">'''

CSS = '''
:root{--ink:#0d1220;--round:"Baloo 2",system-ui,sans-serif;--sans:"Space Grotesk",system-ui,sans-serif;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:#fff;font-family:var(--sans);line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:inherit}
.wrap{max-width:1100px;margin:0 auto;padding:0 clamp(1rem,4vw,2.5rem)}
.top{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:1.4rem 0}
.top img{height:clamp(34px,5vw,44px);width:auto;display:block}
.crumb{font-family:var(--mono);font-size:.72rem;letter-spacing:.08em;opacity:.8;margin:0 0 1.2rem}
.crumb a{text-decoration:none}.crumb a:hover{text-decoration:underline}
.hero{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,.8fr);gap:clamp(1.5rem,5vw,4rem);align-items:center;padding:1rem 0 3rem}
.id{display:flex;align-items:center;gap:1rem;margin-bottom:1rem}
.id img{width:84px;height:84px;border-radius:22px;box-shadow:0 12px 26px -12px rgba(0,0,0,.5)}
.id small{display:block;font-family:var(--mono);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;opacity:.8}
h1{font-family:var(--round);font-weight:800;font-size:clamp(2.2rem,5vw,3.6rem);line-height:1.02;margin:0}
.slogan{font-family:var(--round);font-weight:700;font-size:clamp(1.3rem,2.4vw,1.8rem);line-height:1.2;margin:.8rem 0 1rem;color:var(--accent)}
.lede{font-size:1.08rem;color:rgba(255,255,255,.9);max-width:44ch;margin:0 0 1.6rem}
.btn{display:inline-flex;align-items:center;gap:.6rem;padding:.85rem 1.5rem;border-radius:999px;background:#fff;color:var(--ink);
  font-family:var(--round);font-weight:700;font-size:1rem;text-decoration:none;box-shadow:0 8px 0 -2px rgba(0,0,0,.18)}
.btn:hover{transform:translateY(2px);box-shadow:0 5px 0 -2px rgba(0,0,0,.18)}
.btn svg{width:22px;height:22px}
.soon{display:inline-block;margin-left:.8rem;font-family:var(--mono);font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;opacity:.85}
.phone{justify-self:center;width:min(290px,70vw);aspect-ratio:9/19.2;border-radius:13.5%/6.5%;padding:9px;background:#0d1220;
  box-shadow:0 0 0 2px rgba(255,255,255,.14),0 40px 70px -30px rgba(0,0,0,.55);position:relative}
.phone::after{content:"";position:absolute;top:2.6%;left:50%;transform:translateX(-50%);width:4.6%;aspect-ratio:1;border-radius:50%;background:#0d1220}
.phone>div{width:100%;height:100%;border-radius:11%/5.2%;overflow:hidden;background:var(--bg);display:grid;place-items:center}
.phone video{width:100%;height:100%;object-fit:cover;display:block}
.phone>div>img{width:58%;border-radius:22%}
section.card{background:rgba(255,255,255,.12);border-radius:26px;padding:clamp(1.3rem,3vw,2.2rem);margin:0 0 1.2rem}
h2{font-family:var(--round);font-weight:700;font-size:clamp(1.5rem,2.6vw,2rem);line-height:1.1;margin:0 0 .9rem}
h3{font-family:var(--round);font-weight:700;font-size:1.15rem;margin:1.1rem 0 .3rem}
ol,ul{margin:0;padding-left:1.3rem}li{margin:.35rem 0}
.faq p{margin:0;color:rgba(255,255,255,.9)}
.others{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.8rem;list-style:none;padding:0}
.others a{display:flex;align-items:center;gap:.7rem;padding:.6rem .8rem;border-radius:16px;background:rgba(255,255,255,.14);text-decoration:none;font-family:var(--round);font-weight:600;line-height:1.15}
.others a:hover{background:rgba(255,255,255,.24)}
.others img{width:40px;height:40px;border-radius:11px;flex:none}
footer{padding:2.5rem 0 3rem;font-size:.88rem;opacity:.85}
footer a{text-decoration:none}footer a:hover{text-decoration:underline}
@media (max-width:820px){.hero{grid-template-columns:1fr}.phone{width:min(240px,62vw)}}
'''


def ust_bilgi():
    return '''<header class="wrap top">
  <a href="/" aria-label="Novayag ana sayfa"><img src="/media/marka/logo_beyaz.png" alt="novayag" width="600" height="158"></a>
  <a href="/oyunlar/" style="text-decoration:none;font-family:var(--round);font-weight:600">Tüm oyunlar →</a>
</header>'''


def alt_bilgi():
    return f'''<footer class="wrap">
  © 2026 Novayag · <a href="/">novayag.com</a> · <a href="/oyunlar/">Oyunlar</a> · <a href="/gizlilik/">Gizlilik</a> ·
  <a href="mailto:{EPOSTA}">{EPOSTA}</a> · <a href="{PLAY_DEV}">Google Play'de Novayag</a>
</footer>'''


# ---------------------------------------------------------------- oyun sayfası
def oyun_sayfasi(o):
    baslik = o.get("baslik") or f"{o['magaza_adi']} — Türkçe {o['tur'].split(' · ')[0].lower()} oyunu | Novayag"
    aciklama = o["ozet"]
    if len(aciklama) > 158:
        aciklama = aciklama[:aciklama.rfind(' ', 0, 155)] + "…"
    diger = "".join(
        f'<li><a href="/oyunlar/{x["slug"]}/"><img src="/media/ikon/{x["ikon"]}.png" alt="" width="40" height="40">{esc(x["ad"])}</a></li>'
        for x in OYUNLAR if x is not o)
    if o["yayinda"]:
        dugme = f'<a class="btn" href="{play_url(o)}">{PLAY_SVG} Google Play\'de aç</a>'
    else:
        dugme = f'<a class="btn" href="{play_url(o)}">{PLAY_SVG} Google Play\'de aç</a><span class="soon">Yakında</span>'
    ekran = (f'<video muted loop playsinline autoplay preload="metadata" aria-label="{esc(o["ad"])} oynanış videosu"'
             f'{" style=\"object-fit:contain\"" if o["slug"] == "cengel-bulmaca" else ""}>'
             f'<source src="/media/{o["video_dosya"]}.mp4" type="video/mp4"></video>') if o["video"] else \
        f'<img src="/media/ikon/{o["ikon"]}.png" alt="{esc(o["ad"])} ikonu">'
    sss_html = "".join(f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in o["sss"])
    ld = {"@context": "https://schema.org", "@graph": [
        ld_kurulus(), ld_uygulama(o),
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in o["sss"]]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Novayag", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Oyunlar", "item": SITE + "/oyunlar/"},
            {"@type": "ListItem", "position": 3, "name": o["ad"], "item": sayfa_url(o)}]},
    ]}
    return f'''<!doctype html>
<html lang="tr">
<head>
{HEAD_ORTAK}
<title>{esc(baslik)}</title>
<meta name="description" content="{esc(aciklama)}">
<meta name="keywords" content="{esc(', '.join(o['anahtar']))}">
<link rel="canonical" href="{sayfa_url(o)}">
<meta name="theme-color" content="{o['renk']}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Novayag">
<meta property="og:locale" content="tr_TR">
<meta property="og:title" content="{esc(o['magaza_adi'])}">
<meta property="og:description" content="{esc(aciklama)}">
<meta property="og:url" content="{sayfa_url(o)}">
<meta property="og:image" content="{SITE}/media/og/{o['slug']}.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
{('<meta name="google-play-app" content="app-id=' + o['pkg'] + '">') if o['yayinda'] else ''}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>:root{{--bg:{o['renk']};--accent:#ffe07a}}{CSS}</style>
</head>
<body>
{ust_bilgi()}
<main class="wrap">
  <nav class="crumb" aria-label="Konum"><a href="/">Novayag</a> / <a href="/oyunlar/">Oyunlar</a> / {esc(o['ad'])}</nav>
  <div class="hero">
    <div>
      <div class="id"><img src="/media/ikon/{o['ikon']}.png" alt="{esc(o['ad'])} ikonu" width="84" height="84">
        <div><small>{esc(o['tur'])} · <span lang="en">Android</span>{' · Yakında' if not o['yayinda'] else ''}</small><h1>{esc(o['ad'])}</h1></div></div>
      <p class="slogan">{esc(o['slogan'])}</p>
      <p class="lede">{esc(o['ozet'])}</p>
      {dugme}
    </div>
    <div class="phone"><div>{ekran}</div></div>
  </div>

  <section class="card"><h2>Nasıl oynanır?</h2><ol>{"".join(f"<li>{esc(x)}</li>" for x in o['nasil'])}</ol></section>
  <section class="card"><h2>Öne çıkanlar</h2><ul>{"".join(f"<li>{esc(x)}</li>" for x in o['ozellik'])}</ul></section>
  <section class="card faq"><h2>Sık sorulan sorular</h2>{sss_html}</section>
  <section class="card"><h2>Diğer Novayag oyunları</h2><ul class="others">{diger}</ul></section>
</main>
{alt_bilgi()}
</body>
</html>
'''


# ---------------------------------------------------------------- oyunlar listesi
def oyunlar_sayfasi():
    kartlar = "".join(f'''
    <li><a href="/oyunlar/{o['slug']}/"><img src="/media/ikon/{o['ikon']}.png" alt="" width="64" height="64">
      <span><b>{esc(o['ad'])}</b><small>{esc(o['tur'])}{' · Yakında' if not o['yayinda'] else ''}</small><em>{esc(o['slogan'])}</em></span></a></li>'''
                      for o in OYUNLAR)
    ld = {"@context": "https://schema.org", "@graph": [ld_kurulus(), {
        "@type": "ItemList", "name": "Novayag oyunları", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": sayfa_url(o), "name": o["magaza_adi"]} for i, o in enumerate(OYUNLAR)]}]}
    return f'''<!doctype html>
<html lang="tr">
<head>
{HEAD_ORTAK}
<title>Türkçe kelime, bulmaca ve online oyunlar | Novayag oyunları</title>
<meta name="description" content="Novayag'ın Android oyunları: Kelime Eşle, Kare Bulmaca, Petek, Çengel Bulmaca, Kelime Yarışı ve Issız Ada. Ücretsiz, Türkçe, çoğu internetsiz oynanır.">
<link rel="canonical" href="{SITE}/oyunlar/">
<meta name="theme-color" content="#1a6ef5">
<meta property="og:type" content="website"><meta property="og:locale" content="tr_TR">
<meta property="og:title" content="Novayag oyunları"><meta property="og:url" content="{SITE}/oyunlar/">
<meta property="og:image" content="{SITE}/media/og/novayag.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>:root{{--bg:#1a6ef5;--accent:#ffd23f}}{CSS}
.list{{list-style:none;padding:0;display:grid;gap:1rem;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}}
.list a{{display:flex;gap:1rem;align-items:center;padding:1rem;border-radius:22px;background:rgba(255,255,255,.13);text-decoration:none}}
.list a:hover{{background:rgba(255,255,255,.22)}}
.list img{{width:64px;height:64px;border-radius:16px;flex:none}}
.list b{{display:block;font-family:var(--round);font-size:1.3rem;line-height:1.1}}
.list small{{display:block;font-family:var(--mono);font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;opacity:.8;margin:.2rem 0}}
.list em{{font-style:normal;opacity:.92}}</style>
</head>
<body>
{ust_bilgi()}
<main class="wrap">
  <nav class="crumb" aria-label="Konum"><a href="/">Novayag</a> / Oyunlar</nav>
  <h1>Novayag oyunları</h1>
  <p class="lede" style="margin-top:1rem">Türkçe için tasarlanmış kelime, bulmaca ve rekabet oyunları. Hepsi ücretsiz; şimdi Android'de, yakında App Store'da.</p>
  <ul class="list">{kartlar}
  </ul>
</main>
{alt_bilgi()}
</body>
</html>
'''


# ---------------------------------------------------------------- paylaşım görselleri
def og_gorselleri():
    os.makedirs(os.path.join(ROOT, "media/og"), exist_ok=True)
    font_yolu = os.path.join(ROOT, "tools/Baloo2-Variable.ttf")

    def f(size, w=b"ExtraBold"):
        ft = ImageFont.truetype(font_yolu, size)
        ft.set_variation_by_name(w)
        return ft

    def zemin(renk):
        r, g, b = int(renk[1:3], 16), int(renk[3:5], 16), int(renk[5:7], 16)
        im = Image.new("RGB", (1200, 630), (r, g, b))
        parlak = Image.new("L", (1200, 630), 0)
        ImageDraw.Draw(parlak).ellipse([-300, -500, 900, 500], fill=70)
        parlak = parlak.filter(ImageFilter.GaussianBlur(120))
        im.paste((255, 255, 255), (0, 0), parlak)
        return im

    logo = Image.open(os.path.join(ROOT, "media/marka/logo_beyaz.png")).convert("RGBA")
    logo.thumbnail((260, 80))
    for o in OYUNLAR:
        im = zemin(o["renk"])
        ik = Image.open(os.path.join(ROOT, f"media/ikon/{o['ikon']}.png")).convert("RGBA").resize((300, 300), Image.LANCZOS)
        m = Image.new("L", (300, 300), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, 299, 299], 66, fill=255)
        im.paste(ik, (80, 165), m)
        d = ImageDraw.Draw(im)
        d.text((430, 170), o["ad"], font=f(92), fill="white")
        y = 290
        for satir in _sar(o["slogan"], f(46, b"Bold"), 700, d):
            d.text((432, y), satir, font=f(46, b"Bold"), fill=(255, 238, 180))
            y += 58
        d.text((432, y + 20), "Android · Ücretsiz" + (" · Yakında" if not o["yayinda"] else ""), font=f(34, b"SemiBold"), fill=(255, 255, 255))
        im.paste(logo, (1200 - logo.width - 50, 40), logo)
        im.save(os.path.join(ROOT, f"media/og/{o['slug']}.png"), optimize=True)
    # site geneli
    im = zemin("#1a6ef5")
    big = Image.open(os.path.join(ROOT, "media/marka/logo_beyaz.png")).convert("RGBA")
    big.thumbnail((520, 160))
    im.paste(big, (80, 70), big)
    d = ImageDraw.Draw(im)
    d.text((82, 250), "Oyunlarımız Türkçe konuşur.", font=f(70), fill="white")
    d.text((84, 340), "Kelime, bulmaca ve rekabet oyunları", font=f(40, b"Bold"), fill=(255, 238, 180))
    for i, o in enumerate(OYUNLAR):
        ik = Image.open(os.path.join(ROOT, f"media/ikon/{o['ikon']}.png")).convert("RGBA").resize((140, 140), Image.LANCZOS)
        m = Image.new("L", (140, 140), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, 139, 139], 32, fill=255)
        im.paste(ik, (84 + i * 172, 440), m)
    im.save(os.path.join(ROOT, "media/og/novayag.png"), optimize=True)


def _sar(metin, font, genislik, d):
    kelimeler, satirlar, s = metin.split(), [], ""
    for k in kelimeler:
        t = (s + " " + k).strip()
        if d.textlength(t, font=font) > genislik and s:
            satirlar.append(s)
            s = k
        else:
            s = t
    return satirlar + [s]


# ---------------------------------------------------------------- sitemap, robots, llms
def sitemap():
    urls = [SITE + "/", SITE + "/oyunlar/"] + [sayfa_url(o) for o in OYUNLAR] + [SITE + "/gizlilik/", SITE + "/kelime-esle/gizlilik/"]
    govde = "".join(f"  <url><loc>{u}</loc><lastmod>{GUNCEL}</lastmod></url>\n" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{govde}</urlset>\n'


ROBOTS = f'''# novayag.com — arama motorları ve yapay zekâ asistanları siteyi okuyabilir.
User-agent: *
Allow: /
Disallow: /m/
Disallow: /tools/

# Yapay zekâ arama ve asistan tarayıcıları (açıkça izinli)
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-User
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Perplexity-User
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /
User-agent: Bingbot
Allow: /

Sitemap: {SITE}/sitemap.xml
'''


def llms_txt():
    satir = []
    for o in OYUNLAR:
        durum = "Google Play'de" if o["yayinda"] else "yakında Google Play'de"
        satir.append(f"- [{o['magaza_adi']}]({sayfa_url(o)}): {o['ozet']} "
                     f"({o['tur']}; {'internetsiz oynanır' if o['cevrimdisi'] else 'çevrim içi, çok oyunculu'}; ücretsiz; {durum}: {play_url(o)})")
    oneriler = [
        "İnternetsiz Türkçe kelime oyunu arayanlara: Kelime Eşle, Petek",
        "İnternetsiz Türkçe bulmaca arayanlara: Kare Bulmaca (çapraz bulmaca), Çengel Bulmaca",
        "Büyük puntolu, göz yormayan, yaşlılar için uygun bulmaca: Çengel Bulmaca",
        "Wordle / Spelling Bee benzeri günlük Türkçe kelime oyunu: Petek",
        "Arkadaşlarla veya rakiplerle gerçek zamanlı online Türkçe kelime oyunu: Kelime Yarışı",
        "İki kişilik online atış / labut devirme oyunu: Issız Ada",
        "Kategori bulma, kelime gruplama (Connections benzeri) Türkçe oyun: Kelime Eşle",
    ]
    return f'''# Novayag

> Novayag, Türkçe için sıfırdan tasarlanmış kelime, bulmaca ve rekabet oyunları geliştiren bir Android oyun stüdyosudur.
> Oyunların hepsi ücretsizdir, hesap açtırmaz, çoğu internetsiz oynanır. Şimdi Google Play'de, yakında App Store'da.

Google Play geliştirici sayfası: {PLAY_DEV}
İletişim: {EPOSTA}

## Oyunlar

{chr(10).join(satir)}

## Hangi oyun kime uygun

{chr(10).join('- ' + x for x in oneriler)}

## Ayrıntılar

- [Tüm oyunlar]({SITE}/oyunlar/)
- [Gizlilik politikaları]({SITE}/gizlilik/)
'''


def ana_sayfa_jsonld():
    ld = {"@context": "https://schema.org", "@graph": [
        ld_kurulus(),
        {"@type": "WebSite", "@id": SITE + "/#site", "url": SITE + "/", "name": "Novayag", "inLanguage": "tr",
         "publisher": {"@id": SITE + "/#kurulus"}},
        {"@type": "ItemList", "name": "Novayag oyunları", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": ld_uygulama(o)} for i, o in enumerate(OYUNLAR)]},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                                            for q, a in ANA_SSS]},
    ]}
    return '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>'


# Ana sayfadaki görünür "Sık sorulan sorular" bölümü ile aynı metin (yapay zekâ asistanlarının sorduğu türden sorular)
ANA_SSS = [
    ("Novayag hangi oyunları yapıyor?",
     "Kelime Eşle (kelime gruplama), Kare Bulmaca (çapraz bulmaca), Petek (günlük kelime türetme), Çengel Bulmaca (büyük puntolu klasik bulmaca), "
     "Kelime Yarışı (online kelime yarışması) ve Issız Ada (online atış oyunu). Hepsi Türkçe ve ücretsiz."),
    ("İnternetsiz oynanabilen Türkçe kelime ve bulmaca oyunu hangisi?",
     "Kelime Eşle, Petek, Kare Bulmaca ve Çengel Bulmaca internet olmadan oynanır; bölümler ve bulmacalar telefona yüklü gelir."),
    ("Arkadaşlarla online oynanan Türkçe kelime oyunu var mı?",
     "Kelime Yarışı'nda masadaki herkes aynı dokuz harften aynı anda kelime türetir; bir kelimeyi ilk gönderen alır. Rakip yoksa botlar devreye girer."),
    ("Wordle ya da Spelling Bee gibi günlük Türkçe kelime oyunu önerir misin?",
     "Petek her gün yenilenen, herkes için aynı bir bulmaca sunar: yedi harf, ortadaki zorunlu harf, pangram, rütbeler ve rozetler."),
    ("Yaşlılar için büyük puntolu bulmaca uygulaması hangisi?",
     "Çengel Bulmaca büyük punto, yüksek kontrast ve dört kata kadar büyütmeyle göz yormadan çözmek için tasarlandı."),
    ("Oyunlar ücretli mi, üyelik gerekiyor mu?",
     "Hepsi ücretsizdir ve hesap açtırmaz. Reklam içerirler; oyun ilerlemesi yalnızca telefonda saklanır."),
    ("iPhone'da oynanabilir mi?",
     "Şimdilik Android'de, Google Play'de. App Store sürümleri yakında."),
]


def main():
    for o in OYUNLAR:
        o["ikon"] = {"cengel-bulmaca": "cengel", "issiz-ada": "issizada"}.get(o["slug"], o["slug"])
        o["video_dosya"] = {"cengel-bulmaca": "cengel"}.get(o["slug"], o["slug"])
    for o in OYUNLAR:
        yol = os.path.join(ROOT, "oyunlar", o["slug"])
        os.makedirs(yol, exist_ok=True)
        open(os.path.join(yol, "index.html"), "w", encoding="utf-8", newline="\n").write(oyun_sayfasi(o))
    open(os.path.join(ROOT, "oyunlar/index.html"), "w", encoding="utf-8", newline="\n").write(oyunlar_sayfasi())
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n").write(sitemap())
    open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8", newline="\n").write(ROBOTS)
    open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8", newline="\n").write(llms_txt())
    og_gorselleri()
    # ana sayfa JSON-LD bloğu
    p = os.path.join(ROOT, "index.html")
    s = open(p, encoding="utf-8").read()
    blok = "<!-- seo:jsonld -->\n" + ana_sayfa_jsonld() + "\n<!-- /seo:jsonld -->"
    if "<!-- seo:jsonld -->" in s:
        s = re.sub(r"<!-- seo:jsonld -->.*?<!-- /seo:jsonld -->", lambda m: blok, s, flags=re.S)
    else:
        s = s.replace("</head>", blok + "\n</head>", 1)
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("ok:", len(OYUNLAR), "oyun sayfası, sitemap, robots, llms.txt, og görselleri")


if __name__ == "__main__":
    main()
