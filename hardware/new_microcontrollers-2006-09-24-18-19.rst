:title: new microcontrollers
:date: 2006-09-24 18:19
:category: hardware

I've been playing with <a href="http://www.phidgets.com/">Phidgets</a>
recently, having a lot of <a
href="http://www.lothar.com/Projects/Phidgets/">fun</a>. They're great for
prototyping, but they would be too expensive to use for most of the
production purposes I have in mind. I've been thinking that for gadgets I
plan to make more than one of, I'd use an <a
href="http://www.ftdichip.com/index.html">FTDI</a> usb-to-serial chip
(somewhere around 2.5UKP from their <a
href="http://apple.clickandbuild.com/cnb/shop/ftdichip?op=catalogue-categories-null">web
store</a>, and I think about $5 from the parallax store) and a small AVR
microcontroller (for another few dollars). The FTDI web store also sells
adapter modules (USB B on one side, header pins on the other) for 10UKP. For
the basic make-lights-blink peripheral I have in mind, the FTDI chip alone
would suffice, as it's got 5 GPIO pins in addition to the serial port.

I've played with the AnchorChips/Cypress EZUSB before, and it's pretty handy,
and you can get them from digikey (page 493 of the digikey catalog lists the
full-speed ones at about $10, and the high-speed ones from $15 to $20), but
it uses an 8051 core, which is a real drag to program.

So I was pleased to see that Atmel is in the USB game, with their <a
href="http://www.atmel.com/dyn/products/product_card.asp?part_id=3874">AT90USB1286</a>
and related parts. 128K flash, 8K ram, firmware that lets you program the
flash over the USB box, sample code and libraries to do mouse/keyboard/HID
stuff (although it doesn't look like the sample code is under a free software
license, boo), and a $31 evaluation kit (basically a USB dongle with breakout
headers). Digikey has the chips for $14, and a cheaper 64K-flash version is
due out soon.

And Atmel also has a <a
href="http://www.atmel.com/products/avr/z-link/">handful</a> of
ZigBee/805.15.4 chips available, which could be really cool. They include the
MAC stack. It's not clear where to buy them or how much they'll cost, though.
It looks like there's enough RF goo that you'd want to go with the eval
board, and that probably means a couple hundred bucks. But eventually this
stuff will make it out to smaller boards.

They're also coming out with a <a
href="http://www.atmel.com/products/AVR/picopower/Default.asp">new series</a>
of AVRs with <b>really</b> low power consumption, down below a microamp.
