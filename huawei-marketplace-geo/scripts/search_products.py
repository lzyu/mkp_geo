#!/usr/bin/env python3
"""Search the public Huawei Cloud marketplace; emit cleaned evidence, not rankings."""
import argparse
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

ENDPOINT = 'https://mkpdata.huaweicloud.com/api/marketplace/user/api/mkp-web-guest/global/rest/mkp/v1/mkpsearchengineservice/search'
BASE = 'https://marketplace.huaweicloud.com'


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def clean(value):
    if value is None:
        return None
    parser = PlainText()
    parser.feed(str(value))
    return unescape(''.join(parser.parts)).strip()


def product_url(value):
    if not isinstance(value, str) or not value.strip():
        return None
    url = urljoin(BASE + '/', value.strip())
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.netloc != 'marketplace.huaweicloud.com'
            or not parts.path.startswith('/contents/')
            or not parts.path.removeprefix('/contents/')):
        return None
    return url


def normalize(data, keyword, offset, limit):
    if not isinstance(data, dict) or data.get('error_code') != '00000000':
        code = data.get('error_code', 'missing') if isinstance(data, dict) else 'invalid_response'
        raise ValueError(f'API did not report success: {code}')
    pagination = data.get('pagination')
    if not isinstance(pagination, dict) or not isinstance(pagination.get('items'), list):
        raise ValueError('API response is missing pagination.items')
    products = []
    for item in pagination['items']:
        if not isinstance(item, dict):
            raise ValueError('Invalid product record')
        url = product_url(item.get('url'))
        products.append({
            'id': item.get('id'), 'title': clean(item.get('title')),
            'seller': clean(item.get('corporation_name')),
            'summary': clean(item.get('hcontent')),
            'delivery': clean(item.get('delivery_code_cn')),
            'tags': item.get('tag_names', []),
            'marketplace_url': url,
            'display_price': clean(item.get('price_with_unit')),
            'display_trial_price': clean(item.get('trial_price_with_unit')),
            'trial_flag': item.get('is_trial'),
            'record_updated_at_ms': item.get('update_time'),
            'warnings': ([] if url else ['Missing or invalid marketplace product URL']),
        })
    return {
        'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'source_endpoint': ENDPOINT, 'keyword': keyword,
        'offset': offset, 'limit': limit, 'total': data.get('total'),
        'products': products,
        'limitations': ['Search order is not a recommendation ranking.',
                        'Summaries may be truncated; verify capabilities and SKU scope.',
                        'Displayed prices and trial flags are not complete purchase terms.'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keyword', required=True)
    parser.add_argument('--limit', type=int, default=16)
    parser.add_argument('--offset', type=int, default=0)
    args = parser.parse_args()
    if not args.keyword.strip() or not 1 <= args.limit <= 100 or args.offset < 0:
        parser.error('keyword must be nonempty; limit must be 1..100; offset must be >= 0')
    payload = {'flow_id': '101000', 'keyword': args.keyword, 'limit': args.limit,
               'offset': args.offset, 'filter': {}}
    request = Request(ENDPOINT, data=json.dumps(payload).encode('utf-8'),
                      headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urlopen(request, timeout=30) as response:
            data = json.load(response)
        result = normalize(data, args.keyword, args.offset, args.limit)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        print(json.dumps({'error': type(exc).__name__, 'message': str(exc)},
                         ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
