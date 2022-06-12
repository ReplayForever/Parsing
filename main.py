import requests
from requests import request
import json

from urllib.request import urlopen
from lxml import etree
from dataclasses import dataclass, field


@dataclass
class Ziko:
    address: str
    name: str
    phones: list
    working_hours: list
    latlon: list[int] = field(default_factory=list)


@dataclass
class Monomax:
    address: str
    phones: list
    name: str = "Мономах"


@dataclass
class Kfc:
    address: str
    latlon: list
    name: str
    phones: list
    working_hours: list


def get_address_and_phone_ziko(tree):
    t = 1
    address_tel = tree.xpath('//tr[1]/td[@class="mp-table-address"]/text()')
    infolinia = []
    tel = []
    city = []
    address = []

    while address_tel:
        infolinia.append(address_tel.pop())
        tel.append(address_tel.pop())
        city.append(address_tel.pop())
        address.append(address_tel[0])
        t += 1
        address_tel = tree.xpath(f'//tr[{t}]/td[@class="mp-table-address"]/text()')

    for n in tel:
        ind = tel.index(n)
        tel[ind] = tel[ind].replace(' tel. ', '')
        infolinia[ind] = infolinia[ind].replace('Infolinia: ', '')
        tel[ind] = [tel[ind], infolinia[ind]]
        address[ind] = address[ind] + ',' + city[ind]

    return address, tel


def get_working_time(tree):
    working = tree.xpath('//tr[1]/td[@class="mp-table-hours"]/span/text()')
    time_working = []
    ind_working = 1
    while working:
        time_working_in_one = []
        while working:
            time_working_in_one.append(working.pop(0) + working.pop(0))
        time_working.append(time_working_in_one)
        ind_working += 1
        working = tree.xpath(f'//tr[{ind_working}]/td[@class="mp-table-hours"]/span/text()')
    return time_working


def get_ajax(url):
    headers = {'Content-Type': 'text/html', }
    return request('Post', url).json()


def add_latlon_ziko(class_item, dict_with_latlon):
    for item in class_item:
        for key in dict_with_latlon:
            if dict_with_latlon[key]['address'] in item['address']:
                item['latlon'] = [dict_with_latlon[key]['lat'], dict_with_latlon[key]['lng']]
    pass


def create_json(shop_information_list, file_name):
    with open(f'{file_name}_json', 'w') as f:
        json.dump(shop_information_list, f, ensure_ascii=False)


def get_html(url, file_name):
    headers = {'Content-Type': 'text/html', }
    response = requests.get(url, headers=headers)
    html = response.text
    with open(f'{file_name}_html', 'w') as f:
        f.write(html)


def create_tree(path):
    response = urlopen(f'file:///home/leonid/projects/Parsing/{path}_html')
    htmlparser = etree.HTMLParser()
    return etree.parse(response, htmlparser)


def modify_address_monomax(address):
    for i in range(len(address)):
        if '(' in address[i]:
            address[i], a = address[i].split('(')
        address[i] = address[i][:-1]
    return address


def get_kfc_info(row_json):
    kfc = []
    for i in range(len(row_json['searchResults'])):
        try:
            store = row_json['searchResults'][i]['storePublic']
            name_kfc = store['title']['ru']
            latlon_kfc = store['contacts']['coordinates']['geometry']['coordinates']
            phone_kfc = [store['contacts']['phone']['number']] + store['contacts']['phone']['extensions']
            address_kfc = store['contacts']['streetAddress']['ru'][8:]

            if store['status'] == 'Open':
                daily = store['openingHours']['regularDaily']

                working_time_kfc = ['Пн-Пт ' + daily[0]['timeFrom'] + ' до ' + daily[0]['timeTill']]

                if daily[0]['timeFrom'] != daily[5]['timeFrom'] or daily[0]['timeTill'] != daily[5]['timeTill']:
                    working_time_kfc.append('Сб ' + daily[5]['timeFrom'] + ' до ' + daily[5]['timeTill'])

                    if daily[5]['timeFrom'] != daily[6]['timeFrom'] or daily[5]['timeTill'] != daily[6]['timeTill']:
                        working_time_kfc.append('Вс ' + daily[6]['timeFrom'] + ' до ' + daily[6]['timeTill'])
                    else:
                        working_time_kfc[1] = working_time_kfc[1].replace('Сб', 'Сб-Вс')

                else:
                    if daily[5]['timeFrom'] != daily[6]['timeFrom'] or daily[5]['timeTill'] != daily[6]['timeTill']:
                        working_time_kfc[0] = working_time_kfc[0].replace('Пт', 'Сб')
                        working_time_kfc.append('Вс ' + daily[6]['timeFrom'] + ' до ' + daily[6]['timeTill'])
                    else:
                        working_time_kfc[0] = working_time_kfc[0].replace('Пт', 'Вс')

            else:
                working_time_kfc = ['Close']

            kfc.append(Kfc(
                name=name_kfc,
                address=address_kfc,
                latlon=latlon_kfc,
                phones=phone_kfc,
                working_hours=working_time_kfc
            ).__dict__)

        except TypeError:
            continue
        except KeyError:
            continue

    return kfc


if __name__ == '__main__':

    url_ziko = 'https://www.ziko.pl/lokalizator/'
    file_name_ziko = 'ziko'
    get_html(url_ziko, file_name_ziko)
    tree_ziko = create_tree(file_name_ziko)
    work_time_ziko = get_working_time(tree_ziko)
    name_ziko = tree_ziko.xpath('//tbody/tr/td/span[contains(text(),"Ziko")]/text()')
    address_ziko, phone_ziko = get_address_and_phone_ziko(tree_ziko)

    info_ziko = [Ziko(
        name=name_ziko[i],
        address=address_ziko[i],
        phones=phone_ziko[i],
        working_hours=work_time_ziko[i]
    ).__dict__ for i in range(len(phone_ziko))]

    url_ziko_ajax = 'https://www.ziko.pl/wp-admin/admin-ajax.php?action=get_pharmacies'
    info_ziko_dict = get_ajax(url_ziko_ajax)

    add_latlon_ziko(info_ziko, info_ziko_dict)

    create_json(info_ziko, file_name_ziko)

    url_monomax = 'https://monomax.by/map/'
    file_name_monomax = 'monomax'
    get_html(url_monomax, file_name_monomax)
    tree_monomax = create_tree(file_name_monomax)
    phones_monomax = tree_monomax.xpath('//p/a/text()')
    address_monomax = tree_monomax.xpath('//div[@class="shop"]/p/text()')

    address_monomax = modify_address_monomax(address_monomax)

    info_monomax = [Monomax(
        phones=phones_monomax[i],
        address=address_monomax[i],
    ).__dict__ for i in range(len(phones_monomax))]

    create_json(info_monomax, file_name_monomax)


    kfc_url = 'https://api.kfc.com/api/store/v2/store.get_restaurants?showClosed=true'
    file_name_kfc = 'kfc'
    response = requests.get(kfc_url)
    row_kfc_json = json.loads(response.text)

    info_kfc = get_kfc_info(row_kfc_json)
    create_json(info_kfc, file_name_kfc)
