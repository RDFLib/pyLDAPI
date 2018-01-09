def get_site_observing_capabilities(site_no):
    oc = {
        "observedProperty": "atmosphere-atmosphericTemperature",  # TODO: get from http://cloud.neii.gov.au/neii/neii-observed-property/version-1/concept
        "procedure": "http://externalURI.com",  # TODO: make procedure Reigster
        "observationMethod": "inSituOceanBasedPlatforms",  # TODO: get from http://cloud.neii.gov.au/neii/neii-observation-method/version-1/concept
        "dataAvailabilityStatus": "available-online",
        "samplingRegime": "adhoc",
        "firstObservationDate": "2015-05-14"
    },