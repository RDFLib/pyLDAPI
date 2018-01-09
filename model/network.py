import json
import _config as conf


def get_network(network_no):
    network = {
        [
            {
                "id": '{}{}'.format(conf.URI_NETWORK_INSTANCE_BASE, network_no),
                "name": "Network {}".format(network_no),
                "description": "Description of the network",
                "networkURL": "http://networkURL",
                "contactDetails": {
                    "name": "Fred",
                    "phone": "111111",
                    "address": "PO Box 1",
                    "onlineResource": "fred@somewhere.com"
                },
                "environmentalTheme": ["air","water"],
                "extensionFieldName1": "WMO ID",
                "extensionFieldName2": "Photos available",
                "extensionFieldName3": "More info",
                "extensionFieldName4": "Even more info",
                "extensionFieldName5": "Last Maintenance Date"
            }
        ]
    }

    return json.dumps(network)