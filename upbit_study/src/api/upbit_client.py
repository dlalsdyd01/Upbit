"""
업비트 API 클라이언트
공식 문서: https://docs.upbit.com/reference
"""
import jwt
import hashlib
import requests
import uuid
from urllib.parse import urlencode, unquote
from typing import Dict, List, Optional


class UpbitClient:
    """업비트 거래소 API 클라이언트"""

    def __init__(self, access_key: str, secret_key: str):
        """
        Args:
            access_key: 업비트 Open API Access Key
            secret_key: 업비트 Open API Secret Key
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.server_url = "https://api.upbit.com"

    def _get_headers(self, query: Optional[Dict] = None) -> Dict[str, str]:
        """JWT 토큰이 포함된 헤더 생성"""
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }

        if query:
            query_string = unquote(urlencode(query, doseq=True)).encode("utf-8")
            m = hashlib.sha512()
            m.update(query_string)
            query_hash = m.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'

        jwt_token = jwt.encode(payload, self.secret_key)
        return {'Authorization': f'Bearer {jwt_token}'}

    # ========== 공개 API (인증 불필요) ==========

    def get_market_all(self) -> List[Dict]:
        """마켓 코드 조회 (전체 종목 리스트)"""
        url = f"{self.server_url}/v1/market/all"
        params = {'isDetails': 'true'}
        response = requests.get(url, params=params)
        return response.json()

    def get_ticker(self, markets: List[str]) -> List[Dict]:
        """현재가 정보 조회

        Args:
            markets: 마켓 코드 리스트 (예: ['KRW-BTC', 'KRW-ETH'])
        """
        url = f"{self.server_url}/v1/ticker"
        params = {'markets': ','.join(markets)}
        response = requests.get(url, params=params)
        return response.json()

    def get_orderbook(self, markets: List[str]) -> List[Dict]:
        """호가 정보 조회"""
        url = f"{self.server_url}/v1/orderbook"
        params = {'markets': ','.join(markets)}
        response = requests.get(url, params=params)
        return response.json()

    def get_candles_minute(self, market: str, unit: int = 1, count: int = 200) -> List[Dict]:
        """분봉 데이터 조회

        Args:
            market: 마켓 코드 (예: 'KRW-BTC')
            unit: 분 단위 (1, 3, 5, 15, 10, 30, 60, 240)
            count: 캔들 개수 (최대 200)
        """
        url = f"{self.server_url}/v1/candles/minutes/{unit}"
        params = {'market': market, 'count': count}
        response = requests.get(url, params=params)
        return response.json()

    def get_candles_day(self, market: str, count: int = 200) -> List[Dict]:
        """일봉 데이터 조회"""
        url = f"{self.server_url}/v1/candles/days"
        params = {'market': market, 'count': count}
        response = requests.get(url, params=params)
        return response.json()

    # ========== 인증 필요 API ==========

    def get_accounts(self) -> List[Dict]:
        """전체 계좌 조회 (자산 확인)"""
        url = f"{self.server_url}/v1/accounts"
        headers = self._get_headers()
        response = requests.get(url, headers=headers)
        return response.json()

    def get_orders(self, market: Optional[str] = None,
                   state: str = 'wait',
                   states: Optional[List[str]] = None,
                   page: int = 1,
                   limit: int = 100,
                   order_by: str = 'desc') -> List[Dict]:
        """주문 리스트 조회

        Args:
            market: 마켓 코드
            state: 주문 상태 (wait, watch, done, cancel)
            states: 주문 상태 리스트
            page: 페이지 수
            limit: 요청 개수
            order_by: 정렬 방식 (asc, desc)
        """
        query = {
            'state': state,
            'page': page,
            'limit': limit,
            'order_by': order_by
        }

        if market:
            query['market'] = market
        if states:
            query['states[]'] = states

        url = f"{self.server_url}/v1/orders"
        headers = self._get_headers(query)
        response = requests.get(url, params=query, headers=headers)
        return response.json()

    def buy_limit_order(self, market: str, price: float, volume: float) -> Dict:
        """지정가 매수

        Args:
            market: 마켓 코드 (예: 'KRW-BTC')
            price: 주문 가격
            volume: 주문 수량
        """
        query = {
            'market': market,
            'side': 'bid',
            'ord_type': 'limit',
            'price': str(price),
            'volume': str(volume)
        }

        url = f"{self.server_url}/v1/orders"
        headers = self._get_headers(query)
        response = requests.post(url, json=query, headers=headers)
        return response.json()

    def buy_market_order(self, market: str, price: float) -> Dict:
        """시장가 매수

        Args:
            market: 마켓 코드
            price: 매수 총액 (KRW)
        """
        query = {
            'market': market,
            'side': 'bid',
            'ord_type': 'price',
            'price': str(price)
        }

        url = f"{self.server_url}/v1/orders"
        headers = self._get_headers(query)
        response = requests.post(url, json=query, headers=headers)
        return response.json()

    def sell_limit_order(self, market: str, price: float, volume: float) -> Dict:
        """지정가 매도

        Args:
            market: 마켓 코드
            price: 주문 가격
            volume: 주문 수량
        """
        query = {
            'market': market,
            'side': 'ask',
            'ord_type': 'limit',
            'price': str(price),
            'volume': str(volume)
        }

        url = f"{self.server_url}/v1/orders"
        headers = self._get_headers(query)
        response = requests.post(url, json=query, headers=headers)
        return response.json()

    def sell_market_order(self, market: str, volume: float) -> Dict:
        """시장가 매도

        Args:
            market: 마켓 코드
            volume: 매도 수량
        """
        query = {
            'market': market,
            'side': 'ask',
            'ord_type': 'market',
            'volume': str(volume)
        }

        url = f"{self.server_url}/v1/orders"
        headers = self._get_headers(query)
        response = requests.post(url, json=query, headers=headers)
        return response.json()

    def cancel_order(self, uuid: str) -> Dict:
        """주문 취소

        Args:
            uuid: 주문 UUID
        """
        query = {'uuid': uuid}

        url = f"{self.server_url}/v1/order"
        headers = self._get_headers(query)
        response = requests.delete(url, params=query, headers=headers)
        return response.json()

    def get_balance(self, currency: str = 'KRW') -> float:
        """특정 화폐 잔고 조회

        Args:
            currency: 화폐 코드 (KRW, BTC, ETH 등)

        Returns:
            잔고 (float)
        """
        accounts = self.get_accounts()
        for account in accounts:
            if account['currency'] == currency:
                return float(account['balance'])
        return 0.0
