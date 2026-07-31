"""
行情数据采集模块
支持数据源: AKShare(免费) / Tushare / Yahoo Finance
支持市场: A股(SH/SZ) / 港股(HK) / 美股(US)
"""

import json
import time
import requests
from datetime import datetime
from typing import Optional, Dict, List


class MarketFetcher:
    """行情数据采集器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.cache = {}
        self.cache_ttl = 30  # 缓存30秒
    
    def fetch_realtime(self, symbol: str, market: str = 'cn') -> dict:
        """获取实时行情数据"""
        cache_key = f"{symbol}_rt"
        if cache_key in self.cache and time.time() - self.cache[cache_key]['ts'] < self.cache_ttl:
            return self.cache[cache_key]['data']
        
        try:
            if market in ('cn', 'sh', 'sz'):
                data = self._fetch_a_share(symbol)
            elif market == 'hk':
                data = self._fetch_hk_stock(symbol)
            elif market == 'us':
                data = self._fetch_us_stock(symbol)
            else:
                data = self._fetch_via_yahoo(symbol)
        except Exception as e:
            data = {'error': str(e), 'symbol': symbol}
        
        self.cache[cache_key] = {'data': data, 'ts': time.time()}
        return data
    
    def fetch_history(self, symbol: str, days: int = 60, market: str = 'cn') -> dict:
        """获取历史K线数据"""
        try:
            if market in ('cn', 'sh', 'sz'):
                return self._fetch_a_share_history(symbol, days)
            elif market == 'us':
                return self._fetch_us_history(symbol, days)
            else:
                return self._fetch_via_yahoo_history(symbol, days)
        except Exception as e:
            return {'error': str(e), 'symbol': symbol}
    
    def fetch_news(self, symbol: str, limit: int = 5) -> list:
        """获取相关新闻"""
        try:
            return self._fetch_financial_news(symbol, limit)
        except Exception as e:
            return [{'error': str(e)}]
    
    def _fetch_a_share(self, symbol: str) -> dict:
        """获取A股实时行情 (via AKShare)"""
        try:
            import akshare as ak
            code = symbol.split('.')[0]
            
            # 实时行情
            df = ak.stock_zh_a_spot_em()
            row = df[df['代码'] == code]
            if len(row) == 0:
                return {'error': f'未找到 {symbol}'}
            
            row = row.iloc[0]
            return {
                'symbol': symbol,
                'name': row.get('名称', ''),
                'price': float(row.get('最新价', 0)),
                'change_pct': float(row.get('涨跌幅', 0)),
                'change_amt': float(row.get('涨跌额', 0)),
                'volume': float(row.get('成交量', 0)),
                'amount': float(row.get('成交额', 0)),
                'high': float(row.get('最高', 0)),
                'low': float(row.get('最低', 0)),
                'open': float(row.get('今开', 0)),
                'prev_close': float(row.get('昨收', 0)),
                'turnover_rate': float(row.get('换手率', 0)),
                'pe': float(row.get('市盈率-动态', 0)) if '市盈率-动态' in row else 0,
                'market_cap': float(row.get('总市值', 0)),
                'timestamp': datetime.now().isoformat()
            }
        except ImportError:
            return self._fetch_a_share_web(symbol)
    
    def _fetch_a_share_history(self, symbol: str, days: int) -> dict:
        """获取A股历史K线"""
        try:
            import akshare as ak
            code = symbol.split('.')[0]
            df = ak.stock_zh_a_hist(symbol=code, period='daily', 
                                      start_date=(datetime.now() - __import__('datetime').timedelta(days=days+30)).strftime('%Y%m%d'),
                                      end_date=datetime.now().strftime('%Y%m%d'),
                                      adjust='qfq')
            
            result = {
                'symbol': symbol,
                'count': len(df),
                'dates': df['日期'].tolist(),
                'open': df['开盘'].astype(float).tolist(),
                'high': df['最高'].astype(float).tolist(),
                'low': df['最低'].astype(float).tolist(),
                'close': df['收盘'].astype(float).tolist(),
                'volume': df['成交量'].astype(float).tolist(),
                'amount': df['成交额'].astype(float).tolist() if '成交额' in df.columns else [],
                'turnover': df['换手率'].astype(float).tolist() if '换手率' in df.columns else []
            }
            return result
        except Exception as e:
            return {'error': str(e), 'symbol': symbol}
    
    def _fetch_a_share_web(self, symbol: str) -> dict:
        """通过Web API获取A股行情(备用)"""
        try:
            code = symbol.split('.')[0]
            # 使用东方财富API
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=1.{code}&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60,f116,f117,f162,f167,f168,f169,f170,f171"
            resp = requests.get(url, timeout=5)
            data = resp.json()
            d = data.get('data', {})
            if not d:
                return {'error': f'未找到 {symbol}'}
            return {
                'symbol': symbol,
                'price': d.get('f43', 0) / 100 if d.get('f43') else 0,
                'high': d.get('f44', 0) / 100 if d.get('f44') else 0,
                'low': d.get('f45', 0) / 100 if d.get('f45') else 0,
                'open': d.get('f46', 0) / 100 if d.get('f46') else 0,
                'volume': d.get('f47', 0),
                'amount': d.get('f48', 0),
                'prev_close': d.get('f60', 0) / 100 if d.get('f60') else 0,
                'change_pct': d.get('f170', 0) / 100 if d.get('f170') else 0,
                'turnover_rate': d.get('f168', 0) / 100 if d.get('f168') else 0,
                'pe': d.get('f162', 0) / 100 if d.get('f162') else 0,
                'market_cap': d.get('f116', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e), 'symbol': symbol}
    
    def _fetch_hk_stock(self, symbol: str) -> dict:
        """获取港股行情"""
        try:
            import akshare as ak
            code = symbol.replace('.HK', '')
            df = ak.stock_hk_spot_em()
            row = df[df['代码'] == code]
            if len(row) == 0:
                return {'error': f'未找到 {symbol}'}
            row = row.iloc[0]
            return {
                'symbol': symbol,
                'name': row.get('名称', ''),
                'price': float(row.get('最新价', 0)),
                'change_pct': float(row.get('涨跌幅', 0)),
                'volume': float(row.get('成交量', 0)),
                'amount': float(row.get('成交额', 0)),
                'high': float(row.get('最高', 0)),
                'low': float(row.get('最低', 0)),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e), 'symbol': symbol}
    
    def _fetch_us_stock(self, symbol: str) -> dict:
        """获取美股行情"""
        try:
            import akshare as ak
            code = symbol.replace('.US', '')
            df = ak.stock_us_spot_em()
            row = df[df['代码'] == code]
            if len(row) == 0:
                return {'error': f'未找到 {symbol}'}
            row = row.iloc[0]
            return {
                'symbol': symbol,
                'name': row.get('名称', ''),
                'price': float(row.get('最新价', 0)),
                'change_pct': float(row.get('涨跌幅', 0)),
                'volume': float(row.get('成交量', 0)),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e), 'symbol': symbol}
    
    def _fetch_us_history(self, symbol: str, days: int) -> dict:
        """获取美股历史K线"""
        try:
            import akshare as ak
            code = symbol.replace('.US', '')
            df = ak.stock_us_hist(symbol=code, period='daily', 
                                   adjust='qfq')
            if len(df) > days:
                df = df.tail(days)
            return {
                'symbol': symbol,
                'dates': df.index.tolist() if hasattr(df.index, 'tolist') else list(range(len(df))),
                'open': df['开盘'].astype(float).tolist(),
                'high': df['最高'].astype(float).tolist(),
                'low': df['最低'].astype(float).tolist(),
                'close': df['收盘'].astype(float).tolist(),
                'volume': df['成交量'].astype(float).tolist()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _fetch_via_yahoo(self, symbol: str) -> dict:
        """通过Yahoo Finance获取行情(通用备用)"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            resp = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            data = resp.json()
            result = data.get('chart', {}).get('result', [{}])[0]
            meta = result.get('meta', {})
            return {
                'symbol': symbol,
                'price': meta.get('regularMarketPrice', 0),
                'high': meta.get('regularMarketDayHigh', 0),
                'low': meta.get('regularMarketDayLow', 0),
                'open': meta.get('regularMarketDayOpen', 0),
                'prev_close': meta.get('chartPreviousClose', 0),
                'volume': meta.get('regularMarketVolume', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e), 'symbol': symbol}
    
    def _fetch_via_yahoo_history(self, symbol: str, days: int) -> dict:
        """通过Yahoo Finance获取历史K线(通用备用)"""
        try:
            import akshare as ak
            df = ak.stock_us_hist(symbol=symbol.replace('.SH','').replace('.SZ',''), period='daily', adjust='qfq')
            if len(df) > days:
                df = df.tail(days)
            return {
                'symbol': symbol,
                'close': df['收盘'].astype(float).tolist(),
                'high': df['最高'].astype(float).tolist(),
                'low': df['最低'].astype(float).tolist(),
                'volume': df['成交量'].astype(float).tolist()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _fetch_financial_news(self, symbol: str, limit: int = 5) -> list:
        """获取财经新闻"""
        news_list = []
        sources = [
            self._fetch_cls_news,
            self._fetch_eastmoney_news,
            self._fetch_sina_news
        ]
        
        for fetch_func in sources:
            try:
                news = fetch_func(symbol, limit)
                if news and len(news) > 0:
                    news_list.extend(news)
                    break
            except:
                continue
        
        return news_list[:limit]
    
    def _fetch_cls_news(self, symbol: str, limit: int) -> list:
        """财联社新闻"""
        try:
            import akshare as ak
            df = ak.stock_news_em(symbol=symbol.split('.')[0])
            if len(df) == 0:
                return []
            result = []
            for _, row in df.head(limit).iterrows():
                result.append({
                    'title': row.get('新闻标题', ''),
                    'content': row.get('新闻内容', ''),
                    'time': str(row.get('发布时间', '')),
                    'source': '财联社',
                    'url': row.get('新闻链接', '')
                })
            return result
        except:
            return []
    
    def _fetch_eastmoney_news(self, symbol: str, limit: int) -> list:
        """东方财富新闻"""
        try:
            import akshare as ak
            df = ak.stock_news_em(symbol=symbol.split('.')[0])
            if len(df) == 0:
                return []
            result = []
            for _, row in df.head(limit).iterrows():
                result.append({
                    'title': row.get('新闻标题', ''),
                    'content': row.get('新闻内容', '')[:200],
                    'time': str(row.get('发布时间', '')),
                    'source': '东方财富'
                })
            return result
        except:
            return []
    
    def _fetch_sina_news(self, symbol: str, limit: int) -> list:
        """新浪财经新闻(备用)"""
        try:
            code = symbol.split('.')[0]
            url = f"https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_AllNewsStock/symbol/{code}.phtml"
            resp = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            items = soup.select('.datelist ul li a')[:limit]
            result = []
            for item in items:
                result.append({
                    'title': item.get_text(strip=True),
                    'url': item.get('href', ''),
                    'source': '新浪财经'
                })
            return result
        except:
            return []


def calc_technical_indicators(history: dict) -> dict:
    """根据历史数据计算技术指标"""
    try:
        import numpy as np
        
        closes = np.array(history.get('close', []), dtype=float)
        highs = np.array(history.get('high', []), dtype=float)
        lows = np.array(history.get('low', []), dtype=float)
        volumes = np.array(history.get('volume', []), dtype=float)
        
        if len(closes) < 30:
            return {'error': '数据不足(需要至少30个交易日)'}
        
        result = {}
        
        # 均线
        for period in [5, 10, 20, 60]:
            if len(closes) >= period:
                result[f'ma{period}'] = float(np.mean(closes[-period:]))
        
        # MACD
        if len(closes) >= 35:
            ema12 = _ema(closes, 12)
            ema26 = _ema(closes, 26)
            dif = ema12 - ema26
            dea = _ema(dif[~np.isnan(dif)], 9)
            result['macd_dif'] = float(dif[-1])
            result['macd_dea'] = float(dea[-1]) if len(dea) > 0 else 0
            result['macd_hist'] = float(dif[-1] - dea[-1]) if len(dea) > 0 else 0
        
        # RSI
        if len(closes) >= 15:
            deltas = np.diff(closes[-15:])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            result['rsi'] = float(100 - 100 / (1 + avg_gain / avg_loss)) if avg_loss > 0 else 100.0
        
        # ATR
        if len(highs) >= 15:
            tr = np.zeros(len(highs) - 1)
            for i in range(1, len(highs)):
                tr[i-1] = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
            result['atr'] = float(np.mean(tr[-14:]))
        
        # 布林带
        if len(closes) >= 20:
            ma20 = np.mean(closes[-20:])
            std = np.std(closes[-20:])
            result['boll_upper'] = float(ma20 + 2 * std)
            result['boll_middle'] = float(ma20)
            result['boll_lower'] = float(ma20 - 2 * std)
        
        # 成交量均线
        if len(volumes) >= 20:
            result['vol_ma20'] = float(np.mean(volumes[-20:]))
            result['vol_ratio'] = float(volumes[-1] / np.mean(volumes[-20:]))
        
        # 动量
        for period in [5, 20, 60]:
            if len(closes) >= period:
                result[f'momentum_{period}d'] = float((closes[-1] / closes[-period] - 1) * 100)
        
        result['timestamp'] = datetime.now().isoformat()
        return result
        
    except Exception as e:
        return {'error': str(e)}


def _ema(data, period):
    """计算EMA"""
    if len(data) < period:
        return np.full(len(data), np.nan)
    result = np.full(len(data), np.nan)
    result[period-1] = np.mean(data[:period])
    k = 2.0 / (period + 1)
    for i in range(period, len(data)):
        result[i] = data[i] * k + result[i-1] * (1-k)
    return result


if __name__ == '__main__':
    import sys
    config = {'platform': 'qmt'}
    fetcher = MarketFetcher(config)
    
    symbol = sys.argv[1] if len(sys.argv) > 1 else '600519.SH'
    market = sys.argv[2] if len(sys.argv) > 2 else 'cn'
    
    print(f"=== 行情数据: {symbol} ===")
    rt = fetcher.fetch_realtime(symbol, market)
    for k, v in rt.items():
        if k != 'timestamp':
            print(f"  {k}: {v}")
    
    print(f"\n=== 技术指标 ===")
    hist = fetcher.fetch_history(symbol, 60, market)
    if 'error' not in hist:
        indicators = calc_technical_indicators(hist)
        for k, v in indicators.items():
            print(f"  {k}: {v}")
    
    print(f"\n=== 最新新闻 ===")
    news = fetcher.fetch_news(symbol, 3)
    for n in news:
        print(f"  [{n.get('source','')}] {n.get('title','')}")
