import pymongo
import os
from bs4 import BeautifulSoup, SoupStrainer
import threading
import urllib3
import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
import argparse
import sys
import threading
from multiprocessing import Queue, Pool
from bson.objectid import ObjectId


def client():
  return pymongo.MongoClient(os.environ.get('DATABASE'))
levels = ['root', 'level_1', 'level_2', 'level_3']

# remove_prefix('House123', 'House') returns 123
def remove_prefix(text, prefix):
  if text.startswith(prefix):
      return text[len(prefix):]

  return text

# remove_all_prefixes('https://www.example.com') returns example.com
def remove_all_prefixes(item):
  url = item

  url = remove_prefix(url, 'https')
  url = remove_prefix(url, 'http')
  url = remove_prefix(url, '://')
  url = remove_prefix(url, 'www.')

  return url

def item_is_empty(item):
  return len(item) == 0

def item_is_pdf_link(item):
  return item.endswith('.pdf')

# item_is_subdirectory(/p/monday) return true
def item_is_subdirectory(item):
  return item.startswith('/')

def starts_with_subdomain(url, parent_url):
  try:
    subdomain = re.search(r'([a-z0-9]+[.])*{}'.format(parent_url), url)

  except Exception as e:
    print("Problem with url: {}".format(url))
    return None

  return subdomain != None and subdomain.group(1) != None

def filter_conditions(item, parent_url):
  if item_is_empty(item) or item_is_pdf_link(item):
    return None

  # Check if the parent_url appears in the item
  if parent_url in item:
    url = remove_all_prefixes(item)

    # check if the cleaned url starts with the parent url
    if url.startswith(parent_url):
      return item

    # check if url is a subdomain of the parent_url
    if starts_with_subdomain(url, parent_url):
      return item

  # check if item is a subdirectory link
  if item_is_subdirectory(item):
    return "{}{}".format(parent_url.split('/')[0], item)

  return None

def create_result_dict(url, soup, links):
  result = {}
  result['subpages'] = [{'url': x} for x  in links]
  result['html'] = str(soup)
  result['url'] = url

  return result

def get_mongo_collection(collection_name):
  database = client()["SAM"]
  collection = database[collection_name]

  return collection

def save_to_mongo(data, collection_name, root_level = None):
  collection = get_mongo_collection(collection_name)
  collection_idx = levels.index(collection_name)
  child_collection_idx = collection_idx + 1

  if child_collection_idx + 1 < len(levels):
    child_collection = get_mongo_collection(levels[child_collection_idx])

    for link in data['subpages']:
      link['parent'] = data['url']
      child_collection.insert_one(link)

  if "_id" in data:
    collection.update({'_id': ObjectId(data['_id'])},  {'$set': {"subpages": data['subpages']}}) 
    collection.update({'_id': ObjectId(data['_id'])},  {'$set': {"html": data['html']}}) 
    collection.update({'_id': ObjectId(data['_id'])},  {'$set': {"root": root_level}}) 

  else:
    collection.insert_one(data)

def get_links_from_mongo_collection_above_current_level(url, level):
  collection = get_mongo_collection('root')
  myquery = { "url": url }
  mydoc = collection.find_one(myquery)

  links = mydoc['subpages']

  results = []
  for level in range(1, level):
    collection = get_mongo_collection(levels[level])

    for link in links:
      myquery = { "_id": ObjectId(link['_id']) }
      mydoc = collection.find_one(ObjectId(link['_id']))

      if mydoc != None:
        results += mydoc['subpages']

  links += results

  return links

def get_links_from_mongo_collection_by_url(url, collection_name):
  collection = get_mongo_collection(collection_name)

  if collection_name == 'root':
    myquery = { "url": url }
    mydoc = collection.find_one(myquery)

    return mydoc['subpages']

  else:
    result = []
    myquery = { "root": url }
    mydoc = collection.find(myquery)

    return [x['subpages'] for x in mydoc if len(x['subpages']) > 0]

def get_links_from_soup(soup, url):
  links = set([link['href'] for link in soup.find_all('a', href=True)])
  links = [filter_conditions(link, url) for link in links]
  links = [link for link in links if link != None]

  return links

def get_page_by_urllib3(url):
  http = urllib3.PoolManager()
  response = http.request("GET", url)

  return response

def get_page_by_selenium(url):
  driver = webdriver.Remote(os.environ.get('BROWSER'), DesiredCapabilities.FIREFOX)
  driver.get(url)

  return driver

def get_soup(data):
  return BeautifulSoup(data, features="lxml")

def parse_site_threaded(url, queue):
  result = parse_site(url['url'])

  if result != None: 
    url['subpages'] = result['subpages']
    url['html'] = result['html']

  else:
    url['subpages'] = []
    url['html'] = ''

  queue.put(url)

def parse_site(url):
  try:
    response = get_page_by_urllib3(url)

    if response.status == 403:
      driver = get_page_by_selenium(url)
      soup = get_soup(driver.page_source)
      driver.close()

    else:
      soup = get_soup(response.data)

    links = get_links_from_soup(soup, url)

    data = create_result_dict(url, soup, links)

    return data

  except Exception as e:
    print("Failed: {}".format(url))
    return None

def parse_root(url):
  data = parse_site(url['url'])
  save_to_mongo(data, 'root')

def create_level_threads(links, queue):
  threads = []

  for link in links:
    thread = threading.Thread(target=parse_site_threaded, args=(link, queue))
    threads.append(thread)

  return threads

def run_level_threads(threads, queue):
  sites = []

  for thread in threads:
    thread.start()

  for thread in threads:
    thread.join()
    data = queue.get()
    sites.append(data)

  return sites

def parse_level(root_url, level = 1, duplicates = False):
  print("Scraping: {}".format(root_url))
  links = get_links_from_mongo_collection_by_url(root_url, levels[level - 1])
  queue = Queue()
  threads = create_level_threads(links, queue)
  sites = run_level_threads(threads, queue)

  if not duplicates:

    # remove duplicate urls from working set
    working_urls = []
    for site in sites:
      site['subpages'] = list(filter(lambda x: x['url'] not in working_urls, site['subpages']))
      working_urls += [x['url'] for x in site['subpages']]

    # remove urls already above level
    parent_links = get_links_from_mongo_collection_above_current_level(root_url, level)
    parent_urls = [link['url'] for link in parent_links]
    for site in sites:
      site['subpages'] = list(filter(lambda x: x['url'] not in parent_urls, site['subpages']))

  for site in sites:
    save_to_mongo(site, levels[level], root_url)

  print("Completed scraping: {}".format(root_url))

def parse_root_threaded(urls):
  threads = []
  queue = Queue()
  for url in urls:
    data = {}
    data['url'] = url
    thread = threading.Thread(target=parse_root, args=(data,))
    threads.append(thread)

  for thread in threads:
    thread.start()

  for thread in threads:
    thread.join()

if __name__ == "__main__":
  print(parse_level('visir.is', 1))
  '''
  filename = 'sites.txt'
  site_file = open(filename, 'r')
  urls = [x.strip() for x in site_file.readlines()]
  #parse_root_threaded(urls)

  pool = Pool(processes=4)
  inputs = urls[0:4]
  result = pool.map(parse_level, inputs)
  '''
