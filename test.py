import requests
import hmac
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor


class Trade:
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.symbol = "BTCTUSD"
        self._type = "LIMIT"
        self.time_in_force = "GTC"
        self.recv_window = 5000
        self.benefit = 0
    def send_request(self, method, url, message, signature):
        headers = {
            "X-MBX-APIKEY": self.api_key
        }
        data = f"{message}&signature={signature}"

        if method == "POST":
            response = requests.post(url, headers=headers, data=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, data=data)
        elif method == 'GET':
            response = requests.get(url, headers=headers, params=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        return response

    def sign_message(self, message):
        return hmac.new(self.secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()

    def buy(self, quantity, price):
        current_timestamp = int(time.time() * 1000)
        side = "BUY"
        message = f"symbol={self.symbol}&side={side}&type={self._type}&timeInForce={self.time_in_force}&quantity={quantity}&price={price}&recvWindow={self.recv_window}&timestamp={current_timestamp}"
        signature = self.sign_message(message)
        url = "https://api.binance.com/api/v3/order"
        response = self.send_request("POST", url, message, signature)
        print(f'购买订单已经下单,价格是{price}')
        return response.json()["orderId"]

    def sell(self, quantity, price):
        current_timestamp = int(time.time() * 1000)
        side = "SELL"
        message = f"symbol={self.symbol}&side={side}&type={self._type}&timeInForce={self.time_in_force}&quantity={quantity}&price={price}&recvWindow={self.recv_window}&timestamp={current_timestamp}"
        signature = self.sign_message(message)
        url = "https://api.binance.com/api/v3/order"
        response = self.send_request("POST", url, message, signature)
        print(f'销售订单已经下单,价格是{price}')
        return response.json()["orderId"]

    def get_depth(self):
        response = requests.get("https://api.binance.com/api/v3/depth?symbol=BTCTUSD&limit=1")
        asks = response.json()["asks"][0][0]
        bids = response.json()["bids"][0][0]
        print('当前深度信息为:', response.text)
        return asks, bids

    def cancel(self, order_id):
        url = "https://api.binance.com/api/v3/order"
        current_timestamp = int(time.time() * 1000)
        symbol = "BTCTUSD"
        message = f"symbol={symbol}&orderId={order_id}&timestamp={current_timestamp}"
        signature = self.sign_message(message)
        response = self.send_request("DELETE", url, message, signature)
        return response.text

    def get_orders(self):
        url = "https://api.binance.com/api/v3/openOrders"
        current_timestamp = int(time.time() * 1000)
        symbol = "BTCTUSD"
        message = f"symbol={symbol}&timestamp={current_timestamp}"
        signature = self.sign_message(message)
        response = self.send_request("GET", url, message, signature)
        return response.json()

    def get_account(self):
        url = 'https://api.binance.com/sapi/v3/asset/getUserAsset'
        current_timestamp = int(time.time() * 1000)
        message = f'timestamp={current_timestamp}&needBtcValuation=True'
        signature = self.sign_message(message)
        response = self.send_request('POST',url,message,signature)
        return response.text

    def execute_trades(t, quantity, sell_price, buy_price):
        sell_id = t.sell(quantity, sell_price)
        buy_id = t.buy(quantity, buy_price)
        return sell_id, buy_id


api_key = "WclWVrit66lTgicxWQz0mSSWUlXz4rmrStK4qQuf2NzNRFs3KhJifcAxaKnU3Myh"
secret_key = "3iNZBow4Ye92QknOe9rqA7vt0nslLQbb39fPCBboB6xl61i7V5WddqekN2zhONC1"
t = Trade(api_key, secret_key)

while True:
    time.sleep(0.5)
    quantity = float(0.001)
    sell_price, buy_price = t.get_depth()

    with ThreadPoolExecutor(max_workers=2) as executor:
        sell_future = executor.submit(t.sell, quantity, sell_price)
        buy_future = executor.submit(t.buy, quantity, buy_price)
        sell_id = sell_future.result()
        buy_id = buy_future.result()

    while True:
        time.sleep(0.5)
        orders = t.get_orders()
        if len(orders) == 2:
            print(f'当前订单数为2, 即将取消订单')
            t.cancel(buy_id)
            t.cancel(sell_id)
            print("取消成功")
            break
        elif len(orders) == 1:
            if orders[0]["side"] == 'SELL':
                print(f'当前剩余一个卖单，价格为{orders[0]["price"]}')
            else:
                print(f'当前剩余一个买单，价格为{orders[0]["price"]}')
        else:
            print(f'当前订单数为0')
            t.benefit += (float(sell_price) - float(buy_price))*quantity
            print(f'差价为{float(sell_price) - float(buy_price)}BTC')
            break
    print(f'当前总收益为{t.benefit}')
# print(t.get_account())