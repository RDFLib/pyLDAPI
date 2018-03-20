def get_site_observing_capabilities(site_no):
    oc = {
        # TODO: get from http://cloud.neii.gov.au/neii/neii-observed-property/version-1/concept
        "observedProperty": "atmosphere-atmosphericTemperature",
        # TODO: make procedure Reigster
        "procedure": "http://externalURI.com",
        # TODO: get from http://cloud.neii.gov.au/neii/neii-observation-method/version-1/concept
        "observationMethod": "inSituOceanBasedPlatforms",
        "dataAvailabilityStatus": "available-online",
        "samplingRegime": "adhoc",
        "firstObservationDate": "2015-05-14"
    }
