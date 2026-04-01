import pandas_ta_classic as ta


class ObvMacd:
	def __init__(self, obv_length: int, macd_fast: int, macd_slow: int, macd_signal: int, stoch_k: int, stoch_d: int,
	             stock_smooth: int, sma_lenght: int, macd_w: float, stoch_w: float, obv_w: float, ma_w: float,
	             vol_w: float):
		self.obv_length = obv_length
		self.macd_fast = macd_fast
		self.macd_slow = macd_slow
		self.macd_signal = macd_signal
		self.stoch_k = stoch_k
		self.stoch_d = stoch_d
		self.stock_smooth = stock_smooth
		self.sma_lenght = sma_lenght
		self.macd_w = macd_w
		self.stoch_w = stoch_w
		self.obv_w = obv_w
		self.ma_w = ma_w
		self.vol_w = vol_w

	def calculate_indicators(self, df):
		df['obv'] = ta.obv(df['close'], df['volume'], talib=True)
		df['obv_ema'] = ta.ema(df['obv'], length=self.obv_length, talib=True)  # lenObvEma = 20

		macd_data = ta.macd(df['close'], fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal, talib=True)
		df['macd'] = macd_data[f'MACD_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']
		df['macd_signal'] = macd_data[f'MACDs_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']

		stoch_data = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3, smooth_k=1, talib=True)
		df['stoch_k'] = stoch_data[f'STOCHk_{self.stoch_k}_{self.stoch_d}_{self.stock_smooth}']
		df['stoch_d'] = stoch_data[f'STOCHd_{self.stoch_k}_{self.stoch_d}_{self.stock_smooth}']

		df[f'sma_{self.sma_lenght}'] = ta.sma(df['close'], length=self.sma_lenght, talib=True)

		df["candle_type"] = (df["close"] > df["open"]).astype(int)
		df["candle_type"] = df["candle_type"].replace(0, -1)

		return df

	def crossover(self, c_val, c_sig, p_val, p_sig):
		return 1 if c_val > c_sig and p_val <= p_sig else -1

	def crossunder(self, c_val, c_sig, p_val, p_sig):
		return 1 if c_val < c_sig and p_val >= p_sig else -1

	def check_signals(self, df):
		curr = df.iloc[-1]
		prev = df.iloc[-2]
		obv = self.crossover(curr['obv'], curr['obv_ema'], prev['obv'], prev['obv_ema'])
		macd = self.crossover(curr['macd'], curr['macd_signal'], prev['macd'], prev['macd_signal'])
		stoch = self.crossover(curr['stoch_k'], curr['stoch_d'], prev['stoch_k'], prev['stoch_d'])
		trend = curr['close'] > curr[f'sma_{self.sma_lenght}']
		signal = [macd * self.macd_w, stoch * self.stoch_w, obv * self.obv_w, float(trend * self.ma_w),
		          float(prev['candle_type'] * self.vol_w)]
		signal.append('buy' if sum(signal) > 0 else 'sell')
		return signal
