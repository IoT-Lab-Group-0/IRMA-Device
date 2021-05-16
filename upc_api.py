import requests

import parsepy

BARCODESPIDER_URL = 'https://api.barcodespider.com/v1/lookup'
BARCODESPIDER_TOKEN = BARCODESPIDER_API_KEY

def search(upc):
    new_item = parsepy.item()
    # Call the API and put results into a new Item object
    params = {'token': BARCODESPIDER_TOKEN, 'upc': upc}
    r = requests.get(BARCODESPIDER_URL, params=params)
    if r.status_code == 200:
        item_attributes = r.json()['item_attributes']
        new_item.name = item_attributes['title']  # the product title from the lookup
        new_item.upc = upc
        new_item.imageURL = item_attributes['image']
    else:
        new_item.name = "@@ UPC not found"

    return new_item
