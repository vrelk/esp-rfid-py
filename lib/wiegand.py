"""
weigand.py - read card IDs from a wiegand card reader

(C) 2017 Paul Jimenez - released under LGPLv3+
"""

from machine import Pin, Timer
import utime

#CARD_MASK = 0b11111111111111110 # 16 ones
#FACILITY_MASK = 0b1111111100000000000000000 # 8 ones

#26bit H10301
CARD_MASK_WG26 = 0b11111111111111110 # 16 ones
CARD_MASK_OFFSET_WG26 = 1 #shift 1 because the last bit is not part of the card number
FACILITY_MASK_WG26 = 0b1111111100000000000000000 # 8 ones
FACILITY_MASK_OFFSET_WG26 = 17 #shift 17 because CARD_MASK length + it's offset

# 32bit Wiegand
CARD_MASK_WG32 = 0b1111111111111111 # 16 ones
CARD_MASK_OFFSET_WG32 = 0 #no shift needed
FACILITY_MASK_WG32 = 0b1111111111110000000000000000 # 12 ones
FACILITY_MASK_OFFSET_WG32 = 16 #shift 16 because CARD_MASK length + it's offset (0 for this one)

#34bit HID Standard H10306
CARD_MASK_HID34 = 0b11111111111111110 # 16 ones
CARD_MASK_OFFSET_HID34 = 1 #shift 1 because the last bit is not part of the card number
FACILITY_MASK_HID34 = 0b1111111100000000000000000 # 8 ones
FACILITY_MASK_OFFSET_HID34 = 17 #shift 17 because CARD_MASK length + it's offset

#35bit HID Corporate 1000
CARD_MASK_HID35 = 0b111111111111111111110 # 20 ones
CARD_MASK_OFFSET_HID35 = 1 #shift 1 because the last bit is not part of the card number
FACILITY_MASK_HID35 = 0b111111111111000000000000000000000 # 12 ones
FACILITY_MASK_OFFSET_HID35 = 21 #shift 21 because CARD_MASK length + it's offset



# Max pulse interval: 2ms
# pulse width: 50us

class Wiegand:
    def __init__(self, pin0, pin1, callback):
        """
        pin0 - the GPIO that goes high when a zero is sent by the reader
        pin1 - the GPIO that goes high when a one is sent by the reader
        callback - the function called (with two args: card ID and cardcount)
                   when a card is detected.  Note that micropython interrupt
                   implementation limitations apply to the callback!
        """
        self.pin0 = Pin(pin0, Pin.IN)
        self.pin1 = Pin(pin1, Pin.IN)
        self.callback = callback
        self.last_card = None
        self.next_card = 0
        self._bits = 0
        self.pin0.irq(trigger=Pin.IRQ_FALLING, handler=self._on_pin0)
        self.pin1.irq(trigger=Pin.IRQ_FALLING, handler=self._on_pin1)
        self.last_bit_read = None
        self.timer = Timer(-1)
        self.timer.init(period=50, mode=Timer.PERIODIC, callback=self._cardcheck)
        self.cards_read = 0
        self.CARD_MASK = None #Temporary placeholder to use for the current card length
        self.CARD_MASK_OFFSET = None #Temporary placeholder to use for the current card length
        self.FACILITY_MASK = None #Temporary placeholder to use for the current card length
        self.FACILITY_MASK_OFFSET = None #Temporary placeholder to use for the current card length

    def _on_pin0(self, newstate): self._on_pin(0, newstate)
    def _on_pin1(self, newstate): self._on_pin(1, newstate)

    def _on_pin(self, is_one, newstate):
        now = utime.ticks_ms()
        if self.last_bit_read is not None and now - self.last_bit_read < 2:
            # too fast
            return

        self.last_bit_read = now
        self.next_card <<= 1
        if is_one: self.next_card |= 1
        self._bits += 1

    def get_card(self):
        if self.last_card is None:
            return None
        return ( self.last_card & self.CARD_MASK ) >> self.CARD_MASK_OFFSET

    def get_facility_code(self):
        if self.last_card is None:
            return None
        return ( self.last_card & self.FACILITY_MASK ) >> self.FACILITY_MASK_OFFSET

    def _cardcheck(self, t):
        if self.last_bit_read is None: return
        now = utime.ticks_ms()
        if now - self.last_bit_read > 50:
            # too slow - new start!
            self.last_bit_read = None
            self.last_card = self.next_card
            self.next_card = 0
            tmpBits = self._bits
            self._bits = 0
            self.cards_read += 1
            
            self.CARD_MASK = None
            self.FACILITY_MASK = None
            if tmpBits == 26:
                self.CARD_MASK = CARD_MASK_WG26
                self.CARD_MASK_OFFSET = CARD_MASK_OFFSET_WG26
                self.FACILITY_MASK = FACILITY_MASK_WG26
                self.FACILITY_MASK_OFFSET = FACILITY_MASK_OFFSET_WG26
            elif tmpBits == 32:
                self.CARD_MASK = CARD_MASK_WG32
                self.CARD_MASK_OFFSET = CARD_MASK_OFFSET_WG32
                self.FACILITY_MASK = FACILITY_MASK_WG32
                self.FACILITY_MASK_OFFSET = FACILITY_MASK_OFFSET_WG32
            elif tmpBits == 34:
                self.CARD_MASK = CARD_MASK_HID34
                self.CARD_MASK_OFFSET = CARD_MASK_OFFSET_HID34
                self.FACILITY_MASK = FACILITY_MASK_HID34
                self.FACILITY_MASK_OFFSET = FACILITY_MASK_OFFSET_HID34
            elif tmpBits == 35:
                self.CARD_MASK = CARD_MASK_HID35
                self.CARD_MASK_OFFSET = CARD_MASK_OFFSET_HID35
                self.FACILITY_MASK = FACILITY_MASK_HID35
                self.FACILITY_MASK_OFFSET = FACILITY_MASK_OFFSET_HID35
            
            self.callback(self.get_card(), self.get_facility_code(), self.cards_read, tmpBits)
