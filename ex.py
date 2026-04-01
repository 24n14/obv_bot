import time

import ccxt
from ccxt.base.errors import BadRequest

import handlers


class Exchange:
	def __init__(self, api_key, api_secret):
		self.api_key = api_key
		self.api_secret = api_secret
		self.api_params = {
			"apiKey": self.api_key,
			"secret": self.api_secret,
			"enableRateLimit": True
		}
		self.cex = ccxt.bybit(self.api_params)
		self.cex.enable_demo_trading(True)

	@handlers.retry
	def get_balance(self, token):
		return self.cex.fetch_balance()[token]['free']

	@handlers.retry
	def get_price(self, ticker):
		return self.cex.fetch_ticker(ticker)['last']

	@handlers.retry
	def get_btc_tickers(self):
		tickers = self.cex.fetch_markets()
		tickers = [i['symbol'] for i in tickers if (i['symbol'][:8] == 'BTC/USDT' and i['symbol'][-1] not in ('P', 'C'))
		           or i['symbol'][:8] == 'BTC/USDC']
		return tickers

	@handlers.retry
	def get_ohlcv(self, timeframe, tickers) -> dict:
		candles = {i: self.cex.fetch_ohlcv(i, timeframe, limit=300) for i in tickers}
		return candles

	@handlers.retry
	def preparation_derivative(self, ticker, leverage):
		try:
			self.cex.set_margin_mode('isolated', ticker, params={'leverage': leverage})
			self.cex.set_leverage(symbol=ticker, leverage=leverage)
		except BadRequest:
			pass

	@handlers.retry
	def get_position(self, symbol):
		position = self.cex.fetch_position(symbol)
		if not position['contracts']:
			return None
		return ['buy' if position['side'] == 'long' else 'sell', position['contracts'] * position['contractSize']]

	@handlers.retry
	def get_last_order(self, ticker):
		timestamp = (int(time.time()) - 14700) * 1000  # 4 часа 5 минут (из-за максимального TF 4h)
		orders = self.cex.fetch_closed_orders(ticker, since=timestamp)
		if not orders or not orders[-1]['amount']:
			return None
		return [orders[-1]['side'], orders[-1]['filled']]

	@handlers.retry
	def create_orders(self, ticker, side: str, amount: float):  # amount в BTC
		orders = []
		price = self.get_price(ticker)
		if side == 'buy':
			for i in range(-2, 1):
				orders.append(self.cex.create_order(symbol=ticker,
				                                    type='limit',
				                                    side=side,
				                                    amount=amount,
				                                    price=price * (1 + i * 5 / 1000)))  # 1000 - десятая процента
		else:
			for i in range(0, 3):
				orders.append(self.cex.create_order(symbol=ticker,
				                                    type='limit',
				                                    side=side,
				                                    amount=amount,
				                                    price=price * (1 + i * 5 / 1000)))  # 1000 - десятая процента
		return [i['id'] for i in orders]

	@handlers.retry
	def wait_close_one_order(self, ticker, order_ids):
		while True:
			closed_orders = self.cex.fetch_closed_orders(ticker, limit=10)
			closed_orders_id = [i['id'] for i in closed_orders]
			closed_order_id = [i for i in order_ids if i in closed_orders_id]
			if closed_order_id:
				return closed_order_id
			time.sleep(0.5)

	@handlers.retry
	def close_other_orders(self, ticker):
		self.cex.cancel_all_orders(ticker)
