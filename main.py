import os

import requests
import requests_cache
from bs4 import BeautifulSoup
import time
import sys

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


def xivapi_item(item_name):
    print(f"Searching xivapi for \"{item_name}\"")
    xivapi_headers = {'user-agent': 'https://github.com/mistxiv'}
    columns = [
        'ID',
        'EquipSlotCategory.ID',
        'Name'
    ]
    params = {
        'private_key': xivapi_key,
        'indexes': 'item',
        'string_algo': 'term',
        'columns': ",".join(columns),
        'string': item_name
    }
    r = requests.get(f"https://xivapi.com/search", headers=xivapi_headers, params=params)
    # Wait between requests if they're not answered from cache
    if r.elapsed.total_seconds() > 0:
        time.sleep(0.1)
    results = r.json()['Results']
    return results[0] if len(results) > 0 else None


# Uses xivapi.com to determine if an item can be equipped
def can_equip(item):
    return item['EquipSlotCategory']['ID'] if item else False

def lua_obj1_data_item(item):
    return (
        f'\t\t[{item["ID"]} = {{'
        f'\t\t\t["Col"] = false,'
        f'\t\t\t["Enabled"] = true,'
        f'\t\t\t["HQ"] = true,'
        f'\t\t\t["ItemName"] = "{item["Name"]}",'
        f'\t\t\t["NQ"] = true,'
        f'\t\t}},'
    )


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
                    f.write("\n".join(d["Name"] for d in drops))
                    print(f"Wrote file with {drops_count} equippable items: {outfile}")


# Returns a dict of dungeon_name => lodestone url for a given expansion (0-3)
def dungeon_urls(ex_version):
    r = requests.get(f"{lodestone_base_url}/lodestone/playguide/db/duty/?category2=2&ex_version={ex_version}")
    soup = BeautifulSoup(r.text, 'html.parser')

    urls = {}

    for dungeon in soup.find_all("a", class_="db_popup db-table__txt--detail_link"):
        urls[dungeon.string] = f"{lodestone_base_url}{dungeon.get('href')}"

    return urls


def dungeon_item_names(url):
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')

    drops = set([d.string for d in soup.find_all("a", class_="db_popup tooltip_pos__right_space")])
    drops = list(drops)
    drops.sort()

    return drops


def dungeon_drops(url):
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')

    item_names = set([d.string for d in soup.find_all("a", class_="db_popup tooltip_pos__right_space")])
    item_names = list(item_names)
    item_names.sort()
    drops = []
    for item_name in item_names:
        item = xivapi_item(item_name)
        if can_equip(item):
            drops += [item]
    return drops


if __name__ == '__main__':
    main()
