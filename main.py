import os

import requests
import requests_cache
from bs4 import BeautifulSoup

xivapi_key = os.getenv("XIVAPI_KEY")
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Safari/537.36'}
lodestone_base_url = "https://na.finalfantasyxiv.com"
ex_versions = [
    "A Realm Reborn",
    "Heavensward",
    "Stormblood",
    "Shadowbringers"
]


# Uses xivapi.com to determine if an item can be equipped
def is_equippable(item_name):
    # time.sleep(0.1)
    xivapi_headers = {'user-agent': 'https://github.com/mistxiv'}
    params = {
        'private_key': xivapi_key,
        'indexes': 'item',
        'string_algo': 'term',
        'filters': 'EquipSlotCategory.ID>0',
        'string': item_name
    }
    r = requests.get(f"https://xivapi.com/search", headers=xivapi_headers, params=params)
    return r.json()["Pagination"]["ResultsTotal"] != 0


def main():
    requests_cache.install_cache("requests_cache")

    # For each expansion
    for i, ex in enumerate(ex_versions):
        p = f"output/{ex}"
        os.makedirs(p, exist_ok=True)
        # For each dungeon
        for name, url in dungeon_urls(i).items():
            drops = dungeon_drops(url)
            drops_count = len(drops)
            if drops_count > 0:
                outfile = f"{p}/{name}.txt"
                with open(outfile, "w") as f:
                    f.write("\n".join(drops))
                    print(f"Wrote file with {drops_count} equippable items: {outfile}")


# Returns a dict of dungeon_name => lodestone url for a given expansion (0-3)
def dungeon_urls(ex_version):
    r = requests.get(f"{lodestone_base_url}/lodestone/playguide/db/duty/?category2=2&ex_version={ex_version}")
    soup = BeautifulSoup(r.text, 'html.parser')

    urls = {}

    for dungeon in soup.find_all("a", class_="db_popup db-table__txt--detail_link"):
        urls[dungeon.string] = f"{lodestone_base_url}{dungeon.get('href')}"

    return urls


def dungeon_drops(url):
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')

    drops = set([d.string for d in soup.find_all("a", class_="db_popup tooltip_pos__right_space")])
    drops = list([d for d in drops if is_equippable(d)])
    drops.sort()

    return drops


if __name__ == '__main__':
    main()
