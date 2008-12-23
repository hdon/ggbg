import os, sys, re, sqlite3, urllib

BASE_URL = 'http://ww2.wizards.com/gatherer/index.aspx'
DETAIL_URL = 'http://ww2.wizards.com/gatherer/CardDetails.aspx'
CARD_IMAGE_PATH = 'card-images'
card_details_re = re.compile(r'CardDetails\.aspx\?id=([0-9]+)')
card_url_re = re.compile(r'http://[a-zA-Z0-9.]*wizards\.com/Magic/Cards/[^"]*Card[0-9]+.jpg')

def get_card(name):
    global db, BASE_URL, DETAIL_URL, CARD_IMAGE_PATH, card_details_re, card_url_re
    # Check database for cached result first
    dbc = db.cursor()
    dbc.execute("select id from mtg_card_images where name=?", [name])
    id = dbc.fetchone()
    if id: return os.path.join(CARD_IMAGE_PATH, 'Card%d.jpg'%id)

    # Look up card online
    url = BASE_URL + '?' + urllib.urlencode({
        'term': name,
        'Field_Name': 'on',
        'setfilter': urllib.quote('All sets')
    })
    detail_ids = map(lambda s: int(s),
        card_details_re.findall(urllib.urlopen(url).read()))
    detail_ids.sort()

    # Look up individual printing of card
    id = detail_ids[0]
    url = DETAIL_URL + '?' + urllib.urlencode({
        'id': id
    })

    # Look up actual photo of card image
    card_urls = card_url_re.findall(urllib.urlopen(url).read())
    url = card_urls[0]
    filename = os.path.join(CARD_IMAGE_PATH, os.path.basename(url))
    open(filename,'wb').write(urllib.urlopen(url).read())

    # Save data in database
    dbc.execute("insert into mtg_card_images values(?,?)", [name, id])
    db.commit()
    dbc.close()
    return filename

def initialize():
    global db
    db = sqlite3.connect('mtg.card.db')
    cursor = db.cursor()
    cursor.execute('create table if not exists mtg_card_images(name text, id int)')
    db.commit()
    cursor.close()

initialize()

if __name__ == '__main__':
    for card in sys.argv[1:]:
        print card, get_card(card)

