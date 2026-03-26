import threading
import time
from pprint import pprint

import pandas as pd

import ex
import handlers
import indicator


def trade(ticker, side, amount, leverage = None):
	print(f'Начал сделку по {ticker} в направлении {side}')
	if leverage:
		exchange.preparation_derivative(ticker, leverage)
	orders = exchange.create_orders(ticker, side, amount)
	print('Выставленные ордера: ', *orders)
	closed_order = exchange.wait_close_one_order(ticker, orders)
	print(f'Закрылся ордер: {closed_order}')
	exchange.close_other_orders(ticker)
	if 'USDC' in ticker:
		balance = exchange.get_balance('USDC')
		balance = f'{balance:.2f} USDC'
	else:
		balance = exchange.get_balance('USDT')
		balance = f'{balance:.2f} USDT'
	print(f'Сделка по {ticker} совершена. Баланс: {balance}')


def main():
	print('Получаю свечи по активам')
	candles = exchange.get_ohlcv(indicator_settings['tf'])
	res = {}
	for k, v in candles.items():
		df = pd.DataFrame(v, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
		indicators = ind.calculate_indicators(df)
		dir = ind.check_signals(indicators)
		if dir:
			res[k] = dir
	for k, v in res.items():
		print(f'{k}: obv: {v[0]}, macd: {v[1]}, stoch: {v[2]}, sma: {v[3]}, vol: {v[4]}, '
		      f'signal: {'buy' if sum(v) > 0 else 'sell'}')

	threads = []
	for token, signal in res.items():
		price = exchange.get_price(token)
		if 'USDC' in token:
			balance = exchange.get_balance('USDC')
		else:
			balance = exchange.get_balance('USDT')

		side = 'buy' if sum(signal) > 0 else 'sell'
		amount = order_settings['volume_percent']*balance/price if len([i for i in signal if i > 0]) == 5 \
			else order_settings['volume_const']

		if ':' in token:
			pos = exchange.get_position(token)
			if pos is None:
				threads.append(threading.Thread(target=trade, args=(token, side, amount, order_settings['leverage'],)))
			elif side != pos[0]:
				amount += pos[1]
				threads.append(threading.Thread(target=trade, args=(token, side, amount, order_settings['leverage'],)))
		else:
			order = exchange.get_last_order(token)
			if order is None:
				threads.append(threading.Thread(target=trade, args=(token, side, amount,)))
			elif side != order[0]:
				amount += order[1]
				threads.append(threading.Thread(target=trade, args=(token, side, amount,)))

	if threads:
		print('Совершаю сделки')
		for i in threads:
			i.start()
			i.join()
	print('Всё отработал, жду следующую свечу')


if __name__ == '__main__':
	timeframe_to_shed = {
		'15m': 900,
		'30m': 1800,
		'1h': 3600,
		'4h': 14400
	}

	config = handlers.ConfigHandler()
	api_key, secret_key = config.get_api()
	indicator_settings = config.get_indicator_settings()
	indicator_weights_settings = config.get_indicator_weights_settings()
	order_settings = config.get_order_settings()
	exchange = ex.Exchange(api_key, secret_key)

	ind = indicator.ObvMacd(indicator_settings['obv_length'], indicator_settings['macd_fast'],
	                        indicator_settings['macd_slow'], indicator_settings['macd_signal'],
	                        indicator_settings['stoch_k'], indicator_settings['stoch_d'],
	                        indicator_settings['stoch_smooth'], indicator_settings['sma_lenght'],
	                        indicator_weights_settings['macd'], indicator_weights_settings['stochastic'],
	                        indicator_weights_settings['obv'], indicator_weights_settings['ma'],
	                        indicator_weights_settings['vol'])

	print(f'Привет! Я запустился, жду новую свечу, на {indicator_settings['tf']} таймфрейме')
	while True:
		now = time.time()
		sleep_time = timeframe_to_shed[indicator_settings['tf']] - (now % timeframe_to_shed[indicator_settings['tf']])
		time.sleep(sleep_time)
		try:
			main()
		except (KeyboardInterrupt, SystemExit):
			pass
