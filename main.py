#!/usr/bin/env python3
from time import sleep
from configparser import ConfigParser
from PIL import Image, ImageDraw, ImageFont
from qrcode import QRCode, ERROR_CORRECT_M
from brother_ql.brother_ql_create import create_label
from brother_ql.raster import BrotherQLRaster
import requests

CONFIG_FILE = "./qcos-printer.conf"

class QcosApi:

	api_url = None

	def __init__(self, api_url):
		self.api_url = api_url

	def get_printable_ticket(self):
		tickets = requests.get("{}ticketstoprint/".format(self.api_url)).json()
		if len(tickets) == 0:
			return None
		return tickets[0]

	def mark_ticket_printed(self, ticket):
		response = requests.get("{}markTicketPrinted/{}/".format(self.api_url, ticket['pk'])).json()
		return response['success']

	def get_ticket_info(self, pk):
		return requests.get("{}ticketinfo/{}/".format(self.api_url, pk)).json()

	def get_fee(self, pk):
		return requests.get("{}fee/{}/".format(self.api_url, pk)).json()

	def get_camp(self, pk):
		return requests.get("{}camp/{}/".format(self.api_url, pk)).json()

	def get_clan(self, pk):
		return requests.get("{}clan/{}/".format(self.api_url, pk)).json()

	def get_registration(self, pk):
		return requests.get("{}registration/{}/".format(self.api_url, pk)).json()


def get_font(text, maxwidth, maxheight):
	size = 1
	fnt = ImageFont.truetype('Verdana.ttf', size)
	px_size = fnt.getsize(text)
	while px_size[1] < maxheight and px_size[0] < maxwidth:
		size = size + 1
		fnt = ImageFont.truetype('Verdana.ttf', size)
		px_size = fnt.getsize(text)
	return ImageFont.truetype('Verdana.ttf', size - 1)


def draw_text(image, text, pos, maxwidth, maxheight):
	fnt = get_font(text, maxwidth, maxheight)
	image.text(pos, text, font=fnt, fill=(0, 0, 0))
	size = fnt.getsize(text)
	return pos[0] + size[0], pos[1] + size[1]


def main():
	config_parser = ConfigParser()
	config_parser.read(CONFIG_FILE)
	config = config_parser['Main']
	api = QcosApi(config['api_url'])
	ticket_width = int(config['ticket_width'])
	ticket_height = int(config['ticket_height'])

	while True:
		ticket = api.get_printable_ticket()
		if ticket is not None:
			print(ticket)
			ticket_info = api.get_ticket_info(ticket['ticket_info'])
			print(ticket_info)
			fee = api.get_fee(ticket_info['fee'])
			print(fee)
			camp = api.get_camp(fee['camp'])
			print(camp)
			registration = api.get_registration(ticket_info['registration'])
			print(registration)
			clan = api.get_clan(registration['clan'])
			print(clan)
			ticket_image = Image.new('RGB', (ticket_width, ticket_height), color=(255, 255, 255))
			ticket_draw = ImageDraw.Draw(ticket_image)
			pos = draw_text(ticket_draw, camp['name'], (10, 0), ticket_width, ticket_height * 0.25)
			pos = draw_text(ticket_draw, clan['name'], (10, pos[1]), ticket_width, ticket_height * 0.1)
			pos = draw_text(ticket_draw, fee['name'], (10, pos[1]), ticket_width, ticket_height * 0.1)
			draw_text(ticket_draw, ticket['guid'], (10, pos[1]), ticket_width, ticket_height * 0.05)

			qr = QRCode(version=1, error_correction=ERROR_CORRECT_M, box_size=10, border=4)
			qr.add_data(ticket['guid'])
			qr_img = qr.make_image(fill_color="black", bakc_color="white")

			ticket_image.paste(qr_img, (10, int(ticket_height / 2)))

			ticket_image.save(config['temp_file'])

			qlr = BrotherQLRaster(config['model'])
			create_label(qlr, "test.png", '62')
			with open(config['printer_path'], 'wb') as file:
				file.write(qlr.data)
			api.mark_ticket_printed(ticket)
		sleep(2)


if __name__ == "__main__":
	main()
