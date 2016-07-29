#!/usr/bin/env python

import requests
import sys
import json
from datetime import date, timedelta

#Your PagerDuty API key.  A read-only key will work for this.
AUTH_TOKEN = 'YQstXoCv5Jsib56A6zeu'
#The API base url, make sure to include the subdomain
BASE_URL = 'https://pdt-ryan.pagerduty.com/api/v1'
#The service ID that you would like to query.  You can leave this blank to query all services.
service_id = ""
#The start date that you would like to search.  It's currently setup to start yesterday.
yesterday = date.today() - timedelta(1)
since = yesterday.strftime('%Y-%m-%d')
#The end date that you would like to search.
until = date.today().strftime('%Y-%m-%d')

HEADERS = {
    'Authorization': 'Token token={0}'.format(AUTH_TOKEN),
    'Content-type': 'application/json',
}

def get_incidents(since, until, service_id=None):
    print "since",since
    print "until",until
    file_name = 'pagerduty_export'

    params = {
        'service':service_id,
        'since':since,
        'until':until
    }

    all_incidents = requests.get(
        '{0}/incidents'.format(BASE_URL),
        headers=HEADERS,
        data=json.dumps(params)
    )

    print >>sys.stderr, "Exporting incident data to " + file_name + since
    for incident in all_incidents.json()['incidents']:
        get_incident_details(incident["id"], str(incident["incident_number"]), incident["service"]["name"], file_name+since+".csv")
    print >>sys.stderr, "Exporting has completed successfully."

def get_incident_details(incident_id, incident_number, service, file_name):
    start_time = ""
    end_time = ""
    summary = ""
    facility = ""
    environment = ""
    owners = ""
    output = incident_number + "," + service.rstrip() + ","

    f = open(file_name,'a')

    log_entries = requests.get(
        '{0}/incidents/{1}/log_entries?include[]=channel'.format(BASE_URL,incident_id),
        headers=HEADERS
    )

    for log_entry in log_entries.json()['log_entries']:
        if log_entry["type"] == "trigger":
            if log_entry["created_at"] > start_time:
                start_time = log_entry["created_at"]
                if ("summary" in log_entry["channel"]):
                    summary = log_entry["channel"]["summary"]
                if ("details" in log_entry["channel"]):
                    details = log_entry["channel"]["details"]
                    if("check" in details):
                        check = details["check"]
                        # Override summary with the output from the check only
                        if ("output" in check):
                            summary = check["output"] 
                    if ("client" in details):
                        client = details["client"]
                        if ("facility" in client):
                            facility = client["facility"]
                        if ("environment" in client):
                            environment = client["environment"]
                        if ("owners" in client):
                            owners = client["owners"]

        elif log_entry["type"] == "resolve":
            end_time = log_entry["created_at"]

    output += start_time + ","
    output += end_time
    output += ",\"" + summary.rstrip() + "\""
    output += ",\"" + str(facility) + "\""
    output += ",\"" + str(environment) + "\""
    output += ",\"" + str(owners) + "\""
    output += ",\"" + str(details) + "\""
    output += "\n"
    print output
    f.write(output)

get_incidents(since = since, until = until, service_id = service_id)