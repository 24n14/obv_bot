import time

import ccxt
from ccxt.base.types import OrderRequest
from ccxt.base.errors import BadRequest

import handlers


class Exchange:
	def __init__(self, api_key, api_secret, leverage, volume):
		self.api_key = api_key
		self.api_secret = api_secret
		self.leverage = leverage
		self.volume = volume
		self.api_params = {
			"apiKey": self.api_key,
			"secret": self.api_secret,
			"enableRateLimit": True
		}
		self.cex = ccxt.bybit(self.api_params)
		self.cex.enable_demo_trading(True)

	@handlers.retry
	def get_btc_tickers(self):
		tickers = self.cex.fetch_markets()
		tickers = [i['symbol'] for i in tickers if (i['symbol'][:8] == 'BTC/USDT' and i['symbol'][-1] not in ('P', 'C'))
		           or i['symbol'][:8] == 'BTC/USDC']
		return tickers

	@handlers.retry
	def get_ohlcv(self, timeframe) -> dict:
		tickers = self.get_btc_tickers()
		candles = {i: self.cex.fetch_ohlcv(i, timeframe, limit=300) for i in tickers}
		return candles

	@handlers.retry
	def preparation_derivatives(self):
		cex_tickers = self.get_btc_tickers() # Проверить на контракт
		for token in cex_tickers:
			try:
				self.cex.set_margin_mode('isolated', token, params={'leverage': self.leverage})
				self.cex.set_leverage(symbol=token, leverage=self.leverage)
			except BadRequest:
				pass

	@handlers.retry
	def create_orders(self, ticker, side: str, amount: float): # amount в BTC
		orders = []
		price = self.cex.fetch_ticker(ticker)['last']
		for i in range(-2, 2):
			params = {}
			orders.append(OrderRequest(symbol=ticker, type='limit', side=side, amount=amount, price=price*(1-i/1000), params=params)) # 1000 - десятая процента
		orders = self.cex.create_orders(orders)
		return [i['id'] for i in orders]

	@handlers.retry
	def wait_close_one_order(self, order_ids, ticker):
		while True:
			closed_orders = self.cex.fetch_closed_orders(ticker, limit=10)
			closed_orders_id = [i['id'] for i in closed_orders]
			if [i for i in order_ids if i in closed_orders_id]:
				break
			time.sleep(0.5)

	@handlers.retry
	def close_other_orders(self, ticker):
		self.cex.cancel_all_orders(ticker)
