from discord_webhook import DiscordWebhook, DiscordEmbed
from threading import Thread
from multiprocessing import Process
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor, as_completed
import requests
import time
import datetime
import json
import re


class Vitkac:
    def __init__(self, task, profile):
        self.task = task
        self.profile = profile
        self.s = requests.Session()
        self.title = ""
        self.image_url = ""
        self.driver = None
        self.size_info = ""
        self.product_url = ""
        self.cart_id = ""
        self.site_key = "6LfBVakUAAAAAArEAiLiOFpR0iUMo0kvIUvFy7i4"
        self.captcha_api = "68d7d5fb4f65846f47e34a89945eb18d"
        self.pay_url = ""
        self.captcha_token = ""

    def search_product(self):
        headers = {
            "Host": "www.vitkac.com",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/81.0.4044.138 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Looking for product...")

        try:
            product_search = self.s.get(f"https://www.vitkac.com/pl/sklep/mezczyzni?q={self.task['sku']}",
                                        headers=headers, proxies=self.task['proxy_dict'], timeout=10)
            self.product_url = re.search(r'href="https://www\.vitkac\.com/pl/p/(.*?)"',
                                         product_search.text).group()[6:-1]
            self.image_url = re.search(rf'https://img\.vitkac\.com/uploads/(.*?){self.task["sku"]}(.*?)\.jpg',
                                       product_search.text).group()
            self.title = re.search(r'data-seoname="(.*?)"', product_search.text).group().split('"')[-2]
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Waiting for product: {error}. Retrying...")
            self.search_product()
            return
        except requests.exceptions.RequestException as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Waiting for product: {error}. Retrying...")
            self.search_product()
            return
        except requests.exceptions.ReadTimeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Waiting for product: Timeout. Retrying...")
            self.search_product()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Waiting for product: {error}. Retrying...")
            self.search_product()
            return

        self.load_page()
        return

    def load_page(self):
        headers = {
            "Host": "www.vitkac.com",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/81.0.4044.138 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.9",
            "Referer": f"https://www.vitkac.com/pl/sklep/mezczyzni?q={self.task['sku']}",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Loading product page...")

        try:
            product_page = self.s.get(self.product_url, headers=headers, proxies=self.task['proxy_dict'],
                                      timeout=10)
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Waiting for product...")
            while 'add-to-cart' not in product_page.text:
                headers['Referer'] = self.product_url
                product_page = self.s.get(self.product_url, headers=headers, proxies=self.task['proxy_dict'],
                                          timeout=10)
            sizes = re.findall(r'data-value="(.*?)" data-id="(.*?)" data-stock="(.*?)"', product_page.text)

        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Product page: "
                  f"{error}. Retrying...")
            self.load_page()
            return
        except requests.exceptions.RequestException as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Product page: "
                  f"{error}. Retrying...")
            self.load_page()
            return
        except requests.exceptions.ReadTimeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Product page: "
                  f"Timeout. Retrying...")
            self.load_page()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Product page: "
                  f"{error}. Retrying...")
            self.load_page()
            return

        sizes_dict = {}
        if len(sizes) > 0:
            for size in sizes:
                if size[2] != "0":
                    sizes_dict[size[0]] = [size[1], [size[2]]]
            if self.task['size'] not in list(sizes_dict.keys()):
                self.task['size'] = list(sizes_dict.keys())[0]
                self.size_info = sizes_dict[self.task['size']][0]
            else:
                self.size_info = sizes_dict[self.task['size']][0]
            self.add_to_cart()
            return
        else:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} SOLD OUT. "
                  f"Waiting for restock...")
            time.sleep(.1)
            self.load_page()
            return

    def add_to_cart(self):
        headers = {
            "Host": "www.vitkac.com",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                          " Chrome/81.0.4044.138 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "Referer": self.product_url,
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        try:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Adding to cart...")
            carting = self.s.get(f"https://www.vitkac.com/cart/axAdd?product_id={self.size_info}&qty=1", headers=headers,
                                 proxies=self.task['proxy_dict'], timeout=10)
            while json.loads(carting.content)['count'] == 0:
                carting = self.s.get(f"https://www.vitkac.com/cart/axAdd?product_id={self.size_info}&qty=1", headers=headers,
                                     proxies=self.task['proxy_dict'], timeout=10)
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Added to cart.")
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Carting: "
                  f"{error}. Retrying...")
            self.add_to_cart()
            return
        except requests.exceptions.RequestException as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Carting: "
                  f"{error}. Retrying...")
            self.add_to_cart()
            return
        except requests.exceptions.ReadTimeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Carting: "
                  f"Timeout. Retrying...")
            self.add_to_cart()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Carting: "
                  f"{error}. Retrying...")
            self.add_to_cart()
            return

        self.load_cart_page()
        return

    def load_cart_page(self):
        headers = {
            "Host": "www.vitkac.com",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/81.0.4044.138 Safari/537.36",
            "Referer": self.product_url,
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        try:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Loading cart page...")
            address_page_r = self.s.get("https://www.vitkac.com/quick_order/createFromCart", headers=headers,
                                        proxies=self.task['proxy_dict'], timeout=10)
            while self.task['sku'].upper() not in address_page_r.text:
                address_page_r = self.s.get("https://www.vitkac.com/quick_order/createFromCart", headers=headers,
                                            proxies=self.task['proxy_dict'], timeout=10)

            self.cart_id = re.search('(exponeaCart = ).*(":)', address_page_r.text).group()[16:-2]
            self.captcha_token = self.solve_captcha("https://www.vitkac.com/quick_order/createFromCart")
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Cart page: "
                  f"{error}. Retrying...")
            self.load_cart_page()
            return
        except requests.exceptions.RequestException as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Cart page: "
                  f"{error}. Retrying...")
            self.load_cart_page()
            return
        except requests.exceptions.ReadTimeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Cart page: "
                  f"Timeout. Retrying...")
            self.load_cart_page()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Cart page: "
                  f"{error}. Retrying...")
            self.load_cart_page()
            return

        self.checkout()
        return

    def solve_captcha(self, form_url):
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
              f"[TASK {self.task['id']}] Solving captcha...")
        s = requests.Session()
        r = s.post('http://2captcha.com/in.php?key={}&method=userrecaptcha&googlekey={}&pageurl={}'
                        .format(self.captcha_api, self.site_key, form_url),
                        proxies=self.task['proxy_dict']).text
        # print(r)
        id = r.split("|")[1]
        captcha_r = s.get(f'https://2captcha.com/res.php?key={self.captcha_api}&action=get&id={id}',
                               proxies=self.task['proxy_dict']).text
        while "CAPCHA_NOT_READY" in captcha_r:
            time.sleep(5)
            captcha_r = s.get(f'https://2captcha.com/res.php?key={self.captcha_api}&action=get&id={id}',
                                   proxies=self.task['proxy_dict']).text
        if "OK" in captcha_r:
            return captcha_r.split("|")[1]
        else:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Error solving captcha. Retrying...")
            self.solve_captcha(form_url)
            return

    def checkout(self):
        data = f"cart%5B{self.cart_id}%5D=1&" \
                f"delivery=4&isGift=false&" \
                f"paymentMethod=140&" \
                f"code=&invoice=false&" \
                f"sklep_id=54848&create_account=false&" \
                f"user_address%5Bfirst_name%5D={self.profile['first_name']}&" \
                f"user_address%5Blast_name%5D={self.profile['last_name']}&" \
                f"user_address%5Bcity%5D={self.profile['city']}&" \
                f"user_address%5Bzip_code%5D={self.profile['post_code']}&" \
                f"user_address%5Bstreet%5D={self.profile['street'].replace(' ', '+')}&" \
                f"user_address%5Bstreet_number%5D={self.profile['house_number'].replace(' ', '+')}&" \
                f"user_address%5Bhouse_number%5D=&" \
                f"user_address%5Bcountry_id%5D=PL&" \
                f"user_address%5Bus_state_id%5D=AL&" \
                f"user_address%5Bphone%5D={self.profile['phone']}&" \
                f"user_address%5Bemail_address%5D={self.profile['email'].replace('@', '%40')}&" \
                f"g-recaptcha-response={self.captcha_token}"

        headers = {
            "Host": "www.vitkac.com",
            "Connection": "keep-alive",
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                          " Chrome/81.0.4044.138 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Content-Length": str(len(data)),
            "Origin": "https://www.vitkac.com",
            "Referer": "https://www.vitkac.com/quick_order/createFromCart",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        try:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Trying to checkout...")
            posting_address = self.s.post("https://www.vitkac.com/quick_order/axCreateOrder", headers=headers,
                                          data=data, proxies=self.task['proxy_dict'], timeout=25)

            while not json.loads(posting_address.content)['result']:
                time.sleep(.1)
                posting_address = self.s.post("https://www.vitkac.com/quick_order/axCreateOrder", headers=headers,
                                              data=data, proxies=self.task['proxy_dict'], timeout=25)

            self.pay_url = f'https://www.vitkac.com/p24/' \
                           f'{json.loads(posting_address.content)["response"]["payUrl"].split("/")[-1].replace("amp;", "")}'
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Successful checkout. "
                  f"Finish your payment manually from webhook.")
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Posting address: "
                  f"{error}. Retrying...")
            self.checkout()
            return
        except requests.exceptions.RequestException as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Posting address: "
                  f"{error}. Retrying...")
            self.checkout()
            return
        except requests.exceptions.Timeout as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Posting address: "
                  f"{error}. Retrying...")
            self.checkout()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Posting address: "
                  f"{error}. Retrying...")
            self.checkout()
            return

        self.webhook()
        return

    def webhook(self):
        webhook = DiscordWebhook(
            url=self.task['webhook_url'],
            username="Vitkac Bot")
        embed = DiscordEmbed(title='Successfully checked out a product.', color=242424)
        embed.set_footer(text='via Vitkac Bot', icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/"
                                                         "Internet_Explorer_9_icon.svg/384px-Internet_Explorer_9_"
                                                         "icon.svg.png")
        embed.set_timestamp()
        embed.add_embed_field(name='Product', value=self.title)
        embed.add_embed_field(name='Style Code', value=self.task['sku'])
        embed.add_embed_field(name='Size', value=self.task['size'])
        embed.set_thumbnail(url=self.image_url)
        embed.add_embed_field(name='Email', value=self.profile["email"])
        embed.add_embed_field(name="Payment Link", value="[Click here]({})".format(self.pay_url))
        webhook.add_embed(embed)
        response = webhook.execute()


def main(data):
    task = data[0]
    profile= data[1]
    new_task = Vitkac(task, profile)
    new_task.search_product()


if __name__ == "__main__":
    threads = []
    with open("USER_INPUT_DATA/proxies.txt", "r") as proxies_f, \
            open("USER_INPUT_DATA/tasks.json", "r") as tasks_f, \
            open("USER_INPUT_DATA/profiles.json", "r") as profiles_f:
        proxies = proxies_f.read().split("\n")
        tasks = json.load(tasks_f)
        profiles = json.loads(profiles_f.read())

    # start = time.time()

    for i in range(len(tasks)):
        task = tasks[i]
        proxy_list = proxies[i].split(":")
        proxy_dict = {
            "http": f"http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}",
            "https": f"https://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}"
        }
        task["proxy_dict"] = proxy_dict
        profile = profiles[i]
        t = Process(target=main, args=(task, profile))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # print(time.time() - start)

    # with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
    #     futures = []
    #     for i in range(len(tasks)):
    #         proxy_list = proxies[i].split(":")
    #         proxy_dict = {
    #             "http": f"http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}",
    #             "https": f"https://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}"
    #         }
    #         tasks[i]["proxy_dict"] = proxy_dict
    #         task_data = [tasks[i], profiles[i]]
    #         futures.append(executor.submit(main, task_data))
    #
    #     results = []
    #     for result in as_completed(futures):
    #         results.append(result)
