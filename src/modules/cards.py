import logging
log = logging.getLogger("cards")

import ujson
import uasyncio as asyncio
import events
import cards_storage as storage

import config
readers = config.modules['cards']['readers']

# Multiple cards readers not supported yet
if len(readers) > 1:
	raise NotImplementedError

# Only wiegand reader is supported supported yet
if readers[0]['type'] != 'wiegand.py':
	raise NotImplementedError

def on_card(card_number, facility_code, cards_read, bit_length):
	log.info("Card UID: %s", reader.last_card)
	log.debug("Card UID/card_number: %s", card_number)
	log.debug("Card UID/facility_code: %s", facility_code)
	log.debug("Card Bit Length: %s", bit_length)

	card = storage.get(reader.last_card)
	if not card:
		log.error("Card not known.")
		events.fire('card.card_not_known', reader.last_card)
		return
	log.info("Card found.")
	if 'd' in card and card['d']:
		log.error("Card is disabled.")
		return
	events.fire('card.card_validated', card)

from wiegand import Wiegand
reader = Wiegand(readers[0]['pin_d1'], readers[0]['pin_d0'], on_card)
# TODO: Use config and support multiple readers
