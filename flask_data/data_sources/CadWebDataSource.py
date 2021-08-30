from .TimeSourceBase import TimeSourceBase
from threading import Thread

import requests
import time
import json


class CadWebDataSource(TimeSourceBase):
    tabs = ['https://cadweb.bnl.gov/dashs/Operations/BroadcastWeb/Injection.dash',
            'https://cadweb.bnl.gov/dashs/Operations/BroadcastWeb/Ramp.dash',
            'https://cadweb.bnl.gov/dashs/Operations/BroadcastWeb/Store.dash']

    def __init__(self, tab_id, watch_list) -> None:
        super().__init__()

        self.tab_id = tab_id
        self.watch_list = watch_list

        self.running = True
        self.gather_thread = Thread(target=self._thread_fn)
        self.gather_thread.start()

    def _thread_fn(self):
        while self.running:
            self.gather()

    def init_connection(self):
        curdate = int(time.time() * 3)
        init_message = {
            'v-browserDetails': 1,
            'theme': 'dashs-dark',
            'v-appId': 'dashs-95355681',
            # 4 arguments specifying screen and client window resolution
            # (doesn't seem to matter much)
            'v-sh': 768,
            'v-sw': 1366,
            'v-ch': 768,
            'v-cw': 1366,
            'v-curdate': curdate,  # Unix timestamp
            # Timezone offset?
            'v-tzo': -120,
            'v-dstd': 60,
            'v-rtzo': -60,
            'v-dston': True,
            'v-vw': 1366,
            'v-vh': 768,
            'v-loc': self.tab,
            'v-wn': '759'
        }
        init_url = self.tab + '?v-{}'.format(curdate)

        init_post = self.s.post(init_url, init_message)
        init_resp = json.loads(init_post.text)
        init_uidl = json.loads(init_resp['uidl'])
        return init_resp['v-uiId'], init_uidl

    def find_interesting_types(self, typemap, types):
        our_types = {}
        for element in typemap.items():
            if element[0] == 'gov.bnl.cad.vchart.VChart'\
                    or element[0] == 'com.vaadin.ui.Label':
                # Save both name (for lookup later) and an empty array
                # for items which are of that type.
                our_types[element[1]] = {'name': element[0], 'items': []}

        for element in types.items():
            t = int(element[1])
            if t in our_types:
                our_types[t]['items'].append(element[0])

        return our_types

    def make_update_msg(self, components, UIDL_Data):
        poll_java_method = 'poll'
        poll_java_ns = 'com.vaadin.shared.ui.ui.UIServerRpc'
        poll_array = []
        for comp in components:
            poll_array.append([comp, poll_java_ns, poll_java_method, []])
        msg = {
            'csrfToken': UIDL_Data['token'],
            'clientId': UIDL_Data['clientId'],
            'syncId': UIDL_Data['syncId'],
            'rpc': poll_array,
            'wsver': '7.7.0'
        }
        return msg

    def send_update_request(self, components, UIDL_Data):
        msg = self.make_update_msg(components, UIDL_Data)
        resp = UIDL_Data['requests_session'].post(
            UIDL_Data['uidl_url'], json=msg)
        result = json.loads(resp.text[9:-1:1])

        clientId = 0
        syncId = 0
        if 'clientId' in result:
            clientId = result['clientId']
            syncId = result['syncId']
        UIDL_Data['clientId'] = clientId
        UIDL_Data['syncId'] = syncId

        return result

    def gather(self):
        self.s = requests.Session()

        # Which tab of the application to get:
        self.tab = self.tabs[int(self.tab_id)]

        uidl_id, uidl = self.init_connection()
        token = uidl['Vaadin-Security-Key']

        our_types = self.find_interesting_types(
            uidl['typeMappings'], uidl['types'])

        # Into separate variables
        our_charts = [x for x in our_types.items() if x[1]['name']
                      == 'gov.bnl.cad.vchart.VChart'][0][1]['items']
        our_charts.sort(key=lambda v: int(v))
        our_labels = [x for x in our_types.items() if x[1]['name']
                      == 'com.vaadin.ui.Label'][0][1]['items']
        our_labels.sort(key=lambda v: int(v))

        # Which items are to be polled
        to_sync = [x for x in uidl['state']
                   if 'pollInterval' in uidl['state'][x]]

        we_want = self.watch_list
        prefixes = ['Blue', 'Yellow']
        to_send = {}
        vals = {}
        pick_next = None
        prefix = ''
        for label in our_labels:
            text = uidl['state'][label]['text']
            if pick_next:
                to_send[label] = f'{prefix}{pick_next}'
                vals[label] = text
                pick_next = None
            if text in prefixes:
                prefix = f'{text} '
            if f'{prefix}{text}' in we_want:
                pick_next = text

        uidl_url = 'https://cadweb.bnl.gov/dashs/UIDL/?v-uiId={}'.format(
            uidl_id)
        clientId = 0
        syncId = uidl['syncId']

        UIDL_Data = {
            'clientId': clientId,
            'syncId': syncId,
            'uidl_url': uidl_url,
            'token': token,
            'requests_session': self.s
        }

        while self.running:
            next_call = time.time()

            while self.running:
                result = self.send_update_request(to_sync, UIDL_Data)
                if 'state' not in result:
                    return

                for id in to_send:
                    if id in result['state']:
                        try:
                            val = result['state'][id]['text']
                        except KeyError:
                            return
                        vals[id] = val

                fvals = [float(vals[id].split()[0]) for id in to_send]
                self.raise_on_data(fvals)

                next_call = next_call + 5
                sleeptime = next_call - time.time()
                if sleeptime >= 0:
                    time.sleep(next_call - time.time())
