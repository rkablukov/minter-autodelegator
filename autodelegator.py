#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import math
import logging
from decimal import Decimal
from mintersdk.sdk.transactions import MinterDelegateTx
from mintersdk.minterapi import MinterAPI


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
    level=logging.DEBUG,
)


# Читаем переменные окружения
MINTER_API_URL = os.environ.get('MINTER_API_URL', False)
ADDRESS = os.environ.get('ADDRESS', False)
PRIVATE_KEY = os.environ.get('PRIVATE_KEY', False)
MIN_DELEGATION_AMOUNT = os.environ.get('MIN_DELEGATION_AMOUNT', False) # BIP
VALIDATOR_PUBLIC_KEY = os.environ.get('VALIDATOR_PUBLIC_KEY', False)

if False in [MINTER_API_URL, ADDRESS, PRIVATE_KEY, MIN_DELEGATION_AMOUNT, VALIDATOR_PUBLIC_KEY]:
    raise Exception("MINTER_API_URL or ADDRESS "
                    "or PRIVATE_KEY or MIN_DELEGATION_AMOUNT "
                    "or VALIDATOR_PUBLIC_KEY has not beed defined.")

MIN_DELEGATION_AMOUNT = Decimal(MIN_DELEGATION_AMOUNT)

api = MinterAPI(MINTER_API_URL)


def rewards_per_minute(address):
    status = api.get_status()
    latest_block_height = int(status['result']['latest_block_height'])
    latest_rewards_block_height = latest_block_height - latest_block_height % 12
    events = api.get_events(latest_rewards_block_height)
    rewards = [Decimal(x['value']['amount']) / 10**18 \
        for x in events['result']['events'] \
            if x['value']['address'] == address and x['type'] == 'minter/RewardEvent']
    return sum(rewards)


def delegate(coin, stake):
    tx = MinterDelegateTx(
        pub_key=VALIDATOR_PUBLIC_KEY,
        coin=coin,
        stake=stake-Decimal(0.2),
        nonce=api.get_nonce(ADDRESS),
        gas_coin='BIP'
    )

    tx.sign(PRIVATE_KEY)

    res = api.send_transaction(tx.signed_tx)
    logging.info('%s', res)


def run():
    delay = 60 # значение задержки в секундах

    while True:
        balance = api.get_balance(ADDRESS)
        bip_balance = Decimal(balance['result']['balance']['BIP']) / 10**18
        logging.info('Current balance is %s BIP', bip_balance)

        if bip_balance > MIN_DELEGATION_AMOUNT:
            delegate('BIP', bip_balance)

        delay = math.floor(MIN_DELEGATION_AMOUNT / rewards_per_minute(ADDRESS) * 60)
        delay += 60 # добавим 60 секунд сверху для надёжности

        logging.info('Sleep till %s', time.ctime(int(time.time() + delay)))

        try:
            time.sleep(delay)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    run()
