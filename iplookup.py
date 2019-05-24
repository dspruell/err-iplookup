from errbot import BotPlugin, arg_botcmd 

import requests


IP_API_LOOKUP_URL = 'http://ip-api.com/json/{host}'

# http://ip-api.com/docs/api:json
IP_API_GENERATED_NUMERIC = 262143

class Iplookup(BotPlugin):
    '''
    Interface to query for information about IP address at ip-api.com.

    '''
    def _get_ip_type(self, ipdata):
        ''
        ip_types = [t.capitalize() for t in ipdata.keys() if ipdata[t] is True]
        if ip_types:
            return ', '.join(ip_types)
        else:
            return 'Normal'

    @arg_botcmd('host', type=str)
    @arg_botcmd('-g', '--geo',  action='store_true',
                help='return GeoIP data in output')
    @arg_botcmd('-j', '--json',  action='store_true',
                help='return full JSON data for IP')
    def ip(self, message, host, geo=None, json=None):
        'Query for information about IP or resolved FQDN'

        params = {'fields': IP_API_GENERATED_NUMERIC}
        r = requests.get(IP_API_LOOKUP_URL.format(host=host), params=params)
        if json:
            # Dump the raw JSON in text block
            self.send_card(title=host,
                           body=f'```{r.text}```',
                           in_reply_to=message)
            return

        ipdata = r.json()
        if ipdata['status'] == 'success':
            # Signal presence of a certain class of IP by the card color, to
            # highlight when a host is an identified proxy or mobile IP.
            if ipdata['mobile']:
                card_color = 'cyan'
            elif ipdata['proxy']:
                card_color = 'yellow'
            else:
                card_color = 'green'

            # Send a fancy card with fields.
            # If input was a FQDN, display the resolved IP alongside it in
            # the title for clarity.
            if 'host' != ipdata['query']:
                host = f'{host} ({ipdata["query"]})'
            self.send_card(title=host,
                           color=card_color,
                           fields=(
                               ('AS', ipdata['as']),
                               ('ISP', ipdata['isp']),
                               ('Org', ipdata['org']),
                               ('Reverse DNS', ipdata.get('reverse') or '-'),
                               ('Type', self._get_ip_type(ipdata))
                           ),
                           in_reply_to=message)
            if geo:
                self.send_card(summary='Geo data',
                               color=card_color,
                               fields=(
                                   ('Country', f'{ipdata["country"]} ({ipdata["countryCode"]})'),
                                   ('Region', f'{ipdata["regionName"]} ({ipdata["region"]})'),
                                   ('City', f'{ipdata["city"]}'),
                                   ('Coordinates', f'{ipdata["lat"]}, {ipdata["lon"]}')
                               ),
                               in_reply_to=message)
            return
        else:
            # Send out error card with message from API response
            self.send_card(title=ip,
                           color='black',
                           body=f'Error: {ipdata["message"]}',
                           in_reply_to=message)
            return

