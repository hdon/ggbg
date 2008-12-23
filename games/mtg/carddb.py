import os, sys, re, sqlite3, urllib

DATABASE_FILENAME = os.path.join('games','mtg','mtg.card.db')
BASE_URL = 'http://ww2.wizards.com/gatherer/index.aspx'
DETAIL_URL = 'http://ww2.wizards.com/gatherer/CardDetails.aspx'
CARD_IMAGE_PATH = os.path.join('games','mtg','card-images')
card_details_re = re.compile(r'CardDetails\.aspx\?id=([0-9]+)')
card_url_re = re.compile(r'http://[a-zA-Z0-9.]*wizards\.com/Magic/Cards/[^"]*Card[0-9]+.jpg')

def get_card(name):
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
    detail_ids = [int(x) for x in card_details_re.findall(urllib.urlopen(url).read())]
    # TODO implement an SGML parser!
    # the search interface doesn't provide an "exact name" search mode, so
    # searching for "island" results in cards like "island sanctuary," which
    # unfortunately sometimes have a lower ID number than the one you wanted.
    # This could potentially be solved with a *really* complex regular
    # expression, but I Python's sgmllib can perform the task quite well and
    # produces more maintainable code, and probably consume less memory with
    # expensive regular expressions. Hopefully removing this sort will act as
    # a temporary fix.
    #detail_ids.sort()

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
    db = sqlite3.connect(DATABASE_FILENAME)
    cursor = db.cursor()
    cursor.execute('create table if not exists mtg_card_images(name text, id int)')
    db.commit()
    cursor.close()

initialize()

if __name__ == '__main__':
    for card in sys.argv[1:]:
        print card, get_card(card)

